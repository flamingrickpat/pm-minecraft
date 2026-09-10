"""Live tests for minecraft_craft_item. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_craft_item_planks_once(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'oak_planks')
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'repetitions_crafted', 1)
    assert_field(scenario, result, 'output.count', 4)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=4,
    ),))


def test_craft_item_planks_many(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                3,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 3}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 3}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'oak_planks')
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'repetitions_crafted', 3)
    assert_field(scenario, result, 'output.count', 12)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=12,
    ),))


def test_craft_item_sticks(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_planks',
                4,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'stick', 'repetitions': 2}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'stick', 'repetitions': 2}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'stick')
    assert_field(scenario, result, 'resolved_item', 'stick')
    assert_field(scenario, result, 'repetitions_crafted', 2)
    assert_field(scenario, result, 'output.count', 8)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='stick',
        expected=8,
    ),))


def test_craft_item_sticks_with_crafting_table_window_open(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='table',
                offset=(3, 0, 0),
                block='crafting_table',
            ),),
            items=((
                'oak_planks',
                2,
            ),),
        ),
    )

    truth_before_open = capture_truth(scenario)
    opened = call_mcp(scenario, 'minecraft_use_block', {'position': '$table'}, timeout=660)
    opened_result = parse_result(
        scenario,
        opened,
        'minecraft_use_block',
        {'position': '$table'},
        truth_before=truth_before_open,
    )
    assert opened_result.ok is True
    assert_field(scenario, opened_result, 'action', 'crafting_table_opened')

    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'stick', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'stick', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'resolved_item', 'stick')
    assert_field(scenario, result, 'repetitions_crafted', 1)
    assert_field(scenario, result, 'output.count', 4)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='stick',
        expected=4,
    ),))


def test_craft_item_crafting_table(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_planks',
                4,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'crafting_table', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'crafting_table', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'crafting_table')
    assert_field(scenario, result, 'resolved_item', 'crafting_table')
    assert_field(scenario, result, 'repetitions_crafted', 1)
    assert_field(scenario, result, 'output.count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='crafting_table',
        expected=1,
    ),))



@pytest.mark.smoke
def test_craft_item_missing_ingredients(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'iron_ingot',
                    2,
                ),
                (
                    'stick',
                    2,
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'missing_ingredients'
    assert_message(result, 'missing', 'ingredient')
    assert_field(scenario, result, 'repetitions_crafted', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_table_missing(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'iron_ingot',
                    3,
                ),
                (
                    'stick',
                    2,
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'crafting_table_not_found'
    assert_message(result, 'crafting table', 'not found')
    assert_field(scenario, result, 'repetitions_crafted', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_unknown(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'iron_pickax', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'iron_pickax', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_ambiguous(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'oak_planks',
                    20,
                ),
                (
                    'cobblestone',
                    20,
                ),
                (
                    'stick',
                    20,
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': '*_pickaxe', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': '*_pickaxe', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_three_by_three_at_table(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='table',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='crafting_table',
            ),),
            items=(
                (
                    'iron_ingot',
                    3,
                ),
                (
                    'stick',
                    2,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'resolved_item', 'iron_pickaxe')
    assert_field(scenario, result, 'repetitions_crafted', 1)
    assert_field(scenario, result, 'crafting_table_used', '$table')
    assert_field(scenario, result, 'output.count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='iron_pickaxe',
            expected=1,
        ),
        WorldExpectation(
            kind='inventory',
            target='iron_ingot',
            expected=0,
        ),
        WorldExpectation(
            kind='inventory',
            target='stick',
            expected=0,
        ),
    ))



@pytest.mark.contract
def test_craft_item_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'stone'}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_craft_item_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_craft_item', {}, timeout=660)
    assert_protocol_error(res, 'item')



@pytest.mark.contract
def test_craft_item_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'item')


def test_craft_item_planks_once__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
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
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'oak_planks')
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'repetitions_crafted', 1)
    assert_field(scenario, result, 'output.count', 4)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=4,
    ),))


def test_craft_item_planks_once__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                1,
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'oak_planks')
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'repetitions_crafted', 1)
    assert_field(scenario, result, 'output.count', 4)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=4,
    ),))


def test_craft_item_planks_once__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                1,
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'oak_planks')
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'repetitions_crafted', 1)
    assert_field(scenario, result, 'output.count', 4)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=4,
    ),))


def test_craft_item_planks_once__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                1,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'oak_planks')
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'repetitions_crafted', 1)
    assert_field(scenario, result, 'output.count', 4)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=4,
    ),))


def test_craft_item_planks_once__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                1,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'oak_planks')
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'repetitions_crafted', 1)
    assert_field(scenario, result, 'output.count', 4)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=4,
    ),))


def test_craft_item_planks_once__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'oak_log',
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
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'oak_planks', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'oak_planks')
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'repetitions_crafted', 1)
    assert_field(scenario, result, 'output.count', 4)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=4,
    ),))


def test_craft_item_missing_ingredients__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'iron_ingot',
                    2,
                ),
                (
                    'stick',
                    2,
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
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'missing_ingredients'
    assert_message(result, 'missing', 'ingredient')
    assert_field(scenario, result, 'repetitions_crafted', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_missing_ingredients__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'iron_ingot',
                    2,
                ),
                (
                    'stick',
                    2,
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'missing_ingredients'
    assert_message(result, 'missing', 'ingredient')
    assert_field(scenario, result, 'repetitions_crafted', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_missing_ingredients__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'iron_ingot',
                    2,
                ),
                (
                    'stick',
                    2,
                ),
            ),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'missing_ingredients'
    assert_message(result, 'missing', 'ingredient')
    assert_field(scenario, result, 'repetitions_crafted', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_table_missing__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'iron_ingot',
                    3,
                ),
                (
                    'stick',
                    2,
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
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'crafting_table_not_found'
    assert_message(result, 'crafting table', 'not found')
    assert_field(scenario, result, 'repetitions_crafted', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_table_missing__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'iron_ingot',
                    3,
                ),
                (
                    'stick',
                    2,
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'crafting_table_not_found'
    assert_message(result, 'crafting table', 'not found')
    assert_field(scenario, result, 'repetitions_crafted', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_table_missing__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'iron_ingot',
                    3,
                ),
                (
                    'stick',
                    2,
                ),
            ),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'iron_pickaxe', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'crafting_table_not_found'
    assert_message(result, 'crafting table', 'not found')
    assert_field(scenario, result, 'repetitions_crafted', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_unknown__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'iron_pickax', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'iron_pickax', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_unknown__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'iron_pickax', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'iron_pickax', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_unknown__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': 'iron_pickax', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': 'iron_pickax', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_ambiguous__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'oak_planks',
                    20,
                ),
                (
                    'cobblestone',
                    20,
                ),
                (
                    'stick',
                    20,
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
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': '*_pickaxe', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': '*_pickaxe', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_ambiguous__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'oak_planks',
                    20,
                ),
                (
                    'cobblestone',
                    20,
                ),
                (
                    'stick',
                    20,
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': '*_pickaxe', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': '*_pickaxe', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_item_ambiguous__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'oak_planks',
                    20,
                ),
                (
                    'cobblestone',
                    20,
                ),
                (
                    'stick',
                    20,
                ),
            ),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_item', {'item': '*_pickaxe', 'repetitions': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_item', {'item': '*_pickaxe', 'repetitions': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)
