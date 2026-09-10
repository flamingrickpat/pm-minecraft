"""Live cave exits through a one-wide staircase with three air cells per step."""

import math

import pytest

from tests.live_case import Layout, arrange
from tests.live_case import BlockSpec, call_mcp, setup


def test_surface_uses_dry_ground_next_to_water_target(live_test):
    scenario = setup(live_test, Layout(blocks=(BlockSpec("water", (6, -1, 0), "water"),)))
    response = call_mcp(scenario, "minecraft_walk_to_surface", {"x": "$water.x", "z": "$water.z"})
    assert not response.isError, response
    assert response.structuredContent["ok"], response.structuredContent
    position = next(p for p in live_test.players() if p["username"] == live_test.configuration.player_name)["position"]
    floor = live_test.block(math.floor(position["x"]), math.floor(position["y"]) - 1, math.floor(position["z"]))
    assert floor["name"] != "water", position


@pytest.mark.parametrize("turn", [False, True], ids=["straight", "turn"])
@pytest.mark.parametrize("tool", ["walk_to_visible", "walk_to_exact", "walk_to_surface", "find_path"])
def test_walk_out_of_low_staircase(live_test, tool, turn):
    base = arrange(live_test, Layout())["base"]
    bx, by, bz = (base[axis] for axis in ("x", "y", "z"))

    def fill(start, end, block):
        a = [base[axis] + value for axis, value in zip(("x", "y", "z"), start)]
        b = [base[axis] + value for axis, value in zip(("x", "y", "z"), end)]
        live_test.operator_command(f"fill {' '.join(map(str, a + b))} {block}")

    fill((-8, 0, -8), (24, 11, 24), "stone")
    fill((-8, 12, -8), (24, 12, 24), "dirt")
    steps = [(i, i + 1, 0) if not turn or i < 6 else (5, i + 1, i - 5) for i in range(13)]
    for x, y, z in steps:
        fill((x, y, z), (x, y + 2, z), "air")
    for x, y, z in steps:
        assert live_test.block(bx + x, by + y - 1, bz + z)["name"] in ("stone", "dirt")
        for dy in range(3):
            assert live_test.block(bx + x, by + y + dy, bz + z)["name"] == "air"
    x, y, z = steps[-1]
    # The roof target lies above the start: the exit requires a horizontal detour.
    target = {"x": bx, "y": by + y, "z": bz}
    player = live_test.configuration.player_name
    live_test.operator_command(f"tp {player} {bx + 0.5} {by + 1} {bz + 0.5}")
    live_test.handoff_player_to_mcp()
    args = {axis: value for axis, value in target.items() if tool != "walk_to_surface" or axis != "y"}
    response = live_test.call_tool(f"minecraft_{tool}", args)
    assert not response.isError, response
    result = response.structuredContent
    assert result["ok"], result
    position = next(p for p in live_test.players() if p["username"] == player)["position"]
    if tool == "find_path":
        assert result["state"] == "reachable", result
        assert math.dist(tuple(position.values()), (bx + 0.5, by + 1, bz + 0.5)) < 0.2
        return
    assert abs(position["y"] - target["y"]) < 0.2, position
    assert math.dist((position["x"], position["z"]), (target["x"] + 0.5, target["z"] + 0.5)) < 3, position
