"""Live tests for minecraft_eat_best. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_eat_best_apple(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
            food=10,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_eat_best', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_eat_best', {}, truth_before=truth_before)
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


def test_eat_best_steak_over_apple(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'apple',
                    1,
                ),
                (
                    'cooked_beef',
                    1,
                ),
            ),
            food=5,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_eat_best', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_eat_best', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'ate')
    assert_field(scenario, result, 'item.name', 'cooked_beef')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='cooked_beef',
        expected=0,
    ),))


def test_eat_best_bread_over_rotten_flesh(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'rotten_flesh',
                    1,
                ),
                (
                    'bread',
                    1,
                ),
            ),
            food=10,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_eat_best', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_eat_best', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'ate')
    assert_field(scenario, result, 'item.name', 'bread')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='bread',
        expected=0,
    ),))


def test_eat_best_golden_carrot(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'golden_carrot',
                    1,
                ),
                (
                    'cooked_beef',
                    1,
                ),
            ),
            food=12,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_eat_best', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_eat_best', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'ate')
    assert_field(scenario, result, 'item.name', 'golden_carrot')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='golden_carrot',
        expected=0,
    ),))



@pytest.mark.smoke
def test_eat_best_no_food(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'stone',
                4,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_eat_best', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_eat_best', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_food'
    assert_message(result, 'food', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_eat_best_food_full(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_eat_best', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_eat_best', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'food_full'
    assert_message(result, 'food', 'full')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_eat_best_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_eat_best', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_eat_best_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_eat_best', {'unexpected_argument': True}, timeout=660)
    assert_protocol_error(res, 'unexpected_argument')


def test_eat_best_no_food__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'stone',
                4,
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
    res = call_mcp(scenario, 'minecraft_eat_best', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_eat_best', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_food'
    assert_message(result, 'food', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_eat_best_no_food__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'stone',
                4,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_eat_best', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_eat_best', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_food'
    assert_message(result, 'food', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_eat_best_no_food__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'stone',
                4,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_eat_best', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_eat_best', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_food'
    assert_message(result, 'food', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_eat_best_food_full__armor(live_test):
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
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_eat_best', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_eat_best', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'food_full'
    assert_message(result, 'food', 'full')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_eat_best_food_full__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_eat_best', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_eat_best', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'food_full'
    assert_message(result, 'food', 'full')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_eat_best_food_full__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_eat_best', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_eat_best', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'food_full'
    assert_message(result, 'food', 'full')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='apple',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)
