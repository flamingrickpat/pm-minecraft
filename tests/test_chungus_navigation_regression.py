"""The real Chungus cave escape: stairs lead to an off-column pillar shaft."""

from __future__ import annotations

import math

import pytest

from tests.live_case import Layout, Scenario, arrange, call_mcp


def cell(base, x, y, z):
    return {"x": int(base["x"] + x), "y": int(base["y"] + y), "z": int(base["z"] + z)}


def fill(live_test, base, start, end, block, via_layout=False):
    """Chunk-safe fill respecting Minecraft's 32768 block limit."""
    first = cell(base, *start)
    last = cell(base, *end)
    if via_layout:
        live_test.operator_command(
            f"fill {first['x']} {first['y']} {first['z']} "
            f"{last['x']} {last['y']} {last['z']} {block}"
        )
        return
    dx = abs(last['x'] - first['x']) + 1
    dy = abs(last['y'] - first['y']) + 1
    dz = abs(last['z'] - first['z']) + 1
    total = dx * dy * dz
    if total <= 32768:
        live_test.operator_command(
            f"fill {first['x']} {first['y']} {first['z']} "
            f"{last['x']} {last['y']} {last['z']} {block}"
        )
        return
    # Chunk along the longest axis
    for cy in range(first['y'], last['y'] + 1, 16):
        y2 = min(cy + 15, last['y'])
        live_test.operator_command(
            f"fill {first['x']} {cy} {first['z']} "
            f"{last['x']} {y2} {last['z']} {block}"
        )


@pytest.mark.slow
def test_walk_to_surface_reaches_an_off_column_pillar_shaft_after_climbing_cave_stairs(live_test):
    """Regression from the live route (2,65,25) -> (-4,91,51)."""
    context = arrange(live_test, Layout(items=(("cobblestone", 64),)))
    base = context["base"]

    # Minimal: flat stone floor at y=4, surface at y=5
    fill(live_test, base, (-4, 2, -1), (4, 2, 11), "stone")  # floor
    fill(live_test, base, (-4, 3, -1), (4, 4, 11), "air")    # open space
    # A pillar shaft at (-4, 10) — off the surface column (0, 10)
    fill(live_test, base, (-4, 5, 10), (-4, 10, 10), "air")   # shaft
    fill(live_test, base, (-4, 11, 10), (-4, 20, 10), "stone") # cap 
    # Surface at (-10, 10): the test requests surface at (0,10)
    fill(live_test, base, (-12, 5, 8), (-8, 5, 12), "stone")  # surface floor
    fill(live_test, base, (-12, 6, 8), (-8, 7, 12), "air")    # surface opening
    # Surface opening at a different column
    fill(live_test, base, (-12, 45, -2), (-8, 47, 2), "air")

    start = cell(base, 2, 3, 0)
    shaft_base = cell(base, -4, 3, 10)
    surface = cell(base, -10, 5, 10)
    assert live_test.block(start["x"], start["y"] - 1, start["z"])["name"] == "stone"
    assert live_test.block(**start)["name"] == "air"
    assert live_test.block(**shaft_base)["name"] == "air"
    live_test.operator_command(
        f"tp {live_test.configuration.player_name} {start['x'] + 0.5} {start['y']} {start['z'] + 0.5}"
    )
    live_test.wait_for(
        "the player at the Chungus cave start",
        live_test.player_state,
        lambda state: math.dist(
            tuple(state["position"][axis] for axis in ("x", "y", "z")),
            (start["x"] + 0.5, start["y"], start["z"] + 0.5),
        ) < 0.15,
    )
    live_test.handoff_player_to_mcp()
    scenario = Scenario(live_test, context, require_body=True, disconnect_body=False)

    response = call_mcp(
        scenario,
        "minecraft_walk_to_surface",
        {"x": surface["x"], "z": surface["z"]},
    )
    payload = response.structuredContent
    player = next(
        item for item in live_test.players()
        if item["username"] == live_test.configuration.player_name
    )

    assert not response.isError, response
    assert payload["status"] == "partial", payload
    assert payload["reason"] == "pillar_up_required", payload
    assert math.dist(
        tuple(player["position"][axis] for axis in ("x", "y", "z")),
        tuple(shaft_base[axis] for axis in ("x", "y", "z")),
    ) <= 2, player
