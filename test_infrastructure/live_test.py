"""Operate one real Minecraft test environment.

Code errors stop the test and retain their traceback.
Missing configuration values stop test collection with one clear error.
Checkpoint mode stops the test when the external server is not active.
Isolated-mode startup errors stop the test and name the server log.
The operator remains connected after the setup player leaves.
Teardown always stops the MCP and Mineflayer processes.
Checkpoint-mode teardown does not stop or modify the Minecraft server.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import Future, ThreadPoolExecutor
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import socket
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

from fastmcp import Client
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env_tdd"


@dataclass(frozen=True)
class Configuration:
    python: Path
    java: Path
    node: Path
    server_template: Path
    server_jar: Path
    run_root: Path
    mineflayer_entrypoint: Path
    mcp_entrypoint: Path
    mcp_module: str
    minecraft_host: str
    minecraft_port: int
    minecraft_version: str
    player_name: str
    operator_name: str
    mcp_host: str
    mcp_port: int
    agent_home: Path
    server_memory: str
    server_start_timeout: float
    process_stop_timeout: float
    world_change_timeout: float
    use_server_checkpointing: bool


def load_configuration() -> Configuration:
    """Read the required local configuration and stop for each missing entry."""
    if not ENV_FILE.is_file():
        raise RuntimeError(f"The test configuration does not exist: {ENV_FILE}")

    values = {
        key.strip(): value.strip()
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
        for key, value in [line.split("=", 1)]
    }
    required = (
        "PYTHON_EXE", "JAVA_EXE", "NODE_EXE", "MINECRAFT_SERVER_TEMPLATE",
        "MINECRAFT_SERVER_JAR", "TEST_RUN_ROOT", "MINEFLAYER_ENTRYPOINT",
        "MCP_ENTRYPOINT", "MCP_MODULE", "MINECRAFT_HOST", "MINECRAFT_PORT",
        "MINECRAFT_VERSION", "MINECRAFT_PLAYER", "MINECRAFT_OPERATOR",
        "MCP_HOST", "MCP_PORT", "SERVER_MEMORY",
        "MCMCP_AGENT_HOME",
        "SERVER_START_TIMEOUT_SECONDS", "PROCESS_STOP_TIMEOUT_SECONDS",
        "WORLD_CHANGE_TIMEOUT_SECONDS", "USE_SERVER_CHECKPOINTING",
    )
    missing = [name for name in required if name not in values]
    if missing:
        raise RuntimeError(f"Add these entries to {ENV_FILE}: {', '.join(missing)}")

    paths = {
        name: Path(values[name])
        for name in (
            "PYTHON_EXE", "JAVA_EXE", "NODE_EXE", "MINECRAFT_SERVER_TEMPLATE",
            "MINECRAFT_SERVER_JAR", "MINEFLAYER_ENTRYPOINT", "MCP_ENTRYPOINT",
        )
    }
    absent = [f"{name}={path}" for name, path in paths.items() if not path.exists()]
    if absent:
        raise RuntimeError("Install or restore these required paths:\n" + "\n".join(absent))

    checkpoint_value = values["USE_SERVER_CHECKPOINTING"].lower()
    if checkpoint_value not in ("true", "false"):
        raise RuntimeError("Set USE_SERVER_CHECKPOINTING to true or false in .env.")

    mineflayer_package = paths["MINEFLAYER_ENTRYPOINT"].parent / "node_modules" / "mineflayer" / "package.json"
    if not mineflayer_package.is_file():
        raise RuntimeError(
            f"Mineflayer is not installed. Run `npm install` in {paths['MINEFLAYER_ENTRYPOINT'].parent}."
        )

    return Configuration(
        python=paths["PYTHON_EXE"],
        java=paths["JAVA_EXE"],
        node=paths["NODE_EXE"],
        server_template=paths["MINECRAFT_SERVER_TEMPLATE"],
        server_jar=paths["MINECRAFT_SERVER_JAR"],
        run_root=Path(values["TEST_RUN_ROOT"]),
        mineflayer_entrypoint=paths["MINEFLAYER_ENTRYPOINT"],
        mcp_entrypoint=paths["MCP_ENTRYPOINT"],
        mcp_module=values["MCP_MODULE"],
        minecraft_host=values["MINECRAFT_HOST"],
        minecraft_port=int(values["MINECRAFT_PORT"]),
        minecraft_version=values["MINECRAFT_VERSION"],
        player_name=values["MINECRAFT_PLAYER"],
        operator_name=values["MINECRAFT_OPERATOR"],
        mcp_host=values["MCP_HOST"],
        mcp_port=int(values["MCP_PORT"]),
        agent_home=Path(values["MCMCP_AGENT_HOME"]),
        server_memory=values["SERVER_MEMORY"],
        server_start_timeout=float(values["SERVER_START_TIMEOUT_SECONDS"]),
        process_stop_timeout=float(values["PROCESS_STOP_TIMEOUT_SECONDS"]),
        world_change_timeout=float(values["WORLD_CHANGE_TIMEOUT_SECONDS"]),
        use_server_checkpointing=checkpoint_value == "true",
    )


class LiveMinecraftTest:
    """Own the test clients and optionally own an isolated server."""

    def __init__(self, configuration: Configuration, test_name: str):
        self.configuration = configuration
        safe_name = "".join(character if character.isalnum() else "_" for character in test_name)
        self.run_directory = configuration.run_root / safe_name
        self.agent_directory = configuration.agent_home
        self.server_process: subprocess.Popen[str]
        self.driver_process: subprocess.Popen[str]
        self.mcp_process: subprocess.Popen[str]
        self.server_log_file: Any
        self.driver_log_file: Any
        self.mcp_log_file: Any
        self.request_id = 0
        self.player_released = False
        self.mcp_started = False
        self._tool_threads = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mcp-test-call")

    def __enter__(self) -> "LiveMinecraftTest":
        if self.configuration.use_server_checkpointing:
            self._setup_checkpoint_server()
        else:
            self._setup_isolated_server()
        try:
            self._mcp_test_control("/test/body/stop")
            self._mcp_test_control("/test/reset")
            self._start_mineflayer()
            if self.configuration.use_server_checkpointing:
                messages = self.operator_command("revert")
                if not any("Reverted " in message for message in messages):
                    raise RuntimeError(
                        "The Minecraft server has no checkpoint. "
                        "Start it with `uv run python start_checkpoint_server.py`."
                    )
            self.operator_command(f"deop {self.configuration.player_name}")
            self.operator_command(f"gamemode survival {self.configuration.player_name}")
            self.operator_command("difficulty normal")
            self.operator_command(f"clear {self.configuration.player_name}")
            self.operator_command(f"effect clear {self.configuration.player_name}")
            if self.configuration.use_server_checkpointing:
                self.operator_command(f"spawnpoint {self.configuration.player_name} 0 1 0")
                self.operator_command(f"kill {self.configuration.player_name}")
                self.wait_for(
                    "The checkpoint player reset",
                    self.player_state,
                    # The position check proves the client respawned; a client
                    # that stays on its death screen keeps its stale position.
                    lambda state: state["health"] == 20 and state["food"] == 20
                    and abs(state["position"]["x"] - 0.5) <= 0.2
                    and abs(state["position"]["z"] - 0.5) <= 0.2,
                )
                self.operator_command("kill @e[type=!minecraft:player]")
                self.operator_command("kill @e[type=!minecraft:player]")
            ops_path = (
                self.configuration.server_template / "ops.json"
                if self.configuration.use_server_checkpointing
                else self.run_directory / "ops.json"
            )
            operators = json.loads(ops_path.read_text(encoding="utf-8"))
            operator_names = {entry["name"] for entry in operators}
            if self.configuration.operator_name not in operator_names:
                raise AssertionError("The TDD operator is not configured as an operator.")
            if self.configuration.player_name in operator_names:
                raise AssertionError("The MCP player is configured as an operator.")
            return self
        except BaseException:
            self.close()
            raise

    def __exit__(self, exception_type: Any, exception: Any, traceback: Any) -> None:
        self.close()

    def _setup_checkpoint_server(self) -> None:
        if not port_listening(self.configuration.minecraft_host, self.configuration.minecraft_port):
            raise RuntimeError(
                f"The checkpoint server is not active at "
                f"{self.configuration.minecraft_host}:{self.configuration.minecraft_port}. "
                "Start it with `uv run python start_checkpoint_server.py`."
            )
        self._free_zombie_ports(include_minecraft=False)
        self._create_test_directory()

    def _setup_isolated_server(self) -> None:
        self._free_zombie_ports(include_minecraft=True)
        self._create_world()
        self._start_server()

    def _clear_run_root(self) -> None:
        self.configuration.run_root.mkdir(parents=True, exist_ok=True)

    def _create_test_directory(self) -> None:
        self._clear_run_root()
        self.run_directory.mkdir(exist_ok=True)
        self._create_agent_directory()

    def _create_world(self) -> None:
        self._clear_run_root()
        shutil.copytree(
            self.configuration.server_template,
            self.run_directory,
            ignore=shutil.ignore_patterns(".git", ".fabric", "logs", "world"),
        )
        self._create_agent_directory()
        properties = self.run_directory / "server.properties"
        text = properties.read_text(encoding="utf-8")
        text = _replace_property(text, "server-port", str(self.configuration.minecraft_port))
        properties.write_text(text, encoding="utf-8")

    def _create_agent_directory(self) -> None:
        self.agent_directory.mkdir(parents=True, exist_ok=True)
        skill_directory = self.agent_directory / "skills"
        skill_directory.mkdir(exist_ok=True)
        for source in (PROJECT_ROOT / "test_infrastructure" / "skills").glob("*.ts"):
            shutil.copy2(source, skill_directory / source.name)
        (self.agent_directory / "drafts").mkdir(exist_ok=True)

    def _start_server(self) -> None:
        self.server_log_file = (self.run_directory / "server.log").open("w", encoding="utf-8")
        command = [
            str(self.configuration.java),
            f"-Xms{self.configuration.server_memory}",
            f"-Xmx{self.configuration.server_memory}",
            "-jar",
            self.configuration.server_jar.name,
            "nogui",
        ]
        self.server_process = subprocess.Popen(
            command,
            cwd=self.run_directory,
            stdin=subprocess.PIPE,
            stdout=self.server_log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self._wait_for_log(
            self.server_process,
            self.run_directory / "server.log",
            "Done (",
            self.configuration.server_start_timeout,
            "Minecraft server",
        )

    def _start_mineflayer(self) -> None:
        self.driver_log_file = (self.run_directory / "mineflayer-errors.log").open("w", encoding="utf-8")
        self.driver_process = subprocess.Popen(
            [
                str(self.configuration.node),
                str(self.configuration.mineflayer_entrypoint),
                self.configuration.minecraft_host,
                str(self.configuration.minecraft_port),
                self.configuration.minecraft_version,
                self.configuration.player_name,
                self.configuration.operator_name,
            ],
            cwd=self.configuration.mineflayer_entrypoint.parent,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.driver_log_file,
            text=True,
            bufsize=1,
        )
        ready = self._read_driver_line(self.configuration.server_start_timeout)
        if ready["event"] != "ready":
            raise RuntimeError(f"Mineflayer returned an unexpected startup message: {ready}")

    def start_mcp(self) -> None:
        """Start the persistent MCP's body without restarting its transport."""
        self._mcp_test_control("/test/body/start", timeout=self.configuration.server_start_timeout)
        self.mcp_started = True

    def release_setup_player(self) -> None:
        """Save and release the player name for the MCP."""
        if self.player_released:
            raise RuntimeError("The setup player is already released.")
        self.operator_command("save-all flush")
        self.driver("release_player")
        self.player_released = True
        self.wait_for(
            "The setup player disconnect",
            self.players,
            lambda players: all(player["username"] != self.configuration.player_name for player in players),
        )

    def handoff_player_to_mcp(self) -> dict[str, Any]:
        """Release the setup player, start the MCP, and wait for its player."""
        self.release_setup_player()
        self.start_mcp()
        players = self.wait_for(
            "The MCP player connection",
            self.players,
            lambda players: any(
                player["username"] == self.configuration.player_name and player["position"] is not None
                for player in players
            ),
        )
        if self.entity_data("playerGameType") != 0:
            raise AssertionError("The MCP player is not in survival mode.")
        if self.operator_state()["difficulty"] != "normal":
            raise AssertionError("The Minecraft difficulty is not normal.")
        return players

    def restart_mcp(self, *, require_player: bool = True) -> None:
        """Restart the MCP and keep the same per-test agent directory."""
        self.stop_mcp()
        self.start_mcp()
        if require_player:
            self.wait_for(
                "The MCP player reconnect",
                self.players,
                lambda players: any(
                    player["username"] == self.configuration.player_name and player["position"] is not None
                    for player in players
                ),
            )

    def stop_mcp(self) -> None:
        """Stop the persistent MCP's body while leaving its transport active."""
        if not self.mcp_started:
            raise RuntimeError("The MCP is not active for this test.")
        self._stop_mcp_process()
        self.mcp_started = False

    def _stop_mcp_process(self) -> None:
        """Release the MCP body without stopping the external MCP server."""
        self._mcp_test_control("/test/body/stop", timeout=self.configuration.process_stop_timeout)

    def _mcp_test_control(
        self, path: str, *, timeout: float = 10, value: dict[str, Any] | None = None
    ) -> None:
        """Call one private lifecycle endpoint on the external test MCP."""
        url = f"http://{self.configuration.mcp_host}:{self.configuration.mcp_port}{path}"
        try:
            response = requests.post(url, json=value, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException as error:
            raise RuntimeError(
                f"The external MCP test control failed at {url}. "
                "Start main.py with MCMCP_TEST_MODE=true."
            ) from error

    def mark_entity_interrupted(self, entity_id: int) -> None:
        """Tell the test MCP that an operator will remove an active target."""
        self._mcp_test_control("/test/entity/interrupted", value={"entity_id": entity_id})

    def _wait_for_log(
        self,
        process: subprocess.Popen[str],
        log_path: Path,
        marker: str,
        timeout: float,
        label: str,
    ) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.server_log_file.flush()
            if marker in log_path.read_text(encoding="utf-8", errors="replace"):
                return
            if process.poll() is not None:
                raise RuntimeError(
                    f"{label} stopped during startup. Last log lines:\n{_log_tail(log_path)}"
                )
            time.sleep(0.1)
        raise TimeoutError(
            f"{label} did not start in {timeout:g} seconds. Last log lines:\n{_log_tail(log_path)}"
        )

    def _read_driver_line(self, timeout: float) -> dict[str, Any]:
        lines: queue.Queue[str] = queue.Queue(maxsize=1)
        thread = threading.Thread(target=lambda: lines.put(self.driver_process.stdout.readline()), daemon=True)
        thread.start()
        try:
            line = lines.get(timeout=timeout)
        except queue.Empty as error:
            log_path = self.run_directory / "mineflayer-errors.log"
            raise TimeoutError(f"Mineflayer did not respond. Last log lines:\n{_log_tail(log_path)}") from error
        if not line:
            log_path = self.run_directory / "mineflayer-errors.log"
            raise RuntimeError(f"Mineflayer stopped. Last log lines:\n{_log_tail(log_path)}")
        return json.loads(line)

    def driver(self, action: str, **arguments: Any) -> Any:
        """Send one command to the real Mineflayer test clients."""
        self.request_id += 1
        request = {"id": self.request_id, "action": action, **arguments}
        self.driver_process.stdin.write(json.dumps(request) + "\n")
        self.driver_process.stdin.flush()
        response = self._read_driver_line(self.configuration.server_start_timeout)
        if response["id"] != self.request_id:
            raise RuntimeError(f"Mineflayer returned the wrong response: {response}")
        return response["result"]

    def player_state(self) -> dict[str, Any]:
        """Read the setup player before the MCP handoff."""
        return self.driver("state", bot="player")

    def operator_state(self) -> dict[str, Any]:
        """Read the operator state."""
        return self.driver("state", bot="operator")

    def operator_command(self, command: str) -> list[str]:
        """Use the operator account to change or inspect the test world."""
        return self.driver("command", command=command)["messages"]

    def player_inventory(self) -> list[dict[str, Any]]:
        """Read all setup-player slots before the MCP handoff."""
        return self.driver("inventory", bot="player")

    def player_inventory_counts(self) -> dict[str, int]:
        """Read all player item counts through an operator command."""
        inventory = self.entity_data("Inventory")
        if inventory == "[]":
            return {}
        matches = re.findall(
            r'id:\s*"minecraft:([^"]+)"\s*,\s*Count:\s*(\d+)[bB]',
            inventory,
        )
        if not matches:
            raise RuntimeError(f"The player inventory has an unknown format: {inventory}")
        counts: dict[str, int] = {}
        for item, count in matches:
            counts[item] = counts.get(item, 0) + int(count)
        return counts

    def players(self) -> list[dict[str, Any]]:
        """Read the players that the operator can see."""
        return self.driver("players")

    def entities(self) -> list[dict[str, Any]]:
        """Read all entities that the operator client receives."""
        return self.driver("entities", bot="operator")

    def observed_events(self) -> dict[str, Any]:
        """Read packet events that the independent operator observed."""
        return self.driver("observed_events")

    def block(self, x: int, y: int, z: int) -> dict[str, Any]:
        """Read one loaded block through the operator Mineflayer client."""
        return self.driver("block", bot="operator", x=x, y=y, z=z)

    def container(self, x: int, y: int, z: int) -> dict[str, Any]:
        """Open one real container through the operator and read its slots."""
        return self.driver("container", position={"x": x, "y": y, "z": z})

    def inventory_count(self, item: str) -> int:
        """Read one exact inventory count from the server without removing it."""
        messages = self.operator_command(f"clear {self.configuration.player_name} minecraft:{item} 0")
        text = "\n".join(messages)
        if "No items were found" in text:
            return 0
        match = re.search(r"Found (\d+) matching item", text)
        if match is None:
            raise RuntimeError(f"The inventory query returned an unknown message: {text}")
        return int(match.group(1))

    def set_player_vitals(self, health: float, food: int) -> dict[str, Any]:
        """Set exact setup-player vitals through normal game effects and damage."""
        return self.driver("set_vitals", health=health, food=food)

    def entity_data(self, path: str, selector: str | None = None) -> Any:
        """Read one entity-data path through an operator command."""
        target = selector or self.configuration.player_name
        messages = self.operator_command(f"data get entity {target} {path}")
        if not messages:
            raise RuntimeError(f"The entity-data query returned no message for {target} {path}.")
        text = messages[-1]
        if ": " not in text:
            raise RuntimeError(f"The entity-data query returned an unknown message: {text}")
        return _parse_command_value(text.split(": ", 1)[1])

    def entity_near(self, name: str, x: float, y: float, z: float, tolerance: float = 0.3) -> dict[str, Any]:
        """Find one exact entity near an arranged position."""
        matches = [
            entity for entity in self.entities()
            if entity["name"] == name
            and abs(entity["position"]["x"] - x) <= tolerance
            and abs(entity["position"]["y"] - y) <= tolerance
            and abs(entity["position"]["z"] - z) <= tolerance
        ]
        if len(matches) != 1:
            raise AssertionError(f"Expected one {name} near {(x, y, z)}, found {matches!r}")
        return matches[0]

    def block_counts(self, start: dict[str, int], end: dict[str, int]) -> dict[str, int]:
        """Count each block type in one inclusive box through the operator."""
        return self.driver("block_counts", start=start, end=end)

    def prepare_flat_area(self, radius: int = 40) -> dict[str, int | float]:
        """Create a large empty test area around the setup-player spawn."""
        state = self.player_state()
        x = math.floor(state["position"]["x"])
        y = math.floor(state["position"]["y"])
        z = math.floor(state["position"]["z"])
        self.operator_command(f"tp {self.configuration.player_name} {x + 0.5} {y} {z + 0.5} 0 0")
        self.operator_command(
            f"tp {self.configuration.operator_name} {x + radius + 2.5} {y} {z + radius + 2.5}"
        )
        # The reverted checkpoint provides a floor, but its playable cells are
        # not guaranteed to be empty.  Tests arrange their own terrain above
        # that floor, so establish the documented empty area first.
        #for bottom in range(y, y + 16, 4):
        #    self.operator_command(
        #        f"fill {x - radius} {bottom} {z - radius} "
        #        f"{x + radius} {bottom + 3} {z + radius} air"
        #    )
        self.wait_for(
            "The setup-player position",
            self.player_state,
            lambda value: abs(value["position"]["x"] - (x + 0.5)) < 0.1
            and abs(value["position"]["z"] - (z + 0.5)) < 0.1,
        )
        return {"x": x, "y": y, "z": z, "feet_x": x + 0.5, "feet_y": float(y), "feet_z": z + 0.5}

    def wait_for(
        self,
        description: str,
        read: Callable[[], Any],
        matches: Callable[[Any], bool],
        timeout: float | None = None,
    ) -> Any:
        """Read live state until it contains the expected server change."""
        deadline = time.monotonic() + (timeout or self.configuration.world_change_timeout)
        while time.monotonic() < deadline:
            value = read()
            if matches(value):
                return value
            time.sleep(0.05)
        raise AssertionError(f"{description} did not appear in live state. Last value: {value!r}")

    def call_tool(self, name: str, arguments: dict[str, Any], timeout: float = 660) -> Any:
        """Call one MCP tool without an LLM."""
        async def call() -> Any:
            url = f"http://{self.configuration.mcp_host}:{self.configuration.mcp_port}/mcp"
            async with Client(url) as client:
                return await asyncio.wait_for(client.call_tool_mcp(name, arguments), timeout=timeout)

        return asyncio.run(call())

    def list_tools(self) -> list[Any]:
        """Read the public tool schemas through the real MCP transport."""
        if not self.mcp_started:
            raise RuntimeError("Start the MCP before a tool-list request.")

        async def read() -> list[Any]:
            url = f"http://{self.configuration.mcp_host}:{self.configuration.mcp_port}/mcp"
            async with Client(url) as client:
                return await client.list_tools()

        return asyncio.run(read())

    def begin_tool(self, name: str, arguments: dict[str, Any], timeout: float = 660) -> Future[Any]:
        """Start one MCP call for a world change that occurs during the action."""
        return self._tool_threads.submit(self.call_tool, name, arguments, timeout)

    def require_live_mcp(self, result: Any) -> None:
        """Reject the current random stub before a behavior case can pass."""
        if result.meta and result.meta.get("mode") == "stub":
            raise NotImplementedError("The MCP still uses random stub data. Connect the live Mineflayer backend.")

    def _free_zombie_ports(self, *, include_minecraft: bool) -> None:
        """Leave externally managed server and MCP ports untouched."""

    def close(self) -> None:
        """Stop the per-test driver without stopping the shared server or MCP."""
        self._tool_threads.shutdown(wait=False, cancel_futures=True)
        if hasattr(self, "driver_process") and self.driver_process.poll() is None:
            try:
                self.driver("shutdown")
            except (BrokenPipeError, RuntimeError, TimeoutError):
                self.driver_process.kill()
            try:
                self.driver_process.wait(timeout=self.configuration.process_stop_timeout)
            except subprocess.TimeoutExpired:
                self.driver_process.kill()
                self.driver_process.wait()
        if hasattr(self, "driver_log_file") and not self.driver_log_file.closed:
            self.driver_log_file.close()
        if self.run_directory.exists():
            shutil.rmtree(self.run_directory)


def _replace_property(text: str, name: str, value: str) -> str:
    lines = text.splitlines()
    index = next(index for index, line in enumerate(lines) if line.startswith(f"{name}="))
    lines[index] = f"{name}={value}"
    return "\n".join(lines) + "\n"


def _parse_command_value(text: str) -> Any:
    if text.startswith('"'):
        return json.loads(text)
    if re.fullmatch(r"-?\d+[bBsSlL]", text):
        return int(text[:-1])
    if re.fullmatch(r"-?(?:\d+\.?\d*|\.\d+)[fFdD]", text):
        return float(text[:-1])
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?(?:\d+\.?\d*|\.\d+)", text):
        return float(text)
    return text


def port_listening(host: str, port: int) -> bool:
    """Check whether any process accepts connections on one port."""
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def _wait_for_port(
    process: subprocess.Popen[str],
    host: str,
    port: int,
    timeout: float,
    log_path: Path,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"The MCP stopped during startup. Last log lines:\n{_log_tail(log_path)}")
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise TimeoutError(
        f"The MCP did not start in {timeout:g} seconds. Last log lines:\n{_log_tail(log_path)}"
    )


def _log_tail(path: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-30:])
