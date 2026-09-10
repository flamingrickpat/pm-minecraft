"""Live tests for minecraft_harvest_tree. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_harvest_tree_oak(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='log_0',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_1',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_2',
                    offset=(
                        3,
                        2,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_3',
                    offset=(
                        3,
                        3,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='leaf_0',
                    offset=(
                        2,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_1',
                    offset=(
                        3,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_2',
                    offset=(
                        4,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
            ),
            items=((
                'iron_axe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$log_0'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$log_0'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'base', '$log_0')
    assert_field(scenario, result, 'logs_collected', 4)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='log_0',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_log',
            expected=4,
        ),
    ))


def test_harvest_tree_birch(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='log_0',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='birch_log',
                ),
                BlockSpec(
                    key='log_1',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='birch_log',
                ),
                BlockSpec(
                    key='log_2',
                    offset=(
                        3,
                        2,
                        0,
                    ),
                    block='birch_log',
                ),
                BlockSpec(
                    key='log_3',
                    offset=(
                        3,
                        3,
                        0,
                    ),
                    block='birch_log',
                ),
                BlockSpec(
                    key='leaf_0',
                    offset=(
                        2,
                        4,
                        0,
                    ),
                    block='birch_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_1',
                    offset=(
                        3,
                        4,
                        0,
                    ),
                    block='birch_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_2',
                    offset=(
                        4,
                        4,
                        0,
                    ),
                    block='birch_leaves[persistent=true]',
                ),
            ),
            items=((
                'iron_axe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$log_0'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$log_0'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'base', '$log_0')
    assert_field(scenario, result, 'logs_collected', 4)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='log_0',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='birch_log',
            expected=4,
        ),
    ))


def test_harvest_tree_spruce(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='log_0',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='spruce_log',
                ),
                BlockSpec(
                    key='log_1',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='spruce_log',
                ),
                BlockSpec(
                    key='log_2',
                    offset=(
                        3,
                        2,
                        0,
                    ),
                    block='spruce_log',
                ),
                BlockSpec(
                    key='log_3',
                    offset=(
                        3,
                        3,
                        0,
                    ),
                    block='spruce_log',
                ),
                BlockSpec(
                    key='leaf_0',
                    offset=(
                        2,
                        4,
                        0,
                    ),
                    block='spruce_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_1',
                    offset=(
                        3,
                        4,
                        0,
                    ),
                    block='spruce_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_2',
                    offset=(
                        4,
                        4,
                        0,
                    ),
                    block='spruce_leaves[persistent=true]',
                ),
            ),
            items=((
                'iron_axe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$log_0'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$log_0'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'base', '$log_0')
    assert_field(scenario, result, 'logs_collected', 4)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='log_0',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='spruce_log',
            expected=4,
        ),
    ))


def test_harvest_tree_jungle(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='log_0',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='jungle_log',
                ),
                BlockSpec(
                    key='log_1',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='jungle_log',
                ),
                BlockSpec(
                    key='log_2',
                    offset=(
                        3,
                        2,
                        0,
                    ),
                    block='jungle_log',
                ),
                BlockSpec(
                    key='log_3',
                    offset=(
                        3,
                        3,
                        0,
                    ),
                    block='jungle_log',
                ),
                BlockSpec(
                    key='leaf_0',
                    offset=(
                        2,
                        4,
                        0,
                    ),
                    block='jungle_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_1',
                    offset=(
                        3,
                        4,
                        0,
                    ),
                    block='jungle_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_2',
                    offset=(
                        4,
                        4,
                        0,
                    ),
                    block='jungle_leaves[persistent=true]',
                ),
            ),
            items=((
                'iron_axe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$log_0'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$log_0'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'base', '$log_0')
    assert_field(scenario, result, 'logs_collected', 4)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='log_0',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='jungle_log',
            expected=4,
        ),
    ))


def test_harvest_tree_acacia(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='log_0',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='acacia_log',
                ),
                BlockSpec(
                    key='log_1',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='acacia_log',
                ),
                BlockSpec(
                    key='log_2',
                    offset=(
                        3,
                        2,
                        0,
                    ),
                    block='acacia_log',
                ),
                BlockSpec(
                    key='log_3',
                    offset=(
                        3,
                        3,
                        0,
                    ),
                    block='acacia_log',
                ),
                BlockSpec(
                    key='leaf_0',
                    offset=(
                        2,
                        4,
                        0,
                    ),
                    block='acacia_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_1',
                    offset=(
                        3,
                        4,
                        0,
                    ),
                    block='acacia_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_2',
                    offset=(
                        4,
                        4,
                        0,
                    ),
                    block='acacia_leaves[persistent=true]',
                ),
            ),
            items=((
                'iron_axe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$log_0'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$log_0'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'base', '$log_0')
    assert_field(scenario, result, 'logs_collected', 4)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='log_0',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='acacia_log',
            expected=4,
        ),
    ))



@pytest.mark.smoke
def test_harvest_tree_no_tree(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': None}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_harvest_tree_player_built_log(live_test):
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
                block='oak_log',
            ),),
            items=((
                'iron_axe',
                1,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_a_tree'
    assert_message(result, 'not', 'tree')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='oak_log',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_harvest_tree_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_harvest_tree', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_harvest_tree_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': {'not': 'the declared type'}}, timeout=660)
    assert_protocol_error(res, 'base')



@pytest.mark.contract
def test_harvest_tree_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'base')


def test_harvest_tree_oak__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='log_0',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_1',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_2',
                    offset=(
                        3,
                        2,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_3',
                    offset=(
                        3,
                        3,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='leaf_0',
                    offset=(
                        2,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_1',
                    offset=(
                        3,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_2',
                    offset=(
                        4,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
            ),
            items=((
                'iron_axe',
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
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$log_0'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$log_0'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'base', '$log_0')
    assert_field(scenario, result, 'logs_collected', 4)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='log_0',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_log',
            expected=4,
        ),
    ))


def test_harvest_tree_oak__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='log_0',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_1',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_2',
                    offset=(
                        3,
                        2,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_3',
                    offset=(
                        3,
                        3,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='leaf_0',
                    offset=(
                        2,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_1',
                    offset=(
                        3,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_2',
                    offset=(
                        4,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
            ),
            items=((
                'iron_axe',
                1,
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$log_0'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$log_0'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'base', '$log_0')
    assert_field(scenario, result, 'logs_collected', 4)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='log_0',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_log',
            expected=4,
        ),
    ))


def test_harvest_tree_oak__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='log_0',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_1',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_2',
                    offset=(
                        3,
                        2,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_3',
                    offset=(
                        3,
                        3,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='leaf_0',
                    offset=(
                        2,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_1',
                    offset=(
                        3,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_2',
                    offset=(
                        4,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
            ),
            items=((
                'iron_axe',
                1,
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$log_0'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$log_0'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'base', '$log_0')
    assert_field(scenario, result, 'logs_collected', 4)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='log_0',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_log',
            expected=4,
        ),
    ))


def test_harvest_tree_oak__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='log_0',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_1',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_2',
                    offset=(
                        3,
                        2,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_3',
                    offset=(
                        3,
                        3,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='leaf_0',
                    offset=(
                        2,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_1',
                    offset=(
                        3,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_2',
                    offset=(
                        4,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
            ),
            items=((
                'iron_axe',
                1,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$log_0'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$log_0'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'base', '$log_0')
    assert_field(scenario, result, 'logs_collected', 4)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='log_0',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_log',
            expected=4,
        ),
    ))


def test_harvest_tree_oak__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='log_0',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_1',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_2',
                    offset=(
                        3,
                        2,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_3',
                    offset=(
                        3,
                        3,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='leaf_0',
                    offset=(
                        2,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_1',
                    offset=(
                        3,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_2',
                    offset=(
                        4,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
            ),
            items=((
                'iron_axe',
                1,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$log_0'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$log_0'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'base', '$log_0')
    assert_field(scenario, result, 'logs_collected', 4)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='log_0',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_log',
            expected=4,
        ),
    ))


def test_harvest_tree_oak__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='log_0',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_1',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_2',
                    offset=(
                        3,
                        2,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='log_3',
                    offset=(
                        3,
                        3,
                        0,
                    ),
                    block='oak_log',
                ),
                BlockSpec(
                    key='leaf_0',
                    offset=(
                        2,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_1',
                    offset=(
                        3,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
                BlockSpec(
                    key='leaf_2',
                    offset=(
                        4,
                        4,
                        0,
                    ),
                    block='oak_leaves[persistent=true]',
                ),
            ),
            items=(
                (
                    'iron_axe',
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
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$log_0'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$log_0'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'base', '$log_0')
    assert_field(scenario, result, 'logs_collected', 4)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='log_0',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_log',
            expected=4,
        ),
    ))


def test_harvest_tree_no_tree__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': None}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_harvest_tree_no_tree__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': None}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_harvest_tree_no_tree__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': None}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_harvest_tree_player_built_log__armor(live_test):
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
                block='oak_log',
            ),),
            items=((
                'iron_axe',
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
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_a_tree'
    assert_message(result, 'not', 'tree')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='oak_log',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_harvest_tree_player_built_log__night(live_test):
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
                block='oak_log',
            ),),
            items=((
                'iron_axe',
                1,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_a_tree'
    assert_message(result, 'not', 'tree')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='oak_log',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_harvest_tree_player_built_log__rain(live_test):
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
                block='oak_log',
            ),),
            items=((
                'iron_axe',
                1,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_harvest_tree', {'base': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_harvest_tree', {'base': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_a_tree'
    assert_message(result, 'not', 'tree')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='oak_log',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)
