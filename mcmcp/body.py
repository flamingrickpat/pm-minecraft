"""Own the Node body process and its local HTTP connection.

The client retries a temporary local connection error while the body is alive.
An invalid body response is a code error. Pydantic stops the MCP at that line.
An early body exit is fatal. The MCP logs the body failure and exits immediately.
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import secrets
import subprocess
import time

import requests

from .body_models import (
    BodyAttack,
    BodyBlocks,
    BodyCatalog,
    BodyChestMove,
    BodyCraft,
    BodyCraftMax,
    BodyDrop,
    BodyEat,
    BodyEquip,
    BodyEquipBest,
    BodyFineControl,
    BodyFindBlocks,
    BodyMine,
    BodyObserveSnapshot,
    BodyPathPreview,
    BodyPillar,
    BodyRaytrace,
    BodyRecipeSearch,
    BodyRotate,
    BodySafety,
    BodyScanHorizon,
    BodyScreenshot,
    BodySkillOutcome,
    BodyStaircase,
    BodySleep,
    BodySmelt,
    BodyState,
    BodyStop,
    BodyUseBlock,
    BodyUseItem,
    BodyWalk,
)
from .config import Configuration
from .constants import STATE_SYNC_SECONDS
from .models import ImageRef, Vec3f, Vec3i
from .startup import patch_prismarine_viewer


log = logging.getLogger("mcmcp.body")


class MinecraftBody:
    """Own one Node child and call its typed local endpoints."""

    def __init__(self, configuration: Configuration):
        patch_prismarine_viewer(configuration.body_entrypoint.parents[1])
        self.configuration = configuration
        self.token = secrets.token_urlsafe(32)
        self.url = f"http://{configuration.body_host}:{configuration.body_port}"
        configuration.agent_home.mkdir(parents=True, exist_ok=True)
        self.log_path = configuration.agent_home / "body.log"
        self.log_file = self.log_path.open("w", encoding="utf-8")
        environment = os.environ.copy()
        environment.update(
            {
                "MINECRAFT_HOST": configuration.minecraft_host,
                "MINECRAFT_PORT": str(configuration.minecraft_port),
                "MINECRAFT_VERSION": configuration.minecraft_version,
                "MINECRAFT_PLAYER": configuration.player_name,
                "MCMCP_BODY_HOST": configuration.body_host,
                "MCMCP_BODY_PORT": str(configuration.body_port),
                "MCMCP_BODY_TOKEN": self.token,
                "MCMCP_VIEWER_PORT": str(configuration.viewer_port),
                "BROWSER_EXECUTABLE_PATH": str(configuration.browser_executable),
                "MCMCP_WALK_REACHED_DISTANCE_BLOCKS": str(configuration.walk_reached_distance_blocks),
                "BODY_LOG_LEVEL": os.environ.get("MCMCP_LOG_LEVEL", "info"),
            }
        )
        self.process = subprocess.Popen(
            [str(configuration.node), str(configuration.body_entrypoint)],
            cwd=configuration.body_entrypoint.parents[1],
            stdin=subprocess.PIPE,
            stdout=self.log_file,
            stderr=subprocess.STDOUT,
            text=True,
            env=environment,
        )
        self._request_state()

    def state(self) -> BodyState:
        """Read the current Mineflayer connection and camera state."""
        return self._request_state()

    @property
    def alive(self) -> bool:
        """Return whether the Node body process is still running."""
        return self.process.poll() is None

    def catalog(self) -> BodyCatalog:
        """Read block and item names for the active Minecraft version."""
        return BodyCatalog.model_validate(self._request("GET", "/catalog"))

    def blocks(self, positions: list[Vec3i]) -> BodyBlocks:
        """Read exact loaded block cells in request order."""
        return BodyBlocks.model_validate(
            self._request(
                "POST",
                "/blocks",
                {"positions": [position.model_dump() for position in positions]},
            )
        )

    def observe(self, radius: int) -> BodyObserveSnapshot:
        """Read the full snapshot including nearby blocks and entities."""
        return BodyObserveSnapshot.model_validate(
            self._request("POST", "/observe", {"radius": radius})
        )

    def find_blocks(self, options: dict) -> BodyFindBlocks:
        """Scan the loaded world for exposed matching blocks."""
        return BodyFindBlocks.model_validate(
            self._request("POST", "/find_blocks", options)
        )

    def raytrace(self) -> BodyRaytrace:
        """Read the first block the view ray hits."""
        return BodyRaytrace.model_validate(self._request("GET", "/raytrace"))

    def rotate(self, yaw_degrees: float, pitch_degrees: float, absolute: bool) -> BodyRotate:
        """Turn the Mineflayer camera."""
        return BodyRotate.model_validate(self._request("POST", "/rotate", {
            "yaw_degrees": yaw_degrees,
            "pitch_degrees": pitch_degrees,
            "absolute": absolute,
        }))

    def look_at(self, position: Vec3f) -> BodyRotate:
        """Aim the Mineflayer camera at one world point."""
        return BodyRotate.model_validate(self._request(
            "POST", "/look_at", {"position": position.model_dump()}
        ))

    def fine_control(self, controls: dict[str, bool], duration_ms: int) -> BodyFineControl:
        """Hold raw movement controls for one fixed pulse."""
        return BodyFineControl.model_validate(self._request("POST", "/fine_control", {
            "controls": controls,
            "duration_ms": duration_ms,
        }))

    def walk_visible(self, target: Vec3f, limit: int, timeout_ms: int) -> BodyWalk:
        """Walk through one bounded visible-region search."""
        return BodyWalk.model_validate(self._request("POST", "/walk_visible", {
            "target": target.model_dump(),
            "limit": limit,
            "timeout_ms": timeout_ms,
        }, timeout=timeout_ms / 1000 + 5))

    def walk_exact(self, target: Vec3f, timeout_ms: int) -> BodyWalk:
        """Walk to one exact standable target."""
        return BodyWalk.model_validate(self._request("POST", "/walk_exact", {
            "target": target.model_dump(),
            "timeout_ms": timeout_ms,
        }, timeout=timeout_ms / 1000 + 5))

    def walk_surface(self, x: float, z: float, timeout_ms: int) -> BodyWalk:
        """Walk to a standable surface in one target column."""
        return BodyWalk.model_validate(self._request("POST", "/walk_surface", {
            "x": x,
            "z": z,
            "timeout_ms": timeout_ms,
        }, timeout=timeout_ms / 1000 + 5))

    def find_path(self, target: Vec3f, limit: int, timeout_ms: int) -> BodyPathPreview:
        """Preview a bounded local route without moving."""
        return BodyPathPreview.model_validate(self._request("POST", "/find_path", {
            "target": target.model_dump(),
            "limit": limit,
            "timeout_ms": timeout_ms,
        }, timeout=timeout_ms / 1000 + 5))

    def drop_item(self, item: str, count: int | None) -> BodyDrop:
        """Toss items out of the inventory."""
        return BodyDrop.model_validate(self._request("POST", "/drop", {"item": item, "count": count}, timeout=30))

    def eat_best(self) -> BodyEat:
        """Eat the best food in the inventory."""
        return BodyEat.model_validate(self._request("POST", "/eat_best", timeout=30))

    def equip_best_tool(self, target: Vec3i) -> BodyEquipBest:
        """Equip the best owned tool for a target block."""
        return BodyEquipBest.model_validate(self._request("POST", "/equip_best", {"target": target.model_dump()}))

    def safe_to_dig(self, position: Vec3i) -> BodySafety:
        """Report hazards around a cell you plan to dig."""
        return BodySafety.model_validate(self._request("POST", "/safe_dig", {"position": position.model_dump()}))

    def craft_max(self, item: str, limit: int | None) -> BodyCraftMax:
        """Craft as many of an item as the inventory allows."""
        return BodyCraftMax.model_validate(self._request("POST", "/craft_max", {"item": item, "limit": limit}, timeout=30))

    def sleep(self, bed: Vec3i | None) -> BodySleep:
        """Try to sleep in a bed (or the nearest bed)."""
        return BodySleep.model_validate(self._request("POST", "/sleep", {"bed": None if bed is None else bed.model_dump()}, timeout=30))

    def pillar_up(self) -> BodyPillar:
        """Ascend one block by jump-placing the held block below."""
        return BodyPillar.model_validate(self._request("POST", "/pillar_up", timeout=30))

    def recipe_search(self, item_names: list[str], craftable_now: bool | None, limit: int) -> BodyRecipeSearch:
        """Enumerate recipes for a set of item names."""
        return BodyRecipeSearch.model_validate(self._request("POST", "/recipe_search", {"item_names": item_names, "craftable_now": craftable_now, "limit": limit}, timeout=30))

    def scan_horizon(self) -> BodyScanHorizon:
        """Cast a full horizon scan from fixed headings and pitches."""
        return BodyScanHorizon.model_validate(self._request("POST", "/scan_horizon", timeout=30))

    def staircase_down(self, depth: int, torch: bool) -> BodyStaircase:
        """Carve a descending staircase with hazard stops."""
        return BodyStaircase.model_validate(self._request("POST", "/staircase_down", {"depth": depth, "torch": torch}, timeout=120))

    def execute_skill(self, path: str, source: str, arguments: dict | None, budget_ms: int) -> BodySkillOutcome:
        """Run a sandboxed TypeScript skill with a fixed time budget."""
        return BodySkillOutcome.model_validate(self._request("POST", "/execute_skill", {"path": path, "source": source, "arguments": arguments, "budget_ms": budget_ms}, timeout=budget_ms / 1000 + 15))

    def use_block(self, position: Vec3i, kind: str) -> BodyUseBlock:
        """Activate one loaded block."""
        return BodyUseBlock.model_validate(self._request("POST", "/use_block", {
            "position": position.model_dump(),
            "kind": kind,
        }))

    def equip(self, item: str) -> BodyEquip:
        return BodyEquip.model_validate(self._request("POST", "/equip", {"item": item}))

    def use_item(self) -> BodyUseItem:
        return BodyUseItem.model_validate(self._request("POST", "/use_item", timeout=10))

    def craft(self, item: str, repetitions: int) -> BodyCraft:
        return BodyCraft.model_validate(self._request("POST", "/craft", {"item": item, "repetitions": repetitions}, timeout=30))

    def mine(self, position: Vec3i) -> BodyMine:
        return BodyMine.model_validate(self._request("POST", "/mine", {"position": position.model_dump()}, timeout=65))

    def attack(self, entity_id: int, limit: int) -> BodyAttack:
        return BodyAttack.model_validate(self._request("POST", "/attack", {"entity_id": entity_id, "limit": limit}, timeout=90))

    def chest_move(self, position: Vec3i, item: str, count: int, direction: str) -> BodyChestMove:
        return BodyChestMove.model_validate(self._request("POST", "/chest_move", {"position": position.model_dump(), "item": item, "count": count, "direction": direction}, timeout=30))

    def smelt(self, position: Vec3i, input: str, input_count: int, fuel: str, fuel_count: int) -> BodySmelt:
        return BodySmelt.model_validate(self._request("POST", "/smelt", {"position": position.model_dump(), "input": input, "input_count": input_count, "fuel": fuel, "fuel_count": fuel_count}, timeout=180))

    def stop(self, scope: str) -> BodyStop:
        """Stop pathfinding and raw control states."""
        return BodyStop.model_validate(self._request("POST", "/stop", {"scope": scope}))

    def screenshot(self) -> ImageRef:
        """Capture the real viewer frame and persist it for the MCP adapter."""
        frame = BodyScreenshot.model_validate(self._request("GET", "/screenshot", timeout=30))
        return self.save_frame(frame)

    def save_frame(self, frame: BodyScreenshot) -> ImageRef:
        """Persist PNG bytes returned with a body action."""
        frame_id = secrets.token_hex(16)
        directory = self.configuration.agent_home / "frames"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{frame_id}.png").write_bytes(base64.b64decode(frame.png_base64, validate=True))
        return ImageRef(
            frame_id=frame_id,
            captured_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            width=frame.width,
            height=frame.height,
        )

    def _request_state(self) -> BodyState:
        return BodyState.model_validate(self._request("GET", "/state"))

    def _request(
        self,
        method: str,
        path: str,
        value: dict | None = None,
        timeout: float = 2,
    ) -> object:
        retry_deadline = time.monotonic() + STATE_SYNC_SECONDS
        while True:
            if self.process.poll() is not None:
                self.log_file.flush()
                body_log = self.log_path.read_text(encoding="utf-8", errors="replace")
                log.critical(
                    "Minecraft player body exited unexpectedly with code %s. "
                    "Stopping the MCP because it cannot operate without its player body. "
                    "Last body log:\n%s",
                    self.process.returncode,
                    body_log[-4000:],
                )
                os._exit(1)
            try:
                response = requests.request(
                    method,
                    f"{self.url}{path}",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json=value,
                    timeout=timeout,
                )
                if not response.ok:
                    try:
                        payload = response.json()
                        body_error = payload["error"]
                        message = body_error["message"]
                        error_type = body_error.get("type", "Error")
                    except (ValueError, KeyError, TypeError):
                        response.raise_for_status()
                    raise RuntimeError(f"Player body {error_type}: {message}")
                return response.json()
            except requests.ConnectionError as error:
                if time.monotonic() >= retry_deadline:
                    raise
                print(f"The player body is not ready: {error}. Trying again.", flush=True)
                time.sleep(0.2)

    def close(self) -> None:
        """Stop a live body or finish cleaning up an already-failed body."""
        if self.process.poll() is None:
            if self.process.stdin is not None and not self.process.stdin.closed:
                self.process.stdin.close()
            self.process.wait()
        if not self.log_file.closed:
            self.log_file.close()
