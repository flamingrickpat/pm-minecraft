"""Live tests for minecraft_staircase_down. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Approx, AtLeast, BlockSpec, Layout, WorldExpectation, assert_field, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_truth, parse_result, setup

@pytest.mark.slow

@pytest.mark.smoke
def test_staircase_down_stone_depth_8(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='layer_0',
                    offset=(
                        0,
                        -1,
                        1,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_1',
                    offset=(
                        0,
                        -2,
                        2,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_2',
                    offset=(
                        0,
                        -3,
                        3,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_3',
                    offset=(
                        0,
                        -4,
                        4,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_4',
                    offset=(
                        0,
                        -5,
                        5,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_5',
                    offset=(
                        0,
                        -6,
                        6,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_6',
                    offset=(
                        0,
                        -7,
                        7,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_7',
                    offset=(
                        0,
                        -8,
                        8,
                    ),
                    block='stone',
                ),
            ),
            items=((
                'diamond_pickaxe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_staircase_down', {'depth': 8, 'torch': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_staircase_down', {'depth': 8, 'torch': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'depth_requested', 8)
    assert_field(scenario, result, 'depth_achieved', 8)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='layer_',
            expected=(
                'stone',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=AtLeast(
                value=8,
            ),
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=-8,
                tolerance=0.5,
            ),
        ),
    ))


def test_staircase_down_stops_for_lava(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='layer_0',
                    offset=(
                        0,
                        -1,
                        1,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_1',
                    offset=(
                        0,
                        -2,
                        2,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='hazard',
                    offset=(
                        0,
                        -3,
                        3,
                    ),
                    block='lava',
                    name='lava',
                ),
            ),
            items=(
                (
                    'diamond_pickaxe',
                    1,
                ),
                (
                    'torch',
                    8,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_staircase_down', {'depth': 8, 'torch': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_staircase_down', {'depth': 8, 'torch': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'depth_requested', 8)
    assert_field(scenario, result, 'depth_achieved', 2)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='layer_',
            expected=(
                'stone',
                0,
            ),
        ),
        WorldExpectation(
            kind='block',
            target='hazard',
            expected='lava',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=AtLeast(
                value=2,
            ),
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=-2,
                tolerance=0.5,
            ),
        ),
    ))


def test_staircase_down_stops_for_water(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='layer_0',
                    offset=(
                        0,
                        -1,
                        1,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_1',
                    offset=(
                        0,
                        -2,
                        2,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='hazard',
                    offset=(
                        0,
                        -3,
                        3,
                    ),
                    block='water',
                    name='water',
                ),
            ),
            items=(
                (
                    'diamond_pickaxe',
                    1,
                ),
                (
                    'torch',
                    8,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_staircase_down', {'depth': 8, 'torch': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_staircase_down', {'depth': 8, 'torch': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'depth_requested', 8)
    assert_field(scenario, result, 'depth_achieved', 2)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='layer_',
            expected=(
                'stone',
                0,
            ),
        ),
        WorldExpectation(
            kind='block',
            target='hazard',
            expected='water',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=AtLeast(
                value=2,
            ),
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=-2,
                tolerance=0.5,
            ),
        ),
    ))


def test_staircase_down_stops_for_cave(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='layer_0',
                    offset=(
                        0,
                        -1,
                        1,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_1',
                    offset=(
                        0,
                        -2,
                        2,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='hazard',
                    offset=(
                        0,
                        -3,
                        3,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=(
                (
                    'diamond_pickaxe',
                    1,
                ),
                (
                    'torch',
                    8,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_staircase_down', {'depth': 8, 'torch': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_staircase_down', {'depth': 8, 'torch': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'depth_requested', 8)
    assert_field(scenario, result, 'depth_achieved', 2)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='layer_',
            expected=(
                'stone',
                0,
            ),
        ),
        WorldExpectation(
            kind='block',
            target='hazard',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=AtLeast(
                value=2,
            ),
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=-2,
                tolerance=0.5,
            ),
        ),
    ))


def test_staircase_down_stops_for_bedrock(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='layer_0',
                    offset=(
                        0,
                        -1,
                        1,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_1',
                    offset=(
                        0,
                        -2,
                        2,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='hazard',
                    offset=(
                        0,
                        -3,
                        3,
                    ),
                    block='bedrock',
                    name='bedrock',
                ),
            ),
            items=(
                (
                    'diamond_pickaxe',
                    1,
                ),
                (
                    'torch',
                    8,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_staircase_down', {'depth': 8, 'torch': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_staircase_down', {'depth': 8, 'torch': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'depth_requested', 8)
    assert_field(scenario, result, 'depth_achieved', 2)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='layer_',
            expected=(
                'stone',
                0,
            ),
        ),
        WorldExpectation(
            kind='block',
            target='hazard',
            expected='bedrock',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=AtLeast(
                value=2,
            ),
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=-2,
                tolerance=0.5,
            ),
        ),
    ))


def test_staircase_down_stops_for_gravel(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='layer_0',
                    offset=(
                        0,
                        -1,
                        1,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_1',
                    offset=(
                        0,
                        -2,
                        2,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='hazard',
                    offset=(
                        0,
                        -3,
                        3,
                    ),
                    block='gravel',
                    name='gravel',
                ),
            ),
            items=(
                (
                    'diamond_pickaxe',
                    1,
                ),
                (
                    'torch',
                    8,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_staircase_down', {'depth': 8, 'torch': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_staircase_down', {'depth': 8, 'torch': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'depth_requested', 8)
    assert_field(scenario, result, 'depth_achieved', 2)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='layer_',
            expected=(
                'stone',
                0,
            ),
        ),
        WorldExpectation(
            kind='block',
            target='hazard',
            expected='gravel',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=AtLeast(
                value=2,
            ),
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=-2,
                tolerance=0.5,
            ),
        ),
    ))



@pytest.mark.contract

@pytest.mark.smoke
def test_staircase_down_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_staircase_down', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_staircase_down_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_staircase_down', {'depth': {'not': 'the declared type'}}, timeout=660)
    assert_protocol_error(res, 'depth')



@pytest.mark.contract
def test_staircase_down_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_staircase_down', {'depth': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'depth')


def test_staircase_down_stone_depth_8__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='layer_0',
                    offset=(
                        0,
                        -1,
                        1,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_1',
                    offset=(
                        0,
                        -2,
                        2,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_2',
                    offset=(
                        0,
                        -3,
                        3,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_3',
                    offset=(
                        0,
                        -4,
                        4,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_4',
                    offset=(
                        0,
                        -5,
                        5,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_5',
                    offset=(
                        0,
                        -6,
                        6,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_6',
                    offset=(
                        0,
                        -7,
                        7,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_7',
                    offset=(
                        0,
                        -8,
                        8,
                    ),
                    block='stone',
                ),
            ),
            items=((
                'diamond_pickaxe',
                1,
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
    res = call_mcp(scenario, 'minecraft_staircase_down', {'depth': 8, 'torch': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_staircase_down', {'depth': 8, 'torch': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'depth_requested', 8)
    assert_field(scenario, result, 'depth_achieved', 8)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='layer_',
            expected=(
                'stone',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=AtLeast(
                value=8,
            ),
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=-8,
                tolerance=0.5,
            ),
        ),
    ))


def test_staircase_down_stone_depth_8__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='layer_0',
                    offset=(
                        0,
                        -1,
                        1,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_1',
                    offset=(
                        0,
                        -2,
                        2,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_2',
                    offset=(
                        0,
                        -3,
                        3,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_3',
                    offset=(
                        0,
                        -4,
                        4,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_4',
                    offset=(
                        0,
                        -5,
                        5,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_5',
                    offset=(
                        0,
                        -6,
                        6,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_6',
                    offset=(
                        0,
                        -7,
                        7,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_7',
                    offset=(
                        0,
                        -8,
                        8,
                    ),
                    block='stone',
                ),
            ),
            items=((
                'diamond_pickaxe',
                1,
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_staircase_down', {'depth': 8, 'torch': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_staircase_down', {'depth': 8, 'torch': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'depth_requested', 8)
    assert_field(scenario, result, 'depth_achieved', 8)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='layer_',
            expected=(
                'stone',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=AtLeast(
                value=8,
            ),
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=-8,
                tolerance=0.5,
            ),
        ),
    ))


def test_staircase_down_stone_depth_8__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='layer_0',
                    offset=(
                        0,
                        -1,
                        1,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_1',
                    offset=(
                        0,
                        -2,
                        2,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_2',
                    offset=(
                        0,
                        -3,
                        3,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_3',
                    offset=(
                        0,
                        -4,
                        4,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_4',
                    offset=(
                        0,
                        -5,
                        5,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_5',
                    offset=(
                        0,
                        -6,
                        6,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_6',
                    offset=(
                        0,
                        -7,
                        7,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_7',
                    offset=(
                        0,
                        -8,
                        8,
                    ),
                    block='stone',
                ),
            ),
            items=((
                'diamond_pickaxe',
                1,
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_staircase_down', {'depth': 8, 'torch': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_staircase_down', {'depth': 8, 'torch': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'depth_requested', 8)
    assert_field(scenario, result, 'depth_achieved', 8)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='layer_',
            expected=(
                'stone',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=AtLeast(
                value=8,
            ),
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=-8,
                tolerance=0.5,
            ),
        ),
    ))


def test_staircase_down_stone_depth_8__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='layer_0',
                    offset=(
                        0,
                        -1,
                        1,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_1',
                    offset=(
                        0,
                        -2,
                        2,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_2',
                    offset=(
                        0,
                        -3,
                        3,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_3',
                    offset=(
                        0,
                        -4,
                        4,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_4',
                    offset=(
                        0,
                        -5,
                        5,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_5',
                    offset=(
                        0,
                        -6,
                        6,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_6',
                    offset=(
                        0,
                        -7,
                        7,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_7',
                    offset=(
                        0,
                        -8,
                        8,
                    ),
                    block='stone',
                ),
            ),
            items=((
                'diamond_pickaxe',
                1,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_staircase_down', {'depth': 8, 'torch': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_staircase_down', {'depth': 8, 'torch': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'depth_requested', 8)
    assert_field(scenario, result, 'depth_achieved', 8)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='layer_',
            expected=(
                'stone',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=AtLeast(
                value=8,
            ),
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=-8,
                tolerance=0.5,
            ),
        ),
    ))


def test_staircase_down_stone_depth_8__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='layer_0',
                    offset=(
                        0,
                        -1,
                        1,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_1',
                    offset=(
                        0,
                        -2,
                        2,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_2',
                    offset=(
                        0,
                        -3,
                        3,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_3',
                    offset=(
                        0,
                        -4,
                        4,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_4',
                    offset=(
                        0,
                        -5,
                        5,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_5',
                    offset=(
                        0,
                        -6,
                        6,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_6',
                    offset=(
                        0,
                        -7,
                        7,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_7',
                    offset=(
                        0,
                        -8,
                        8,
                    ),
                    block='stone',
                ),
            ),
            items=((
                'diamond_pickaxe',
                1,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_staircase_down', {'depth': 8, 'torch': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_staircase_down', {'depth': 8, 'torch': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'depth_requested', 8)
    assert_field(scenario, result, 'depth_achieved', 8)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='layer_',
            expected=(
                'stone',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=AtLeast(
                value=8,
            ),
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=-8,
                tolerance=0.5,
            ),
        ),
    ))


def test_staircase_down_stone_depth_8__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='layer_0',
                    offset=(
                        0,
                        -1,
                        1,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_1',
                    offset=(
                        0,
                        -2,
                        2,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_2',
                    offset=(
                        0,
                        -3,
                        3,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_3',
                    offset=(
                        0,
                        -4,
                        4,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_4',
                    offset=(
                        0,
                        -5,
                        5,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_5',
                    offset=(
                        0,
                        -6,
                        6,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_6',
                    offset=(
                        0,
                        -7,
                        7,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='layer_7',
                    offset=(
                        0,
                        -8,
                        8,
                    ),
                    block='stone',
                ),
            ),
            items=(
                (
                    'diamond_pickaxe',
                    1,
                ),
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
    res = call_mcp(scenario, 'minecraft_staircase_down', {'depth': 8, 'torch': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_staircase_down', {'depth': 8, 'torch': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'depth_requested', 8)
    assert_field(scenario, result, 'depth_achieved', 8)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='layer_',
            expected=(
                'stone',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=AtLeast(
                value=8,
            ),
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=-8,
                tolerance=0.5,
            ),
        ),
    ))
