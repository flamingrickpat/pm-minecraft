"""Live tests for minecraft_is_safe_to_dig. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, Layout, Length, WorldExpectation, assert_field, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_truth, parse_result, run_operator_command, setup

@pytest.mark.smoke
def test_is_safe_to_dig_safe_stone(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='behind',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='stone',
                    name='stone',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_is_safe_to_dig', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'risk', 'low_risk')
    assert_field(scenario, result, 'will_fall', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='behind',
            expected='stone',
        ),
    ))


def test_is_safe_to_dig_lava_behind(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='behind',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='lava',
                    name='lava',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_is_safe_to_dig', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'risk', 'warning')
    assert_field(scenario, result, 'will_fall', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='behind',
            expected='lava',
        ),
    ))


def test_is_safe_to_dig_water_behind(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='behind',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='water',
                    name='water',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_is_safe_to_dig', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'risk', 'warning')
    assert_field(scenario, result, 'will_fall', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='behind',
            expected='water',
        ),
    ))


def test_is_safe_to_dig_air_drop(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='behind',
                    offset=(
                        4,
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
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_is_safe_to_dig', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'risk', 'warning')
    assert_field(scenario, result, 'will_fall', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='behind',
            expected='air',
        ),
    ))


def test_is_safe_to_dig_bedrock_behind(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='behind',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='bedrock',
                    name='bedrock',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_is_safe_to_dig', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'risk', 'warning')
    assert_field(scenario, result, 'will_fall', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='behind',
            expected='bedrock',
        ),
    ))


def test_is_safe_to_dig_gravel_behind(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='behind',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='gravel',
                    name='gravel',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_is_safe_to_dig', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'risk', 'warning')
    assert_field(scenario, result, 'will_fall', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='behind',
            expected='gravel',
        ),
    ))


def test_is_safe_to_dig_hidden_lava_sound_at_limit(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'sound',
                (
                    15.5,
                    1.62,
                    0.0,
                ),
            ),),
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='support',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='lava',
                    offset=(
                        16,
                        1,
                        0,
                    ),
                    block='lava',
                ),
                BlockSpec(
                    key='seal_0',
                    offset=(
                        15,
                        1,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_1',
                    offset=(
                        17,
                        1,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_2',
                    offset=(
                        16,
                        0,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_3',
                    offset=(
                        16,
                        2,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_4',
                    offset=(
                        16,
                        1,
                        -1,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_5',
                    offset=(
                        16,
                        1,
                        1,
                    ),
                    block='deepslate',
                ),
            ),
            player_offset=(
                0.0,
                0.0,
                0.0,
            ),
        ),
    )
    run_operator_command(scenario, 'playsound minecraft:block.lava.ambient block tdd_player {sound_x} {sound_y} {sound_z} 1 1 0')
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_is_safe_to_dig', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'risk', 'warning')
    assert_field(scenario, result, 'hazards', Length(
        value=1,
    ))
    assert_field(scenario, result, 'hazards.0.kind', 'lava')
    assert_field(scenario, result, 'hazards.0.direction', 'east')
    assert_field(scenario, result, 'hazards.0.position', None)
    assert_field(scenario, result, 'hazards.0.distance_band', 'audible')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='lava',
            expected='lava',
        ),
    ))


def test_is_safe_to_dig_hidden_lava_sound_outside_limit(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'sound',
                (
                    17.0,
                    1.62,
                    0.0,
                ),
            ),),
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='support',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='lava',
                    offset=(
                        17,
                        1,
                        0,
                    ),
                    block='lava',
                ),
                BlockSpec(
                    key='seal_0',
                    offset=(
                        16,
                        1,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_1',
                    offset=(
                        18,
                        1,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_2',
                    offset=(
                        17,
                        0,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_3',
                    offset=(
                        17,
                        2,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_4',
                    offset=(
                        17,
                        1,
                        -1,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_5',
                    offset=(
                        17,
                        1,
                        1,
                    ),
                    block='deepslate',
                ),
            ),
            player_offset=(
                0.0,
                0.0,
                0.0,
            ),
        ),
    )
    run_operator_command(scenario, 'playsound minecraft:block.lava.ambient block tdd_player {sound_x} {sound_y} {sound_z} 1 1 0')
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_is_safe_to_dig', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'risk', 'low_risk')
    assert_field(scenario, result, 'hazards', [])
    assert_field(scenario, result, 'will_fall', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='lava',
            expected='lava',
        ),
    ))



@pytest.mark.contract

@pytest.mark.smoke
def test_is_safe_to_dig_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_is_safe_to_dig_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {}, timeout=660)
    assert_protocol_error(res, 'position')



@pytest.mark.contract
def test_is_safe_to_dig_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': {'x': {'wrong': True}, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'position')


def test_is_safe_to_dig_safe_stone__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='behind',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='stone',
                    name='stone',
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
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_is_safe_to_dig', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'risk', 'low_risk')
    assert_field(scenario, result, 'will_fall', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='behind',
            expected='stone',
        ),
    ))


def test_is_safe_to_dig_safe_stone__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='behind',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='stone',
                    name='stone',
                ),
            ),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_is_safe_to_dig', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'risk', 'low_risk')
    assert_field(scenario, result, 'will_fall', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='behind',
            expected='stone',
        ),
    ))


def test_is_safe_to_dig_safe_stone__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='behind',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='stone',
                    name='stone',
                ),
            ),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_is_safe_to_dig', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'risk', 'low_risk')
    assert_field(scenario, result, 'will_fall', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='behind',
            expected='stone',
        ),
    ))


def test_is_safe_to_dig_safe_stone__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='behind',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='stone',
                    name='stone',
                ),
            ),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_is_safe_to_dig', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'risk', 'low_risk')
    assert_field(scenario, result, 'will_fall', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='behind',
            expected='stone',
        ),
    ))


def test_is_safe_to_dig_safe_stone__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='behind',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='stone',
                    name='stone',
                ),
            ),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_is_safe_to_dig', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'risk', 'low_risk')
    assert_field(scenario, result, 'will_fall', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='behind',
            expected='stone',
        ),
    ))


def test_is_safe_to_dig_safe_stone__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='behind',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='stone',
                    name='stone',
                ),
            ),
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
    res = call_mcp(scenario, 'minecraft_is_safe_to_dig', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_is_safe_to_dig', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'position', '$target')
    assert_field(scenario, result, 'risk', 'low_risk')
    assert_field(scenario, result, 'will_fall', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='behind',
            expected='stone',
        ),
    ))
