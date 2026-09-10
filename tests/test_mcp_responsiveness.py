"""Live tests for the long-action responsiveness contract.

The failure this guards against: `minecraft_walk_to_exact` to an unreachable
target (an unclimbable wall / void gap) hung for the full action budget while
the bot never moved, cheap reads stopped answering, and `minecraft_stop` could
not preempt it.

Three contracts are pinned here:

1. An unreachable target terminates with `no_path`/`timeout` instead of hanging.
2. Cheap reads (`info`) and `stop` stay responsive while a long walk is
   running, because the body serves the walk and the HTTP API on one thread.
3. `stop` halts composite tools (harvest/mine/smelt) that chain inner walks,
   not just the single inner walk.
"""

from __future__ import annotations

import pytest

from tests.live_case import (
    BlockSpec,
    DuringAction,
    FillSpec,
    Layout,
    assert_background_stopped,
    begin_mcp_call,
    call_mcp,
    capture_truth,
    finish_mcp_call,
    parse_result,
    setup,
    wait_for_action,
)


def _giant_wall_layout() -> Layout:
    """A 4-tall bedrock wall spanning the whole playable width.

    The target sits behind it at the same height. The survival movements
    cannot dig (bedrock), cannot tower, and cannot jump 4 blocks, so there is
    no route across.
    """
    return Layout(
        blocks=(BlockSpec(key="destination", offset=(8, 0, 0), block="air", name="air"),),
        fills=(FillSpec(start=(4, 0, -40), end=(4, 3, 40), block="bedrock"),),
    )


def _void_gap_layout() -> Layout:
    """A full-width, 8-block trench with the ground removed down to a void.

    The target sits on the far side. A sprint jump reaches at most 3 blocks,
    so an 8-block trench is too wide to jump. The floor is removed down
    several layers so the player cannot drop into it either (maxDropDown=1).
    """
    return Layout(
        blocks=(BlockSpec(key="destination", offset=(12, 0, 0), block="air", name="air"),),
        # The surface (y=-1 offset) and the layers beneath it are removed so
        # there is no landing block within the 1-block drop allowance.
        fills=(FillSpec(start=(3, -5, -40), end=(10, 0, 40), block="air"),),
    )


def _far_unreachable_height_layout() -> Layout:
    """A raised 3-high platform far away, with the target standing on top.

    The player can walk the flat grass to the platform but cannot climb 3
    blocks (no tower/dig). The walk must fail fast -- instead the body wanders
    across the whole distance, loading chunks as it goes, before it gives up.
    """
    return Layout(
        blocks=(BlockSpec(key="destination", offset=(300, 3, 0), block="air", name="air"),),
        fills=(FillSpec(start=(298, 0, -2), end=(302, 2, 2), block="stone"),),
    )


def _lava_unreachable_layout() -> Layout:
    """A 3-up unreachable target with a lava fall pouring down beside the path.

    Matches the real end-to-end failure: the target stands on a 3-high platform
    the player cannot climb, and a lava source on an adjacent pillar flows down
    (flowing lava fires block updates that reset pathfinding).
    """
    return Layout(
        blocks=(
            BlockSpec(key="destination", offset=(8, 3, 0), block="air", name="air"),
            BlockSpec(key="lava_0", offset=(4, 3, 0), block="lava"),
        ),
        fills=(
            FillSpec(start=(6, 0, -2), end=(10, 2, 2), block="stone"),
            FillSpec(start=(4, 0, 0), end=(4, 2, 0), block="stone"),
        ),
    )


def _lava_reachable_layout() -> Layout:
    """A reachable walk past a flowing lava fall.

    The lava ledge sits beside the path (z=3), so the route stays open while
    flowing lava changes blocks adjacent to it. The body must keep answering
    cheap reads and stop while it pathfinds past the flow.
    """
    return Layout(
        blocks=(
            BlockSpec(key="destination", offset=(40, 0, 0), block="air", name="air"),
            BlockSpec(key="lava_0", offset=(12, 2, 3), block="lava"),
            BlockSpec(key="lava_1", offset=(13, 2, 4), block="lava"),
            BlockSpec(key="lava_2", offset=(14, 2, 5), block="lava"),
        ),
        fills=(
            FillSpec(start=(12, 0, 3), end=(14, 1, 5), block="stone"),
        ),
    )


def _reachable_layout(offset_x: int) -> Layout:
    """A flat reachable destination far enough that walking takes several seconds."""
    return Layout(
        blocks=(BlockSpec(key="destination", offset=(offset_x, 0, 0), block="air", name="air"),),
    )


def _oak_tree_layout() -> Layout:
    """Four oak logs with a canopy, matching the standard harvest_tree setup."""
    return Layout(
        blocks=(
            BlockSpec(key="log_0", offset=(3, 0, 0), block="oak_log"),
            BlockSpec(key="log_1", offset=(3, 1, 0), block="oak_log"),
            BlockSpec(key="log_2", offset=(3, 2, 0), block="oak_log"),
            BlockSpec(key="log_3", offset=(3, 3, 0), block="oak_log"),
            BlockSpec(key="leaf_0", offset=(2, 4, 0), block="oak_leaves[persistent=true]"),
            BlockSpec(key="leaf_1", offset=(3, 4, 0), block="oak_leaves[persistent=true]"),
            BlockSpec(key="leaf_2", offset=(4, 4, 0), block="oak_leaves[persistent=true]"),
        ),
        items=(("iron_axe", 1),),
    )


@pytest.mark.slow
def test_walk_to_exact_far_unreachable_height_terminates_promptly(live_test):
    # The same unreachable-height failure as the real end-to-end run: the bot
    # must not wander for minutes loading chunks before admitting there is no
    # way up. It must return no_path/timeout promptly.
    scenario = setup(live_test, layout=_far_unreachable_height_layout())
    truth_before = capture_truth(scenario)
    res = call_mcp(
        scenario,
        "minecraft_walk_to_exact",
        {"x": "$destination.x", "y": "$destination.y", "z": "$destination.z"},
        timeout=30,
    )
    result = parse_result(
        scenario,
        res,
        "minecraft_walk_to_exact",
        {"x": "$destination.x", "y": "$destination.y", "z": "$destination.z"},
        truth_before=truth_before,
    )
    assert result.ok is False
    assert result.reason in ("no_path", "timeout")


@pytest.mark.slow
def test_walk_to_exact_flowing_lava_unreachable_terminates(live_test):
    # The real failure: a 3-up target with flowing lava nearby. The walk must
    # still terminate instead of hanging while lava resets the path.
    scenario = setup(live_test, layout=_lava_unreachable_layout())
    truth_before = capture_truth(scenario)
    res = call_mcp(
        scenario,
        "minecraft_walk_to_exact",
        {"x": "$destination.x", "y": "$destination.y", "z": "$destination.z"},
        timeout=30,
    )
    result = parse_result(
        scenario,
        res,
        "minecraft_walk_to_exact",
        {"x": "$destination.x", "y": "$destination.y", "z": "$destination.z"},
        truth_before=truth_before,
    )
    assert result.ok is False
    assert result.reason in ("no_path", "timeout")


@pytest.mark.slow
def test_info_stays_responsive_during_walk_with_flowing_lava(live_test):
    # Flowing lava fires block updates along the route; the body must keep
    # answering cheap reads and stop while it pathfinds through them.
    scenario = setup(live_test, layout=_lava_reachable_layout())
    background = begin_mcp_call(
        scenario,
        "minecraft_walk_to_exact",
        {"x": "$destination.x", "y": "$destination.y", "z": "$destination.z"},
        timeout=60,
    )
    wait_for_action(scenario, DuringAction("player_moved", "player", ""))
    rejected = call_mcp(scenario, "minecraft_observe", {"include_image": False}, timeout=10)
    assert rejected.structuredContent["reason"] == "concurrent_tool_call"
    res = call_mcp(scenario, "minecraft_info", {}, timeout=10)
    assert res.isError is False
    assert res.structuredContent is not None
    assert res.structuredContent["ok"] is True

    call_mcp(scenario, "minecraft_stop", {"scope": "command"}, timeout=10)
    assert_background_stopped(
        finish_mcp_call(background, timeout=60),
        "minecraft_walk_to_exact",
        "stopped",
    )


@pytest.mark.slow
def test_walk_to_exact_giant_wall_terminates_promptly(live_test):
    scenario = setup(live_test, layout=_giant_wall_layout())
    truth_before = capture_truth(scenario)
    res = call_mcp(
        scenario,
        "minecraft_walk_to_exact",
        {"x": "$destination.x", "y": "$destination.y", "z": "$destination.z"},
        timeout=30,
    )
    result = parse_result(
        scenario,
        res,
        "minecraft_walk_to_exact",
        {"x": "$destination.x", "y": "$destination.y", "z": "$destination.z"},
        truth_before=truth_before,
    )
    assert result.ok is False
    assert result.reason in ("no_path", "timeout")


@pytest.mark.slow
def test_walk_to_exact_void_gap_terminates_promptly(live_test):
    scenario = setup(live_test, layout=_void_gap_layout())
    truth_before = capture_truth(scenario)
    res = call_mcp(
        scenario,
        "minecraft_walk_to_exact",
        {"x": "$destination.x", "y": "$destination.y", "z": "$destination.z"},
        timeout=30,
    )
    result = parse_result(
        scenario,
        res,
        "minecraft_walk_to_exact",
        {"x": "$destination.x", "y": "$destination.y", "z": "$destination.z"},
        truth_before=truth_before,
    )
    assert result.ok is False
    assert result.reason in ("no_path", "timeout")


@pytest.mark.slow
def test_info_stays_responsive_during_long_walk(live_test):
    scenario = setup(live_test, layout=_reachable_layout(40))
    background = begin_mcp_call(
        scenario,
        "minecraft_walk_to_exact",
        {"x": "$destination.x", "y": "$destination.y", "z": "$destination.z"},
        timeout=60,
    )
    wait_for_action(scenario, DuringAction("player_moved", "player", ""))
    rejected = call_mcp(scenario, "minecraft_observe", {"include_image": False}, timeout=10)
    assert rejected.structuredContent["reason"] == "concurrent_tool_call"
    res = call_mcp(scenario, "minecraft_info", {}, timeout=10)
    assert res.isError is False
    assert res.structuredContent is not None
    assert res.structuredContent["ok"] is True

    stop_res = call_mcp(scenario, "minecraft_stop", {"scope": "command"}, timeout=10)
    assert stop_res.isError is False
    assert stop_res.structuredContent["ok"] is True
    assert stop_res.structuredContent["stopped_command"] == "minecraft_walk_to_exact"
    assert_background_stopped(
        finish_mcp_call(background, timeout=60),
        "minecraft_walk_to_exact",
        "stopped",
    )


@pytest.mark.slow
def test_info_stays_responsive_during_long_walk_visible(live_test):
    # walk_to_visible shares the same body walk path as walk_to_exact, so the
    # same liveness guarantee must hold for the shared code.
    scenario = setup(live_test, layout=_reachable_layout(25))
    background = begin_mcp_call(
        scenario,
        "minecraft_walk_to_visible",
        {"x": "$destination.x", "y": "$destination.y", "z": "$destination.z"},
        timeout=60,
    )
    wait_for_action(scenario, DuringAction("player_moved", "player", ""))
    rejected = call_mcp(scenario, "minecraft_observe", {"include_image": False}, timeout=10)
    assert rejected.structuredContent["reason"] == "concurrent_tool_call"
    res = call_mcp(scenario, "minecraft_info", {}, timeout=10)
    assert res.isError is False
    assert res.structuredContent is not None
    assert res.structuredContent["ok"] is True

    call_mcp(scenario, "minecraft_stop", {"scope": "command"}, timeout=10)
    assert_background_stopped(
        finish_mcp_call(background, timeout=60),
        "minecraft_walk_to_visible",
        "stopped",
    )


@pytest.mark.slow
def test_find_path_giant_wall_terminates(live_test):
    # find_path shares the same pathfinder. It must report blocked/unknown
    # instead of hanging on an unreachable target.
    scenario = setup(live_test, layout=_giant_wall_layout())
    truth_before = capture_truth(scenario)
    res = call_mcp(
        scenario,
        "minecraft_find_path",
        {"x": "$destination.x", "y": "$destination.y", "z": "$destination.z"},
        timeout=30,
    )
    result = parse_result(
        scenario,
        res,
        "minecraft_find_path",
        {"x": "$destination.x", "y": "$destination.y", "z": "$destination.z"},
        truth_before=truth_before,
    )
    assert result.ok is True
    assert result.state in ("blocked", "unknown")


@pytest.mark.slow
def test_stop_halts_composite_harvest_tree(live_test):
    # Composite tools chain inner walk/mine calls in a loop. One stop must
    # halt the composite, not just the currently-running inner walk.
    scenario = setup(live_test, layout=_oak_tree_layout())
    truth_before = capture_truth(scenario)
    background = begin_mcp_call(
        scenario,
        "minecraft_harvest_tree",
        {"base": "$log_0"},
        timeout=90,
    )
    wait_for_action(scenario, DuringAction("player_moved", "player", ""))
    stop_res = call_mcp(scenario, "minecraft_stop", {"scope": "both"}, timeout=10)
    assert stop_res.isError is False
    assert stop_res.structuredContent["ok"] is True

    result = parse_result(
        scenario,
        finish_mcp_call(background, timeout=90),
        "minecraft_harvest_tree",
        {"base": "$log_0"},
        truth_before=truth_before,
    )
    # A stopped composite must not keep going and finish every log.
    assert result.logs_collected < 4
