"""Live tests for minecraft_inspect_block. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_inspect_block_stone(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'block_name', 'stone')
    assert_field(scenario, result, 'is_solid', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))


def test_inspect_block_water(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='water',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'block_name', 'water')
    assert_field(scenario, result, 'is_solid', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='water',
    ),))


def test_inspect_block_lava(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='lava',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'block_name', 'lava')
    assert_field(scenario, result, 'is_solid', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='lava',
    ),))


def test_inspect_block_bedrock(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='bedrock',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'block_name', 'bedrock')
    assert_field(scenario, result, 'is_solid', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='bedrock',
    ),))


def test_inspect_block_farmland(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='farmland[moisture=7]',
                properties={'moisture': '7'},
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'block_name', 'farmland')
    assert_field(scenario, result, 'is_solid', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='farmland',
    ),))


def test_inspect_block_snow_layers(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='snow[layers=5]',
                properties={'layers': '5'},
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'block_name', 'snow')
    assert_field(scenario, result, 'is_solid', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='snow',
    ),))


def test_inspect_block_lit_furnace(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[lit=true,facing=north]',
                properties={'lit': True, 'facing': 'north'},
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'block_name', 'furnace')
    assert_field(scenario, result, 'is_solid', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='furnace',
    ),))


def test_inspect_block_waterlogged_stair(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
            # The waterlogged stair spills water; without walls the flow
            # carries the player out of the arranged position.
            BlockSpec(
                key='seal_west',
                offset=(
                    2,
                    0,
                    0,
                ),
                block='stone',
            ),
            BlockSpec(
                key='seal_east',
                offset=(
                    4,
                    0,
                    0,
                ),
                block='stone',
            ),
            BlockSpec(
                key='seal_north',
                offset=(
                    3,
                    0,
                    1,
                ),
                block='stone',
            ),
            BlockSpec(
                key='seal_south',
                offset=(
                    3,
                    0,
                    -1,
                ),
                block='stone',
            ),
            BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='oak_stairs[waterlogged=true,facing=east]',
                properties={'waterlogged': True, 'facing': 'east'},
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'block_name', 'oak_stairs')
    assert_field(scenario, result, 'is_solid', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='oak_stairs',
    ),))



@pytest.mark.smoke
def test_inspect_block_air_cell(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'position', '$target')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_inspect_block_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_inspect_block_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_inspect_block', {}, timeout=660)
    assert_protocol_error(res, 'position')



@pytest.mark.contract
def test_inspect_block_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': {'x': {'wrong': True}, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'position')


def test_inspect_block_stone__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
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
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'block_name', 'stone')
    assert_field(scenario, result, 'is_solid', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))


def test_inspect_block_stone__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'block_name', 'stone')
    assert_field(scenario, result, 'is_solid', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))


def test_inspect_block_stone__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'block_name', 'stone')
    assert_field(scenario, result, 'is_solid', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))


def test_inspect_block_stone__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'block_name', 'stone')
    assert_field(scenario, result, 'is_solid', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))


def test_inspect_block_stone__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'block_name', 'stone')
    assert_field(scenario, result, 'is_solid', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))


def test_inspect_block_stone__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
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
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target', 'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'block_name', 'stone')
    assert_field(scenario, result, 'is_solid', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))


def test_inspect_block_air_cell__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'position', '$target')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_inspect_block_air_cell__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'position', '$target')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_inspect_block_air_cell__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_inspect_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_inspect_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'position', '$target')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)
