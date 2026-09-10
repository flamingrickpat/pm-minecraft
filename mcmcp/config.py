"""Read the local `.env` file.

The setting definitions below are the one source for parsing and for the
template shown when no environment file exists.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
SUPPORTED_MINECRAFT_VERSION = "1.19.4"
MINIMUM_NODE_MAJOR_VERSION = 20


@dataclass(frozen=True)
class EnvironmentSetting:
    name: str
    default: str
    description: str


SETTINGS = (
    EnvironmentSetting("NODE_EXE", "node", "Node.js executable."),
    EnvironmentSetting("MCMCP_BODY_ENTRYPOINT", str(PROJECT_ROOT / "body" / "dist" / "main.js"), "Mineflayer body entry point."),
    EnvironmentSetting("MCMCP_BODY_HOST", "127.0.0.1", "Body HTTP host."),
    EnvironmentSetting("MCMCP_BODY_PORT", "6768", "Body HTTP port."),
    EnvironmentSetting("MCMCP_VIEWER_PORT", "6769", "Prismarine viewer port."),
    EnvironmentSetting("BROWSER_EXECUTABLE_PATH", "", "Browser executable for screenshots. Set this path."),
    EnvironmentSetting("MINECRAFT_HOST", "127.0.0.1", "Minecraft server host."),
    EnvironmentSetting("MINECRAFT_PORT", "12345", "Minecraft server port."),
    EnvironmentSetting("MINECRAFT_VERSION", "1.19.4", "Minecraft protocol version."),
    EnvironmentSetting("MINECRAFT_PLAYER", "minecraft_mcp", "Minecraft account name."),
    EnvironmentSetting("MCMCP_AGENT_HOME", str(PROJECT_ROOT / "agent-data"), "Character data directory."),
    EnvironmentSetting("MINECRAFT_RCON_HOST", "127.0.0.1", "RCON server host."),
    EnvironmentSetting("MINECRAFT_RCON_PORT", "25575", "RCON server port."),
    EnvironmentSetting("MINECRAFT_RCON_PASSWORD", "", "RCON password. Set this value."),
    EnvironmentSetting("MCP_HOST", "127.0.0.1", "MCP HTTP host."),
    EnvironmentSetting("MCP_PORT", "6767", "MCP HTTP port."),
    EnvironmentSetting("MCMCP_TEST_MODE", "false", "Enable test-only MCP routes."),
    EnvironmentSetting("MCMCP_WALK_REACHED_DISTANCE_BLOCKS", "3", "Distance that completes a walk."),
    EnvironmentSetting("MCMCP_LOG_LEVEL", "info", "Log level: error, warning, info, or debug."),
    EnvironmentSetting("MCMCP_INSPECTOR_ENABLED", "false", "Start the manual MCP inspector."),
    EnvironmentSetting("MCMCP_INSPECTOR_HOST", "0.0.0.0", "Inspector HTTP host."),
    EnvironmentSetting("MCMCP_INSPECTOR_PORT", "0", "Inspector port. Zero selects a random port."),
)
SETTING_DEFAULTS = {setting.name: setting.default for setting in SETTINGS}


@dataclass(frozen=True)
class Configuration:
    node: Path
    body_entrypoint: Path
    body_host: str
    body_port: int
    viewer_port: int
    browser_executable: Path
    minecraft_host: str
    minecraft_port: int
    minecraft_version: str
    player_name: str
    agent_home: Path
    rcon_host: str
    rcon_port: int
    rcon_password: str
    mcp_host: str
    mcp_port: int
    test_mode: bool
    walk_reached_distance_blocks: float
    inspector_enabled: bool
    inspector_host: str
    inspector_port: int


def environment_template() -> str:
    """Build a copyable `.env` template from the live setting definitions."""
    return "\n".join(f"# {item.description}\n{item.name}={item.default}" for item in SETTINGS) + "\n"


def _read_values(config_file: Path) -> dict[str, str]:
    values = SETTING_DEFAULTS.copy()
    values.update({
        key.strip(): value.strip()
        for line in config_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
        for key, value in [line.split("=", 1)]
    })
    values.update({key: value for key, value in os.environ.items() if key in values})
    os.environ.update(values)
    return values


def load_configuration(config_file: Path | None = None) -> Configuration:
    """Read all settings from one explicit `.env` file and process overrides."""
    selected_file = config_file or ENV_FILE
    if not selected_file.is_file():
        raise RuntimeError(f"The MCP configuration does not exist: {selected_file}")
    values = _read_values(selected_file)
    if sys.version_info < (3, 12):
        raise RuntimeError(f"Python {sys.version.split()[0]} is unsupported; Python 3.12 or newer is required.")
    if values["MINECRAFT_VERSION"] != SUPPORTED_MINECRAFT_VERSION:
        raise RuntimeError(
            f"Minecraft {values['MINECRAFT_VERSION']} is unsupported; this MCP requires {SUPPORTED_MINECRAFT_VERSION}."
        )
    node = Path(shutil.which(values["NODE_EXE"]) or values["NODE_EXE"])
    body_entrypoint = Path(values["MCMCP_BODY_ENTRYPOINT"])
    browser_executable = Path(values["BROWSER_EXECUTABLE_PATH"])
    absent = [path for path in (node, body_entrypoint, browser_executable) if not path.is_file()]
    if absent:
        raise RuntimeError(f"Install or build these required files:\n{'\n'.join(str(path) for path in absent)}")
    version = subprocess.run([str(node), "--version"], check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
    major = int(version.removeprefix("v").split(".", 1)[0])
    if major < MINIMUM_NODE_MAJOR_VERSION:
        raise RuntimeError(f"Node.js {version} is unsupported; Node.js {MINIMUM_NODE_MAJOR_VERSION} or newer is required.")
    return Configuration(
        node, body_entrypoint, values["MCMCP_BODY_HOST"], int(values["MCMCP_BODY_PORT"]), int(values["MCMCP_VIEWER_PORT"]), browser_executable,
        values["MINECRAFT_HOST"], int(values["MINECRAFT_PORT"]), values["MINECRAFT_VERSION"], values["MINECRAFT_PLAYER"], Path(values["MCMCP_AGENT_HOME"]),
        values["MINECRAFT_RCON_HOST"], int(values["MINECRAFT_RCON_PORT"]), values["MINECRAFT_RCON_PASSWORD"], values["MCP_HOST"], int(values["MCP_PORT"]),
        values["MCMCP_TEST_MODE"].lower() == "true", float(values["MCMCP_WALK_REACHED_DISTANCE_BLOCKS"]),
        values["MCMCP_INSPECTOR_ENABLED"].lower() == "true", values["MCMCP_INSPECTOR_HOST"], int(values["MCMCP_INSPECTOR_PORT"]),
    )
