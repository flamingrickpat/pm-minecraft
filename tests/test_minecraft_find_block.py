"""Live tests for minecraft_find_block. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Approx, BlockSpec, Layout, Length, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_find_block_east_limit(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        32,
                        1,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        32,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearest.position', '$target')
    assert_field(scenario, result, 'nearest.block_name', 'iron_ore')
    assert_field(scenario, result, 'total_matches', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))



@pytest.mark.smoke
def test_find_block_east_outside(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        33,
                        1,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        33,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_west_limit(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        -32,
                        1,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        -32,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearest.position', '$target')
    assert_field(scenario, result, 'nearest.block_name', 'iron_ore')
    assert_field(scenario, result, 'total_matches', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))


def test_find_block_up_limit(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        2,
                        17,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        2,
                        16,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearest.position', '$target')
    assert_field(scenario, result, 'nearest.block_name', 'iron_ore')
    assert_field(scenario, result, 'total_matches', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))


def test_find_block_up_outside(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        2,
                        18,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        2,
                        17,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_down_limit(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        2,
                        -23,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        2,
                        -24,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearest.position', '$target')
    assert_field(scenario, result, 'nearest.block_name', 'iron_ore')
    assert_field(scenario, result, 'total_matches', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))


def test_find_block_down_outside(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        2,
                        -24,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        2,
                        -25,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_negative_chunk_edge(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        -16,
                        1,
                        -16,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        -16,
                        0,
                        -16,
                    ),
                    block='iron_ore',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearest.position', '$target')
    assert_field(scenario, result, 'nearest.block_name', 'iron_ore')
    assert_field(scenario, result, 'total_matches', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))


def test_find_block_positive_chunk_edge(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        16,
                        1,
                        16,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        16,
                        0,
                        16,
                    ),
                    block='iron_ore',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearest.position', '$target')
    assert_field(scenario, result, 'nearest.block_name', 'iron_ore')
    assert_field(scenario, result, 'total_matches', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))


def test_find_block_sealed_ore_is_hidden(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='seal_0',
                    offset=(
                        3,
                        -2,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_1',
                    offset=(
                        5,
                        -2,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_2',
                    offset=(
                        4,
                        -3,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_3',
                    offset=(
                        4,
                        -1,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_4',
                    offset=(
                        4,
                        -2,
                        -1,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_5',
                    offset=(
                        4,
                        -2,
                        1,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        4,
                        -2,
                        0,
                    ),
                    block='diamond_ore',
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'diamond_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'diamond_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='diamond_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_mixed_case_name(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'dIamond_Ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'dIamond_Ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_typo_candidates(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'definitely_not_a_block'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'definitely_not_a_block'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_equal_distance_stable_order(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='ore_0',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_1',
                    offset=(
                        -4,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_2',
                    offset=(
                        0,
                        0,
                        4,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_3',
                    offset=(
                        0,
                        0,
                        -4,
                    ),
                    block='iron_ore',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'total_matches', 4)
    assert_field(scenario, result, 'results.0.distance', Approx(
        value=3.5356,
        tolerance=0.1,
    ))
    assert_response_image(res, result, False)


def test_find_block_result_limit_and_total(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='ore_0',
                    offset=(
                        3,
                        0,
                        -8,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_1',
                    offset=(
                        4,
                        0,
                        -8,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_2',
                    offset=(
                        5,
                        0,
                        -8,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_3',
                    offset=(
                        6,
                        0,
                        -8,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_4',
                    offset=(
                        7,
                        0,
                        -8,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_5',
                    offset=(
                        3,
                        0,
                        -5,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_6',
                    offset=(
                        4,
                        0,
                        -5,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_7',
                    offset=(
                        5,
                        0,
                        -5,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_8',
                    offset=(
                        6,
                        0,
                        -5,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_9',
                    offset=(
                        7,
                        0,
                        -5,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_10',
                    offset=(
                        3,
                        0,
                        -2,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_11',
                    offset=(
                        4,
                        0,
                        -2,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_12',
                    offset=(
                        5,
                        0,
                        -2,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_13',
                    offset=(
                        6,
                        0,
                        -2,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_14',
                    offset=(
                        7,
                        0,
                        -2,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_15',
                    offset=(
                        3,
                        0,
                        1,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_16',
                    offset=(
                        4,
                        0,
                        1,
                    ),
                    block='iron_ore',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results', Length(
        value=16,
    ))
    assert_field(scenario, result, 'total_matches', 17)
    assert_response_image(res, result, False)


def test_find_block_wildcard_multiple_types(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='iron',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='coal',
                    offset=(
                        -3,
                        0,
                        0,
                    ),
                    block='coal_ore',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': '*_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': '*_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'matched_types', Length(
        value=2,
    ))
    assert_field(scenario, result, 'total_matches', 2)
    assert_response_image(res, result, False)


def test_find_block_harvestable_with_held_pickaxe(live_test):
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
                block='iron_ore',
            ),),
            items=((
                'iron_pickaxe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearest.harvestable_with_held', True)
    assert_response_image(res, result, False)


def test_find_block_not_harvestable_with_bare_hand(live_test):
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
                block='iron_ore',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearest.harvestable_with_held', False)
    assert_response_image(res, result, False)



@pytest.mark.contract
def test_find_block_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'stone'}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_find_block_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_find_block', {}, timeout=660)
    assert_protocol_error(res, 'pattern')



@pytest.mark.contract
def test_find_block_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'pattern')


def test_find_block_east_limit__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        32,
                        1,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        32,
                        0,
                        0,
                    ),
                    block='iron_ore',
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
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearest.position', '$target')
    assert_field(scenario, result, 'nearest.block_name', 'iron_ore')
    assert_field(scenario, result, 'total_matches', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))


def test_find_block_east_limit__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        32,
                        1,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        32,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearest.position', '$target')
    assert_field(scenario, result, 'nearest.block_name', 'iron_ore')
    assert_field(scenario, result, 'total_matches', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))


def test_find_block_east_limit__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        32,
                        1,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        32,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearest.position', '$target')
    assert_field(scenario, result, 'nearest.block_name', 'iron_ore')
    assert_field(scenario, result, 'total_matches', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))


def test_find_block_east_limit__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        32,
                        1,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        32,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearest.position', '$target')
    assert_field(scenario, result, 'nearest.block_name', 'iron_ore')
    assert_field(scenario, result, 'total_matches', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))


def test_find_block_east_limit__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        32,
                        1,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        32,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearest.position', '$target')
    assert_field(scenario, result, 'nearest.block_name', 'iron_ore')
    assert_field(scenario, result, 'total_matches', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))


def test_find_block_east_limit__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        32,
                        1,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        32,
                        0,
                        0,
                    ),
                    block='iron_ore',
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
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearest.position', '$target')
    assert_field(scenario, result, 'nearest.block_name', 'iron_ore')
    assert_field(scenario, result, 'total_matches', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))


def test_find_block_east_outside__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        33,
                        1,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        33,
                        0,
                        0,
                    ),
                    block='iron_ore',
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
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_east_outside__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        33,
                        1,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        33,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_east_outside__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        33,
                        1,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        33,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_up_outside__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        2,
                        18,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        2,
                        17,
                        0,
                    ),
                    block='iron_ore',
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
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_up_outside__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        2,
                        18,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        2,
                        17,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_up_outside__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        2,
                        18,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        2,
                        17,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_down_outside__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        2,
                        -24,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        2,
                        -25,
                        0,
                    ),
                    block='iron_ore',
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
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_down_outside__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        2,
                        -24,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        2,
                        -25,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_down_outside__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='exposure',
                    offset=(
                        2,
                        -24,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        2,
                        -25,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_sealed_ore_is_hidden__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='seal_0',
                    offset=(
                        3,
                        -2,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_1',
                    offset=(
                        5,
                        -2,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_2',
                    offset=(
                        4,
                        -3,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_3',
                    offset=(
                        4,
                        -1,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_4',
                    offset=(
                        4,
                        -2,
                        -1,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_5',
                    offset=(
                        4,
                        -2,
                        1,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        4,
                        -2,
                        0,
                    ),
                    block='diamond_ore',
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
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'diamond_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'diamond_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='diamond_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_sealed_ore_is_hidden__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='seal_0',
                    offset=(
                        3,
                        -2,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_1',
                    offset=(
                        5,
                        -2,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_2',
                    offset=(
                        4,
                        -3,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_3',
                    offset=(
                        4,
                        -1,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_4',
                    offset=(
                        4,
                        -2,
                        -1,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_5',
                    offset=(
                        4,
                        -2,
                        1,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        4,
                        -2,
                        0,
                    ),
                    block='diamond_ore',
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'diamond_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'diamond_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='diamond_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_sealed_ore_is_hidden__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='seal_0',
                    offset=(
                        3,
                        -2,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_1',
                    offset=(
                        5,
                        -2,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_2',
                    offset=(
                        4,
                        -3,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_3',
                    offset=(
                        4,
                        -1,
                        0,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_4',
                    offset=(
                        4,
                        -2,
                        -1,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='seal_5',
                    offset=(
                        4,
                        -2,
                        1,
                    ),
                    block='deepslate',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        4,
                        -2,
                        0,
                    ),
                    block='diamond_ore',
                ),
            ),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'diamond_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'diamond_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'candidates', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='diamond_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_mixed_case_name__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
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
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'dIamond_Ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'dIamond_Ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_mixed_case_name__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'dIamond_Ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'dIamond_Ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_mixed_case_name__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'dIamond_Ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'dIamond_Ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_typo_candidates__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
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
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'definitely_not_a_block'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'definitely_not_a_block'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_typo_candidates__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'definitely_not_a_block'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'definitely_not_a_block'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_block_typo_candidates__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_block', {'pattern': 'definitely_not_a_block'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_block', {'pattern': 'definitely_not_a_block'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'total_matches', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)
