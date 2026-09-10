"""Live tests for minecraft_walk_to_visible. Each test states its complete setup, MCP call, and assertions."""

import pytest

from mcmcp.constants import VISIBLE_WALK_TOLERANCE_BLOCKS
from tests.live_case import Approx, BlockSpec, DuringAction, FillSpec, Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, call_mcp_during, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_walk_to_visible_flat_reachable(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    8,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_field(scenario, result, 'requested', '$destination')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=VISIBLE_WALK_TOLERANCE_BLOCKS,
    ),))


def test_walk_to_visible_spiral_staircase(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='step_1',
                    offset=(
                        1,
                        0,
                        0,
                    ),
                    block='polished_andesite',
                ),
                BlockSpec(
                    key='step_2',
                    offset=(
                        1,
                        1,
                        1,
                    ),
                    block='polished_andesite',
                ),
                BlockSpec(
                    key='step_3',
                    offset=(
                        0,
                        2,
                        1,
                    ),
                    block='polished_andesite',
                ),
                BlockSpec(
                    key='step_4',
                    offset=(
                        0,
                        3,
                        0,
                    ),
                    block='polished_andesite',
                ),
                BlockSpec(
                    key='destination',
                    offset=(
                        0,
                        4,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=VISIBLE_WALK_TOLERANCE_BLOCKS,
    ),))



@pytest.mark.smoke
def test_walk_to_visible_sealed_wall(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    4,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            fills=(
                # Closed bedrock shell: walls and roof, no gaps to walk around.
                FillSpec(
                    start=(
                        1,
                        0,
                        -3,
                    ),
                    end=(
                        1,
                        4,
                        3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        7,
                        0,
                        -3,
                    ),
                    end=(
                        7,
                        4,
                        3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        2,
                        0,
                        -3,
                    ),
                    end=(
                        6,
                        4,
                        -3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        2,
                        0,
                        3,
                    ),
                    end=(
                        6,
                        4,
                        3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        2,
                        4,
                        -2,
                    ),
                    end=(
                        6,
                        4,
                        2,
                    ),
                    block='bedrock',
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_visible_void_cut(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    4,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            fills=(
                # Chasm moat: a closed ring around the destination island,
                # too wide to jump (no parkour) and too deep to enter.
                FillSpec(
                    start=(
                        1,
                        -4,
                        -4,
                    ),
                    end=(
                        2,
                        -1,
                        4,
                    ),
                    block='air',
                ),
                FillSpec(
                    start=(
                        6,
                        -4,
                        -4,
                    ),
                    end=(
                        9,
                        -1,
                        4,
                    ),
                    block='air',
                ),
                FillSpec(
                    start=(
                        3,
                        -4,
                        -4,
                    ),
                    end=(
                        5,
                        -1,
                        -2,
                    ),
                    block='air',
                ),
                FillSpec(
                    start=(
                        3,
                        -4,
                        2,
                    ),
                    end=(
                        5,
                        -1,
                        4,
                    ),
                    block='air',
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_visible_negative_coordinates(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    -8,
                    0,
                    -8,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=VISIBLE_WALK_TOLERANCE_BLOCKS,
    ),))


def test_walk_to_visible_local_search_distance_boundary(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'destination',
                (
                    32.5,
                    0,
                    0.5,
                ),
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_field(scenario, result, 'requested', '$destination')
    assert_field(scenario, result, 'distance_remaining', Approx(
        value=0,
    ))
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=VISIBLE_WALK_TOLERANCE_BLOCKS,
    ),))


def test_walk_to_visible_outside_local_search_distance(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'destination',
                (
                    33.5,
                    0,
                    0.5,
                ),
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_visible_cross_slabs(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='surface_0',
                    offset=(
                        2,
                        -1,
                        0,
                    ),
                    block='stone_slab[type=bottom]',
                ),
                BlockSpec(
                    key='surface_1',
                    offset=(
                        3,
                        -1,
                        0,
                    ),
                    block='stone_slab[type=bottom]',
                ),
                BlockSpec(
                    key='surface_2',
                    offset=(
                        4,
                        -1,
                        0,
                    ),
                    block='stone_slab[type=bottom]',
                ),
                BlockSpec(
                    key='surface_3',
                    offset=(
                        5,
                        -1,
                        0,
                    ),
                    block='stone_slab[type=bottom]',
                ),
                BlockSpec(
                    key='surface_4',
                    offset=(
                        6,
                        -1,
                        0,
                    ),
                    block='stone_slab[type=bottom]',
                ),
                BlockSpec(
                    key='surface_5',
                    offset=(
                        7,
                        -1,
                        0,
                    ),
                    block='stone_slab[type=bottom]',
                ),
                BlockSpec(
                    key='destination',
                    offset=(
                        7,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=VISIBLE_WALK_TOLERANCE_BLOCKS,
    ),))


def test_walk_to_visible_cross_stairs(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='surface_0',
                    offset=(
                        2,
                        -1,
                        0,
                    ),
                    block='stone_stairs[facing=east,half=bottom]',
                ),
                BlockSpec(
                    key='surface_1',
                    offset=(
                        3,
                        -1,
                        0,
                    ),
                    block='stone_stairs[facing=east,half=bottom]',
                ),
                BlockSpec(
                    key='surface_2',
                    offset=(
                        4,
                        -1,
                        0,
                    ),
                    block='stone_stairs[facing=east,half=bottom]',
                ),
                BlockSpec(
                    key='surface_3',
                    offset=(
                        5,
                        -1,
                        0,
                    ),
                    block='stone_stairs[facing=east,half=bottom]',
                ),
                BlockSpec(
                    key='surface_4',
                    offset=(
                        6,
                        -1,
                        0,
                    ),
                    block='stone_stairs[facing=east,half=bottom]',
                ),
                BlockSpec(
                    key='surface_5',
                    offset=(
                        7,
                        -1,
                        0,
                    ),
                    block='stone_stairs[facing=east,half=bottom]',
                ),
                BlockSpec(
                    key='destination',
                    offset=(
                        7,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=VISIBLE_WALK_TOLERANCE_BLOCKS,
    ),))


def test_walk_to_visible_cross_soul_sand(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='surface_0',
                    offset=(
                        2,
                        -1,
                        0,
                    ),
                    block='soul_sand',
                ),
                BlockSpec(
                    key='surface_1',
                    offset=(
                        3,
                        -1,
                        0,
                    ),
                    block='soul_sand',
                ),
                BlockSpec(
                    key='surface_2',
                    offset=(
                        4,
                        -1,
                        0,
                    ),
                    block='soul_sand',
                ),
                BlockSpec(
                    key='surface_3',
                    offset=(
                        5,
                        -1,
                        0,
                    ),
                    block='soul_sand',
                ),
                BlockSpec(
                    key='surface_4',
                    offset=(
                        6,
                        -1,
                        0,
                    ),
                    block='soul_sand',
                ),
                BlockSpec(
                    key='surface_5',
                    offset=(
                        7,
                        -1,
                        0,
                    ),
                    block='soul_sand',
                ),
                BlockSpec(
                    key='destination',
                    offset=(
                        7,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=VISIBLE_WALK_TOLERANCE_BLOCKS,
    ),))


def test_walk_to_visible_cross_open_gate(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='surface_0',
                    offset=(
                        2,
                        -1,
                        0,
                    ),
                    block='oak_fence_gate[facing=east,open=true]',
                ),
                BlockSpec(
                    key='surface_1',
                    offset=(
                        3,
                        -1,
                        0,
                    ),
                    block='oak_fence_gate[facing=east,open=true]',
                ),
                BlockSpec(
                    key='surface_2',
                    offset=(
                        4,
                        -1,
                        0,
                    ),
                    block='oak_fence_gate[facing=east,open=true]',
                ),
                BlockSpec(
                    key='surface_3',
                    offset=(
                        5,
                        -1,
                        0,
                    ),
                    block='oak_fence_gate[facing=east,open=true]',
                ),
                BlockSpec(
                    key='surface_4',
                    offset=(
                        6,
                        -1,
                        0,
                    ),
                    block='oak_fence_gate[facing=east,open=true]',
                ),
                BlockSpec(
                    key='surface_5',
                    offset=(
                        7,
                        -1,
                        0,
                    ),
                    block='oak_fence_gate[facing=east,open=true]',
                ),
                BlockSpec(
                    key='destination',
                    offset=(
                        7,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=VISIBLE_WALK_TOLERANCE_BLOCKS,
    ),))



@pytest.mark.contract
def test_walk_to_visible_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': 0, 'y': 0, 'z': 0}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_walk_to_visible_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {}, timeout=660)
    assert_protocol_error(res, 'x')



@pytest.mark.contract
def test_walk_to_visible_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': {'wrong': True}, 'y': 0, 'z': 0}, timeout=660)
    assert_protocol_error(res, 'x')


def test_walk_to_visible_destination_blocked_during_walk(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    12,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_walk_to_visible',
        {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'},
        DuringAction(
            wait='player_moved',
            target='destination',
            command='setblock {destination_x} {destination_y} {destination_z} stone',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='destination',
        expected='stone',
    ),))


def test_walk_to_visible_flat_reachable__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    8,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            equipment=(
                (
                    'armor.head',
                    'iron_helmet',
                ),
                (
                    'armor.chest',
                    'iron_chestplate',
                ),
                (
                    'armor.legs',
                    'iron_leggings',
                ),
                (
                    'armor.feet',
                    'iron_boots',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_field(scenario, result, 'requested', '$destination')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=VISIBLE_WALK_TOLERANCE_BLOCKS,
    ),))


def test_walk_to_visible_flat_reachable__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    8,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_field(scenario, result, 'requested', '$destination')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=VISIBLE_WALK_TOLERANCE_BLOCKS,
    ),))


def test_walk_to_visible_flat_reachable__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    8,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_field(scenario, result, 'requested', '$destination')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=VISIBLE_WALK_TOLERANCE_BLOCKS,
    ),))


def test_walk_to_visible_flat_reachable__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    8,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_field(scenario, result, 'requested', '$destination')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=VISIBLE_WALK_TOLERANCE_BLOCKS,
    ),))


def test_walk_to_visible_flat_reachable__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    8,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_field(scenario, result, 'requested', '$destination')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=VISIBLE_WALK_TOLERANCE_BLOCKS,
    ),))


def test_walk_to_visible_flat_reachable__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    8,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            items=(
                (
                    'wheat_seeds',
                    13,
                ),
                (
                    'string',
                    7,
                ),
                (
                    'poisonous_potato',
                    2,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_field(scenario, result, 'requested', '$destination')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=VISIBLE_WALK_TOLERANCE_BLOCKS,
    ),))


def test_walk_to_visible_sealed_wall__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    4,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            fills=(
                # Closed bedrock shell: walls and roof, no gaps to walk around.
                FillSpec(
                    start=(
                        1,
                        0,
                        -3,
                    ),
                    end=(
                        1,
                        4,
                        3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        7,
                        0,
                        -3,
                    ),
                    end=(
                        7,
                        4,
                        3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        2,
                        0,
                        -3,
                    ),
                    end=(
                        6,
                        4,
                        -3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        2,
                        0,
                        3,
                    ),
                    end=(
                        6,
                        4,
                        3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        2,
                        4,
                        -2,
                    ),
                    end=(
                        6,
                        4,
                        2,
                    ),
                    block='bedrock',
                ),
            ),
            equipment=(
                (
                    'armor.head',
                    'iron_helmet',
                ),
                (
                    'armor.chest',
                    'iron_chestplate',
                ),
                (
                    'armor.legs',
                    'iron_leggings',
                ),
                (
                    'armor.feet',
                    'iron_boots',
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_visible_sealed_wall__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    4,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            fills=(
                # Closed bedrock shell: walls and roof, no gaps to walk around.
                FillSpec(
                    start=(
                        1,
                        0,
                        -3,
                    ),
                    end=(
                        1,
                        4,
                        3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        7,
                        0,
                        -3,
                    ),
                    end=(
                        7,
                        4,
                        3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        2,
                        0,
                        -3,
                    ),
                    end=(
                        6,
                        4,
                        -3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        2,
                        0,
                        3,
                    ),
                    end=(
                        6,
                        4,
                        3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        2,
                        4,
                        -2,
                    ),
                    end=(
                        6,
                        4,
                        2,
                    ),
                    block='bedrock',
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_visible_sealed_wall__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    4,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            fills=(
                # Closed bedrock shell: walls and roof, no gaps to walk around.
                FillSpec(
                    start=(
                        1,
                        0,
                        -3,
                    ),
                    end=(
                        1,
                        4,
                        3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        7,
                        0,
                        -3,
                    ),
                    end=(
                        7,
                        4,
                        3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        2,
                        0,
                        -3,
                    ),
                    end=(
                        6,
                        4,
                        -3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        2,
                        0,
                        3,
                    ),
                    end=(
                        6,
                        4,
                        3,
                    ),
                    block='bedrock',
                ),
                FillSpec(
                    start=(
                        2,
                        4,
                        -2,
                    ),
                    end=(
                        6,
                        4,
                        2,
                    ),
                    block='bedrock',
                ),
            ),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_visible_void_cut__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    4,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            fills=(
                # Chasm moat: a closed ring around the destination island,
                # too wide to jump (no parkour) and too deep to enter.
                FillSpec(
                    start=(
                        1,
                        -4,
                        -4,
                    ),
                    end=(
                        2,
                        -1,
                        4,
                    ),
                    block='air',
                ),
                FillSpec(
                    start=(
                        6,
                        -4,
                        -4,
                    ),
                    end=(
                        9,
                        -1,
                        4,
                    ),
                    block='air',
                ),
                FillSpec(
                    start=(
                        3,
                        -4,
                        -4,
                    ),
                    end=(
                        5,
                        -1,
                        -2,
                    ),
                    block='air',
                ),
                FillSpec(
                    start=(
                        3,
                        -4,
                        2,
                    ),
                    end=(
                        5,
                        -1,
                        4,
                    ),
                    block='air',
                ),
            ),
            equipment=(
                (
                    'armor.head',
                    'iron_helmet',
                ),
                (
                    'armor.chest',
                    'iron_chestplate',
                ),
                (
                    'armor.legs',
                    'iron_leggings',
                ),
                (
                    'armor.feet',
                    'iron_boots',
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_visible_void_cut__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    4,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            fills=(
                # Chasm moat: a closed ring around the destination island,
                # too wide to jump (no parkour) and too deep to enter.
                FillSpec(
                    start=(
                        1,
                        -4,
                        -4,
                    ),
                    end=(
                        2,
                        -1,
                        4,
                    ),
                    block='air',
                ),
                FillSpec(
                    start=(
                        6,
                        -4,
                        -4,
                    ),
                    end=(
                        9,
                        -1,
                        4,
                    ),
                    block='air',
                ),
                FillSpec(
                    start=(
                        3,
                        -4,
                        -4,
                    ),
                    end=(
                        5,
                        -1,
                        -2,
                    ),
                    block='air',
                ),
                FillSpec(
                    start=(
                        3,
                        -4,
                        2,
                    ),
                    end=(
                        5,
                        -1,
                        4,
                    ),
                    block='air',
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_visible_void_cut__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    4,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            fills=(
                # Chasm moat: a closed ring around the destination island,
                # too wide to jump (no parkour) and too deep to enter.
                FillSpec(
                    start=(
                        1,
                        -4,
                        -4,
                    ),
                    end=(
                        2,
                        -1,
                        4,
                    ),
                    block='air',
                ),
                FillSpec(
                    start=(
                        6,
                        -4,
                        -4,
                    ),
                    end=(
                        9,
                        -1,
                        4,
                    ),
                    block='air',
                ),
                FillSpec(
                    start=(
                        3,
                        -4,
                        -4,
                    ),
                    end=(
                        5,
                        -1,
                        -2,
                    ),
                    block='air',
                ),
                FillSpec(
                    start=(
                        3,
                        -4,
                        2,
                    ),
                    end=(
                        5,
                        -1,
                        4,
                    ),
                    block='air',
                ),
            ),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_visible_outside_local_search_distance__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'destination',
                (
                    33.5,
                    0,
                    0.5,
                ),
            ),),
            equipment=(
                (
                    'armor.head',
                    'iron_helmet',
                ),
                (
                    'armor.chest',
                    'iron_chestplate',
                ),
                (
                    'armor.legs',
                    'iron_leggings',
                ),
                (
                    'armor.feet',
                    'iron_boots',
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_visible_outside_local_search_distance__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'destination',
                (
                    33.5,
                    0,
                    0.5,
                ),
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_visible_outside_local_search_distance__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'destination',
                (
                    33.5,
                    0,
                    0.5,
                ),
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_visible_destination_blocked_during_walk__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    12,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            equipment=(
                (
                    'armor.head',
                    'iron_helmet',
                ),
                (
                    'armor.chest',
                    'iron_chestplate',
                ),
                (
                    'armor.legs',
                    'iron_leggings',
                ),
                (
                    'armor.feet',
                    'iron_boots',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_walk_to_visible',
        {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'},
        DuringAction(
            wait='player_moved',
            target='destination',
            command='setblock {destination_x} {destination_y} {destination_z} stone',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='destination',
        expected='stone',
    ),))


def test_walk_to_visible_destination_blocked_during_walk__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    12,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_walk_to_visible',
        {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'},
        DuringAction(
            wait='player_moved',
            target='destination',
            command='setblock {destination_x} {destination_y} {destination_z} stone',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='destination',
        expected='stone',
    ),))


def test_walk_to_visible_destination_blocked_during_walk__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    12,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_walk_to_visible',
        {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'},
        DuringAction(
            wait='player_moved',
            target='destination',
            command='setblock {destination_x} {destination_y} {destination_z} stone',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_walk_to_visible', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='destination',
        expected='stone',
    ),))
