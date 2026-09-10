"""Compute Minecraft cells without world access."""

from __future__ import annotations

from collections.abc import Iterable

from .models import Box, Vec3i


def build_cells(
    shape: str,
    start: Vec3i,
    end: Vec3i | None,
    ref: Vec3i | None,
) -> tuple[list[Vec3i], Box]:
    """Return the exact ordered cells for one public build shape."""
    raw_end = end or start
    start = _absolute(start, ref)
    end = _absolute(raw_end, ref)
    minimum = Vec3i(
        x=min(start.x, end.x),
        y=min(start.y, end.y),
        z=min(start.z, end.z),
    )
    maximum = Vec3i(
        x=max(start.x, end.x),
        y=max(start.y, end.y),
        z=max(start.z, end.z),
    )
    bounds = Box(min=minimum, max=maximum)
    if shape == "staircase":
        return _line(start, end, include_y=True), bounds
    if shape == "bridge":
        return _line(start, end, include_y=False), bounds
    if shape == "column":
        return [
            Vec3i(x=start.x, y=y, z=start.z)
            for y in _inclusive(start.y, end.y)
        ], bounds

    cells = [
        Vec3i(x=x, y=y, z=z)
        for x in _inclusive(minimum.x, maximum.x)
        for y in _inclusive(minimum.y, maximum.y)
        for z in _inclusive(minimum.z, maximum.z)
    ]
    if shape == "fill":
        return cells, bounds
    if shape == "floor":
        return [cell for cell in cells if cell.y == minimum.y], bounds
    if shape == "ceiling":
        return [cell for cell in cells if cell.y == maximum.y], bounds
    if shape == "wall":
        return [
            cell for cell in cells
            if cell.x in (minimum.x, maximum.x)
            or cell.z in (minimum.z, maximum.z)
        ], bounds
    if shape == "shell":
        return [
            cell for cell in cells
            if cell.x in (minimum.x, maximum.x)
            or cell.y in (minimum.y, maximum.y)
            or cell.z in (minimum.z, maximum.z)
        ], bounds
    if shape == "frame":
        return [
            cell for cell in cells
            if sum(
                (
                    cell.x in (minimum.x, maximum.x),
                    cell.y in (minimum.y, maximum.y),
                    cell.z in (minimum.z, maximum.z),
                )
            ) >= 2
        ], bounds
    raise ValueError(f"The build shape is invalid: {shape}")


def _absolute(position: Vec3i, ref: Vec3i | None) -> Vec3i:
    if ref is None:
        return position
    return Vec3i(
        x=ref.x + position.x,
        y=ref.y + position.y,
        z=ref.z + position.z,
    )


def _inclusive(start: int, end: int) -> Iterable[int]:
    step = 1 if end >= start else -1
    return range(start, end + step, step)


def _line(start: Vec3i, end: Vec3i, include_y: bool) -> list[Vec3i]:
    steps = max(abs(end.x - start.x), abs(end.z - start.z))
    if include_y:
        steps = max(steps, abs(end.y - start.y))
    if steps == 0:
        return [start]
    return [
        Vec3i(
            x=round(start.x + (end.x - start.x) * index / steps),
            y=(
                round(start.y + (end.y - start.y) * index / steps)
                if include_y else start.y
            ),
            z=round(start.z + (end.z - start.z) * index / steps),
        )
        for index in range(steps + 1)
    ]
