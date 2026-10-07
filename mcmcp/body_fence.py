"""Retain the body epoch at the server boundary after a client exits."""
from __future__ import annotations

import json
import os
from pathlib import Path
import threading

# A read can use an unowned connection. Scans and horizon reads rotate the body.
READ_TOOLS = frozenset({
    "minecraft_observe", "minecraft_count_inventory", "minecraft_inspect_block",
    "minecraft_find_block", "minecraft_find_interactables", "minecraft_raytrace",
    "minecraft_recipe_search", "minecraft_info", "minecraft_list_capabilities",
    "minecraft_list_waypoints", "minecraft_relative", "minecraft_distance",
    "minecraft_screenshot", "minecraft_analyze_area", "minecraft_find_path",
    "minecraft_is_safe_to_dig", "minecraft_recall", "minecraft_status",
})


class BodyFence:
    """Own the durable high-water epoch and a thread-local dispatch token.

    CommandGate holds its condition during validation and claim changes.
    A replacement claim waits for dispatched work, including a dead client.
    The receipt survives MCP restarts when the character directory survives.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"epoch": 0, "active": False}
        self.local = threading.local()
        if self.state["active"]:
            # A new body process has no observation from the old session.
            # Retain its high-water epoch and require a replacement claim.
            self.commit({**self.state, "active": False, "interrupted": "mcp_restart"})

    def commit(self, value: dict) -> dict:
        """Flush the next token before publishing it to callers."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(self.path)
        self.state = value
        return {"ok": True, **value}

    def validate(self, name: str, token: dict | None) -> None:
        """Reject stale commands before any runtime or body call."""
        if token is not None:
            if not self.state["active"] or any(token.get(key) != self.state.get(key) for key in ("epoch", "owner", "session")):
                raise PermissionError("Stale Minecraft body epoch.")
        elif self.state["active"] and name not in READ_TOOLS:
            raise PermissionError("The Minecraft body requires its active lease token.")
