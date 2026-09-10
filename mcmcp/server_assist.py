"""Run the small set of approved server-assisted survival actions.

Only typed methods can make RCON commands. No public tool accepts a command.
An RCON connection error is external. The command call raises that error.
An invalid generated name is a code error. The regular expression rejects it.
"""

from __future__ import annotations

import re

from mcrcon import MCRcon

from .config import Configuration
from .models import Vec3i


MINECRAFT_NAME = re.compile(r"(?:[a-z0-9_.-]+:)?[a-z0-9_./-]+")


class ServerAssist:
    """Give approved quality-of-life actions to one configured player."""

    def __init__(self, configuration: Configuration):
        self.configuration = configuration

    def require_babymode(self) -> None:
        reply = self._command("babymode version")
        version = re.search(r"Agentic Babymode v(\d+)\.(\d+)\.(\d+)", reply)
        if version is None or tuple(map(int, version.groups())) < (0, 5, 0):
            raise RuntimeError("Minecraft MCP requires Agentic Babymode 0.5.0 or newer on the server.")

    def has_player(self) -> bool:
        """Return whether RCON can execute as the Mineflayer player."""
        reply = self._command(
            f"execute as {self.configuration.player_name} run babymode version"
        )
        return "Agentic Babymode" in reply

    def kill_player(self) -> str:
        """Kill the configured player through the server console."""
        return self._command(f"kill {self.configuration.player_name}")

    def remove_items(self, item: str, count: int) -> str:
        """Remove an exact item count from the configured player."""
        name = self._name(item)
        return self._command(
            f"clear {self.configuration.player_name} {name} {count}"
        )

    def place_cells(self, material: str, cells: list[Vec3i]) -> list[str]:
        """Place blocks into cells already classified as replaceable."""
        name = self._name(material)
        with MCRcon(
            self.configuration.rcon_host,
            self.configuration.rcon_password,
            port=self.configuration.rcon_port,
        ) as client:
            return [
                client.command(
                    f"setblock {cell.x} {cell.y} {cell.z} {name} replace"
                )
                for cell in cells
            ]

    def pillar_step(self, material: str, cell: Vec3i, x: float, y: float, z: float) -> str:
        """Place one inventory block at the player's feet and move them above it."""
        name = self._name(material)
        reply = self._command(f"setblock {cell.x} {cell.y} {cell.z} {name} replace")
        if "Changed the block" not in reply:
            return reply
        self.remove_items(material, 1)
        self._command(f"tp {self.configuration.player_name} {x} {y + 1} {z}")
        return reply

    def _command(self, command: str) -> str:
        with MCRcon(
            self.configuration.rcon_host,
            self.configuration.rcon_password,
            port=self.configuration.rcon_port,
        ) as client:
            return client.command(command)

    def _name(self, value: str) -> str:
        if MINECRAFT_NAME.fullmatch(value) is None:
            raise ValueError(f"The Minecraft name is invalid: {value}")
        return value if ":" in value else f"minecraft:{value}"
