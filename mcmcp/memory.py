"""Store plain durable notes, waypoints, and skill descriptions.

A missing memory file means that the memory is empty.
Invalid JSON is a code or manual-edit error. The parser raises at that line.
File-system errors are permanent local errors. The operation raises them.
"""

from __future__ import annotations

from datetime import datetime, timezone
from fnmatch import fnmatchcase
import json
from pathlib import Path
import re
from uuid import uuid4

from .constants import RECALL_RESULT_LIMIT, WAYPOINT_CAPACITY
from .models import Capability, MemoryHit, Vec3i, Waypoint


MEMORY_KINDS = ("world", "places", "routes", "chests", "failures", "journal")


class AgentMemory:
    """Own the files in one character workspace."""

    def __init__(self, agent_home: Path):
        self.agent_home = agent_home
        self.memory_directory = agent_home / "memory"
        self.memory_directory.mkdir(parents=True, exist_ok=True)
        (agent_home / "drafts").mkdir(exist_ok=True)
        (agent_home / "skills").mkdir(exist_ok=True)
        self.waypoint_file = self.memory_directory / "waypoints.json"

    def reset(self) -> None:
        """Remove mutable test memory while preserving installed skills."""
        for path in self.memory_directory.iterdir():
            if path.is_file():
                path.unlink()
        for path in (self.agent_home / "drafts").iterdir():
            if path.is_file():
                path.unlink()

    def remember(self, kind: str, markdown: str) -> tuple[MemoryHit, int]:
        """Append one note and return the stored note and file count."""
        note = MemoryHit(
            kind=kind,
            file=self._relative(self._note_file(kind)),
            note_id=uuid4().hex,
            markdown=markdown,
            created_at=_now(),
        )
        with self._note_file(kind).open("a", encoding="utf-8") as file:
            file.write(json.dumps(note.model_dump(), ensure_ascii=False) + "\n")
            # Keep the original Markdown literally present for humans and for
            # durable-file verification. The JSON line remains authoritative.
            file.write(markdown + "\n")
        return note, len(self._read_notes(kind))

    def recall(self, pattern: str) -> tuple[list[MemoryHit], int]:
        """Search all notes and return the newest matching notes."""
        notes = [note for kind in MEMORY_KINDS for note in self._read_notes(kind)]
        glob = pattern if any(symbol in pattern for symbol in "*?[") else f"*{pattern}*"
        hits = [
            note
            for note in sorted(notes, key=lambda value: value.created_at, reverse=True)
            if fnmatchcase(f"{note.kind} {note.markdown}".lower(), glob.lower())
        ]
        return hits[:RECALL_RESULT_LIMIT], len(notes)

    def add_waypoint(
        self,
        description: str,
        position: Vec3i,
        dimension: str,
    ) -> tuple[Waypoint, list[Waypoint], Waypoint | None]:
        """Append one waypoint and remove the oldest item at capacity."""
        waypoints = self.list_waypoints()
        waypoint = Waypoint(
            id=uuid4().hex,
            description=description,
            position=position,
            dimension=dimension,
            tags=[],
            created_at=_now(),
            last_visited_at=None,
        )
        waypoints.append(waypoint)
        evicted = waypoints.pop(0) if len(waypoints) > WAYPOINT_CAPACITY else None
        self.waypoint_file.write_text(
            json.dumps([item.model_dump(mode="json") for item in waypoints], indent=2),
            encoding="utf-8",
        )
        return waypoint, waypoints, evicted

    def list_waypoints(self) -> list[Waypoint]:
        """Read all persistent waypoints in their stored order."""
        if not self.waypoint_file.is_file():
            return []
        return [
            Waypoint.model_validate(value)
            for value in json.loads(self.waypoint_file.read_text(encoding="utf-8"))
        ]

    def list_capabilities(self) -> list[Capability]:
        """Describe each TypeScript file in the skills directory."""
        return [
            Capability(
                name=path.stem,
                description=f"Reusable TypeScript skill: {path.stem}.",
                path=self._relative(path),
                arguments=_skill_arguments(path.read_text(encoding="utf-8")),
                required_items=[],
                stopping_conditions=[],
                postconditions=[],
            )
            for path in sorted((self.agent_home / "skills").glob("*.ts"))
        ]

    def _read_notes(self, kind: str) -> list[MemoryHit]:
        path = self._note_file(kind)
        if not path.is_file():
            return []
        return [
            MemoryHit.model_validate_json(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("{")
        ]

    def _note_file(self, kind: str) -> Path:
        return self.memory_directory / f"{kind}.jsonl"

    def _relative(self, path: Path) -> str:
        return path.relative_to(self.agent_home).as_posix()


def _skill_arguments(source: str) -> list[str]:
    match = re.search(r"arguments_\s*:\s*\{([^}]*)\}", source, re.DOTALL)
    if match is None:
        return []
    return re.findall(r"([A-Za-z_$][\w$]*)\s*:", match.group(1))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
