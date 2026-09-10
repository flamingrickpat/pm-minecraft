"""Resolve exact names and globs at one external name boundary."""

from __future__ import annotations

from difflib import SequenceMatcher
from fnmatch import fnmatchcase
from typing import Protocol

from .models import NameCandidate


class Named(Protocol):
    """The fields required for name resolution."""

    name: str
    display_name: str


def matching(pattern: str, values: list[Named]) -> list[Named]:
    """Prefer one exact name, then return case-insensitive substring matches."""
    exact = [value for value in values if value.name.lower() == pattern.lower()]
    if exact:
        return exact
    substring = f"*{pattern}*"
    return sorted(
        [value for value in values if fnmatchcase(value.name.lower(), substring.lower())],
        key=lambda value: value.name,
    )


def candidates(pattern: str, values: list[Named]) -> list[NameCandidate]:
    """Return close names for an unknown external name."""
    ranked = sorted(
        values,
        key=lambda value: SequenceMatcher(
            None, pattern.lower(), value.name.lower()
        ).ratio(),
        reverse=True,
    )[:5]
    return [
        NameCandidate(
            name=value.name,
            display_name=value.display_name,
            similarity=SequenceMatcher(
                None, pattern.lower(), value.name.lower()
            ).ratio(),
            match_kind=(
                "prefix"
                if value.name.startswith(pattern.lower())
                or pattern.lower().startswith(value.name)
                else "fuzzy"
            ),
        )
        for value in ranked
    ]


def glob_candidates(values: list[Named]) -> list[NameCandidate]:
    """Convert glob matches into actionable exact-name choices."""
    return [
        NameCandidate(
            name=value.name,
            display_name=value.display_name,
            similarity=1.0,
            match_kind="glob",
        )
        for value in values
    ]
