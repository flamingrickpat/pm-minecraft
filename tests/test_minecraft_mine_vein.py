"""Live tests for minecraft_mine_vein. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_mine_vein_single(live_test):
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
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block', 'iron_ore')
    assert_field(scenario, result, 'mined_count', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='target',
            expected=(
                'iron_ore',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='raw_iron',
            expected=1,
        ),
    ))


def test_mine_vein_branch(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='ore_0',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_1',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_2',
                    offset=(
                        4,
                        1,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_3',
                    offset=(
                        4,
                        1,
                        1,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_4',
                    offset=(
                        3,
                        1,
                        1,
                    ),
                    block='iron_ore',
                ),
            ),
            items=((
                'iron_pickaxe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block', 'iron_ore')
    assert_field(scenario, result, 'mined_count', 5)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='ore_',
            expected=(
                'iron_ore',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='raw_iron',
            expected=5,
        ),
    ))


def test_mine_vein_limit_plus_one(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='ore_0',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_1',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_2',
                    offset=(
                        5,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_3',
                    offset=(
                        6,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_4',
                    offset=(
                        7,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_5',
                    offset=(
                        8,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_6',
                    offset=(
                        9,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_7',
                    offset=(
                        10,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_8',
                    offset=(
                        11,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_9',
                    offset=(
                        12,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_10',
                    offset=(
                        13,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_11',
                    offset=(
                        14,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_12',
                    offset=(
                        15,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_13',
                    offset=(
                        16,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_14',
                    offset=(
                        17,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_15',
                    offset=(
                        18,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
                BlockSpec(
                    key='ore_16',
                    offset=(
                        19,
                        0,
                        0,
                    ),
                    block='iron_ore',
                ),
            ),
            items=((
                'diamond_pickaxe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block', 'iron_ore')
    assert_field(scenario, result, 'mined_count', 16)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='ore_',
            expected=(
                'iron_ore',
                1,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='raw_iron',
            expected=16,
        ),
    ))



@pytest.mark.smoke
def test_mine_vein_none_visible(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_vein_ambiguous_ore_glob(live_test):
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
                        4,
                        0,
                        0,
                    ),
                    block='coal_ore',
                ),
            ),
            items=((
                'iron_pickaxe',
                1,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': '*_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': '*_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_mine_vein_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': 'iron_ore'}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_mine_vein_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_mine_vein', {}, timeout=660)
    assert_protocol_error(res, 'block')



@pytest.mark.contract
def test_mine_vein_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'block')


def test_mine_vein_single__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block', 'iron_ore')
    assert_field(scenario, result, 'mined_count', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='target',
            expected=(
                'iron_ore',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='raw_iron',
            expected=1,
        ),
    ))


def test_mine_vein_single__damaged(live_test):
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
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block', 'iron_ore')
    assert_field(scenario, result, 'mined_count', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='target',
            expected=(
                'iron_ore',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='raw_iron',
            expected=1,
        ),
    ))


def test_mine_vein_single__hungry(live_test):
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
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block', 'iron_ore')
    assert_field(scenario, result, 'mined_count', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='target',
            expected=(
                'iron_ore',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='raw_iron',
            expected=1,
        ),
    ))


def test_mine_vein_single__night(live_test):
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
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block', 'iron_ore')
    assert_field(scenario, result, 'mined_count', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='target',
            expected=(
                'iron_ore',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='raw_iron',
            expected=1,
        ),
    ))


def test_mine_vein_single__rain(live_test):
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
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block', 'iron_ore')
    assert_field(scenario, result, 'mined_count', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='target',
            expected=(
                'iron_ore',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='raw_iron',
            expected=1,
        ),
    ))


def test_mine_vein_single__junk_inventory(live_test):
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
            items=(
                (
                    'iron_pickaxe',
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
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block', 'iron_ore')
    assert_field(scenario, result, 'mined_count', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='named_block_count',
            target='target',
            expected=(
                'iron_ore',
                0,
            ),
        ),
        WorldExpectation(
            kind='inventory',
            target='raw_iron',
            expected=1,
        ),
    ))


def test_mine_vein_none_visible__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_vein_none_visible__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_vein_none_visible__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': 'iron_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': 'iron_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_vein_ambiguous_ore_glob__armor(live_test):
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
                        4,
                        0,
                        0,
                    ),
                    block='coal_ore',
                ),
            ),
            items=((
                'iron_pickaxe',
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': '*_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': '*_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_vein_ambiguous_ore_glob__night(live_test):
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
                        4,
                        0,
                        0,
                    ),
                    block='coal_ore',
                ),
            ),
            items=((
                'iron_pickaxe',
                1,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': '*_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': '*_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_vein_ambiguous_ore_glob__rain(live_test):
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
                        4,
                        0,
                        0,
                    ),
                    block='coal_ore',
                ),
            ),
            items=((
                'iron_pickaxe',
                1,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_vein', {'block': '*_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_vein', {'block': '*_ore'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)
