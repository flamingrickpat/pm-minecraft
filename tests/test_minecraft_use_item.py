"""Live tests for minecraft_use_item. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_use_item_eat_apple(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
            held_item='apple',
            food=10,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'ate')
    assert_field(scenario, result, 'item.name', 'apple')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=0,
    ),))


def test_use_item_drink_potion(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'potion',
                1,
            ),),
            held_item='potion',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'drank')
    assert_field(scenario, result, 'item.name', 'potion')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='potion',
        expected=0,
    ),))


def test_use_item_throw_snowball(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'snowball',
                1,
            ),),
            held_item='snowball',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'threw')
    assert_field(scenario, result, 'item.name', 'snowball')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='snowball',
        expected=0,
    ),))


def test_use_item_activate_shield(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'shield',
                1,
            ),),
            held_item='shield',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'activated')
    assert_field(scenario, result, 'item.name', 'shield')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='shield',
        expected=1,
    ),))



@pytest.mark.smoke
def test_use_item_empty_hand(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_held_item'
    assert_message(result, 'hand', 'empty')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_item_stone_not_usable(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'stone',
                1,
            ),),
            held_item='stone',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_usable'
    assert_message(result, 'not', 'usable')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='stone',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_item_food_full(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
            held_item='apple',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'food_full'
    assert_message(result, 'food', 'full')
    assert_field(scenario, result, 'action', 'nothing')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_use_item_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_use_item_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_use_item', {'unexpected_argument': True}, timeout=660)
    assert_protocol_error(res, 'unexpected_argument')


def test_use_item_eat_apple__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
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
            held_item='apple',
            food=10,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'ate')
    assert_field(scenario, result, 'item.name', 'apple')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=0,
    ),))


def test_use_item_eat_apple__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
            held_item='apple',
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'ate')
    assert_field(scenario, result, 'item.name', 'apple')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=0,
    ),))


def test_use_item_eat_apple__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
            held_item='apple',
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'ate')
    assert_field(scenario, result, 'item.name', 'apple')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=0,
    ),))


def test_use_item_eat_apple__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
            held_item='apple',
            time=18000,
            food=10,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'ate')
    assert_field(scenario, result, 'item.name', 'apple')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=0,
    ),))


def test_use_item_eat_apple__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
            held_item='apple',
            weather='rain',
            food=10,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'ate')
    assert_field(scenario, result, 'item.name', 'apple')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=0,
    ),))


def test_use_item_eat_apple__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'apple',
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
            held_item='apple',
            food=10,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'ate')
    assert_field(scenario, result, 'item.name', 'apple')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=0,
    ),))


def test_use_item_empty_hand__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_held_item'
    assert_message(result, 'hand', 'empty')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_item_empty_hand__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_held_item'
    assert_message(result, 'hand', 'empty')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_item_empty_hand__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_held_item'
    assert_message(result, 'hand', 'empty')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_item_stone_not_usable__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'stone',
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
            held_item='stone',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_usable'
    assert_message(result, 'not', 'usable')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='stone',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_item_stone_not_usable__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'stone',
                1,
            ),),
            held_item='stone',
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_usable'
    assert_message(result, 'not', 'usable')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='stone',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_item_stone_not_usable__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'stone',
                1,
            ),),
            held_item='stone',
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_usable'
    assert_message(result, 'not', 'usable')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='stone',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_item_food_full__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
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
            held_item='apple',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'food_full'
    assert_message(result, 'food', 'full')
    assert_field(scenario, result, 'action', 'nothing')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_item_food_full__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
            held_item='apple',
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'food_full'
    assert_message(result, 'food', 'full')
    assert_field(scenario, result, 'action', 'nothing')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_item_food_full__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
            held_item='apple',
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_item', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_item', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'food_full'
    assert_message(result, 'food', 'full')
    assert_field(scenario, result, 'action', 'nothing')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)
