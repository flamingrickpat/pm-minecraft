from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar, Literal
from uuid import uuid4

import requests
from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from mcp.types import ImageContent, TextContent
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ._runtime import ensure_node_runtime, node_executable
from .standalone_support import atomic_write_bytes, read_readable_yaml, readable_yaml_bytes

PACKAGE_DIR = Path(__file__).resolve().parents[1]
MCP_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = MCP_DIR / "templates"
RUNNER_PATH = MCP_DIR / "ts_runner.ts"
COLLECT_BLOCKS_PRIMITIVE = MCP_DIR / "primitives" / "collect_blocks.ts"
SDK_PATH = MCP_DIR / "sdk" / "minecraft.ts"
# The body and every skill run inside the Node runtime resolved by
# pm_minecraft_mcp._runtime.ensure_node_runtime(): the repository root in a
# source checkout, or a per-environment bootstrapped directory in an
# installed wheel. Children are attached to their parent through stdin pipes
# (see BodySupervisor) and are never detached into their own process group.
BODY_STDIN_LIFECYCLE_ENV = "MINECRAFT_STDIN_LIFECYCLE"
MAX_TYPESCRIPT_TIMEOUT_SECONDS = 90.0
DEFAULT_SKILL_TIMEOUT_SECONDS = MAX_TYPESCRIPT_TIMEOUT_SECONDS
# Caps on the model-visible state. The full snapshot stays on disk under
# artifacts/minecraft/state; these bound what every tool result has to carry.
COMPACT_NEARBY_BLOCK_KINDS = 12
COMPACT_NEARBY_ENTITIES = 8
COMPACT_FRONTIER_WAYPOINTS = 4
MATERIAL_ACTIONS = frozenset(
    {
        "collect_blocks",
        "craft_item",
        "execute_typescript",
        "fine_control",
        "find_block",
        "mine_block",
        "pillar_up",
        "place_block",
        "smelt",
        "walk_to",
    }
)
MATERIAL_NO_GAIN_REASSESSMENT_THRESHOLD = 2
# The anti-stall circuit breaker is OFF by default and only armed when the
# operator passes --enable-anti-stall-guard. It was a relic of older, weaker
# models that retried identical no-gain operations in a loop; modern agents
# stall for unrelated reasons and the guard keyed to a single "relevant item"
# wrongly blocked unrelated skill ops (see playtest findings 2b).
DEFAULT_ANTI_STALL_GUARD = False
# mine_block relaxes its head-line-of-sight gate for targets this close so a
# bot can tunnel forward from a 1-wide shaft without first mining the head
# cell (playtest finding 2c).
DEFAULT_MINE_VISIBILITY_IGNORE_DISTANCE = 3.0
# walk_to is deliberately capped at one chunk (16 blocks) so a failed call is
# cheap to diagnose; longer routes are split into hops by the caller.
DEFAULT_WALK_TO_MAX_DISTANCE = 512.0
MATERIAL_ATTEMPT_FAILURE_REASONS = frozenset(
    {
        "dig_failed",
        "unharvestable",
        "place_failed",
        "place_unverified",
        "pillar_up_failed",
    }
)


def material_action_key(
    action: str,
    parameters: dict[str, Any],
) -> str:
    """Return the identity used to count repeated no-progress attempts.

    The circuit breaker applies to an identical material operation, not every
    invocation of a tool.  A new target or other argument is a new attempt and
    must therefore begin with its own no-gain count.
    """
    if action not in MATERIAL_ACTIONS:
        return action
    serialized_parameters = json.dumps(
        parameters,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"{action}\x1f{serialized_parameters}"


def material_action_name(action_key: str) -> str:
    """Extract the user-facing tool name from a material attempt key."""
    return action_key.partition("\x1f")[0]


def navigation_cell(
    position: dict[str, Any],
) -> tuple[int, int, int] | None:
    if not all(
        isinstance(position.get(axis), (int, float))
        for axis in ("x", "y", "z")
    ):
        return None
    return (
        int(float(position["x"]) // 3),
        int(float(position["y"]) // 1),
        int(float(position["z"]) // 3),
    )


def typescript_runner_command(
    skill_path: Path,
    input_path: Path,
    result_path: Path,
) -> list[str]:
    arguments = [
        str(RUNNER_PATH),
        "--skill",
        str(skill_path),
        "--input",
        str(input_path),
        "--result",
        str(result_path),
    ]
    node = node_executable()
    loader = tsx_loader_arguments(ensure_node_runtime())
    return [node, *loader, *arguments]


def tsx_loader_arguments(runtime_dir: Path) -> list[str]:
    """Node flags that load the tsx TypeScript loader in-process.

    The ``tsx`` CLI wrapper spawns a second process, which would break the
    stdin-pipe lifecycle contract; passing the loader flags to node directly
    keeps exactly one PID per runner.
    """
    tsx_dist = runtime_dir / "node_modules" / "tsx" / "dist"
    preflight = tsx_dist / "preflight.cjs"
    loader = tsx_dist / "loader.mjs"
    if not preflight.is_file() or not loader.is_file():
        raise FileNotFoundError(f"tsx loader not found under {tsx_dist}")
    return ["--require", str(preflight), "--import", loader.as_uri()]


def body_entry_command(runtime_dir: Path) -> list[str]:
    """Command that starts the Minecraft body as a single Node process.

    The TypeScript entry runs through the tsx loader directly (no tsx CLI
    wrapper and no npm), so the stdin lifecycle pipe from the supervisor
    controls exactly one PID. In a source checkout ``runtime_dir`` is the
    repository root; in an installed wheel it is the bootstrapped directory.
    """
    node = node_executable()
    entry = runtime_dir / "src" / "main.ts"
    if not entry.is_file():
        raise FileNotFoundError(f"Minecraft body entry not found: {entry}")
    return [node, *tsx_loader_arguments(runtime_dir), str(entry)]


def tcp_reachable(host: str, port: int, timeout_seconds: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def local_port_available(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", port))
            return True
    except OSError:
        return False


def check_prerequisites(config: ServerConfig, external_body: bool = False) -> None:
    """Fail fast with a specific error before anything is spawned.

    Mirrors the standalone launcher checks: initialized agent home, a
    reachable Minecraft server, free local service ports, and a Node.js
    executable on PATH. With ``external_body=True`` the web port is expected
    to belong to an already-running body, so only the viewer and MCP ports
    are required to be free.
    """
    AgentHome(config).validate()
    if not tcp_reachable(config.minecraft_host, config.minecraft_port):
        raise RuntimeError(
            f"Minecraft server is not reachable at "
            f"{config.minecraft_host}:{config.minecraft_port}"
        )
    ports = (config.viewer_port, config.mcp_port)
    if not external_body:
        ports = (config.web_port, *ports)
    for port in ports:
        if not local_port_available(port):
            raise RuntimeError(
                f"Local service port {port} is already owned by another process"
            )
    node_executable()


def drafts_source_dir() -> Path:
    packaged = MCP_DIR / "drafts"
    if packaged.is_dir() and any(packaged.glob("*.ts")):
        return packaged
    repository = PACKAGE_DIR / "deploy" / "drafts"
    if repository.is_dir() and any(repository.glob("*.ts")):
        return repository
    raise FileNotFoundError(
        f"Example drafts not found (looked in {packaged} and {repository})"
    )


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def write_readable_yaml(path: Path, value: Any) -> None:
    atomic_write_bytes(path, readable_yaml_bytes(without_image_bytes(value)))


def relative_workspace_paths(value: Any, workspace: Path) -> Any:
    if isinstance(value, dict):
        return {
            key: relative_workspace_paths(item, workspace)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [relative_workspace_paths(item, workspace) for item in value]
    if isinstance(value, str):
        candidate = Path(value)
        if candidate.is_absolute():
            try:
                return candidate.resolve().relative_to(
                    workspace.resolve()
                ).as_posix()
            except ValueError:
                return value
    return value


def slug(value: str) -> str:
    rendered = "".join(
        character if character.isalnum() or character in "-_" else "_" for character in value
    )
    if not rendered:
        raise ValueError("username must contain at least one filename-safe character")
    return rendered


class EventNotifications(BaseModel):
    """Which body-state changes become report-event inbox messages.

    The MCP polls/diffs the body and emits one pm.inbox.v1 report-event per
    real change. No change, no emission. Everything downstream of the inbox
    file is decided by agents, not by this configuration.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = True
    poll_seconds: float = Field(default=5.0, ge=1.0)
    death: bool = True
    respawn: bool = True
    disconnect: bool = True
    chat: bool = True
    sun_cycle: bool = True
    oxygen: bool = True
    damage_min_hearts: float = Field(default=1.0, ge=0.0)
    hunger_min_points: float = Field(default=2.0, ge=0.0)


class ServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    minecraft_host: str
    minecraft_port: int = Field(ge=1, le=65535)
    username: str
    agent_home: Path
    artifact_root: Path
    web_host: str
    web_port: int = Field(ge=1, le=65535)
    viewer_port: int = Field(ge=1, le=65535)
    mcp_host: str
    mcp_port: int = Field(ge=1, le=65535)
    startup_timeout_seconds: float = Field(gt=0)
    capture_images: bool
    max_skill_characters: int = Field(ge=1)
    viewer_scale: int = Field(ge=1)
    viewer_fov: int = Field(ge=1)
    view_distance: int = Field(ge=1)
    anti_stall_guard: bool = False
    mine_visibility_ignore_distance: float = Field(default=3.0, ge=0)
    walk_to_max_distance: float = Field(default=16.0, gt=0)
    skill_timeout_seconds: float = Field(default=90.0, ge=1)
    event_notifications: EventNotifications = Field(
        default_factory=EventNotifications
    )

    @model_validator(mode="after")
    def validate_instance_binding(self) -> ServerConfig:
        if not re.fullmatch(r"[A-Za-z0-9_]{1,16}", self.username):
            raise ValueError("Minecraft username must contain 1-16 letters, digits, or underscores")
        ports = {
            self.minecraft_port,
            self.web_port,
            self.viewer_port,
            self.mcp_port,
        }
        if len(ports) != 4:
            raise ValueError("Minecraft, body, viewer, and MCP ports must be distinct")
        return self

    @property
    def body_url(self) -> str:
        return f"http://{self.web_host}:{self.web_port}"

    @property
    def mcp_url(self) -> str:
        return f"http://{self.mcp_host}:{self.mcp_port}/mcp"

    @property
    def player_log_dir(self) -> Path:
        """Compatibility alias for the instance-owned artifact directory."""
        return self.artifact_root


class PositionTarget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    x: float
    y: float
    z: float


class MaterialProgressSignal(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )

    schema_name: Literal["cog.material-progress-signal.v1"] = Field(
        default="cog.material-progress-signal.v1",
        serialization_alias="schema",
    )
    kind: Literal[
        "material_inventory_changed",
        "relevant_state_changed",
        "material_no_gain",
        "material_action_blocked",
    ]
    action: str = Field(min_length=1)
    consecutive_no_gain_count: int = Field(
        ge=0,
        serialization_alias="consecutiveNoGainCount",
    )
    same_action_no_gain_count: int = Field(
        ge=0,
        serialization_alias="sameActionNoGainCount",
    )
    inventory_changes: dict[str, int] = Field(
        serialization_alias="inventoryChanges",
    )
    relevant_inventory_items: list[str] = Field(
        serialization_alias="relevantInventoryItems",
    )
    requires_reassessment: bool = Field(
        serialization_alias="requiresReassessment",
    )


class PostconditionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal[
        "inventory_min",
        "inventory_delta_min",
        "y_min",
        "y_max",
        "health_min",
        "position_changed_min",
        "distance_max",
        "held_item",
        "entity_id_absent",
        "block_at",
    ] | None = None
    item: str | None = None
    count: int | None = None
    value: float | None = None
    target: PositionTarget | None = None
    block: PositionTarget | None = None
    entity_id: int | None = None
    all: list[PostconditionSpec] | None = None

    @model_validator(mode="after")
    def validate_shape(self) -> PostconditionSpec:
        if self.all is not None:
            if not self.all:
                raise ValueError("postcondition all must not be empty")
            if any(
                value is not None
                for value in (
                    self.kind,
                    self.item,
                    self.count,
                    self.value,
                    self.target,
                    self.block,
                    self.entity_id,
                )
            ):
                raise ValueError(
                    "composite postcondition accepts only all"
                )
            return self
        if self.kind in {"inventory_min", "inventory_delta_min"}:
            if (
                not self.item
                or self.count is None
                or self.count < 0
            ):
                raise ValueError(
                    f"{self.kind} requires item and non-negative count"
                )
            return self
        if self.kind in {
            "y_min",
            "y_max",
            "health_min",
            "position_changed_min",
        }:
            if self.value is None:
                raise ValueError(f"{self.kind} requires value")
            return self
        if self.kind == "distance_max":
            if self.target is None or self.value is None:
                raise ValueError(
                    "distance_max requires target and value"
                )
            return self
        if self.kind == "held_item":
            if not self.item:
                raise ValueError("held_item requires item")
            return self
        if self.kind == "entity_id_absent":
            if self.entity_id is None or self.entity_id < 0:
                raise ValueError("entity_id_absent requires a non-negative entity_id")
            return self
        if self.kind == "block_at":
            if self.block is None or not self.item:
                raise ValueError("block_at requires block and item")
            if any(
                float(value) != int(value)
                for value in (self.block.x, self.block.y, self.block.z)
            ):
                raise ValueError("block_at coordinates must be integers")
            return self
        raise ValueError("postcondition requires kind or all")

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class BodyHttpError(RuntimeError):
    def __init__(self, method: str, path: str, status: int, payload: Any) -> None:
        super().__init__(
            f"Minecraft body {method} {path} returned HTTP {status}: {json.dumps(payload, ensure_ascii=False)}"
        )
        self.method = method
        self.path = path
        self.status = status
        self.payload = payload


class MinecraftBodyUnavailableError(RuntimeError):
    """The body runtime answered, but no live player observation exists.

    Typical causes: the bot is not connected to the Minecraft server, or it
    died and has not spawned again yet. The observation endpoint returns an
    error envelope instead of a player observation in that state.
    """

    def __init__(self, message: str, payload: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.payload = payload or {}


class TeeTextStream:
    def __init__(self, terminal: Any, log_stream: Any) -> None:
        self.terminal = terminal
        self.log_stream = log_stream
        self.lock = threading.Lock()
        self.encoding = terminal.encoding
        self.errors = terminal.errors

    def write(self, value: str) -> int:
        with self.lock:
            terminal_result = self.terminal.write(value)
            self.log_stream.write(value)
            return terminal_result

    def flush(self) -> None:
        with self.lock:
            self.terminal.flush()
            self.log_stream.flush()

    def isatty(self) -> bool:
        return self.terminal.isatty()

    def fileno(self) -> int:
        return self.terminal.fileno()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.terminal, name)


class BodyApi:
    ACTION_ROUTES: ClassVar[dict[str, tuple[str, str]]] = {
        "find_block": ("POST", "/api/world/find-block"),
        "walk_to": ("POST", "/api/command/walk-to"),
        "mine_block": ("POST", "/api/command/mine-block"),
        "place_block": ("POST", "/api/command/place-block"),
        "jump_place_block": ("POST", "/api/command/jump-place-block"),
        "pillar_up": ("POST", "/api/command/pillar-up"),
        "use_block": ("POST", "/api/command/use-block"),
        "attack_entity": ("POST", "/api/command/attack-entity"),
        "inspect": ("POST", "/api/command/inspect"),
        "rotate": ("POST", "/api/command/rotate"),
        "look_at": ("POST", "/api/command/look-at"),
        "fine_control": ("POST", "/api/command/fine-control"),
        "sync_orientation": ("POST", "/api/command/sync-orientation"),
        "stop": ("POST", "/api/command/stop"),
        "hotbar_select": ("POST", "/api/hotbar/select"),
        "inventory_select": ("POST", "/api/inventory/select"),
        "inventory_equip": ("POST", "/api/inventory/equip"),
        "open_inventory": ("POST", "/api/crafting/open-inventory"),
        "craft_item": ("POST", "/api/crafting/craft-item"),
        "open_crafting_table": ("POST", "/api/crafting/open-crafting-table"),
        "set_crafting_grid": ("POST", "/api/crafting/set-grid"),
        "take_crafting_output": ("POST", "/api/crafting/take-output"),
        "clear_crafting_grid": ("POST", "/api/crafting/clear-grid"),
        "close_crafting_window": ("POST", "/api/crafting/close-window"),
        "smelt": ("POST", "/api/furnace/smelt"),
        "resolve_pixel": ("POST", "/api/targeting/resolve-pixel"),
        "chat": ("POST", "/api/chat/send"),
    }

    ACTION_SCHEMAS: ClassVar[dict[str, dict[str, Any]]] = {
        "find_block": {
            "blockName": "string",
            "maxDistance": "positive integer",
            "requireVisible": "must be true; line-of-sight search is enforced",
        },
        "walk_to": {
            "target": {"x": "number", "y": "number", "z": "number"},
            "tolerance": "positive number",
            "profile": "adaptive|walk_only; adaptive preserves the existing destructive-capable pathfinder default",
        },
        "mine_block": {
            "block": {"x": "integer", "y": "integer", "z": "integer"},
            "walkIntoRange": "boolean",
        },
        "place_block": {
            "referenceBlock": {"x": "integer", "y": "integer", "z": "integer"},
            "face": {"x": "-1|0|1", "y": "-1|0|1", "z": "-1|0|1"},
            "walkIntoRange": "boolean",
        },
        "jump_place_block": {
            "referenceBlock": {"x": "integer", "y": "integer", "z": "integer"},
            "face": {"x": "-1|0|1", "y": "-1|0|1", "z": "-1|0|1"},
            "walkIntoRange": "boolean",
        },
        "pillar_up": {},
        "use_block": {
            "block": {"x": "integer", "y": "integer", "z": "integer"},
            "walkIntoRange": "boolean",
        },
        "attack_entity": {
            "entityId": "non-negative integer from a fresh observation",
            "walkIntoRange": "boolean",
        },
        "inspect": {"block": {"x": "integer", "y": "integer", "z": "integer"}},
        "rotate": {
            "yaw": "relative degrees; positive is right",
            "pitch": "relative degrees; positive is up",
        },
        "look_at": {"target": {"x": "number", "y": "number", "z": "number"}},
        "fine_control": {
            "controls": {"forward|back|left|right|jump|sprint|sneak": "boolean"},
            "durationMs": "1..3000",
            "visualCheckFrameId": "fresh frame id required by MCP",
        },
        "sync_orientation": {},
        "stop": {},
        "hotbar_select": {"hotbarIndex": "integer 0..8"},
        "inventory_select": {"slot": "inventory slot integer"},
        "inventory_equip": {"itemName": "exact Mineflayer item name"},
        "open_inventory": {},
        "craft_item": {
            "itemName": "exact Mineflayer item name",
            "repetitions": "positive integer recipe repetitions",
        },
        "open_crafting_table": {},
        "set_crafting_grid": {"grid": "4 or 9 entries; each null or {itemName,count}"},
        "take_crafting_output": {},
        "clear_crafting_grid": {},
        "close_crafting_window": {},
        "smelt": {
            "inputItemName": "string",
            "inputCount": "positive integer",
            "fuelItemName": "string",
            "fuelCount": "positive integer",
            "timeoutMs": "positive integer",
        },
        "resolve_pixel": {
            "frameId": "string",
            "x": "pixel x",
            "y": "pixel y",
            "maxDistance": "positive number",
        },
        "chat": {"text": "ordinary chat or informational command only"},
    }

    ACTION_ALIASES: ClassVar[dict[str, str]] = {
        "findBlock": "find_block",
        "walkTo": "walk_to",
        "mineBlock": "mine_block",
        "placeBlock": "place_block",
        "jumpPlaceBlock": "jump_place_block",
        "pillarUp": "pillar_up",
        "useBlock": "use_block",
        "attackEntity": "attack_entity",
        "lookAt": "look_at",
        "fineControl": "fine_control",
        "syncOrientation": "sync_orientation",
        "hotbarSelect": "hotbar_select",
        "inventorySelect": "inventory_select",
        "inventoryEquip": "inventory_equip",
        "openInventory": "open_inventory",
        "craftItem": "craft_item",
        "openCraftingTable": "open_crafting_table",
        "setCraftingGrid": "set_crafting_grid",
        "takeCraftingOutput": "take_crafting_output",
        "clearCraftingGrid": "clear_crafting_grid",
        "closeCraftingWindow": "close_crafting_window",
        "resolvePixel": "resolve_pixel",
    }

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        timeout_seconds: float = 30,
    ) -> dict[str, Any]:
        response = self.session.request(
            method, f"{self.base_url}{path}", json=body, timeout=timeout_seconds
        )
        payload = response.json()
        if response.status_code < 200 or response.status_code >= 300:
            if isinstance(payload, dict) and payload.get("ok") is False:
                payload["httpStatus"] = response.status_code
                return payload
            raise BodyHttpError(method, path, response.status_code, payload)
        if not isinstance(payload, dict):
            raise TypeError(f"Minecraft body {method} {path} returned a non-object JSON response")
        return payload

    def health(self) -> dict[str, Any]:
        return self.request("GET", "/api/health", timeout_seconds=5)

    def state(self) -> dict[str, Any]:
        return self.request("GET", "/api/state", timeout_seconds=5)

    def observe(self) -> dict[str, Any]:
        return self.request("GET", "/api/observation", timeout_seconds=10)

    def capture_frame(self) -> dict[str, Any]:
        return self.request("GET", "/api/frame/current", timeout_seconds=30)

    def call(
        self, action: str, parameters: dict[str, Any], timeout_seconds: float
    ) -> dict[str, Any]:
        action = self.ACTION_ALIASES.get(action, action)
        if action not in self.ACTION_ROUTES:
            raise ValueError(
                f"Unknown Minecraft action {action!r}. Available actions: {', '.join(sorted(self.ACTION_ROUTES))}"
            )
        method, path = self.ACTION_ROUTES[action]
        body = dict(parameters)
        if path.startswith("/api/command/") and action not in {"stop", "sync_orientation"}:
            body["timeoutMs"] = round(timeout_seconds * 1000)
        return self.request(method, path, body, timeout_seconds=timeout_seconds + 5)

    def stop_and_wait(self, timeout_seconds: float = 10) -> dict[str, Any]:
        stop_result = self.call("stop", {}, timeout_seconds=5)
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            state = self.state()
            if state.get("currentCommand") is None:
                return {"stop": stop_result, "idle": True, "state": state}
            time.sleep(0.1)
        state = self.state()
        raise TimeoutError(
            f"Mineflayer command queue did not become idle after stop: {json.dumps(state.get('currentCommand'))}"
        )

    def wait_until_idle(self, timeout_seconds: float = 10) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            state = self.state()
            if state.get("currentCommand") is None:
                return state
            time.sleep(0.1)
        state = self.state()
        raise TimeoutError(
            f"Mineflayer command queue remained active: {json.dumps(state.get('currentCommand'))}"
        )


class AgentHome:
    MEMORY_FILES: ClassVar[dict[str, str]] = {
        "world": "WORLD.md",
        "places": "PLACES.md",
        "routes": "ROUTES.md",
        "chests": "CHESTS.md",
        "failures": "FAILURES.md",
        "journal": "JOURNAL.md",
    }

    def __init__(self, config: ServerConfig) -> None:
        self.config = config
        self.root = config.agent_home
        self.memory_dir = self.root / "memory" / "minecraft"
        self.drafts_dir = self.root / "drafts"
        self.skills_dir = self.root / "skills"
        self.lib_dir = self.root / "lib"
        self.agent_skills_dir = self.root / "skills"

    def validate(self) -> None:
        required = [
            self.root / "AGENTS.md",
            self.root / ".mcp.json",
            self.root / "lib" / "minecraft.ts",
            self.memory_dir,
            self.drafts_dir,
            self.skills_dir,
        ]
        missing = [path for path in required if not path.exists()]
        if missing:
            rendered = ", ".join(str(path) for path in missing)
            raise FileNotFoundError(
                f"agent home was not initialized by this repository: {rendered}"
            )

    def write_character(self, observation: dict[str, Any]) -> None:
        if not isinstance(observation, dict) or not isinstance(
            observation.get("player"), dict
        ):
            raise ValueError(
                "write_character requires a live observation with a player "
                "section; got an error or disconnected payload instead"
            )
        player = observation["player"]
        world = observation["world"]
        inventory = observation["inventory"]
        surroundings = observation["surroundings"]
        items = (
            ", ".join(f"{item['name']} x {item['count']}" for item in inventory["items"]) or "empty"
        )
        nearby_blocks = (
            "\n".join(
                f"- {block['name']}: {block['count']} (nearest {json.dumps(block['nearest'])}, distance {block['distance']})"
                for block in surroundings["nearbyBlocks"][:20]
            )
            or "- none"
        )
        nearby_entities = (
            "\n".join(
                f"- {entity['name']} ({entity['kind']}) at {json.dumps(entity['position'])}, distance {entity['distance']}"
                for entity in surroundings["nearbyEntities"]
            )
            or "- none"
        )
        local_airspace = surroundings.get("localAirspace", {})
        horizontal_openings = local_airspace.get(
            "horizontalOpenings",
            [],
        )
        opening_lines = "\n".join(
            format_airspace_opening(opening) for opening in horizontal_openings
        ) or "- unavailable"
        text = f"""# Character: {self.config.username}

Automatically refreshed by the Minecraft MCP server after observations and actions.

- Captured: {observation["capturedAt"]}
- Position: {json.dumps(player["position"], ensure_ascii=False)}
- Block position: {json.dumps(player["blockPosition"], ensure_ascii=False)}
- Facing: {player["facing"]} (yaw {player["yawDegrees"]}, pitch {player["pitchDegrees"]})
- Dimension: {world["dimension"]}
- Biome: {world["biome"]}
- Health: {player["health"]}
- Food: {player["food"]}
- Oxygen: {player["oxygenLevel"]}
- Experience level: {player["experienceLevel"]}
- Held item: {json.dumps(inventory["heldItem"], ensure_ascii=False)}
- Armor: {json.dumps(inventory["armor"], ensure_ascii=False)}
- Empty inventory slots: {inventory["emptySlots"]}
- Inventory: {items}

## Nearby blocks

{nearby_blocks}

## Nearby entities

{nearby_entities}

## Local airspace

- Scan radius: {local_airspace.get("scanRadius", "unavailable")}
- Clear blocks above head: {local_airspace.get("clearanceBlocksAboveHead", "unavailable")}

{opening_lines}
"""
        (self.memory_dir / "CHARACTER.md").write_text(text, encoding="utf-8")

    def append_note(
        self,
        kind: Literal[
            "world",
            "places",
            "routes",
            "chests",
            "failures",
            "journal",
        ],
        markdown: str,
    ) -> Path:
        if not markdown.strip():
            raise ValueError("markdown note must not be blank")
        path = self.memory_dir / self.MEMORY_FILES[kind]
        with path.open("a", encoding="utf-8") as stream:
            stream.write(f"\n## {utc_now()}\n\n{markdown.rstrip()}\n")
        return path


def format_airspace_opening(opening: dict[str, Any]) -> str:
    """Render the explicit no-boundary state emitted by the body service."""
    boundary = opening["firstBlockedBy"]
    prefix = f"- {opening['direction']}: {opening['openBlocks']} open block(s); "
    if boundary is None:
        return prefix + "no boundary inside the scan radius"
    return prefix + f"first boundary feet={boundary['feet']}, head={boundary['head']}"


class BodySupervisor:
    def __init__(self, config: ServerConfig, api: BodyApi) -> None:
        self.config = config
        self.api = api
        self.process: subprocess.Popen[str] | None = None
        self.output_thread: threading.Thread | None = None
        self.log_stream: Any = None

    def start(self) -> dict[str, Any]:
        check_prerequisites(self.config)
        try:
            existing = self.api.health()
        except requests.RequestException:
            existing = None
        if existing is not None:
            raise RuntimeError(
                f"A Minecraft body service is already responding at {self.config.body_url}"
            )

        self.config.player_log_dir.mkdir(parents=True, exist_ok=True)
        body_log_path = self.config.player_log_dir / "body.log"
        self.log_stream = body_log_path.open("a", encoding="utf-8", buffering=1)
        env = os.environ.copy()
        env.update(
            {
                "MINECRAFT_HOST": self.config.minecraft_host,
                "MINECRAFT_PORT": str(self.config.minecraft_port),
                "MINECRAFT_USERNAME": self.config.username,
                "MINECRAFT_VIEW_DISTANCE": str(self.config.view_distance),
                "WEB_HOST": self.config.web_host,
                "WEB_PORT": str(self.config.web_port),
                "VIEWER_ENABLED": "true",
                "VIEWER_PORT": str(self.config.viewer_port),
                "VIEWER_FIRST_PERSON": "true",
                "VIEWER_VIEW_DISTANCE": str(self.config.view_distance),
                "VIEWER_DEVICE_SCALE_FACTOR": str(self.config.viewer_scale),
                "VIEWER_FOV_DEGREES": str(self.config.viewer_fov),
                "EVIDENCE_DIR": str(self.config.player_log_dir),
                "ACTION_LOG_ENABLED": "true",
                "ACTION_LOG_DIR": str(self.config.player_log_dir / "body-actions"),
                "MINECRAFT_BODY_LOG_DIR": str(self.config.player_log_dir),
                "MINECRAFT_MINE_VISIBILITY_IGNORE_DISTANCE": str(
                    self.config.mine_visibility_ignore_distance
                ),
                "MINECRAFT_WALK_TO_MAX_DISTANCE": str(
                    self.config.walk_to_max_distance
                ),
            }
        )
        runtime_dir = ensure_node_runtime()
        env["NODE_PATH"] = str(runtime_dir / "node_modules")
        env[BODY_STDIN_LIFECYCLE_ENV] = "1"
        command = body_entry_command(runtime_dir)
        self.process = subprocess.Popen(
            command,
            cwd=runtime_dir,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        self.output_thread = threading.Thread(target=self._copy_output, daemon=True)
        self.output_thread.start()

        deadline = time.monotonic() + self.config.startup_timeout_seconds
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(
                    f"Minecraft body exited with code {self.process.returncode}; inspect {body_log_path}"
                )
            try:
                health = self.api.health()
            except requests.RequestException:
                time.sleep(0.25)
                continue
            if health.get("ready") is True:
                return health
            last_error = health["mineflayer"]["lastError"]
            if last_error:
                raise RuntimeError(f"Mineflayer connection failed: {last_error}")
            time.sleep(0.25)
        raise TimeoutError(
            f"Minecraft body did not become ready in {self.config.startup_timeout_seconds}s; inspect {body_log_path}"
        )

    def _copy_output(self) -> None:
        if self.process is None or self.process.stdout is None or self.log_stream is None:
            raise RuntimeError("Body output copier started before process initialization")
        for line in self.process.stdout:
            self.log_stream.write(line)
            print(f"[minecraft-body] {line.rstrip()}", file=sys.stderr)

    def stop(self) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            with contextlib.suppress(OSError):
                self.process.stdin.close()
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.process.kill()
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired as error:
                    raise RuntimeError(
                        f"Minecraft body (pid {self.process.pid}) did not exit after "
                        "stdin EOF and a hard kill"
                    ) from error
        if self.output_thread is not None:
            self.output_thread.join(timeout=2)
        if self.log_stream is not None:
            self.log_stream.close()


class MinecraftMcpRuntime:
    def __init__(self, config: ServerConfig, api: BodyApi, home: AgentHome) -> None:
        self.config = config
        self.api = api
        self.home = home
        self.execution_dir = config.player_log_dir / "executions"
        self.execution_dir.mkdir(parents=True, exist_ok=True)
        self.run_status_path = config.player_log_dir / "run-status.json"
        self.skill_versions_path = config.player_log_dir / "skill-versions.json"
        self.skill_versions: dict[str, str] = (
            json.loads(self.skill_versions_path.read_text(encoding="utf-8"))
            if self.skill_versions_path.exists()
            else {}
        )
        if not self.run_status_path.exists():
            self._write_run_status("active", "fresh_character", {})
        self.recent_visual_frames: dict[str, float] = {}
        self.model_state_id = 0
        self.last_model_observation: dict[str, Any] | None = None
        self.material_no_gain_streak = 0
        self.material_no_gain_by_action: dict[str, int] = {}
        self.material_relevant_items_by_action: dict[str, list[str]] = {}
        self.visited_navigation_cells: set[tuple[int, int, int]] = set()
        self.no_frontier_recovery_walks: set[
            tuple[tuple[int, int, int], tuple[int, int, int]]
        ] = set()
        self.lock = asyncio.Lock()
        self.active_skill: asyncio.subprocess.Process | None = None
        self.active_skill_info: dict[str, Any] | None = None
        self.skill_timeout_seconds = float(config.skill_timeout_seconds)
        # Body event detection cursor (in-memory; baselined on first sight).
        self.event_cursor: dict[str, Any] | None = None
        self.last_activity = time.monotonic()

    def _reset_material_progress(self) -> None:
        self.material_no_gain_streak = 0
        self.material_no_gain_by_action.clear()
        self.material_relevant_items_by_action.clear()

    def _reset_action_progress(self, action: str) -> None:
        self.material_no_gain_streak = 0
        self.material_no_gain_by_action.pop(action, None)
        self.material_relevant_items_by_action.pop(action, None)

    def _material_action_blocked(self, action: str) -> bool:
        if not self.config.anti_stall_guard:
            return False
        return (
            material_action_name(action) in MATERIAL_ACTIONS
            and self.material_no_gain_by_action.get(action, 0)
            >= MATERIAL_NO_GAIN_REASSESSMENT_THRESHOLD
        )

    def _claim_no_frontier_recovery_walk(
        self,
        observation: dict[str, Any],
        parameters: dict[str, Any],
    ) -> bool:
        navigation = (
            observation.get("surroundings", {})
            .get("localAirspace", {})
            .get("navigationSummary", {})
        )
        if (
            not isinstance(navigation, dict)
            or navigation.get("frontierWaypoints") != []
        ):
            return False
        player = observation.get("player")
        target = parameters.get("target")
        if not isinstance(player, dict) or not isinstance(target, dict):
            return False
        origin_cell = navigation_cell(player.get("position"))
        target_cell = navigation_cell(target)
        if (
            origin_cell is None
            or target_cell is None
            or origin_cell == target_cell
        ):
            return False
        attempt = (origin_cell, target_cell)
        if attempt in self.no_frontier_recovery_walks:
            return False
        self.no_frontier_recovery_walks.add(attempt)
        # A recovery walk is only useful if the body must actually leave the
        # current cell.  The ordinary default tolerance can otherwise report a
        # nearby target as reached without moving at all.
        tolerance = parameters.get("tolerance", 1.5)
        if isinstance(tolerance, int | float):
            parameters["tolerance"] = min(float(tolerance), 0.25)
        else:
            parameters["tolerance"] = 0.25
        return True

    @staticmethod
    def _align_observed_navigation_waypoint(
        observation: dict[str, Any],
        parameters: dict[str, Any],
    ) -> bool:
        """Translate a published standable block cell into its world center."""
        navigation = (
            observation.get("surroundings", {})
            .get("localAirspace", {})
            .get("navigationSummary", {})
        )
        target = parameters.get("target")
        if not isinstance(navigation, dict) or not isinstance(target, dict):
            return False
        waypoints = [
            navigation.get("highestWaypoint"),
            navigation.get("maxClearanceWaypoint"),
            navigation.get("furthestWaypoint"),
        ]
        frontiers = navigation.get("frontierWaypoints")
        if isinstance(frontiers, list):
            waypoints.extend(frontiers)
        target_cell = navigation_cell(target)
        for waypoint in waypoints:
            if not isinstance(waypoint, dict):
                continue
            position = waypoint.get("position")
            if (
                not isinstance(position, dict)
                or navigation_cell(position) != target_cell
            ):
                continue
            try:
                exactly_published_cell = all(
                    float(target[axis]) == float(position[axis])
                    for axis in ("x", "y", "z")
                )
            except (KeyError, TypeError, ValueError):
                return False
            if not exactly_published_cell:
                continue
            parameters["target"] = {
                "x": float(position["x"]) + 0.5,
                "y": float(position["y"]),
                "z": float(position["z"]) + 0.5,
            }
            tolerance = parameters.get("tolerance", 1.5)
            if isinstance(tolerance, int | float):
                parameters["tolerance"] = min(float(tolerance), 0.25)
            else:
                parameters["tolerance"] = 0.25
            return True
        return False

    def _progress_signal(
        self,
        action_key: str,
        delta: dict[str, Any],
        *,
        progress_observed: bool | None = None,
        relevant_inventory_items: set[str] | None = None,
    ) -> dict[str, Any] | None:
        action = material_action_name(action_key)
        if action not in MATERIAL_ACTIONS:
            walked_to_new_material_context = (
                action == "walk_to"
                and position_distance(
                    delta["positionBefore"],
                    delta["positionAfter"],
                )
                >= 3
            )
            if walked_to_new_material_context:
                self._reset_material_progress()
            return None

        inventory_changes = delta["inventoryChanges"]
        relevant_items = sorted(relevant_inventory_items or set())
        if progress_observed is None:
            if action == "pillar_up":
                progress_observed = (
                    float(delta["positionAfter"]["y"])
                    >= float(delta["positionBefore"]["y"]) + 0.99
                    or any(change < 0 for change in inventory_changes.values())
                )
            elif action in {"fine_control", "walk_to"}:
                before_cell = navigation_cell(delta["positionBefore"])
                after_cell = navigation_cell(delta["positionAfter"])
                if before_cell is not None:
                    self.visited_navigation_cells.add(before_cell)
                moved = position_distance(
                    delta["positionBefore"],
                    delta["positionAfter"],
                ) >= 1
                progress_observed = (
                    moved
                    and after_cell is not None
                    and after_cell not in self.visited_navigation_cells
                )
                if moved and after_cell is not None:
                    self.visited_navigation_cells.add(after_cell)
            elif action == "place_block":
                progress_observed = any(
                    change < 0 for change in inventory_changes.values()
                )
            else:
                progress_observed = any(
                    change > 0 for change in inventory_changes.values()
                )
        if progress_observed:
            if action == "find_block":
                self._reset_action_progress(action_key)
            else:
                self._reset_material_progress()
            return MaterialProgressSignal(
                kind=(
                    "material_inventory_changed"
                    if inventory_changes
                    else "relevant_state_changed"
                ),
                action=action,
                consecutive_no_gain_count=0,
                same_action_no_gain_count=0,
                inventory_changes=inventory_changes,
                relevant_inventory_items=relevant_items,
                requires_reassessment=False,
            ).model_dump(mode="json", by_alias=True)

        self.material_no_gain_streak += 1
        same_action_count = (
            self.material_no_gain_by_action.get(action_key, 0) + 1
        )
        self.material_no_gain_by_action[action_key] = same_action_count
        self.material_relevant_items_by_action[action_key] = relevant_items
        return MaterialProgressSignal(
            kind="material_no_gain",
            action=action,
            consecutive_no_gain_count=self.material_no_gain_streak,
            same_action_no_gain_count=same_action_count,
            inventory_changes=inventory_changes,
            relevant_inventory_items=relevant_items,
            requires_reassessment=(
                self.config.anti_stall_guard
                and same_action_count
                >= MATERIAL_NO_GAIN_REASSESSMENT_THRESHOLD
            ),
        ).model_dump(mode="json", by_alias=True)

    def _blocked_progress_signal(self, action_key: str) -> dict[str, Any]:
        action = material_action_name(action_key)
        return MaterialProgressSignal(
            kind="material_action_blocked",
            action=action,
            consecutive_no_gain_count=self.material_no_gain_streak,
            same_action_no_gain_count=self.material_no_gain_by_action[
                action_key
            ],
            inventory_changes={},
            relevant_inventory_items=(
                self.material_relevant_items_by_action.get(action_key, [])
            ),
            requires_reassessment=True,
        ).model_dump(mode="json", by_alias=True)

    def run_status(self) -> dict[str, Any]:
        return json.loads(self.run_status_path.read_text(encoding="utf-8"))

    def _write_run_status(self, status: str, reason: str, details: dict[str, Any]) -> None:
        document = {
            "username": self.config.username,
            "status": status,
            "reason": reason,
            "details": details,
            "updatedAt": utc_now(),
            "survivalOnly": True,
        }
        self.run_status_path.write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    def retire_character(self, reason: str, details: dict[str, Any]) -> None:
        current = self.run_status()
        if current["status"] == "active":
            self._write_run_status("retired", reason, details)

    @staticmethod
    def _skill_digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def register_skill_version(self, skill_path: Path) -> None:
        key = str(skill_path)
        digest = self._skill_digest(skill_path)
        self.skill_versions[key] = digest
        self.skill_versions_path.write_text(
            json.dumps(self.skill_versions, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    @property
    def capability_catalog_path(self) -> Path:
        return self.home.skills_dir / "capabilities.json"

    def list_capabilities(self) -> dict[str, Any]:
        """List reusable character skills and their verified promotion evidence."""
        catalog: dict[str, Any] = {}
        if self.capability_catalog_path.is_file():
            try:
                loaded = json.loads(
                    self.capability_catalog_path.read_text(encoding="utf-8")
                )
                if isinstance(loaded, dict):
                    catalog = loaded
            except (OSError, json.JSONDecodeError):
                catalog = {}
        metadata_by_path = {
            str(item.get("path")): item
            for item in catalog.get("capabilities", [])
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        }
        capabilities = []
        for path in sorted(self.home.skills_dir.glob("*.ts")):
            relative = path.relative_to(self.home.root).as_posix()
            metadata = metadata_by_path.get(relative, {})
            digest = self._skill_digest(path)
            capabilities.append(
                {
                    "name": metadata.get("name") or path.stem,
                    "path": relative,
                    "description": metadata.get("description") or "",
                    "sha256": digest,
                    "verifiedExecutionId": metadata.get("verifiedExecutionId"),
                    "verifiedPostcondition": metadata.get("verifiedPostcondition"),
                    "promotedAt": metadata.get("promotedAt"),
                    "sourceTaskId": metadata.get("sourceTaskId"),
                    "versionExecuted": self.skill_versions.get(str(path)) == digest,
                }
            )
        return {
            "schema": "pm.minecraft-capabilities.v1",
            "skillsDirectory": str(self.home.skills_dir),
            "count": len(capabilities),
            "capabilities": capabilities,
        }

    def promote_skill(
        self,
        *,
        draft_path: str,
        name: str,
        description: str,
        execution_id: str,
        source_task_id: str | None = None,
        replace: bool = False,
    ) -> dict[str, Any]:
        """Promote one draft only when a matching execution passed its postcondition."""
        if not re.fullmatch(r"[a-z][a-z0-9_-]{1,63}", name):
            raise ValueError(
                "name must use 2-64 lowercase letters, digits, hyphens, or underscores"
            )
        rendered_description = description.strip()
        if not rendered_description or len(rendered_description) > 500:
            raise ValueError("description must contain 1-500 characters")
        if not re.fullmatch(r"exec-[a-f0-9]{12}", execution_id):
            raise ValueError("execution_id must be an MCP TypeScript execution id")

        source = Path(draft_path).expanduser()
        if not source.is_absolute():
            source = self.home.root / source
        source = source.resolve()
        drafts_root = self.home.drafts_dir.resolve()
        try:
            source.relative_to(drafts_root)
        except ValueError as exc:
            raise ValueError("draft_path must be inside this character's drafts directory") from exc
        if not source.is_file() or source.suffix.lower() not in {".ts", ".mts", ".cts"}:
            raise FileNotFoundError(source)

        run_dir = self.execution_dir / execution_id
        input_path = run_dir / "input.yaml"
        result_path = run_dir / "result.yaml"
        if not input_path.is_file() or not result_path.is_file():
            raise ValueError("execution evidence is missing")
        execution_input = read_readable_yaml(input_path)
        execution_result = read_readable_yaml(result_path)
        if not isinstance(execution_input, dict) or not isinstance(execution_result, dict):
            raise ValueError("execution evidence is invalid")
        recorded_path = Path(str(execution_input.get("skill_path") or ""))
        if not recorded_path.is_absolute():
            recorded_path = self.home.root / recorded_path
        recorded_digest = str(execution_input.get("skill_sha256") or "")
        digest = self._skill_digest(source)
        if recorded_path.resolve() != source or recorded_digest != digest:
            raise ValueError("the draft changed after the named execution")
        verification = execution_result.get("verification")
        if (
            execution_result.get("ok") is not True
            or execution_result.get("status") != "succeeded"
            or not isinstance(verification, dict)
            or verification.get("ok") is not True
        ):
            raise ValueError("the named execution did not pass its postcondition")

        existing: list[dict[str, Any]] = []
        if self.capability_catalog_path.is_file():
            try:
                current_catalog = json.loads(
                    self.capability_catalog_path.read_text(encoding="utf-8")
                )
                if isinstance(current_catalog, dict) and isinstance(
                    current_catalog.get("capabilities"), list
                ):
                    existing = [
                        item
                        for item in current_catalog["capabilities"]
                        if isinstance(item, dict)
                    ]
            except (OSError, json.JSONDecodeError):
                existing = []
        same_name = next(
            (item for item in existing if item.get("name") == name), None
        )
        if same_name is not None and not replace:
            raise FileExistsError(
                f"capability already exists: {name}; pass replace=true to revise it"
            )
        destination = (self.home.skills_dir / f"{name}{source.suffix.lower()}").resolve()
        if destination.exists() and not replace:
            raise FileExistsError(
                f"capability already exists: {destination.name}; pass replace=true to revise it"
            )
        shutil.copy2(source, destination)
        entry = {
            "name": name,
            "path": destination.relative_to(self.home.root).as_posix(),
            "description": rendered_description,
            "sha256": digest,
            "sourceDraft": source.relative_to(self.home.root).as_posix(),
            "verifiedExecutionId": execution_id,
            "verifiedPostcondition": execution_input.get("postcondition"),
            "promotedAt": utc_now(),
            "sourceTaskId": source_task_id,
        }
        if replace and same_name is not None:
            old_relative = same_name.get("path")
            if isinstance(old_relative, str):
                old_path = (self.home.root / old_relative).resolve()
                try:
                    old_path.relative_to(self.home.skills_dir.resolve())
                except ValueError:
                    old_path = destination
                if old_path != destination and old_path.is_file():
                    old_path.unlink()
        rows = [
            item
            for item in existing
            if isinstance(item, dict) and item.get("name") != name
        ]
        rows.append(entry)
        rows.sort(key=lambda item: str(item.get("name") or ""))
        atomic_write_bytes(
            self.capability_catalog_path,
            (
                json.dumps(
                    {
                        "schema": "pm.minecraft-capabilities.v1",
                        "capabilities": rows,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n"
            ).encode("utf-8"),
        )
        return entry

    def set_skill_timeout(self, seconds: float, minimum: float = 1.0, maximum: float = 3600.0) -> float:
        if (
            isinstance(seconds, bool)
            or not isinstance(seconds, (int, float))
            or seconds < minimum
            or seconds > maximum
        ):
            raise ValueError(
                f"skill timeout must be a number within {minimum:g}..{maximum:g} seconds"
            )
        self.skill_timeout_seconds = float(seconds)
        return self.skill_timeout_seconds

    def assert_character_active(self) -> None:
        status = self.run_status()
        if status["status"] != "active":
            raise RuntimeError(
                f"Minecraft character {self.config.username} is retired ({status['reason']}). "
                "Preserve its logs and restart with the next fresh username."
            )

    def inspect_survival_provenance(self, observation: dict[str, Any]) -> None:
        game_mode = observation.get("player", {}).get("gameMode")
        if game_mode is not None and game_mode != "survival":
            self.retire_character(
                "non_survival_game_mode",
                {"observedGameMode": game_mode, "capturedAt": observation.get("capturedAt")},
            )

    def _body_unavailable_reason(
        self, observation: dict[str, Any]
    ) -> str:
        """Build one diagnostic line for a missing live observation."""
        reason = str(
            observation.get("message")
            or observation.get("error")
            or "observation unavailable"
        )
        details: list[str] = []
        try:
            state = self.api.state()
            details.append(f"connected={state.get('connected')}")
        except Exception:
            details.append("state endpoint unreachable")
        try:
            health = self.api.health()
            mineflayer = health.get("mineflayer") if isinstance(health, dict) else None
            if isinstance(mineflayer, dict):
                details.append(f"spawned={mineflayer.get('spawned')}")
                details.append(f"deathCount={mineflayer.get('deathCount')}")
                if mineflayer.get("lastDeathAt"):
                    details.append(f"lastDeathAt={mineflayer['lastDeathAt']}")
        except Exception:
            details.append("health endpoint unreachable")
        return (
            f"Minecraft body '{self.config.username}' cannot observe right "
            f"now: {reason} ({'; '.join(details) if details else 'no diagnostics'}). "
            "The body must be connected to the server and spawned before "
            "observations or actions can run. This is an environment state, "
            "not a script defect; do not repair drafts because of it."
        )

    def _snapshot_sync(self, include_image: bool | None = None) -> dict[str, Any]:
        self.last_activity = time.monotonic()
        observation = self.api.observe()
        if not isinstance(observation, dict) or not isinstance(
            observation.get("player"), dict
        ):
            # The body answered, but no live player exists (disconnected or
            # dead before respawn). Fail with diagnostics instead of crashing
            # on missing observation sections.
            raise MinecraftBodyUnavailableError(
                self._body_unavailable_reason(observation), observation
            )
        self.inspect_survival_provenance(observation)
        self.home.write_character(observation)
        # A screenshot is captured (and written to artifacts/.../screenshots)
        # for every state, regardless of include_image, so there is a
        # complete on-disk visual history to fall back on later. include_image
        # only controls whether the pixel bytes are also attached to this
        # tool call's response - the disk write always happens.
        frame = self.api.capture_frame() if self.config.capture_images else None
        want_image_in_response = include_image is not False
        if isinstance(frame, dict) and frame.get("ok") is not False and not want_image_in_response:
            frame = {key: value for key, value in frame.items() if key != "pngBase64"}
        frame_id = frame_identifier(frame)
        if frame_id is not None:
            self.recent_visual_frames[frame_id] = time.monotonic()
            self.recent_visual_frames = {
                key: captured
                for key, captured in self.recent_visual_frames.items()
                if time.monotonic() - captured <= 60
            }
        state_id = f"mcstate-{uuid4().hex[:12]}"
        captured = str(observation.get("capturedAt", utc_now()))
        timestamp = re.sub(r"[^0-9A-Za-z_-]", "-", captured)
        state_record = {
            "schema": "cog.minecraft-state.v1",
            "state_id": state_id,
            "captured_at": captured,
            "username": self.config.username,
            "observation": observation,
            "screenshot": relative_workspace_paths(
                screenshot_reference(frame),
                self.home.root,
            ),
        }
        state_path = self.config.player_log_dir / "state" / f"{timestamp}-{state_id}.yaml"
        write_readable_yaml(state_path, state_record)
        write_readable_yaml(
            self.config.player_log_dir / "current_state.yaml",
            state_record,
        )
        self._detect_and_emit_body_events(
            observation, state_record, frame, state_path
        )
        return {
            "observation": observation,
            "frame": frame,
            "stateId": state_id,
            "stateRef": state_path.relative_to(self.home.root).as_posix(),
        }

    async def snapshot(self, include_image: bool | None = None) -> dict[str, Any]:
        return await asyncio.to_thread(self._snapshot_sync, include_image)

    # -- body event detection ------------------------------------------------ #
    #
    # Every snapshot (tool-driven or idle-poll-driven) diffs the body state
    # against the previous sighting. A real value change becomes one
    # pm.inbox.v1 report-event file in agent-home/ingress/inbox/new/. No
    # change means no emission at all. What an event *means* is decided
    # downstream by agents; the MCP only senses and reports.

    @staticmethod
    def _event_cursor_from(
        mineflayer: dict[str, Any], observation: dict[str, Any]
    ) -> dict[str, Any]:
        player = observation.get("player") if isinstance(observation.get("player"), dict) else {}
        world = observation.get("world") if isinstance(observation.get("world"), dict) else {}
        chat = observation.get("chat") if isinstance(observation.get("chat"), dict) else {}
        messages = chat.get("messages") if isinstance(chat.get("messages"), list) else []
        return {
            "deaths": int(mineflayer.get("deathCount") or 0),
            "spawns": int(mineflayer.get("spawnCount") or 0),
            "connected": bool(mineflayer.get("connected")),
            "health": player.get("health"),
            "food": player.get("food"),
            "oxygen": player.get("oxygenLevel"),
            "is_day": world.get("isDay"),
            "chat_ids": {
                str(message.get("id"))
                for message in messages
                if isinstance(message, dict) and message.get("id")
            },
        }

    def _detect_and_emit_body_events(
        self,
        observation: dict[str, Any],
        state_record: dict[str, Any] | None = None,
        frame: dict[str, Any] | None = None,
        state_path: Path | None = None,
    ) -> None:
        settings = self.config.event_notifications
        health = self.api.health()
        mineflayer = health.get("mineflayer") if isinstance(health, dict) else {}
        mineflayer = mineflayer if isinstance(mineflayer, dict) else {}
        cursor = self.event_cursor
        fresh = self._event_cursor_from(mineflayer, observation)
        self.event_cursor = fresh
        if not settings.enabled or cursor is None:
            return
        username = self.config.username
        events: list[dict[str, Any]] = []
        if settings.death:
            for _ in range(max(0, fresh["deaths"] - cursor["deaths"])):
                events.append({
                    "event": "death",
                    "intent": f"{username} died in Minecraft.",
                    "detail": {
                        "deathCount": fresh["deaths"],
                        "lastDeathAt": mineflayer.get("lastDeathAt"),
                    },
                })
        if settings.respawn and fresh["spawns"] > cursor["spawns"]:
            player = observation.get("player") or {}
            events.append({
                "event": "respawn",
                "intent": f"{username} respawned in Minecraft.",
                "detail": {
                    "spawnCount": fresh["spawns"],
                    "position": player.get("position"),
                },
            })
        gauge_events = [
            ("health", "damage", settings.damage_min_hearts * 2,
             lambda before, after: (
                 f"{username} took damage in Minecraft: health "
                 f"{before} -> {after} of 20."
             )),
            ("food", "hunger", settings.hunger_min_points,
             lambda before, after: (
                 f"{username} grew hungrier in Minecraft: food "
                 f"{before} -> {after} of 20."
             )),
        ]
        if settings.oxygen:
            gauge_events.append(
                ("oxygen", "losing_air", 1,
                 lambda before, after: (
                     f"{username} is running out of air in Minecraft: "
                     f"oxygen {before} -> {after} of 20."
                 ))
            )
        for key, event_type, threshold, intent_for in gauge_events:
            previous, current = cursor.get(key), fresh.get(key)
            if (
                isinstance(previous, (int, float))
                and isinstance(current, (int, float))
                and previous - current >= threshold
            ):
                events.append({
                    "event": event_type,
                    "intent": intent_for(previous, current),
                    "detail": {"before": previous, "after": current},
                })
        if (
            settings.sun_cycle
            and isinstance(cursor.get("is_day"), bool)
            and isinstance(fresh.get("is_day"), bool)
            and cursor["is_day"] != fresh["is_day"]
        ):
            if fresh["is_day"]:
                events.append({
                    "event": "sunrise",
                    "intent": f"The sun rises in {username}'s Minecraft world.",
                    "detail": {"timeOfDay": (observation.get("world") or {}).get("timeOfDay")},
                })
            else:
                events.append({
                    "event": "sunset",
                    "intent": (
                        f"Night falls in {username}'s Minecraft world; time "
                        "to get to safety."
                    ),
                    "detail": {"timeOfDay": (observation.get("world") or {}).get("timeOfDay")},
                })
        if settings.chat:
            chat = observation.get("chat") if isinstance(observation.get("chat"), dict) else {}
            messages = chat.get("messages") if isinstance(chat.get("messages"), list) else []
            fresh_messages = [
                message
                for message in messages
                if isinstance(message, dict)
                and str(message.get("id") or "") not in cursor["chat_ids"]
            ]
            fresh_messages.sort(key=lambda message: str(message.get("receivedAt") or ""))
            for message in fresh_messages:
                text = str(message.get("text") or "").strip()
                events.append({
                    "event": "chat_message",
                    "intent": (
                        f"Someone spoke in {username}'s Minecraft world: "
                        f"{text[:300]}"
                    ),
                    "detail": {
                        "messageId": message.get("id"),
                        "text": text,
                        "position": message.get("position"),
                        "receivedAt": message.get("receivedAt"),
                    },
                })
        for event in events:
            self._emit_body_episode(event, state_record, frame, state_path)

    def _emit_body_episode(
        self,
        event: dict[str, Any],
        state_record: dict[str, Any] | None,
        frame: dict[str, Any] | None = None,
        state_path: Path | None = None,
    ) -> None:
        """Write one report-event inbox file for one detected body event."""
        inbox_new = self.config.agent_home / "ingress" / "inbox" / "new"
        inbox_new.mkdir(parents=True, exist_ok=True)
        identifier = f"inbox-{uuid4().hex}"
        screenshot_rel: str | None = None
        state_ref: str | None = None
        state_id: str | None = None
        excerpt: dict[str, Any] = {}
        if isinstance(state_record, dict):
            observation = state_record.get("observation") or {}
            player = observation.get("player") if isinstance(observation.get("player"), dict) else {}
            world = observation.get("world") if isinstance(observation.get("world"), dict) else {}
            excerpt = {
                "position": player.get("position"),
                "dimension": world.get("dimension"),
                "biome": world.get("biome"),
                "health": player.get("health"),
                "food": player.get("food"),
                "isDay": world.get("isDay"),
            }
            state_id = state_record.get("state_id")
            shot = state_record.get("screenshot")
            if isinstance(shot, dict) and isinstance(shot.get("pngPath"), str):
                screenshot_rel = shot["pngPath"]
        if state_path is not None:
            state_ref = state_path.relative_to(self.home.root).as_posix()
        screenshot_abs: str | None = None
        if screenshot_rel:
            screenshot_abs = str((self.home.root / screenshot_rel).resolve())
        payload = {
            "schema": "pm.minecraft-body-episode.v1",
            "event": event["event"],
            "username": self.config.username,
            "detected_at": utc_now(),
            "intent": event["intent"],
            "detail": event["detail"],
            "state_id": state_id,
            "state_ref": state_ref,
            "screenshot": screenshot_rel,
            "screenshot_abs": screenshot_abs,
            "state_excerpt": excerpt,
        }
        value = {
            "schema": "pm.inbox.v1",
            "id": identifier,
            "type": "report-event",
            "created_at": utc_now(),
            "source": {
                "kind": "minecraft-body",
                "provider": "pm-minecraft-mcp",
                "conversation_id": "minecraft-body",
            },
            "task_ids": [],
            "project_ids": [],
            "related_input_ids": [],
            "intent": event["intent"],
            "interface_interpretation": (
                "Body episode report from the Minecraft body. The structured "
                "payload lives in extensions.body_episode, including a "
                "screenshot path and a state snapshot reference. Decide "
                "whether this deserves the character's attention: significant "
                "experiences should reach the personality cycle as one "
                "pending stimulus; minor events, or events already covered by "
                "a live Minecraft task, may be recorded without further "
                "action."
            ),
            "extensions": {"body_episode": payload},
        }
        write_readable_yaml(inbox_new / f"{identifier}.yaml", value)
        print(
            f"body event: {event['event']} -> inbox {identifier}",
            file=sys.stderr,
            flush=True,
        )

    def _idle_poll_once(self) -> None:
        """One idle-poll step: snapshot when spawned, else watch the link.

        Runs only when no tool-driven snapshot happened recently, so an
        active task's own snapshots already carry event detection.
        """
        settings = self.config.event_notifications
        if time.monotonic() - self.last_activity < settings.poll_seconds:
            return
        health = self.api.health()
        mineflayer = health.get("mineflayer") if isinstance(health, dict) else {}
        mineflayer = mineflayer if isinstance(mineflayer, dict) else {}
        connected = bool(mineflayer.get("connected"))
        spawned = bool(mineflayer.get("spawned"))
        if spawned:
            self._snapshot_sync()
            return
        cursor = self.event_cursor
        if cursor is None:
            self.event_cursor = {
                "deaths": int(mineflayer.get("deathCount") or 0),
                "spawns": int(mineflayer.get("spawnCount") or 0),
                "connected": connected,
                "health": None,
                "food": None,
                "oxygen": None,
                "is_day": None,
                "chat_ids": set(),
            }
            return
        if settings.disconnect and settings.enabled and cursor.get("connected") and not connected:
            self._emit_body_episode(
                {
                    "event": "disconnect",
                    "intent": (
                        f"{self.config.username}'s Minecraft body "
                        "disconnected from the server."
                    ),
                    "detail": {
                        "lastError": mineflayer.get("lastError"),
                        "lastDeathAt": mineflayer.get("lastDeathAt"),
                    },
                },
                None,
                None,
            )
        cursor["connected"] = connected

    def model_state_update(
        self, observation: dict[str, Any], force_full: bool = False
    ) -> dict[str, Any]:
        base_state_id = self.model_state_id or None
        self.model_state_id += 1
        if self.last_model_observation is None or force_full:
            update = {
                "mode": "full",
                "stateId": self.model_state_id,
                "baseStateId": base_state_id,
                "state": compact_observation(observation),
            }
        else:
            update = {
                "mode": "delta",
                "stateId": self.model_state_id,
                "baseStateId": base_state_id,
                "delta": model_state_delta(self.last_model_observation, observation),
            }
        self.last_model_observation = observation
        return update

    def tool_result(
        self, envelope: dict[str, Any], summary: str, force_full: bool = False
    ) -> ToolResult:
        structured = public_envelope(envelope)
        observation = envelope.get("observation") or envelope.get("stateAfter")
        if isinstance(observation, dict):
            structured["stateUpdate"] = self.model_state_update(observation, force_full)
        content: list[Any] = [
            TextContent(
                type="text", text=summary + "\n\n" + json.dumps(structured, ensure_ascii=False)
            )
        ]
        frame = envelope.get("frameAfter") or envelope.get("frame")
        if isinstance(frame, dict) and isinstance(frame.get("pngBase64"), str):
            content.append(
                ImageContent(type="image", data=frame["pngBase64"], mimeType="image/png")
            )
        return ToolResult(content=content, structured_content=structured)

    async def observe_tool(
        self, include_image: bool = False, full_state: bool = False
    ) -> ToolResult:
        async with self.lock:
            snapshot = await self.snapshot(include_image)
            snapshot["runStatus"] = self.run_status()
        return self.tool_result(snapshot, "Fresh Minecraft state captured.", full_state)

    def _blocked_action_tool_result(
        self,
        action: str,
        parameters: dict[str, Any],
        timeout_seconds: float,
        snapshot: dict[str, Any],
        *,
        progress_action: str | None = None,
        target_assessment: dict[str, Any] | None = None,
    ) -> ToolResult:
        action_id = f"mcaction-{uuid4().hex[:12]}"
        observation = snapshot["observation"]
        progress_signal = self._blocked_progress_signal(
            progress_action or action
        )
        result = {
            "ok": False,
            "status": "strategy_reassessment_required",
            "reason": "repeated_material_no_gain",
            "message": (
                f"{action} was not executed because its last "
                f"{progress_signal['sameActionNoGainCount']} attempts "
                "produced no task-relevant state gain."
            ),
        }
        if target_assessment is not None:
            result["data"] = {"targetAssessment": target_assessment}
        envelope = {
            "actionId": action_id,
            "ok": False,
            "status": "strategy_reassessment_required",
            "action": action,
            "durationMs": 0,
            "result": result,
            "stateBefore": observation,
            "stateAfter": observation,
            "stateDelta": state_delta(observation, observation),
            "progressSignal": progress_signal,
            "frameAfter": snapshot["frame"],
            "runStatus": self.run_status(),
        }
        self._write_action_log(
            envelope,
            {
                "schema": "cog.minecraft-action-request.v1",
                "action_id": action_id,
                "action": action,
                "parameters": parameters,
                "timeout_seconds": timeout_seconds,
                "requested_at": utc_now(),
                "state_before_ref": snapshot.get("stateRef"),
            },
        )
        assessment_summary = ""
        if target_assessment is not None:
            held_item = target_assessment.get("heldItem")
            held_name = (
                held_item.get("name")
                if isinstance(held_item, dict)
                else None
            )
            eligibility = target_assessment.get(
                "canHarvestWithHeldItem"
            )
            if eligibility is False:
                assessment_summary = (
                    " Current target assessment: "
                    f"{held_name or 'empty hand'} cannot harvest drops from "
                    f"{target_assessment.get('blockName', 'this block')}."
                )
        return self.tool_result(
            envelope,
            (
                "STRATEGY REASSESSMENT REQUIRED: "
                f"{result['message']}{assessment_summary} "
                "Establish a changed prerequisite or "
                "task-relevant state before retrying this action."
            ),
        )

    async def _mine_target_assessment(
        self,
        parameters: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any] | None:
        block = parameters.get("block")
        if not isinstance(block, dict):
            return None
        try:
            inspected = await asyncio.to_thread(
                self.api.call,
                "inspect",
                {"block": block},
                min(timeout_seconds, 10),
            )
        except (requests.RequestException, TimeoutError):
            return None
        data = inspected.get("data")
        return data if inspected.get("ok") is True and isinstance(data, dict) else None

    async def call_tool(
        self,
        action: str,
        parameters: dict[str, Any],
        timeout_seconds: float,
        include_image: bool = False,
    ) -> ToolResult:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        async with self.lock:
            self.assert_character_active()
            if action == "fine_control":
                frame_id = parameters.pop("visualCheckFrameId", None)
                if not isinstance(frame_id, str) or frame_id not in self.recent_visual_frames:
                    raise ValueError(
                        "fine_control requires visualCheckFrameId from a fresh minecraft_observe(include_image=true) call"
                    )
            progress_action = material_action_key(action, parameters)
            preloaded_before: dict[str, Any] | None = None
            if self._material_action_blocked(progress_action):
                target_assessment = (
                    await self._mine_target_assessment(
                        parameters,
                        timeout_seconds,
                    )
                    if action == "mine_block"
                    else None
                )
                if (
                    target_assessment is not None
                    and target_assessment.get(
                        "canHarvestWithHeldItem"
                    )
                    is True
                ):
                    self._reset_material_progress()
                else:
                    snapshot = await self.snapshot(include_image)
                    if (
                        material_action_name(progress_action) == "walk_to"
                        and self._claim_no_frontier_recovery_walk(
                            snapshot["observation"],
                            parameters,
                        )
                    ):
                        self._reset_action_progress(progress_action)
                        preloaded_before = snapshot
                    else:
                        return self._blocked_action_tool_result(
                            action,
                            parameters,
                            timeout_seconds,
                            snapshot,
                            progress_action=progress_action,
                            target_assessment=target_assessment,
                        )
            before = preloaded_before or await self.snapshot(False)
            if action == "walk_to":
                self._align_observed_navigation_waypoint(
                    before["observation"],
                    parameters,
                )
            self.assert_character_active()
            started = time.monotonic()
            try:
                result = await asyncio.to_thread(
                    self.api.call,
                    action,
                    parameters,
                    timeout_seconds,
                )
                await asyncio.to_thread(self.api.wait_until_idle, 10)
            except (requests.RequestException, TimeoutError) as error:
                try:
                    cleanup: dict[str, Any] = await asyncio.to_thread(
                        self.api.stop_and_wait,
                        10,
                    )
                except (requests.RequestException, TimeoutError) as cleanup_error:
                    cleanup = {
                        "idle": False,
                        "errorType": type(cleanup_error).__name__,
                        "error": str(cleanup_error),
                    }
                result = {
                    "ok": False,
                    "status": "boundary_failed",
                    "reason": "body_boundary_error",
                    "message": f"{type(error).__name__}: {error}",
                    "data": {
                        "action": action,
                        "cleanup": cleanup,
                    },
                }
            after = await self.snapshot(include_image)
            delta = state_delta(before["observation"], after["observation"])
            progress_signal = (
                self._progress_signal(
                    progress_action,
                    delta,
                    progress_observed=(
                        bool(result.get("ok"))
                        if action == "find_block"
                        else None
                    ),
                )
                if (
                    action == "find_block"
                    or material_action_reached_world(result, delta)
                )
                else None
            )
        action_id = f"mcaction-{uuid4().hex[:12]}"
        envelope = {
            "actionId": action_id,
            "ok": bool(result["ok"]),
            "status": result["status"]
            if "status" in result
            else "succeeded"
            if result["ok"]
            else "failed",
            "action": action,
            "durationMs": round((time.monotonic() - started) * 1000),
            "result": result,
            "stateBefore": before["observation"],
            "stateAfter": after["observation"],
            "stateDelta": delta,
            "progressSignal": progress_signal,
            "frameAfter": after["frame"],
            "runStatus": self.run_status(),
        }
        self._write_action_log(
            envelope,
            {
                "schema": "cog.minecraft-action-request.v1",
                "action_id": action_id,
                "action": action,
                "parameters": parameters,
                "timeout_seconds": timeout_seconds,
                "requested_at": utc_now(),
                "state_before_ref": before.get("stateRef"),
            },
        )
        summary = f"{action}: {result.get('message', envelope['status'])}."
        if (
            material_action_name(progress_action) in MATERIAL_ACTIONS
            and progress_signal is not None
        ):
            inventory_changes = envelope["stateDelta"]["inventoryChanges"]
            if inventory_changes:
                summary += (
                    " Verified inventory delta: "
                    + json.dumps(
                        inventory_changes,
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    + "."
                )
            else:
                summary += " Verified inventory delta: unchanged."
            result_data = result.get("data")
            if (
                action == "mine_block"
                and isinstance(result_data, dict)
                and result_data.get("canHarvest") is False
            ):
                held_before = result_data.get("heldItemBefore")
                held_name = (
                    held_before.get("name")
                    if isinstance(held_before, dict)
                    else None
                )
                summary += (
                    " Harvest eligibility: "
                    f"{held_name or 'empty hand'} cannot harvest drops from "
                    f"{result_data.get('blockName', 'this block')}."
                )
        if (
            progress_signal is not None
            and progress_signal["requiresReassessment"]
        ):
            summary = (
                "PROGRESS STALLED: repeated actions produced no "
                "task-relevant state gain. Reassess unmet dependencies and "
                "choose a "
                "materially different strategy before another state-changing "
                f"action. Consecutive no-gain count: "
                f"{progress_signal['consecutiveNoGainCount']}. "
                + summary
            )
        return self.tool_result(envelope, summary)

    def _write_action_log(
        self,
        envelope: dict[str, Any],
        request: dict[str, Any],
    ) -> None:
        action_dir = self.config.player_log_dir / "actions" / str(envelope["actionId"])
        action_dir.mkdir(parents=True, exist_ok=False)
        write_readable_yaml(
            action_dir / "request.yaml",
            relative_workspace_paths(request, self.home.root),
        )
        write_readable_yaml(
            action_dir / "result.yaml",
            relative_workspace_paths(
                {
                    "schema": "cog.minecraft-action-result.v1",
                    **envelope,
                },
                self.home.root,
            ),
        )

    async def suicide_avatar(
        self,
        reason: str,
        timeout_seconds: float = 30,
    ) -> ToolResult:
        if not reason.strip():
            raise ValueError("suicide reason must not be blank")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        execution_id = f"suicide-{uuid4().hex[:12]}"
        run_dir = self.execution_dir / execution_id
        run_dir.mkdir(parents=True, exist_ok=False)
        write_readable_yaml(
            run_dir / "input.yaml",
            {
                "schema": "cog.minecraft-suicide-input.v1",
                "execution_id": execution_id,
                "username": self.config.username,
                "reason": reason.strip(),
                "requested_at": utc_now(),
                "timeout_seconds": timeout_seconds,
            },
        )
        async with self.lock:
            self.assert_character_active()
            before = await self.snapshot(True)
            health_before = await asyncio.to_thread(self.api.health)
            mineflayer_before = health_before.get("mineflayer", {})
            death_before = int(mineflayer_before.get("deathCount", 0))
            spawn_before = int(mineflayer_before.get("spawnCount", 0))
            command = await asyncio.to_thread(
                self.api.call,
                "chat",
                {"text": "/kill"},
                5,
            )
            deadline = time.monotonic() + timeout_seconds
            death_observed = False
            respawn_observed = False
            final_health = health_before
            while time.monotonic() < deadline:
                final_health = await asyncio.to_thread(self.api.health)
                status = final_health.get("mineflayer", {})
                death_observed = int(status.get("deathCount", 0)) > death_before
                respawn_observed = (
                    death_observed
                    and int(status.get("spawnCount", 0)) > spawn_before
                    and status.get("spawned") is True
                )
                if respawn_observed:
                    break
                await asyncio.sleep(0.1)
            after = await self.snapshot(True) if respawn_observed else None

        final_status = final_health.get("mineflayer", {})
        same_username = final_status.get("username") == self.config.username
        ok = death_observed and respawn_observed and same_username
        envelope = {
            "schema": "cog.minecraft-suicide-result.v1",
            "ok": ok,
            "status": "succeeded" if ok else "failed",
            "executionId": execution_id,
            "reason": reason.strip(),
            "actualEffect": ok,
            "deathObserved": death_observed,
            "respawnObserved": respawn_observed,
            "sameUsername": same_username,
            "username": final_status.get("username"),
            "deathCountBefore": death_before,
            "deathCountAfter": final_status.get("deathCount"),
            "spawnCountBefore": spawn_before,
            "spawnCountAfter": final_status.get("spawnCount"),
            "lastDeathAt": final_status.get("lastDeathAt"),
            "lastSpawnAt": final_status.get("lastSpawnAt"),
            "command": command,
            "stateBefore": before["observation"],
            "stateBeforeRef": before.get("stateRef"),
            "screenshotBefore": screenshot_reference(before.get("frame")),
            "frameBefore": before.get("frame"),
            "stateAfter": after["observation"] if after else None,
            "stateAfterRef": after.get("stateRef") if after else None,
            "screenshotAfter": (
                screenshot_reference(after.get("frame")) if after else None
            ),
            "frameAfter": after.get("frame") if after else None,
            "finishedAt": utc_now(),
        }
        write_readable_yaml(
            run_dir / "result.yaml",
            relative_workspace_paths(envelope, self.home.root),
        )
        if ok:
            self.model_state_id = 0
            self.last_model_observation = None
        summary = (
            "Genuine Minecraft death and respawn observed."
            if ok
            else "Minecraft death or respawn was not observed; suicide failed."
        )
        return self.tool_result(envelope, summary, force_full=ok)

    async def execute_typescript(
        self,
        path: str,
        arguments: dict[str, Any],
        timeout_seconds: float,
        heartbeat_seconds: float,
        ctx: Context,
        postcondition: dict[str, Any],
        include_image: bool = False,
    ) -> ToolResult:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if timeout_seconds > self.skill_timeout_seconds:
            raise ValueError(
                "timeout_seconds must be at most "
                f"{self.skill_timeout_seconds:g} (the configured skill timeout; "
                "raise it with minecraft_set_skill_timeout)"
            )
        if heartbeat_seconds <= 0:
            raise ValueError("heartbeat_seconds must be positive")
        skill_path = Path(path).expanduser()
        if not skill_path.is_absolute():
            skill_path = self.home.root / skill_path
        skill_path = skill_path.resolve()
        if not skill_path.is_file():
            raise FileNotFoundError(skill_path)
        if skill_path.suffix.lower() not in {".ts", ".mts", ".cts"}:
            raise ValueError(f"TypeScript skill must end in .ts, .mts, or .cts: {skill_path}")
        allowed_roots = (
            self.home.drafts_dir.resolve(),
            self.home.skills_dir.resolve(),
        )
        workspace_owned = False
        for root in allowed_roots:
            try:
                skill_path.relative_to(root)
                workspace_owned = True
                break
            except ValueError:
                continue
        if not workspace_owned and skill_path != COLLECT_BLOCKS_PRIMITIVE.resolve():
            raise ValueError(
                "TypeScript execution is limited to this instance's drafts and skills directories"
            )
        character_count = len(skill_path.read_text(encoding="utf-8"))
        if character_count > self.config.max_skill_characters:
            raise ValueError(
                f"Skill is too complex: {character_count} characters exceeds the "
                f"{self.config.max_skill_characters}-character limit. Split it into small reusable skills."
            )

        async with self.lock:
            self.assert_character_active()
            if self._material_action_blocked("execute_typescript"):
                snapshot = await self.snapshot(include_image)
                if unsatisfied_inventory_postcondition_items(
                    postcondition,
                    snapshot["observation"],
                ):
                    return self._blocked_action_tool_result(
                        "execute_typescript",
                        {
                            "path": str(skill_path),
                            "arguments": arguments,
                            "postcondition": postcondition,
                        },
                        timeout_seconds,
                        snapshot,
                    )
            self.register_skill_version(skill_path)
        # The long subprocess wait must NOT hold the runtime lock: releasing it
        # here lets minecraft_stop / minecraft_kill_skill acquire the lock and
        # terminate a runaway skill instead of deadlocking behind it.
        return await self._execute_typescript_locked(
                skill_path,
                arguments,
                timeout_seconds,
                heartbeat_seconds,
                ctx,
                postcondition,
                include_image,
            )

    async def _execute_typescript_locked(
        self,
        skill_path: Path,
        arguments: dict[str, Any],
        timeout_seconds: float,
        heartbeat_seconds: float,
        ctx: Context,
        postcondition: dict[str, Any],
        include_image: bool,
    ) -> ToolResult:
        execution_id = f"exec-{uuid4().hex[:12]}"
        run_dir = self.execution_dir / execution_id
        run_dir.mkdir(parents=True)
        input_path = run_dir / "runner-input.json"
        result_path = run_dir / "runner-result.json"
        input_path.write_text(json.dumps(arguments, ensure_ascii=False), encoding="utf-8")
        before = await self.snapshot(False)
        write_readable_yaml(
            run_dir / "input.yaml",
            relative_workspace_paths(
                {
                    "schema": "cog.minecraft-typescript-input.v1",
                    "execution_id": execution_id,
                    "skill_path": str(skill_path),
                    "skill_sha256": self._skill_digest(skill_path),
                    "arguments": arguments,
                    "postcondition": postcondition,
                    "timeout_seconds": timeout_seconds,
                    "state_before_ref": before.get("stateRef"),
                },
                self.home.root,
            ),
        )
        command = typescript_runner_command(
            skill_path,
            input_path,
            result_path,
        )
        env = os.environ.copy()
        env["NODE_PATH"] = str(ensure_node_runtime() / "node_modules")
        env.update(
            {
                "MINECRAFT_BODY_URL": self.config.body_url,
                "MINECRAFT_AGENT_HOME": str(self.home.root),
                "MINECRAFT_USERNAME": self.config.username,
                "MINECRAFT_EXECUTION_ID": execution_id,
                "MINECRAFT_CANCEL_PATH": str(run_dir / "cancel"),
            }
        )
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=self.home.root,
            env=env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_task = asyncio.create_task(process.stdout.read())
        stderr_task = asyncio.create_task(process.stderr.read())
        # Terminate any stale skill (e.g. an orphaned runner from a previously
        # timed-out call) before this one takes over the physical avatar.
        if self.active_skill is not None:
            await self.kill_skill()
        self.active_skill = process
        self.active_skill_info = {
            "executionId": execution_id,
            "skillPath": str(skill_path),
            "runDir": str(run_dir),
        }
        started = time.monotonic()
        heartbeats: list[dict[str, Any]] = []
        timed_out = False

        try:
            while process.returncode is None:
                elapsed = time.monotonic() - started
                remaining = timeout_seconds - elapsed
                if remaining <= 0:
                    timed_out = True
                    break
                try:
                    await asyncio.wait_for(
                        process.wait(), timeout=min(heartbeat_seconds, remaining)
                    )
                except TimeoutError:
                    observation = await asyncio.to_thread(self.api.observe)
                    heartbeat = heartbeat_from_observation(
                        elapsed=time.monotonic() - started, observation=observation
                    )
                    heartbeats.append(heartbeat)
                    write_readable_yaml(
                        run_dir / "heartbeats.yaml",
                        {"heartbeats": heartbeats},
                    )
                    try:
                        await ctx.report_progress(
                            progress=min(time.monotonic() - started, timeout_seconds),
                            total=timeout_seconds,
                            message=heartbeat["message"],
                        )
                    except Exception as error:
                        heartbeat["progressDeliveryError"] = f"{type(error).__name__}: {error}"
        except asyncio.CancelledError:
            current_task = asyncio.current_task()
            if current_task is not None:
                while current_task.cancelling():
                    current_task.uncancel()
            cleanup = await self._terminate_execution(process, run_dir)
            stdout_bytes, stderr_bytes = await asyncio.gather(
                stdout_task,
                stderr_task,
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            (run_dir / "stdout.log").write_text(stdout, encoding="utf-8")
            (run_dir / "stderr.log").write_text(stderr, encoding="utf-8")
            runner_result = (
                json.loads(result_path.read_text(encoding="utf-8"))
                if result_path.exists()
                else None
            )
            after = await asyncio.shield(self.snapshot(False))
            envelope = {
                "ok": False,
                "status": "client_cancelled",
                "executionId": execution_id,
                "skillPath": str(skill_path),
                "arguments": arguments,
                "timeoutSeconds": timeout_seconds,
                "durationMs": round((time.monotonic() - started) * 1000),
                "processExitCode": process.returncode,
                "runnerResult": runner_result,
                "stdout": stdout,
                "stderr": stderr,
                "heartbeats": heartbeats,
                "cleanup": cleanup,
                "stateBefore": before["observation"],
                "stateAfter": after["observation"],
                "stateDelta": state_delta(before["observation"], after["observation"]),
                "frameAfter": None,
                "logDirectory": str(run_dir),
                "runStatus": self.run_status(),
            }
            write_readable_yaml(
                run_dir / "result.yaml",
                relative_workspace_paths(envelope, self.home.root),
            )
            write_readable_yaml(
                run_dir / "heartbeats.yaml",
                {"heartbeats": heartbeats},
            )
            self.active_skill = None
            self.active_skill_info = None
            raise

        cleanup: dict[str, Any]
        if timed_out:
            cleanup = await self._terminate_execution(process, run_dir)
        else:
            await process.wait()
            state = await asyncio.to_thread(self.api.state)
            cleanup = {
                "processTerminated": True,
                "mineflayerIdle": state.get("currentCommand") is None,
            }
            if state.get("currentCommand") is not None:
                cleanup["mineflayer"] = await asyncio.to_thread(self.api.stop_and_wait, 10)
                cleanup["mineflayerIdle"] = True

        stdout = (await stdout_task).decode("utf-8", errors="replace")
        stderr = (await stderr_task).decode("utf-8", errors="replace")
        (run_dir / "stdout.log").write_text(stdout, encoding="utf-8")
        (run_dir / "stderr.log").write_text(stderr, encoding="utf-8")
        runner_result = (
            json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else None
        )
        after = await self.snapshot(include_image)
        await asyncio.to_thread(
            add_exact_block_evidence,
            self.api,
            postcondition,
            after["observation"],
        )
        delta = state_delta(
            before["observation"],
            after["observation"],
        )
        relevant_inventory_items = (
            unsatisfied_inventory_postcondition_items(
                postcondition,
                before["observation"],
            )
        )
        progress_signal = None
        if relevant_inventory_items:
            progress_signal = self._progress_signal(
                "execute_typescript",
                delta,
                progress_observed=any(
                    delta["inventoryChanges"].get(item, 0) > 0
                    for item in relevant_inventory_items
                ),
                relevant_inventory_items=relevant_inventory_items,
            )
        duration_ms = round((time.monotonic() - started) * 1000)
        process_ok = (
            not timed_out
            and process.returncode == 0
            and isinstance(runner_result, dict)
            and runner_result.get("ok") is True
        )
        verification = evaluate_postcondition(
            postcondition, before["observation"], after["observation"]
        )
        ok = process_ok and verification["ok"]
        status = (
            "timed_out"
            if timed_out
            else "postcondition_failed"
            if process_ok and not verification["ok"]
            else "succeeded"
            if ok
            else "failed"
        )
        envelope = {
            "ok": ok,
            "status": status,
            "executionId": execution_id,
            "skillPath": str(skill_path),
            "arguments": arguments,
            "timeoutSeconds": timeout_seconds,
            "durationMs": duration_ms,
            "processExitCode": process.returncode,
            "runnerResult": runner_result,
            "postcondition": postcondition,
            "verification": verification,
            "stdout": stdout,
            "stderr": stderr,
            "heartbeats": heartbeats,
            "cleanup": cleanup,
            "stateBefore": before["observation"],
            "stateAfter": after["observation"],
            "stateDelta": delta,
            "progressSignal": progress_signal,
            "frameAfter": after["frame"],
            "logDirectory": str(run_dir),
            "runStatus": self.run_status(),
        }
        write_readable_yaml(
            run_dir / "result.yaml",
            relative_workspace_paths(envelope, self.home.root),
        )
        write_readable_yaml(
            run_dir / "heartbeats.yaml",
            {"heartbeats": heartbeats},
        )
        self.active_skill = None
        self.active_skill_info = None
        if timed_out:
            summary = f"{skill_path.name} timed out after {timeout_seconds}s and was terminated."
        elif ok:
            summary = f"{skill_path.name} succeeded in {duration_ms}ms."
        elif process_ok:
            summary = f"{skill_path.name} exited normally but failed its postcondition: {json.dumps(verification, ensure_ascii=False)}."
        else:
            stack = (
                runner_result.get("error", {}).get("stack")
                if isinstance(runner_result, dict)
                else stderr
            )
            summary = f"{skill_path.name} failed with exit code {process.returncode}.\n{stack}"
        if progress_signal is not None:
            inventory_changes = delta["inventoryChanges"]
            if inventory_changes:
                summary += (
                    " Verified inventory delta: "
                    + json.dumps(
                        inventory_changes,
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    + "."
                )
            else:
                summary += " Verified inventory delta: unchanged."
            if (
                progress_signal["kind"] == "material_no_gain"
                and progress_signal["relevantInventoryItems"]
            ):
                summary += (
                    " Relevant inventory gain for "
                    + json.dumps(
                        progress_signal["relevantInventoryItems"],
                        ensure_ascii=False,
                    )
                    + ": none."
                )
            if progress_signal["requiresReassessment"]:
                summary = (
                    "PROGRESS STALLED: repeated material operations produced "
                    "no inventory gain. Reassess unmet dependencies and choose "
                    "a materially different strategy before another material "
                    f"operation. Consecutive no-gain count: "
                    f"{progress_signal['consecutiveNoGainCount']}. "
                    + summary
                )
        return self.tool_result(envelope, summary)

    async def kill_skill(self) -> dict[str, Any]:
        """Terminate the currently running skill subprocess (and its in-flight command).

        Returns a small report so the caller can tell whether a stale skill
        actually existed and was killed. Safe to call when no skill is running.
        """
        process = self.active_skill
        if process is None:
            return {
                "killed": False,
                "processTerminated": False,
                "reason": "no_active_skill",
            }
        info = self.active_skill_info or {}
        if process.returncode is not None:
            self.active_skill = None
            self.active_skill_info = None
            return {
                "killed": False,
                "processTerminated": True,
                "reason": "already_exited",
                "processExitCode": process.returncode,
                **info,
            }
        run_dir = Path(info.get("runDir")) if info.get("runDir") else None
        cleanup = await self._terminate_execution(process, run_dir)
        self.active_skill = None
        self.active_skill_info = None
        return {
            "killed": True,
            "processTerminated": True,
            "reason": "killed",
            "cleanup": cleanup,
            **info,
        }

    async def _terminate_execution(self, process: asyncio.subprocess.Process, run_dir: Path | None = None) -> dict[str, Any]:
        # 1) Cooperative cancellation: drop the marker the skill checks between
        #    API calls, and give it a moment to break out and write a clean
        #    result. Only escalate to a hard kill if it stays alive.
        if run_dir is not None and process.returncode is None:
            with contextlib.suppress(OSError):
                (run_dir / "cancel").write_text("cancel\r\n", encoding="utf-8")
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(process.wait(), timeout=2.0)
        # 2) Hard kill only if the skill is still running. Closing stdin ends
        # the runner's lifecycle pipe (the runner treats EOF as cancellation);
        # process.kill() covers runners stuck in a single long call.
        if process.returncode is None:
            if process.stdin is not None:
                process.stdin.close()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except TimeoutError:
                process.kill()
        try:
            await asyncio.wait_for(process.wait(), timeout=10)
        except TimeoutError as error:
            raise RuntimeError(
                f"Skill subprocess (pid {process.pid}) did not exit after stdin EOF "
                "and a hard kill"
            ) from error
        stop_result = await asyncio.to_thread(
            self.api.stop_and_wait,
            10,
        )
        await asyncio.sleep(1)
        late_state = await asyncio.to_thread(self.api.state)
        late_stop = None
        if late_state.get("currentCommand") is not None:
            late_stop = await asyncio.to_thread(
                self.api.stop_and_wait,
                10,
            )
        return {
            "processTerminated": True,
            "mineflayerIdle": True,
            "mineflayer": stop_result,
            "lateMineflayer": late_stop,
        }


def without_image_bytes(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: without_image_bytes(item) for key, item in value.items() if key != "pngBase64"}
    if isinstance(value, list):
        return [without_image_bytes(item) for item in value]
    return value


def frame_identifier(frame: Any) -> str | None:
    if not isinstance(frame, dict):
        return None
    if isinstance(frame.get("frameId"), str):
        return frame["frameId"]
    metadata = frame.get("metadata")
    return (
        metadata.get("frameId")
        if isinstance(metadata, dict) and isinstance(metadata.get("frameId"), str)
        else None
    )


def screenshot_reference(frame: Any) -> dict[str, Any] | None:
    if not isinstance(frame, dict):
        return None
    if frame.get("ok") is False:
        # A requested capture that actually failed (viewer/bot not ready, no
        # browser executable, etc.) must be distinguishable from a capture
        # that was never requested (screenshot_reference returns None for
        # that case) - otherwise the failure is silently invisible to the agent.
        return {"error": frame.get("error", "capture_failed"), "message": frame.get("message")}
    metadata = frame.get("metadata") if isinstance(frame.get("metadata"), dict) else frame
    return without_image_bytes(
        {
            key: metadata.get(key)
            for key in (
                "frameId",
                "capturedAt",
                "pngPath",
                "metadataPath",
                "width",
                "height",
                "projection",
                "quality",
            )
            if metadata.get(key) is not None
        }
    )


def compact_waypoint(waypoint: dict[str, Any]) -> dict[str, Any]:
    """Flatten a navigation waypoint to the fields that pick a destination.

    The nested position object and the distance are dropped: the coordinates are
    what a walk_to call needs, and the distance only restates them against a
    player position the same state already carries.
    """
    position = waypoint.get("position")
    if not isinstance(position, dict):
        position = {}
    return {
        "x": position.get("x"),
        "y": position.get("y"),
        "z": position.get("z"),
        "clearance": waypoint.get("clearanceBlocksAboveHead"),
        "openNeighbors": waypoint.get("openHorizontalNeighbors"),
    }


def compact_navigation(navigation: dict[str, Any]) -> dict[str, Any]:
    frontier = navigation.get("frontierWaypoints")
    elevation = navigation.get("elevationRange")
    if not isinstance(elevation, dict):
        elevation = {}
    compact: dict[str, Any] = {
        "reachableStandableCells": navigation.get("reachableStandableCells"),
        "elevationDeltaRange": [
            elevation.get("minimumDelta"),
            elevation.get("maximumDelta"),
        ],
    }
    for role, key in (
        ("highest", "highestWaypoint"),
        ("maxClearance", "maxClearanceWaypoint"),
        ("furthest", "furthestWaypoint"),
    ):
        waypoint = navigation.get(key)
        if isinstance(waypoint, dict):
            compact[role] = compact_waypoint(waypoint)
    compact["frontier"] = [
        compact_waypoint(waypoint)
        for waypoint in (frontier if isinstance(frontier, list) else [])[
            :COMPACT_FRONTIER_WAYPOINTS
        ]
        if isinstance(waypoint, dict)
    ]
    return compact


def compact_local_airspace(airspace: Any) -> dict[str, Any]:
    """Restate the airspace scan without the parts an agent can already infer.

    Every direction's `delta` repeats its compass name, and an ordinary wall
    repeats the open-block count that already stops there.  Only the count per
    direction, the boundaries that are *not* an ordinary wall, and the reachable
    waypoints change a decision.  `boundaryDetail` stays present even when empty
    so a delta can report that a boundary disappeared.
    """
    if not isinstance(airspace, dict):
        airspace = {}
    open_blocks: dict[str, Any] = {}
    boundaries: dict[str, str] = {}
    openings = airspace.get("horizontalOpenings")
    for opening in openings if isinstance(openings, list) else []:
        direction = opening.get("direction")
        if not isinstance(direction, str):
            continue
        open_blocks[direction] = opening.get("openBlocks")
        boundary = opening.get("firstBlockedBy")
        if isinstance(boundary, dict) and (
            boundary.get("feet") != "solid" or boundary.get("head") != "solid"
        ):
            boundaries[direction] = (
                f"feet={boundary.get('feet')},head={boundary.get('head')}"
            )
    navigation = airspace.get("navigationSummary")
    return {
        "scanRadius": airspace.get("scanRadius", 0),
        "clearanceBlocksAboveHead": airspace.get("clearanceBlocksAboveHead", 0),
        "openBlocksByDirection": open_blocks,
        "boundaryDetail": boundaries,
        "navigation": compact_navigation(
            navigation if isinstance(navigation, dict) else {}
        ),
    }


def compact_nearby_block(block: dict[str, Any]) -> dict[str, Any]:
    """Keep harvest guidance only where the held item is not already enough."""
    compact = {
        key: block.get(key) for key in ("name", "count", "nearest", "distance")
    }
    if block.get("canHarvestWithHeldItem") is False:
        compact["canHarvestWithHeldItem"] = False
        options = block.get("harvestToolOptions")
        if isinstance(options, list) and options:
            compact["needsHarvestTool"] = options[0]
    return compact


def compact_observation(observation: dict[str, Any]) -> dict[str, Any]:
    player = observation["player"]
    world = observation["world"]
    inventory = observation["inventory"]
    surroundings = observation["surroundings"]
    return {
        "capturedAt": observation["capturedAt"],
        "chat": {"unreadMessages": observation.get("chat", {}).get("messages", [])},
        "player": {
            key: player.get(key)
            for key in (
                "username",
                "position",
                "blockPosition",
                "yawDegrees",
                "pitchDegrees",
                "facing",
                "health",
                "food",
                "foodSaturation",
                "oxygenLevel",
                "experienceLevel",
                "gameMode",
            )
            if key in player
        },
        "world": {
            key: world.get(key)
            for key in (
                "dimension",
                "minecraftVersion",
                "difficulty",
                "biome",
                "timeOfDay",
                "isDay",
                "isRaining",
            )
            if key in world
        },
        "inventory": {
            "heldItem": inventory.get("heldItem"),
            "armor": inventory.get("armor"),
            "emptySlots": inventory.get("emptySlots"),
            "items": item_counts(observation),
        },
        "blocksAtPlayer": {
            key: surroundings.get(key) for key in ("blockAtFeet", "blockBelowFeet", "blockAtHead")
        },
        "nearbyBlocks": [
            compact_nearby_block(block)
            for block in surroundings.get("nearbyBlocks", [])[
                :COMPACT_NEARBY_BLOCK_KINDS
            ]
        ],
        "localAirspace": compact_local_airspace(surroundings.get("localAirspace")),
        "nearbyEntities": [
            {key: entity.get(key) for key in ("id", "name", "kind", "position", "distance")}
            for entity in surroundings.get("nearbyEntities", [])[
                :COMPACT_NEARBY_ENTITIES
            ]
        ],
        "hazards": surroundings.get("hazards", []),
    }


def model_state_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_compact = compact_observation(before)
    after_compact = compact_observation(after)
    delta: dict[str, Any] = {"capturedAt": after_compact["capturedAt"]}

    read_message_ids = {message.get("id") for message in before_compact["chat"]["unreadMessages"]}
    unread_messages = [
        message
        for message in after_compact["chat"]["unreadMessages"]
        if message.get("id") not in read_message_ids
    ]
    if unread_messages:
        delta["chat"] = {"unreadMessages": unread_messages}

    for section in (
        "world",
        "blocksAtPlayer",
        "localAirspace",
    ):
        changed = {
            key: value
            for key, value in after_compact[section].items()
            if before_compact[section].get(key) != value
        }
        if changed:
            delta[section] = changed

    # The player section always carries the vital fields (position and
    # health/satiety) even when unchanged, so an agent never has to guess
    # coordinates from a timestamp or re-derive its own vitals from a delta.
    player_changed = {
        key: value
        for key, value in after_compact["player"].items()
        if before_compact["player"].get(key) != value
    }
    player_always = {
        key: after_compact["player"].get(key)
        for key in (
            "position",
            "blockPosition",
            "health",
            "food",
            "foodSaturation",
            "yawDegrees",
            "pitchDegrees",
            "facing",
        )
        if key in after_compact["player"]
    }
    player_delta = {**player_always, **player_changed}
    if player_delta:
        delta["player"] = player_delta

    # Nearby water/lava is a sound cue the bot must always get, so it is
    # reported on every state/delta, not only when it changes (the bot hears
    # lava and water even when standing still).
    delta["hazards"] = after_compact.get("hazards", [])

    before_inventory = before_compact["inventory"]
    after_inventory = after_compact["inventory"]
    # heldItem is always reported so the agent sees exactly which tool the
    # character is holding after every action (see playtest finding 4).
    inventory_delta = {"heldItem": after_inventory.get("heldItem")}
    for key in ("armor", "emptySlots"):
        if before_inventory.get(key) != after_inventory.get(key):
            inventory_delta[key] = after_inventory.get(key)
    before_items = before_inventory["items"]
    after_items = after_inventory["items"]
    item_changes = {
        name: {
            "count": after_items.get(name, 0),
            "delta": after_items.get(name, 0) - before_items.get(name, 0),
        }
        for name in sorted(set(before_items) | set(after_items))
        if before_items.get(name, 0) != after_items.get(name, 0)
    }
    if item_changes:
        inventory_delta["itemChanges"] = item_changes
    if inventory_delta:
        delta["inventory"] = inventory_delta

    before_blocks = {block["name"]: block for block in before_compact["nearbyBlocks"]}
    after_blocks = {block["name"]: block for block in after_compact["nearbyBlocks"]}
    block_changes = {
        name: after_blocks.get(name)
        for name in sorted(set(before_blocks) | set(after_blocks))
        if before_blocks.get(name) != after_blocks.get(name)
    }
    if block_changes:
        delta["nearbyBlockChanges"] = block_changes

    if before_compact["nearbyEntities"] != after_compact["nearbyEntities"]:
        delta["nearbyEntities"] = after_compact["nearbyEntities"]
    return delta


def reportable_run_status(run_status: Any) -> Any:
    """Repeat the run status only when it is not the ordinary active state.

    An active character is the precondition of every tool call, so restating it
    after each action tells an agent nothing.  A retirement must still arrive
    with the action that observed it.
    """
    if isinstance(run_status, dict) and run_status.get("status") == "active":
        return None
    return run_status


def public_envelope(envelope: dict[str, Any]) -> dict[str, Any]:
    run_status = reportable_run_status(envelope.get("runStatus"))
    if "observation" in envelope:
        observed = {
            "stateId": envelope.get("stateId"),
            "stateRef": envelope.get("stateRef"),
            "screenshot": screenshot_reference(envelope.get("frame")),
        }
        if run_status is not None:
            observed["runStatus"] = run_status
        return observed
    result = {
        key: without_image_bytes(envelope[key])
        for key in (
            "ok",
            "status",
            "actionId",
            "action",
            "executionId",
            "skillPath",
            "durationMs",
            "result",
            "runnerResult",
            "postcondition",
            "verification",
            "stdout",
            "stderr",
            "heartbeats",
            "cleanup",
            "logDirectory",
            "progressSignal",
            "actualEffect",
            "deathObserved",
            "respawnObserved",
            "sameUsername",
            "username",
            "deathCountBefore",
            "deathCountAfter",
            "spawnCountBefore",
            "spawnCountAfter",
            "lastDeathAt",
            "lastSpawnAt",
            "screenshotBefore",
            "screenshotAfter",
        )
        if key in envelope
    }
    if run_status is not None:
        result["runStatus"] = run_status
    result["screenshotAfter"] = screenshot_reference(envelope.get("frameAfter"))
    return result


def unsatisfied_inventory_postcondition_items(
    specification: dict[str, Any],
    before: dict[str, Any],
) -> set[str]:
    children = specification.get("all")
    if isinstance(children, list):
        items: set[str] = set()
        for child in children:
            if isinstance(child, dict):
                items.update(
                    unsatisfied_inventory_postcondition_items(
                        child,
                        before,
                    )
                )
        return items
    if specification.get("kind") not in {
        "inventory_min",
        "inventory_delta_min",
    }:
        return set()
    item = specification.get("item")
    if not isinstance(item, str):
        return set()
    if evaluate_postcondition(
        specification,
        before,
        before,
    )["ok"]:
        return set()
    return {item}


def postcondition_requires_inventory_change(
    specification: dict[str, Any],
    before: dict[str, Any],
) -> bool:
    return bool(
        unsatisfied_inventory_postcondition_items(
            specification,
            before,
        )
    )


def evaluate_postcondition(
    specification: dict[str, Any], before: dict[str, Any], after: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(specification, dict):
        raise TypeError("postcondition must be an object")
    checks = specification.get("all")
    if checks is None:
        checks = [specification]
    if not isinstance(checks, list) or not checks:
        raise ValueError("postcondition.all must be a non-empty array")
    results = [evaluate_postcondition_check(check, before, after) for check in checks]
    return {"ok": all(result["ok"] for result in results), "checks": results}


def evaluate_postcondition_check(
    check: Any, before: dict[str, Any], after: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(check, dict) or not isinstance(check.get("kind"), str):
        raise ValueError("each postcondition check must be an object with a string kind")
    kind = check["kind"]
    before_items = item_counts(before)
    after_items = item_counts(after)
    if kind in {"inventory_min", "inventory_delta_min"}:
        item = check.get("item")
        count = check.get("count")
        if not isinstance(item, str) or not isinstance(count, int) or count < 0:
            raise ValueError(f"{kind} requires item:string and count:non-negative integer")
        actual = (
            after_items.get(item, 0)
            if kind == "inventory_min"
            else after_items.get(item, 0) - before_items.get(item, 0)
        )
        return {
            "kind": kind,
            "ok": actual >= count,
            "item": item,
            "expectedAtLeast": count,
            "actual": actual,
        }
    if kind in {"y_min", "y_max", "health_min", "position_changed_min"}:
        value = check.get("value")
        if not isinstance(value, (int, float)):
            raise ValueError(f"{kind} requires value:number")
        if kind == "health_min":
            actual = after["player"]["health"]
            ok = actual >= value
        elif kind == "y_min":
            actual = after["player"]["position"]["y"]
            ok = actual >= value
        elif kind == "y_max":
            actual = after["player"]["position"]["y"]
            ok = actual <= value
        else:
            actual = vector_distance(before["player"]["position"], after["player"]["position"])
            ok = actual >= value
        return {"kind": kind, "ok": ok, "expected": value, "actual": actual}
    if kind == "distance_max":
        target = check.get("target")
        value = check.get("value")
        if (
            not isinstance(target, dict)
            or not all(isinstance(target.get(axis), (int, float)) for axis in ("x", "y", "z"))
            or not isinstance(value, (int, float))
        ):
            raise ValueError("distance_max requires target:{x,y,z} and value:number")
        actual = vector_distance(after["player"]["position"], target)
        return {
            "kind": kind,
            "ok": actual <= value,
            "target": target,
            "expectedAtMost": value,
            "actual": actual,
        }
    if kind == "held_item":
        item = check.get("item")
        if not isinstance(item, str):
            raise ValueError("held_item requires item:string")
        held = after["inventory"].get("heldItem")
        actual = held.get("name") if isinstance(held, dict) else None
        return {"kind": kind, "ok": actual == item, "expected": item, "actual": actual}
    if kind == "entity_id_absent":
        entity_id = check.get("entity_id")
        if not isinstance(entity_id, int) or entity_id < 0:
            raise ValueError("entity_id_absent requires entity_id:non-negative integer")
        nearby = after.get("surroundings", {}).get("nearbyEntities", [])
        present = any(
            isinstance(entity, dict) and entity.get("id") == entity_id
            for entity in nearby
        )
        return {
            "kind": kind,
            "ok": not present,
            "entityId": entity_id,
            "present": present,
        }
    if kind == "block_at":
        block = check.get("block")
        item = check.get("item")
        if (
            not isinstance(block, dict)
            or not all(isinstance(block.get(axis), (int, float)) for axis in ("x", "y", "z"))
            or not isinstance(item, str)
        ):
            raise ValueError("block_at requires block:{x,y,z} and item:string")
        coordinate = block_coordinate_key(block)
        evidence = after.get("postconditionBlocks", {}).get(coordinate)
        actual = evidence.get("blockName") if isinstance(evidence, dict) else None
        return {
            "kind": kind,
            "ok": actual == item,
            "block": {axis: int(block[axis]) for axis in ("x", "y", "z")},
            "expected": item,
            "actual": actual,
            "evidence": evidence,
        }
    raise ValueError(f"unknown postcondition kind {kind!r}")


def block_coordinate_key(block: dict[str, Any]) -> str:
    return ",".join(str(int(block[axis])) for axis in ("x", "y", "z"))


def postcondition_block_targets(specification: dict[str, Any]) -> list[dict[str, int]]:
    children = specification.get("all")
    if isinstance(children, list):
        targets: list[dict[str, int]] = []
        for child in children:
            if isinstance(child, dict):
                targets.extend(postcondition_block_targets(child))
        return targets
    if specification.get("kind") != "block_at":
        return []
    block = specification.get("block")
    if not isinstance(block, dict) or not all(
        isinstance(block.get(axis), (int, float)) for axis in ("x", "y", "z")
    ):
        return []
    return [{axis: int(block[axis]) for axis in ("x", "y", "z")}]


def add_exact_block_evidence(
    api: BodyApi,
    specification: dict[str, Any],
    observation: dict[str, Any],
) -> None:
    targets = postcondition_block_targets(specification)
    if not targets:
        return
    evidence: dict[str, Any] = {}
    for block in targets:
        key = block_coordinate_key(block)
        if key in evidence:
            continue
        try:
            result = api.call("inspect", {"block": block}, timeout_seconds=5)
            data = result.get("data") if isinstance(result, dict) else None
            evidence[key] = data if isinstance(data, dict) else {"error": result}
        except (BodyHttpError, OSError, TimeoutError) as error:
            evidence[key] = {"error": str(error)}
    observation["postconditionBlocks"] = evidence


def vector_distance(left: dict[str, Any], right: dict[str, Any]) -> float:
    return sum((float(left[axis]) - float(right[axis])) ** 2 for axis in ("x", "y", "z")) ** 0.5


def observation_summary(observation: dict[str, Any]) -> str:
    player = observation["player"]
    inventory = observation["inventory"]
    items = ", ".join(f"{item['name']}x{item['count']}" for item in inventory["items"]) or "empty"
    return (
        f"{player['username']} is at {player['position']} facing {player['facing']}; "
        f"health {player['health']}, food {player['food']}, held {inventory['heldItem']}, inventory [{items}]."
    )


def item_counts(observation: dict[str, Any]) -> dict[str, int]:
    return {item["name"]: item["count"] for item in observation["inventory"]["items"]}


def state_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_items = item_counts(before)
    after_items = item_counts(after)
    names = sorted(set(before_items) | set(after_items))
    inventory_changes = {
        name: after_items.get(name, 0) - before_items.get(name, 0)
        for name in names
        if after_items.get(name, 0) != before_items.get(name, 0)
    }
    return {
        "positionBefore": before["player"]["position"],
        "positionAfter": after["player"]["position"],
        "healthChange": numeric_delta(before["player"]["health"], after["player"]["health"]),
        "foodChange": numeric_delta(before["player"]["food"], after["player"]["food"]),
        "heldItemBefore": before.get("inventory", {}).get("heldItem"),
        "heldItemAfter": after.get("inventory", {}).get("heldItem"),
        "inventoryChanges": inventory_changes,
    }


def material_action_reached_world(
    result: dict[str, Any],
    delta: dict[str, Any],
) -> bool:
    if result.get("ok") is True:
        return True
    if delta["inventoryChanges"]:
        return True
    if result.get("status") in {"timed_out", "boundary_failed"}:
        return True
    return result.get("reason") in MATERIAL_ATTEMPT_FAILURE_REASONS


def numeric_delta(before: Any, after: Any) -> float | None:
    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
        return after - before
    return None


def position_distance(
    before: dict[str, Any],
    after: dict[str, Any],
) -> float:
    return sum(
        (float(after[axis]) - float(before[axis])) ** 2
        for axis in ("x", "y", "z")
    ) ** 0.5


def heartbeat_from_observation(elapsed: float, observation: dict[str, Any]) -> dict[str, Any]:
    player = observation["player"]
    inventory = observation["inventory"]
    message = (
        f"Running {round(elapsed)}s â€” position {player['position']}, health {player['health']}, "
        f"food {player['food']}, held {inventory['heldItem']}"
    )
    return {
        "capturedAt": observation["capturedAt"],
        "elapsedSeconds": round(elapsed, 2),
        "position": player["position"],
        "health": player["health"],
        "food": player["food"],
        "heldItem": inventory["heldItem"],
        "message": message,
    }


async def _poll_body_events(runtime: MinecraftMcpRuntime) -> None:
    """Keep sensing the body while no task is driving snapshots.

    The poller shares the runtime lock with tool calls and reuses the same
    snapshot path, so event detection has exactly one code path.
    """
    settings = runtime.config.event_notifications
    while True:
        await asyncio.sleep(settings.poll_seconds)
        if not settings.enabled:
            continue
        async with runtime.lock:
            try:
                await asyncio.to_thread(runtime._idle_poll_once)
            except Exception as exc:
                print(
                    f"body event poll skipped: {exc}",
                    file=sys.stderr,
                    flush=True,
                )


def build_mcp(runtime: MinecraftMcpRuntime) -> FastMCP:
    @contextlib.asynccontextmanager
    async def _body_event_lifespan(server: FastMCP):
        poller = asyncio.create_task(_poll_body_events(runtime))
        try:
            yield {}
        finally:
            poller.cancel()

    mcp = FastMCP(
        name=f"Minecraft: {runtime.config.username}",
        lifespan=_body_event_lifespan,
        instructions=(
            f"You embody Minecraft player {runtime.config.username}. Observe before acting. "
            f"Use low-level tools while discovering a procedure, write TypeScript drafts in {runtime.home.drafts_dir}, and promote verified skills to {runtime.home.skills_dir} "
            f"and run them with minecraft_execute_typescript. Each skill is limited to {runtime.config.max_skill_characters} characters; "
            "compose short skills instead of building monoliths. Record durable world facts with minecraft_remember. "
            "Never use progression-changing console commands or operator powers. Never claim success without checking returned state and inventory. "
            "Revise failed skills in place and retry from actual state. Retire only a cheated, teleported, operator-modified, or genuinely broken character. "
            "Returned state is compact: coordinates, distances, and angles carry one decimal; "
            "a nearbyBlocks entry names canHarvestWithHeldItem and needsHarvestTool only when the held item cannot harvest it; "
            "localAirspace.openBlocksByDirection is open blocks per compass direction and boundaryDetail lists only boundaries that are not an ordinary wall; "
            "localAirspace.navigation waypoints are standable {x,y,z,clearance,openNeighbors} cells you can pass straight to walk_to; "
            "runStatus is reported only once this character is no longer active. "
            f"Full uncompacted snapshots stay on disk under {runtime.config.player_log_dir / 'state'}."
        ),
        mask_error_details=False,
    )

    @mcp.tool
    async def minecraft_info() -> dict[str, Any]:
        """Return this character's connection, agent-home, skill, memory, and log locations."""
        health = await asyncio.to_thread(runtime.api.health)
        return {
            "username": runtime.config.username,
            "minecraftServer": f"{runtime.config.minecraft_host}:{runtime.config.minecraft_port}",
            "bodyUrl": runtime.config.body_url,
            "agentHome": str(runtime.home.root),
            "skillsDirectory": str(runtime.home.skills_dir),
            "draftsDirectory": str(runtime.home.drafts_dir),
            "memoryDirectory": str(runtime.home.memory_dir),
            "logDirectory": str(runtime.config.player_log_dir),
            "actionSchemas": runtime.api.ACTION_SCHEMAS,
            "postconditionSchemas": {
                "inventory_min": {"kind": "inventory_min", "item": "iron_pickaxe", "count": 1},
                "inventory_delta_min": {"kind": "inventory_delta_min", "item": "coal", "count": 1},
                "distance_max": {
                    "kind": "distance_max",
                    "target": {"x": 0, "y": 64, "z": 0},
                    "value": 2,
                },
                "y_min|y_max|health_min|position_changed_min": {"kind": "y_min", "value": 64},
                "held_item": {"kind": "held_item", "item": "stone_pickaxe"},
                "entity_id_absent": {"kind": "entity_id_absent", "entity_id": 123},
                "block_at": {
                    "kind": "block_at",
                    "block": {"x": 0, "y": 64, "z": 0},
                    "item": "oak_planks",
                },
                "all (compose any postconditions)": {
                    "all": [
                        {"kind": "inventory_min", "item": "iron_pickaxe", "count": 1},
                        {"kind": "health_min", "value": 1},
                    ]
                },
            },
            "skillPolicy": {
                "maxCharacters": runtime.config.max_skill_characters,
                "maxTimeoutSeconds": runtime.skill_timeout_seconds,
                "acceptedExtensions": [".ts", ".mts", ".cts"],
                "compositionPreferred": True,
                "promotionRequiresVerifiedExecution": True,
            },
            "capabilities": runtime.list_capabilities(),
            "timeouts": {
                "skillTimeoutSeconds": runtime.skill_timeout_seconds,
                "hint": "Use minecraft_set_skill_timeout to raise/lower the max skill duration to match your client's requestTimeoutMs; keep it below your agent harness's request timeout or long skills will run server-side past your client window.",
            },
            "runStatus": runtime.run_status(),
            "health": health,
        }

    @mcp.tool
    async def minecraft_list_capabilities() -> dict[str, Any]:
        """List reusable TypeScript skills that belong to this character."""
        async with runtime.lock:
            return runtime.list_capabilities()

    @mcp.tool
    async def minecraft_promote_skill(
        draft_path: str,
        name: str,
        description: str,
        execution_id: str,
        source_task_id: str | None = None,
        replace: bool = False,
    ) -> dict[str, Any]:
        """Promote a character draft after its named execution passed the mandatory postcondition."""
        async with runtime.lock:
            return runtime.promote_skill(
                draft_path=draft_path,
                name=name,
                description=description,
                execution_id=execution_id,
                source_task_id=source_task_id,
                replace=replace,
            )

    @mcp.tool
    async def minecraft_observe(
        include_image: bool = True, full_state: bool = False
    ) -> ToolResult:
        """Get fresh state, including a screenshot by default so the agent can see the world. Results are deltas after the first call; set full_state to reset the model-visible baseline. A screenshot is always captured and saved to disk regardless; include_image=False only skips attaching it to this response, to save context when only state is needed."""
        return await runtime.observe_tool(include_image, full_state)

    @mcp.tool
    async def minecraft_call(
        action: str,
        parameters: dict[str, Any],
        timeout_seconds: float = 30,
        include_image: bool = False,
    ) -> ToolResult:
        """Call a named Minecraft action using the exact schema from minecraft_info. Returns authoritative after-state and delta."""
        safe_parameters = dict(parameters)
        if action == "find_block":
            safe_parameters["requireVisible"] = True
        return await runtime.call_tool(
            action, safe_parameters, timeout_seconds, include_image
        )

    @mcp.tool
    async def minecraft_find_block(
        block_name: str,
        max_distance: int = 64,
        include_image: bool = False,
    ) -> ToolResult:
        """Find the nearest instance of an exact block. It ONLY returns blocks with an unobstructed head-ray line of sight (requireVisible is hard-locked to true â€” no x-ray; walled/underground targets return block_not_found), so you must explore or get a better viewpoint first. Returns a single nearest result; """
        require_visible = True
        return await runtime.call_tool(
            "find_block",
            {
                "blockName": block_name,
                "maxDistance": max_distance,
                "requireVisible": require_visible,
            },
            15,
            include_image,
        )

    @mcp.tool
    async def minecraft_walk_to(
        x: float,
        y: float,
        z: float,
        tolerance: float = 1.0,
        profile: Literal["adaptive", "walk_only"] = "adaptive",
        timeout_seconds: float = 60,
        include_image: bool = False,
    ) -> ToolResult:
        """Walk to a point (flat x, y, z coordinates, NOT a position/block object). Adaptive by default: it may dig, place scaffold, tower, parkour, or drop up to four blocks to reach the target, and stops within `tolerance` blocks. Set profile="walk_only" to forbid changing blocks (digging, placement, towers, parkour, drops over one block). tolerance defaults to 1 so the body gets adjacent (needed to reach pickups/placements); raise it only for long noisy hops."""
        return await runtime.call_tool(
            "walk_to",
            {
                "target": {"x": x, "y": y, "z": z},
                "tolerance": tolerance,
                "profile": profile,
            },
            timeout_seconds,
            include_image,
        )

    @mcp.tool
    async def minecraft_mine_block(
        x: int,
        y: int,
        z: int,
        walk_into_range: bool = True,
        timeout_seconds: float = 60,
        include_image: bool = False,
    ) -> ToolResult:
        """Mine the block at exact world coordinates (flat x, y, z, NOT a block dict) and verify the resulting block change. Set walk_into_range=False only when the target is already in front of you and within reach; otherwise leave it true so the body walks adjacent (and can collect the drop). Correct-tool harvesting is enforced."""
        return await runtime.call_tool(
            "mine_block",
            {"block": {"x": x, "y": y, "z": z}, "walkIntoRange": walk_into_range},
            timeout_seconds,
            include_image,
        )

    @mcp.tool
    async def minecraft_pillar_up(include_image: bool = False) -> ToolResult:
        """Ascend exactly one block by naturally jumping and placing the currently held placeable block beneath the character. No coordinates or face are needed: the body derives the block below, retries up to three jumps, verifies the placed block, and waits for landing. Equip a suitable solid block and use a fresh observation whose localAirspace.clearanceBlocksAboveHead is at least 1."""
        return await runtime.call_tool("pillar_up", {}, 30, include_image)

    @mcp.tool
    async def minecraft_collect_blocks(
        block_name: str,
        item_name: str,
        count: int,
        ctx: Context,
        max_distance: int = 48,
        timeout_seconds: float | None = None,
    ) -> ToolResult:
        """Repeatedly find and mine an exact block until after-state proves the requested inventory delta. Uses only this body's ordinary find/mine primitives, not collectblock."""
        if count <= 0:
            raise ValueError("count must be positive")
        effective_timeout = timeout_seconds if timeout_seconds is not None else runtime.skill_timeout_seconds
        return await runtime.execute_typescript(
            str(COLLECT_BLOCKS_PRIMITIVE),
            {
                "blockName": block_name,
                "itemName": item_name,
                "count": count,
                "maxDistance": max_distance,
            },
            effective_timeout,
            15,
            ctx,
            {"kind": "inventory_delta_min", "item": item_name, "count": count},
            False,
        )

    @mcp.tool
    async def minecraft_craft_item(
        item_name: str, repetitions: int = 1, timeout_seconds: float = 60
    ) -> ToolResult:
        """Craft an exact item recipe through Mineflayer's normal survival crafting API and verify inventory after-state."""
        return await runtime.call_tool(
            "craft_item",
            {"itemName": item_name, "repetitions": repetitions},
            timeout_seconds,
            False,
        )

    @mcp.tool
    async def minecraft_smelt_item(
        input_item_name: str,
        input_count: int,
        fuel_item_name: str,
        fuel_count: int = 1,
        timeout_seconds: float = 180,
    ) -> ToolResult:
        """Smelt ordinary inventory items in a nearby furnace and return verified after-state."""
        return await runtime.call_tool(
            "smelt",
            {
                "inputItemName": input_item_name,
                "inputCount": input_count,
                "fuelItemName": fuel_item_name,
                "fuelCount": fuel_count,
                "timeoutMs": round(timeout_seconds * 1000),
            },
            timeout_seconds,
            False,
        )

    @mcp.tool
    async def minecraft_equip(
        item_name: str, timeout_seconds: float = 15, include_image: bool = False
    ) -> ToolResult:
        """Equip an inventory item by exact Mineflayer item name."""
        return await runtime.call_tool(
            "inventory_equip", {"itemName": item_name}, timeout_seconds, include_image
        )

    @mcp.tool
    async def minecraft_rotate(
        yaw_degrees: float = 0, pitch_degrees: float = 0, include_image: bool = False
    ) -> ToolResult:
        """Rotate relative to the current view. Positive yaw turns right; positive pitch looks up."""
        return await runtime.call_tool(
            "rotate", {"yaw": yaw_degrees, "pitch": pitch_degrees}, 10, include_image
        )

    @mcp.tool
    async def minecraft_kill_command(include_image: bool = False) -> ToolResult:
        """Stop only the currently running physical Mineflayer command (pathfinding/digging/controls). Leaves a running skill process alive."""
        return await runtime.call_tool("stop", {}, 10, include_image)

    @mcp.tool
    async def minecraft_kill_skill() -> dict[str, Any]:
        """Terminate the running TypeScript skill process (and, necessarily, whatever command it was issuing). No-op when no skill is running."""
        async with runtime.lock:
            result = await runtime.kill_skill()
        return {
            "ok": result["killed"],
            "killed": result["killed"],
            "reason": result.get("reason"),
            "skillPath": result.get("skillPath"),
            "executionId": result.get("executionId"),
            "processTerminated": result.get("processTerminated", False),
            "runStatus": runtime.run_status(),
        }

    @mcp.tool
    async def minecraft_stop(include_image: bool = False) -> ToolResult:
        """Stop the active Mineflayer command AND terminate any running skill process (kills both). Use for an emergency halt."""
        command = await runtime.call_tool("stop", {}, 10, include_image)
        async with runtime.lock:
            skill = await runtime.kill_skill()
        structured = command.structured_content
        if isinstance(structured, dict):
            structured = dict(structured)
            structured["killSkill"] = {
                "killed": skill["killed"],
                "reason": skill.get("reason"),
                "skillPath": skill.get("skillPath"),
                "processTerminated": skill.get("processTerminated", False),
            }
        return ToolResult(content=command.content, structured_content=structured)

    @mcp.tool
    async def minecraft_execute_typescript(
        path: str,
        ctx: Context,
        postcondition: PostconditionSpec,
        arguments: dict[str, Any] | None = None,
        timeout_seconds: float | None = None,
        heartbeat_seconds: float = 15,
        include_image: bool = False,
    ) -> ToolResult:
        """Execute a local TypeScript skill in drafts/ or skills/. Normal exit counts as success only if the mandatory after-state `postcondition` also passes.

        postcondition kinds (pick ONE): inventory_min{item,count}, inventory_delta_min{item,count}, held_item{item}, entity_id_absent{entity_id}, block_at{block:{x,y,z},item}, y_min/y_max/health_min/position_changed_min{value}, distance_max{target:{x,y,z},value}. To compose several, pass a single object with only an `all` array (NO kind key): {"all":[{...},{...}]}.

        Runs up to timeout_seconds (default = the server's skillTimeoutSeconds; raise with minecraft_set_skill_timeout) in its own subprocess and returns a heartbeat every heartbeat_seconds. If it completes, Returns the result; if the caller times out first the skill keeps running server-side (call minecraft_observe to track, minecraft_stop/minecraft_kill_skill to halt it). Keep skillTimeoutSeconds at or below your client's requestTimeoutMs."""
        effective_timeout = timeout_seconds if timeout_seconds is not None else runtime.skill_timeout_seconds
        return await runtime.execute_typescript(
            path,
            arguments or {},
            effective_timeout,
            heartbeat_seconds,
            ctx,
            postcondition.as_dict(),
            include_image,
        )

    @mcp.tool
    async def minecraft_check_postcondition(
        postcondition: PostconditionSpec,
    ) -> dict[str, Any]:
        """Evaluate a deterministic postcondition against a fresh state. Delta checks compare the same snapshot and are therefore zero."""
        async with runtime.lock:
            snapshot = await runtime.snapshot(False)
        observation = snapshot["observation"]
        specification = postcondition.as_dict()
        await asyncio.to_thread(
            add_exact_block_evidence,
            runtime.api,
            specification,
            observation,
        )
        return {
            "stateId": snapshot["stateId"],
            "stateRef": snapshot["stateRef"],
            "screenshot": relative_workspace_paths(
                screenshot_reference(snapshot.get("frame")),
                runtime.home.root,
            ),
            "verification": evaluate_postcondition(
                specification,
                observation,
                observation,
            ),
            "stateUpdate": runtime.model_state_update(observation),
        }

    @mcp.tool
    async def minecraft_set_skill_timeout(seconds: float) -> dict[str, Any]:
        """Set the maximum allowed skill/collect_blocks duration (1..3600 s) for this server instance, so you can match it to your client's requestTimeoutMs. Long skills that run past your client's request window will be terminated server-side at their own timeout; minecraft_stop / minecraft_kill_skill halt them sooner (cooperative kill-signal + hard kill)."""
        async with runtime.lock:
            new = runtime.set_skill_timeout(seconds)
        return {
            "ok": True,
            "skillTimeoutSeconds": new,
            "runStatus": runtime.run_status(),
        }

    @mcp.tool
    async def minecraft_remember(
        kind: Literal[
            "world",
            "places",
            "routes",
            "chests",
            "failures",
            "journal",
        ],
        markdown: str,
    ) -> dict[str, Any]:
        """Append a durable Markdown fact or note to the character's memory. Record coordinates, dimension, evidence, and uncertainty."""
        path = await asyncio.to_thread(runtime.home.append_note, kind, markdown)
        return {"ok": True, "kind": kind, "path": str(path), "writtenAt": utc_now()}

    @mcp.tool
    async def minecraft_suicide(
        reason: str,
        timeout_seconds: float = 30,
    ) -> ToolResult:
        """Kill and respawn only this avatar, with observed death evidence."""
        return await runtime.suicide_avatar(reason, timeout_seconds)

    @mcp.tool
    async def minecraft_retire_character(
        reason: Literal["cheated_item", "teleport", "operator_power", "character_broken", "other"],
        evidence: str,
    ) -> dict[str, Any]:
        """Permanently retire this username after contamination. Preserve its logs and restart the MCP with a fresh numbered username."""
        if not evidence.strip():
            raise ValueError("evidence must describe what contaminated the character")
        runtime.retire_character(reason, {"evidence": evidence.strip(), "reportedBy": "agent"})
        return {
            "ok": True,
            "runStatus": runtime.run_status(),
            "logDirectory": str(runtime.config.player_log_dir),
        }

    return mcp


def parse_args(argv: list[str] | None = None) -> ServerConfig:
    parser = argparse.ArgumentParser(
        description="Start a per-character Minecraft body and MCP server."
    )
    parser.add_argument("--mc-host", default="127.0.0.1")
    parser.add_argument("--mc-port", type=int, required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--agent-home", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--web-host", default="127.0.0.1")
    parser.add_argument("--web-port", type=int, default=3000)
    parser.add_argument("--viewer-port", type=int, default=3007)
    parser.add_argument("--mcp-host", default="127.0.0.1")
    parser.add_argument("--mcp-port", type=int, default=8765)
    parser.add_argument("--startup-timeout-seconds", type=float, default=60)
    parser.add_argument("--max-skill-characters", type=int, default=50000)
    parser.add_argument("--viewer-scale", type=int, default=1)
    parser.add_argument("--viewer-fov", type=int, default=80)
    parser.add_argument("--view-distance", type=int, default=12)
    parser.add_argument(
        "--enable-anti-stall-guard",
        action="store_true",
        help="Opt in to the repeated-no-gain circuit breaker (default off; blocked material actions are disabled unless this is set).",
    )
    parser.add_argument(
        "--mine-visibility-ignore-distance",
        type=float,
        default=DEFAULT_MINE_VISIBILITY_IGNORE_DISTANCE,
        help="mine_block skips its head-line-of-sight gate for targets within this many blocks (default 3, for tunneling).",
    )
    parser.add_argument(
        "--walk-to-max-distance",
        type=float,
        default=DEFAULT_WALK_TO_MAX_DISTANCE,
        help="Reject walk_to targets farther than this many blocks (default 16, one chunk).",
    )
    parser.add_argument(
        "--skill-timeout-seconds",
        type=float,
        default=DEFAULT_SKILL_TIMEOUT_SECONDS,
        help=f"Maximum duration in seconds for a skill / collect_blocks run; agent can raise/lower it later with minecraft_set_skill_timeout (default {DEFAULT_SKILL_TIMEOUT_SECONDS:g}).",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Return state without capturing fresh frames from MCP tools.",
    )
    args = parser.parse_args(argv)
    return ServerConfig(
        minecraft_host=args.mc_host,
        minecraft_port=args.mc_port,
        username=args.username,
        agent_home=args.agent_home.expanduser().resolve(),
        artifact_root=args.artifact_root.expanduser().resolve(),
        web_host=args.web_host,
        web_port=args.web_port,
        viewer_port=args.viewer_port,
        mcp_host=args.mcp_host,
        mcp_port=args.mcp_port,
        startup_timeout_seconds=args.startup_timeout_seconds,
        capture_images=not args.no_images,
        max_skill_characters=args.max_skill_characters,
        viewer_scale=args.viewer_scale,
        viewer_fov=args.viewer_fov,
        view_distance=args.view_distance,
        anti_stall_guard=args.enable_anti_stall_guard,
        mine_visibility_ignore_distance=args.mine_visibility_ignore_distance,
        walk_to_max_distance=args.walk_to_max_distance,
        skill_timeout_seconds=args.skill_timeout_seconds,
    )


CHARACTER_INSTRUCTIONS_PATH = MCP_DIR / "character_instructions.txt"


def _character_instructions(draft_list: str) -> str:
    template = CHARACTER_INSTRUCTIONS_PATH.read_text(encoding="utf-8")
    return template.replace("@@DRAFT_LIST@@", draft_list)


def init_character(
    name: str,
    agent_root: Path | str,
    artifact_root: Path | str,
    minecraft_host: str = "127.0.0.1",
    minecraft_port: int = 12345,
    web_port: int = 3000,
    viewer_port: int = 3007,
    mcp_port: int = 8765,
    mcp_request_timeout_ms: int = 200000,
) -> Path:
    """Initialize a character workspace, the Python port of init_character.ps1.

    Creates the agent home layout, copies the TypeScript SDK and example
    drafts, and writes AGENTS.md, .mcp.json, memory stubs, and
    minecraft-character.json. Raises if the name is invalid, the ports
    collide, or the agent root is not empty. Returns the agent root.
    """
    if not re.fullmatch(r"[A-Za-z0-9_]{1,16}", name):
        raise ValueError("Minecraft username must contain 1-16 letters, digits, or underscores")
    ports = {minecraft_port, web_port, viewer_port, mcp_port}
    if len(ports) != 4:
        raise ValueError("Minecraft, web, viewer, and MCP ports must be distinct.")
    root = Path(agent_root).expanduser().resolve()
    artifacts = Path(artifact_root).expanduser().resolve()
    if not SDK_PATH.is_file():
        raise FileNotFoundError(f"Minecraft SDK is missing: {SDK_PATH}")
    drafts = sorted(drafts_source_dir().glob("*.ts"))
    if not drafts:
        raise FileNotFoundError(f"Example drafts are missing from {drafts_source_dir()}")
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"agent_root must be empty or not exist: {root}")

    for relative in (
        "drafts",
        "skills",
        "lib",
        "memory/minecraft",
        "artifacts/minecraft/actions",
        "artifacts/minecraft/executions",
        "artifacts/minecraft/screenshots",
        "artifacts/minecraft/state",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)

    shutil.copy2(SDK_PATH, root / "lib" / "minecraft.ts")
    for draft in drafts:
        shutil.copy2(draft, root / "drafts" / draft.name)
    draft_list = "\n".join(f"  - drafts/{draft.name}" for draft in drafts)
    (root / "AGENTS.md").write_text(_character_instructions(draft_list), encoding="utf-8")
    for memory_name in ("WORLD", "PLACES", "ROUTES", "CHESTS", "FAILURES", "JOURNAL"):
        (root / "memory" / "minecraft" / f"{memory_name}.md").write_text(
            f"# {memory_name}\n", encoding="utf-8"
        )
    mcp_config = {
        "mcpServers": {
            "minecraft": {
                "url": f"http://127.0.0.1:{mcp_port}/mcp",
                "requestTimeoutMs": mcp_request_timeout_ms,
            }
        }
    }
    (root / ".mcp.json").write_text(
        json.dumps(mcp_config, indent=2) + "\n", encoding="utf-8"
    )
    character_manifest = {
        "schema": "pm.minecraft-character.v1",
        "name": name,
        "minecraft": {"host": minecraft_host, "port": minecraft_port},
        "ports": {"web": web_port, "viewer": viewer_port, "mcp": mcp_port},
        "paths": {"agent_root": str(root), "artifact_root": str(artifacts)},
    }
    (root / "minecraft-character.json").write_text(
        json.dumps(character_manifest, indent=2) + "\n", encoding="utf-8"
    )
    return root


def _wait_for_external_body(config: ServerConfig, api: BodyApi) -> dict[str, Any]:
    """Block until an externally managed body reports ready."""
    deadline = time.monotonic() + config.startup_timeout_seconds
    while time.monotonic() < deadline:
        try:
            health = api.health()
        except requests.RequestException:
            time.sleep(0.25)
            continue
        if health.get("ready") is True:
            return health
        last_error = health["mineflayer"]["lastError"]
        if last_error:
            raise RuntimeError(f"Mineflayer connection failed: {last_error}")
        time.sleep(0.25)
    raise TimeoutError(
        f"Externally managed Minecraft body at {config.body_url} did not become "
        f"ready in {config.startup_timeout_seconds}s"
    )


def execute_node_main_loop(config: ServerConfig) -> None:
    """Blocking entry point that runs only the Minecraft body (Node process).

    Use this in its own daemon thread when you want the body and the MCP
    server in separate threads; pair it with
    ``execute_python_main_loop(config, manage_body=False)``. The body is a
    child attached through a stdin pipe: when this thread (or the whole
    process) dies, the body receives EOF on stdin and shuts down cleanly.
    Prerequisite failures raise immediately.
    """
    config.player_log_dir.mkdir(parents=True, exist_ok=True)
    api = BodyApi(config.body_url)
    supervisor = BodySupervisor(config, api)
    print(
        f"Starting Minecraft body for character {config.username} against "
        f"{config.minecraft_host}:{config.minecraft_port}",
        file=sys.stderr,
        flush=True,
    )
    try:
        supervisor.start()
        while supervisor.process is not None and supervisor.process.poll() is None:
            time.sleep(0.5)
        if supervisor.process is not None and supervisor.process.returncode not in (0, None):
            raise RuntimeError(
                f"Minecraft body exited with code {supervisor.process.returncode}"
            )
    finally:
        supervisor.stop()


def execute_python_main_loop(config: ServerConfig, manage_body: bool = True) -> None:
    """Blocking entry point: serve the Minecraft MCP server.

    Designed to run in a daemon thread of an embedding process. With
    ``manage_body=True`` (default) the Node body is started here as a child
    attached through a stdin pipe: when this thread (or the whole process)
    dies, the body receives EOF on stdin and shuts down cleanly; no detached
    processes are created anywhere. With ``manage_body=False`` the body must
    already be running (for example via ``execute_node_main_loop`` in a
    second daemon thread) and this call only waits for it to become ready.
    Prerequisite failures (no Minecraft server, wrong version, ports taken,
    missing agent home) raise immediately before anything is served.
    """
    config.player_log_dir.mkdir(parents=True, exist_ok=True)
    home = AgentHome(config)
    home.validate()
    api = BodyApi(config.body_url)
    supervisor = BodySupervisor(config, api) if manage_body else None
    print(
        f"Starting Minecraft character {config.username} against "
        f"{config.minecraft_host}:{config.minecraft_port}",
        file=sys.stderr,
        flush=True,
    )
    try:
        # With manage_body=True this thread owns the body; otherwise the
        # companion thread running execute_node_main_loop started it and this
        # thread only waits for it to become ready.
        health = supervisor.start() if manage_body else _wait_for_external_body(config, api)
        print(f"Minecraft body ready: {json.dumps(health['mineflayer'])}", file=sys.stderr, flush=True)
        mineflayer = health.get("mineflayer", {})
        if mineflayer.get("username") != config.username:
            raise RuntimeError(
                f"Mineflayer joined with an unexpected username: {mineflayer.get('username')!r}"
            )
        negotiated_version = mineflayer.get("version")
        if not isinstance(negotiated_version, str) or not negotiated_version.startswith("1.19"):
            raise RuntimeError(
                f"Minecraft negotiated version must be 1.19.x, got {negotiated_version!r}"
            )
        initial_observation = api.observe()
        if initial_observation.get("player", {}).get("gameMode") != "survival":
            raise RuntimeError(
                "Minecraft game mode must be survival, got "
                f"{initial_observation.get('player', {}).get('gameMode')!r}"
            )
        home.write_character(initial_observation)
        runtime = MinecraftMcpRuntime(config, api, home)
        mcp = build_mcp(runtime)
        print(f"Agent home: {home.root}", file=sys.stderr, flush=True)
        print(f"Artifact root: {config.player_log_dir}", file=sys.stderr, flush=True)
        print(f"Minecraft MCP: {config.mcp_url}", file=sys.stderr, flush=True)
        mcp.run(
            transport="streamable-http",
            host=config.mcp_host,
            port=config.mcp_port,
            path="/mcp",
            show_banner=True,
        )
    finally:
        if supervisor is not None:
            supervisor.stop()


def main(argv: list[str] | None = None) -> None:
    config = parse_args(argv)
    config.player_log_dir.mkdir(parents=True, exist_ok=True)
    server_log = (config.player_log_dir / "mcp-server.log").open("a", encoding="utf-8", buffering=1)
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = TeeTextStream(original_stdout, server_log)
    sys.stderr = TeeTextStream(original_stderr, server_log)
    try:
        execute_python_main_loop(config)
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        server_log.close()


if __name__ == "__main__":
    main()
