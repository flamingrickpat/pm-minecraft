"""Live tests for minecraft_find_path. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import AtLeast, BlockSpec, FillSpec, Layout, NonEmpty, WorldExpectation, assert_field, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_find_path_flat_reachable(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
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
    res = call_mcp(scenario, 'minecraft_find_path', {'x': '$target.x', 'y': '$target.y', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_path', {'x': '$target.x', 'y': '$target.y', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'state', 'reachable')
    assert_field(scenario, result, 'path_length', AtLeast(
        value=0,
    ))
    assert_field(scenario, result, 'hops', AtLeast(
        value=0,
    ))
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_find_path_spiral_reachable(live_test):
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
    res = call_mcp(scenario, 'minecraft_find_path', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_path', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'state', 'reachable')
    assert_field(scenario, result, 'path_length', AtLeast(
        value=0,
    ))
    assert_field(scenario, result, 'hops', AtLeast(
        value=0,
    ))
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_find_path_sealed_blocked(live_test):
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
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_path', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_path', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'state', 'blocked')
    assert_field(scenario, result, 'blocker', NonEmpty())
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_find_path_void_blocked(live_test):
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
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_path', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_path', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'state', 'blocked')
    assert_field(scenario, result, 'blocker', NonEmpty())
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_find_path_search_distance_boundary(live_test):
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
    res = call_mcp(scenario, 'minecraft_find_path', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_path', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'state', 'reachable')
    assert_field(scenario, result, 'path_length', AtLeast(
        value=0,
    ))
    assert_field(scenario, result, 'hops', AtLeast(
        value=0,
    ))
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_find_path_outside_search_distance(live_test):
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
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_path', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_path', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'state', 'unknown')
    assert_field(scenario, result, 'path_length', None)
    assert_field(scenario, result, 'hops', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))



@pytest.mark.contract

@pytest.mark.smoke
def test_find_path_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_find_path', {'x': 0, 'y': 0, 'z': 0}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_find_path_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_find_path', {}, timeout=660)
    assert_protocol_error(res, 'x')



@pytest.mark.contract
def test_find_path_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_find_path', {'x': {'wrong': True}, 'y': 0, 'z': 0}, timeout=660)
    assert_protocol_error(res, 'x')


def test_find_path_flat_reachable__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
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
    res = call_mcp(scenario, 'minecraft_find_path', {'x': '$target.x', 'y': '$target.y', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_path', {'x': '$target.x', 'y': '$target.y', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'state', 'reachable')
    assert_field(scenario, result, 'path_length', AtLeast(
        value=0,
    ))
    assert_field(scenario, result, 'hops', AtLeast(
        value=0,
    ))
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_find_path_flat_reachable__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
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
    res = call_mcp(scenario, 'minecraft_find_path', {'x': '$target.x', 'y': '$target.y', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_path', {'x': '$target.x', 'y': '$target.y', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'state', 'reachable')
    assert_field(scenario, result, 'path_length', AtLeast(
        value=0,
    ))
    assert_field(scenario, result, 'hops', AtLeast(
        value=0,
    ))
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_find_path_flat_reachable__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
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
    res = call_mcp(scenario, 'minecraft_find_path', {'x': '$target.x', 'y': '$target.y', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_path', {'x': '$target.x', 'y': '$target.y', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'state', 'reachable')
    assert_field(scenario, result, 'path_length', AtLeast(
        value=0,
    ))
    assert_field(scenario, result, 'hops', AtLeast(
        value=0,
    ))
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_find_path_flat_reachable__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
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
    res = call_mcp(scenario, 'minecraft_find_path', {'x': '$target.x', 'y': '$target.y', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_path', {'x': '$target.x', 'y': '$target.y', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'state', 'reachable')
    assert_field(scenario, result, 'path_length', AtLeast(
        value=0,
    ))
    assert_field(scenario, result, 'hops', AtLeast(
        value=0,
    ))
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_find_path_flat_reachable__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
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
    res = call_mcp(scenario, 'minecraft_find_path', {'x': '$target.x', 'y': '$target.y', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_path', {'x': '$target.x', 'y': '$target.y', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'state', 'reachable')
    assert_field(scenario, result, 'path_length', AtLeast(
        value=0,
    ))
    assert_field(scenario, result, 'hops', AtLeast(
        value=0,
    ))
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_find_path_flat_reachable__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
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
    res = call_mcp(scenario, 'minecraft_find_path', {'x': '$target.x', 'y': '$target.y', 'z': '$target.z'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_path', {'x': '$target.x', 'y': '$target.y', 'z': '$target.z'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'state', 'reachable')
    assert_field(scenario, result, 'path_length', AtLeast(
        value=0,
    ))
    assert_field(scenario, result, 'hops', AtLeast(
        value=0,
    ))
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))
