"""Live tests for minecraft_walk_to_surface. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, FillSpec, Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.slow

@pytest.mark.smoke
def test_walk_to_surface_flat_100_blocks(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    38,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='target',
        expected=None,
        tolerance=2.0,
    ),))



@pytest.mark.slow
def test_walk_to_surface_negative_column(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    -30,
                    0,
                    -30,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='target',
        expected=None,
        tolerance=2.0,
    ),))



@pytest.mark.slow
def test_walk_to_surface_chunk_crossing(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    34,
                    0,
                    17,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='target',
        expected=None,
        tolerance=2.0,
    ),))



@pytest.mark.smoke
def test_walk_to_surface_liquid_column(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    6,
                    0,
                    0,
                ),
                block='water',
            ),),
            fills=(FillSpec(
                start=(
                    3,
                    -1,
                    -2,
                ),
                end=(
                    8,
                    0,
                    2,
                ),
                block='water',
            ),),
            player_offset=(
                0.5,
                0.0,
                8.5,
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_standable_surface'
    assert_message(result, 'standable', 'surface')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_surface_sealed_route(live_test):
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
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$destination.x', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$destination.x', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_walk_to_surface_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': 0, 'z': 0}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_walk_to_surface_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {}, timeout=660)
    assert_protocol_error(res, 'x')



@pytest.mark.contract
def test_walk_to_surface_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': {'wrong': True}, 'z': 0}, timeout=660)
    assert_protocol_error(res, 'x')


def test_walk_to_surface_flat_100_blocks__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    38,
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
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='target',
        expected=None,
        tolerance=2.0,
    ),))


def test_walk_to_surface_flat_100_blocks__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    38,
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
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='target',
        expected=None,
        tolerance=2.0,
    ),))


def test_walk_to_surface_flat_100_blocks__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    38,
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
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='target',
        expected=None,
        tolerance=2.0,
    ),))


def test_walk_to_surface_flat_100_blocks__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    38,
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
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='target',
        expected=None,
        tolerance=2.0,
    ),))


def test_walk_to_surface_flat_100_blocks__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    38,
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
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='target',
        expected=None,
        tolerance=2.0,
    ),))


def test_walk_to_surface_flat_100_blocks__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    38,
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
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'status', 'reached')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='target',
        expected=None,
        tolerance=2.0,
    ),))


def test_walk_to_surface_liquid_column__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    6,
                    0,
                    0,
                ),
                block='water',
            ),),
            fills=(FillSpec(
                start=(
                    3,
                    -1,
                    -2,
                ),
                end=(
                    8,
                    0,
                    2,
                ),
                block='water',
            ),),
            player_offset=(
                0.5,
                0.0,
                8.5,
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
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_standable_surface'
    assert_message(result, 'standable', 'surface')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_surface_liquid_column__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    6,
                    0,
                    0,
                ),
                block='water',
            ),),
            fills=(FillSpec(
                start=(
                    3,
                    -1,
                    -2,
                ),
                end=(
                    8,
                    0,
                    2,
                ),
                block='water',
            ),),
            player_offset=(
                0.5,
                0.0,
                8.5,
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_standable_surface'
    assert_message(result, 'standable', 'surface')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_surface_liquid_column__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    6,
                    0,
                    0,
                ),
                block='water',
            ),),
            fills=(FillSpec(
                start=(
                    3,
                    -1,
                    -2,
                ),
                end=(
                    8,
                    0,
                    2,
                ),
                block='water',
            ),),
            player_offset=(
                0.5,
                0.0,
                8.5,
            ),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$target.x', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_standable_surface'
    assert_message(result, 'standable', 'surface')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_surface_sealed_route__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$destination.x', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$destination.x', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_surface_sealed_route__night(live_test):
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
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$destination.x', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$destination.x', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_walk_to_surface_sealed_route__rain(live_test):
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
    res = call_mcp(scenario, 'minecraft_walk_to_surface', {'x': '$destination.x', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_walk_to_surface', {'x': '$destination.x', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_path'
    assert_message(result, 'path')
    assert_field(scenario, result, 'status', 'no_path')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)
