"""Live tests for minecraft_find_interactables. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, Excludes, Includes, Layout, Length, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_find_interactables_chest(live_test):
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
                block='chest',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results.0.block_name', 'chest')
    assert_field(scenario, result, 'results.0.kind', 'chest')
    assert_response_image(res, result, False)


def test_find_interactables_furnace(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    4,
                    0,
                    0,
                ),
                block='furnace',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results.0.block_name', 'furnace')
    assert_field(scenario, result, 'results.0.kind', 'furnace')
    assert_response_image(res, result, False)


def test_find_interactables_crafting_table(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    5,
                    0,
                    0,
                ),
                block='crafting_table',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results.0.block_name', 'crafting_table')
    assert_field(scenario, result, 'results.0.kind', 'crafting_table')
    assert_response_image(res, result, False)


def test_find_interactables_bed(live_test):
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
                block='red_bed[part=foot,facing=south]',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results.0.block_name', 'red_bed')
    assert_field(scenario, result, 'results.0.kind', 'bed')
    assert_response_image(res, result, False)


def test_find_interactables_gate(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    7,
                    0,
                    0,
                ),
                block='oak_fence_gate[facing=south,open=false]',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results.0.block_name', 'oak_fence_gate')
    assert_field(scenario, result, 'results.0.kind', 'gate')
    assert_response_image(res, result, False)


def test_find_interactables_lever(live_test):
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
                block='lever[face=floor,facing=north,powered=false]',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results.0.block_name', 'lever')
    assert_field(scenario, result, 'results.0.kind', 'lever')
    assert_response_image(res, result, False)



@pytest.mark.smoke
def test_find_interactables_none_nearby(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': 'chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': 'chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'results', [])
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_interactables_unknown_pattern(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': 'chesstt'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': 'chesstt'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_interactables_fixed_radius_boundary(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='inside',
                    offset=(
                        16,
                        0,
                        0,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='outside',
                    offset=(
                        17,
                        0,
                        0,
                    ),
                    block='barrel',
                ),
            ),
            player_offset=(
                0.0,
                0.0,
                0.0,
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results', Includes(
        value='chest',
        key='block_name',
    ))
    assert_field(scenario, result, 'results', Excludes(
        value='barrel',
        key='block_name',
    ))
    assert_response_image(res, result, False)


def test_find_interactables_result_limit(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='chest_0',
                    offset=(
                        -10,
                        0,
                        -10,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_1',
                    offset=(
                        -10,
                        0,
                        -8,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_2',
                    offset=(
                        -10,
                        0,
                        -6,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_3',
                    offset=(
                        -10,
                        0,
                        -4,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_4',
                    offset=(
                        -10,
                        0,
                        -2,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_5',
                    offset=(
                        -10,
                        0,
                        0,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_6',
                    offset=(
                        -10,
                        0,
                        2,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_7',
                    offset=(
                        -10,
                        0,
                        4,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_8',
                    offset=(
                        -10,
                        0,
                        6,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_9',
                    offset=(
                        -10,
                        0,
                        8,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_10',
                    offset=(
                        -10,
                        0,
                        10,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_11',
                    offset=(
                        -8,
                        0,
                        -10,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_12',
                    offset=(
                        -8,
                        0,
                        -8,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_13',
                    offset=(
                        -8,
                        0,
                        -6,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_14',
                    offset=(
                        -8,
                        0,
                        -4,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_15',
                    offset=(
                        -8,
                        0,
                        -2,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_16',
                    offset=(
                        -8,
                        0,
                        0,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_17',
                    offset=(
                        -8,
                        0,
                        2,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_18',
                    offset=(
                        -8,
                        0,
                        4,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_19',
                    offset=(
                        -8,
                        0,
                        6,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_20',
                    offset=(
                        -8,
                        0,
                        8,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_21',
                    offset=(
                        -8,
                        0,
                        10,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_22',
                    offset=(
                        -6,
                        0,
                        -10,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_23',
                    offset=(
                        -6,
                        0,
                        -8,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_24',
                    offset=(
                        -6,
                        0,
                        -6,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_25',
                    offset=(
                        -6,
                        0,
                        -4,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_26',
                    offset=(
                        -6,
                        0,
                        -2,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_27',
                    offset=(
                        -6,
                        0,
                        0,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_28',
                    offset=(
                        -6,
                        0,
                        2,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_29',
                    offset=(
                        -6,
                        0,
                        4,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_30',
                    offset=(
                        -6,
                        0,
                        6,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_31',
                    offset=(
                        -6,
                        0,
                        8,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='chest_32',
                    offset=(
                        -6,
                        0,
                        10,
                    ),
                    block='chest',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': 'chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': 'chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results', Length(
        value=32,
    ))
    assert_response_image(res, result, False)



@pytest.mark.contract
def test_find_interactables_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_find_interactables', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_find_interactables_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': {'not': 'the declared type'}}, timeout=660)
    assert_protocol_error(res, 'pattern')



@pytest.mark.contract
def test_find_interactables_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'pattern')


def test_find_interactables_chest__armor(live_test):
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
                block='chest',
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
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results.0.block_name', 'chest')
    assert_field(scenario, result, 'results.0.kind', 'chest')
    assert_response_image(res, result, False)


def test_find_interactables_chest__damaged(live_test):
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
                block='chest',
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results.0.block_name', 'chest')
    assert_field(scenario, result, 'results.0.kind', 'chest')
    assert_response_image(res, result, False)


def test_find_interactables_chest__hungry(live_test):
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
                block='chest',
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results.0.block_name', 'chest')
    assert_field(scenario, result, 'results.0.kind', 'chest')
    assert_response_image(res, result, False)


def test_find_interactables_chest__night(live_test):
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
                block='chest',
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results.0.block_name', 'chest')
    assert_field(scenario, result, 'results.0.kind', 'chest')
    assert_response_image(res, result, False)


def test_find_interactables_chest__rain(live_test):
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
                block='chest',
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results.0.block_name', 'chest')
    assert_field(scenario, result, 'results.0.kind', 'chest')
    assert_response_image(res, result, False)


def test_find_interactables_chest__junk_inventory(live_test):
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
                block='chest',
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
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'results.0.block_name', 'chest')
    assert_field(scenario, result, 'results.0.kind', 'chest')
    assert_response_image(res, result, False)


def test_find_interactables_none_nearby__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': 'chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': 'chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'results', [])
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_interactables_none_nearby__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': 'chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': 'chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'results', [])
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_interactables_none_nearby__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': 'chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': 'chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'results', [])
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_interactables_unknown_pattern__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': 'chesstt'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': 'chesstt'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_interactables_unknown_pattern__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': 'chesstt'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': 'chesstt'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_find_interactables_unknown_pattern__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_find_interactables', {'pattern': 'chesstt'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_find_interactables', {'pattern': 'chesstt'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)
