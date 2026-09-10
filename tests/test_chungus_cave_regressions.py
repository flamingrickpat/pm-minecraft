"""Failing live regressions distilled from the Chungus survival playtest.

These cases deliberately use real cave geometry and the real MCP stack. Each
test describes behavior required to make the failed run recoverable. The
flowing-water case documents movement that remains unsupported.
"""

from __future__ import annotations

import math
import time

import pytest

from tests.live_case import Layout, Scenario, arrange, call_mcp


def _cell(base, x, y, z):
    return {
        "x": int(base["x"] + x),
        "y": int(base["y"] + y),
        "z": int(base["z"] + z),
    }


def _fill(live_test, base, start, end, block):
    first = _cell(base, *start)
    last = _cell(base, *end)
    live_test.operator_command(
        f"fill {first['x']} {first['y']} {first['z']} "
        f"{last['x']} {last['y']} {last['z']} {block}"
    )


def _setblock(live_test, base, offset, block):
    position = _cell(base, *offset)
    live_test.operator_command(
        f"setblock {position['x']} {position['y']} {position['z']} {block}"
    )
    return position


def _handoff_in_cave(live_test, context, player_offset):
    base = context["base"]
    position = {
        "x": base["x"] + player_offset[0],
        "y": base["y"] + player_offset[1],
        "z": base["z"] + player_offset[2],
    }
    live_test.operator_command(
        f"tp {live_test.configuration.player_name} "
        f"{position['x']} {position['y']} {position['z']} 0 0"
    )
    live_test.wait_for(
        "the player at the arranged cave start",
        live_test.player_state,
        lambda state: math.dist(
            tuple(state["position"][axis] for axis in ("x", "y", "z")),
            tuple(position[axis] for axis in ("x", "y", "z")),
        ) < 0.15,
    )
    context["player"] = position
    live_test.handoff_player_to_mcp()
    return Scenario(live_test, context, require_body=True, disconnect_body=False)


def _natural_cavern(live_test, item, target_offset, target_block):
    """Create a broad, irregular cave whose void cells are cave_air."""
    context = arrange(live_test, Layout(items=((item, 4),)))
    base = context["base"]

    # A stone envelope with an uneven main chamber, two side galleries, a
    # raised shelf, a flooded alcove, and mineral/decorative wall patches.
    _fill(live_test, base, (-18, 1, -14), (18, 15, 14), "stone")
    _fill(live_test, base, (-8, 3, -5), (8, 9, 5), "cave_air")
    _fill(live_test, base, (-16, 4, -2), (-8, 6, 2), "cave_air")
    _fill(live_test, base, (8, 5, -3), (16, 8, 3), "cave_air")
    _fill(live_test, base, (-4, 9, -3), (4, 11, 3), "cave_air")
    _fill(live_test, base, (9, 3, 6), (15, 6, 11), "cave_air")
    _fill(live_test, base, (8, 4, 3), (10, 6, 7), "cave_air")
    _fill(live_test, base, (10, 3, 7), (14, 3, 10), "water")
    _fill(live_test, base, (-7, 2, -4), (-3, 2, 1), "moss_block")
    _fill(live_test, base, (3, 2, -4), (7, 2, 0), "gravel")
    _setblock(live_test, base, (-8, 6, -1), "coal_ore")
    _setblock(live_test, base, (-8, 7, 0), "iron_ore")
    _setblock(live_test, base, (8, 7, 2), "copper_ore")
    _setblock(live_test, base, (-3, 10, 0), "pointed_dripstone[vertical_direction=down]")
    target = _setblock(live_test, base, target_offset, target_block)
    context["target"] = target

    assert live_test.block(**target)["name"] == target_block.split("[", 1)[0]
    return _handoff_in_cave(live_test, context, (0.5, 3, 0.5))


@pytest.mark.slow
@pytest.mark.parametrize(
    ("material", "target_offset", "target_block"),
    [
        pytest.param("crafting_table", (12, 3, 8), "water", id="crafting-table-in-shallow-water"),
        pytest.param(
            "torch",
            (0, 5, 5),
            "glow_lichen[south=true]",
            id="torch-replacing-wall-lichen",
        ),
    ],
)
def test_build_replaces_nonsolid_cave_block_without_waiting_for_timeout(
    live_test, material, target_offset, target_block
):
    scenario = _natural_cavern(live_test, material, target_offset, target_block)

    started = time.monotonic()
    response = call_mcp(
        scenario,
        "minecraft_build",
        {
            "shape": "fill",
            "material": material,
            "start": "$target",
            "end": "$target",
            "include_image": False,
        },
        timeout=45,
    )
    elapsed = time.monotonic() - started
    payload = response.structuredContent
    actual = live_test.block(**scenario.context["target"])["name"]

    assert elapsed < 2, payload
    assert not response.isError, response
    assert payload["ok"], payload
    assert payload["placed_count"] == 1, payload
    assert actual == material


def _winding_gallery_and_open_mine_shaft(live_test):
    context = arrange(live_test, Layout(items=(("cobblestone", 64),)))
    base = context["base"]

    # This models a player-made branch mine opening into a cave and ending at
    # the bottom of a straight-down access shaft.  The route to the shaft is
    # walkable, but reaching the surface requires pillaring in the open shaft.
    _fill(live_test, base, (-18, 1, -12), (18, 18, 12), "deepslate")
    _fill(live_test, base, (-13, 2, -6), (-5, 8, 6), "cave_air")
    _fill(live_test, base, (-5, 2, -1), (1, 4, 1), "air")
    _fill(live_test, base, (1, 2, -1), (3, 4, 5), "air")
    _fill(live_test, base, (3, 2, 3), (8, 4, 5), "air")
    _fill(live_test, base, (7, 2, 0), (10, 4, 5), "air")
    _fill(live_test, base, (9, 2, -1), (11, 4, 1), "air")
    _fill(live_test, base, (10, 2, 0), (10, 22, 0), "air")
    _fill(live_test, base, (-12, 1, -5), (-8, 1, -2), "moss_block")
    _setblock(live_test, base, (-5, 5, 0), "iron_ore")
    _setblock(live_test, base, (3, 5, 4), "coal_ore")
    _setblock(live_test, base, (8, 5, 4), "copper_ore")

    context["shaft_base"] = _cell(base, 10, 2, 0)
    context["surface"] = _cell(base, 10, 19, 0)
    assert live_test.block(**context["shaft_base"])["name"] == "air"
    assert live_test.block(context["surface"]["x"] - 1, context["surface"]["y"] - 1, context["surface"]["z"])["name"] == "deepslate"
    return _handoff_in_cave(live_test, context, (-10.5, 2, 0.5))


@pytest.mark.slow
def test_walk_to_surface_returns_partial_route_when_open_shaft_needs_pillaring(live_test):
    scenario = _winding_gallery_and_open_mine_shaft(live_test)
    response = call_mcp(
        scenario,
        "minecraft_walk_to_surface",
        {"x": "$surface.x", "z": "$surface.z"},
    )
    payload = response.structuredContent
    player = next(
        value
        for value in live_test.players()
        if value["username"] == live_test.configuration.player_name
    )

    assert not response.isError, response
    assert not payload["ok"], payload
    assert payload["status"] == "partial", payload
    assert payload["reason"] == "pillar_up_required", payload
    assert payload["requested"]["y"] >= scenario.context["surface"]["y"] - 1, payload
    assert math.dist(
        tuple(player["position"][axis] for axis in ("x", "y", "z")),
        tuple(scenario.context["shaft_base"][axis] for axis in ("x", "y", "z")),
    ) <= 2, player


@pytest.mark.slow
def test_walk_to_surface_escapes_a_mine_through_a_flowing_water_shaft(live_test):
    context = arrange(live_test, Layout())
    base = context["base"]

    _fill(live_test, base, (-14, 1, -10), (14, 18, 10), "stone")
    _fill(live_test, base, (-11, 2, -5), (-4, 8, 5), "cave_air")
    _fill(live_test, base, (-4, 2, -1), (8, 4, 1), "air")
    _fill(live_test, base, (8, 2, 0), (8, 22, 0), "air")
    _fill(live_test, base, (-10, 1, -4), (-7, 1, 0), "moss_block")
    _setblock(live_test, base, (-4, 5, 1), "coal_ore")
    _setblock(live_test, base, (5, 5, -1), "iron_ore")
    context["surface"] = _cell(base, 8, 19, 0)

    scenario = _handoff_in_cave(live_test, context, (-9.5, 2, 0.5))
    source = _setblock(live_test, base, (8, 18, 0), "water")
    shaft_bottom = _cell(base, 8, 2, 0)
    live_test.wait_for(
        "water flowing to the bottom of the mine shaft",
        lambda: live_test.block(**shaft_bottom),
        lambda block: block["name"] == "water",
    )
    assert live_test.block(**source)["properties"]["level"] == "0"
    assert live_test.block(**shaft_bottom)["properties"]["level"] != "0"

    response = call_mcp(
        scenario,
        "minecraft_walk_to_surface",
        {"x": "$surface.x", "z": "$surface.z"},
    )
    payload = response.structuredContent
    player = next(
        value
        for value in live_test.players()
        if value["username"] == live_test.configuration.player_name
    )

    assert not response.isError, response
    assert payload["ok"], payload
    assert payload["status"] == "reached", payload
    assert player["position"]["y"] >= scenario.context["surface"]["y"] - 1, player


def _ravine_with_separate_ore_bodies(live_test):
    context = arrange(
        live_test,
        Layout(slot_items=(("hotbar.0", "stone_pickaxe", 1),)),
    )
    base = context["base"]

    # Two galleries face each other across a deep ravine.  The three near ores
    # form one connected exposed vein.  Four far ores are a separate body and
    # cannot be reached without a bridge or a dangerous drop.
    _fill(live_test, base, (-18, 1, -12), (18, 14, 12), "stone")
    _fill(live_test, base, (-14, 3, -7), (-1, 10, 7), "cave_air")
    _fill(live_test, base, (5, 2, -8), (16, 11, 8), "cave_air")
    _fill(live_test, base, (0, -10, -8), (4, 10, 8), "cave_air")
    _fill(live_test, base, (-13, 2, -6), (-8, 2, -2), "moss_block")
    _fill(live_test, base, (-6, 2, 3), (-2, 2, 6), "water")
    _fill(live_test, base, (7, 1, -6), (12, 1, -2), "lava")

    near = [
        _setblock(live_test, base, (-1, 4, -1), "iron_ore"),
        _setblock(live_test, base, (-1, 5, -1), "iron_ore"),
        _setblock(live_test, base, (-1, 4, 0), "iron_ore"),
    ]
    far = [
        _setblock(live_test, base, (5, 4, -1), "iron_ore"),
        _setblock(live_test, base, (5, 5, -1), "iron_ore"),
        _setblock(live_test, base, (5, 4, 0), "iron_ore"),
        _setblock(live_test, base, (6, 4, 0), "iron_ore"),
    ]
    context["near_ore"] = near
    context["far_ore"] = far
    return _handoff_in_cave(live_test, context, (-4.5, 3, 0.5))


@pytest.mark.slow
def test_mine_vein_only_reports_blocks_mined_from_one_connected_reachable_body(live_test):
    scenario = _ravine_with_separate_ore_bodies(live_test)
    response = call_mcp(scenario, "minecraft_mine_vein", {"block": "iron_ore"})
    payload = response.structuredContent
    reported = {
        (cell["x"], cell["y"], cell["z"])
        for cell in payload["mined_cells"]
    }
    near = {
        (cell["x"], cell["y"], cell["z"])
        for cell in scenario.context["near_ore"]
    }
    far = {
        (cell["x"], cell["y"], cell["z"])
        for cell in scenario.context["far_ore"]
    }
    far_still_present = {
        position
        for position in far
        if live_test.block(*position)["name"] == "iron_ore"
    }

    assert not response.isError, response
    assert reported == near, payload
    assert payload["mined_count"] == len(near), payload
    assert far_still_present == far
    assert live_test.inventory_count("raw_iron") >= len(near)
