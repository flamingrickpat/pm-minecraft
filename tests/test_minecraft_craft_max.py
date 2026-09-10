"""Live tests for minecraft_craft_max. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_craft_max_zero(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'crafted', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=0,
    ),))


def test_craft_max_one(live_test):
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
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'crafted', 4)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=4,
    ),))


def test_craft_max_many(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                5,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'crafted', 20)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=20,
    ),))


def test_craft_max_limit_below(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                5,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': 8}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': 8}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'crafted', 8)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=8,
    ),))


def test_craft_max_limit_equal(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                5,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': 20}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': 20}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'crafted', 20)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=20,
    ),))


def test_craft_max_limit_above(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                5,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': 40}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': 40}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'crafted', 20)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=20,
    ),))



@pytest.mark.smoke
def test_craft_max_unknown(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_plankk'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_plankk'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_max_ambiguous(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                1,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': '*_planks'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': '*_planks'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_craft_max_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'stone'}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_craft_max_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_craft_max', {}, timeout=660)
    assert_protocol_error(res, 'item')



@pytest.mark.contract
def test_craft_max_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'item')


def test_craft_max_zero__armor(live_test):
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
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'crafted', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=0,
    ),))


def test_craft_max_zero__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'crafted', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=0,
    ),))


def test_craft_max_zero__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'crafted', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=0,
    ),))


def test_craft_max_zero__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'crafted', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=0,
    ),))


def test_craft_max_zero__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'crafted', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=0,
    ),))


def test_craft_max_zero__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
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
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_planks', 'limit': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'resolved_item', 'oak_planks')
    assert_field(scenario, result, 'crafted', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='oak_planks',
        expected=0,
    ),))


def test_craft_max_unknown__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_plankk'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_plankk'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_max_unknown__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_plankk'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_plankk'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_max_unknown__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': 'oak_plankk'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': 'oak_plankk'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_max_ambiguous__armor(live_test):
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': '*_planks'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': '*_planks'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_max_ambiguous__night(live_test):
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': '*_planks'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': '*_planks'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_craft_max_ambiguous__rain(live_test):
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_craft_max', {'item': '*_planks'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_craft_max', {'item': '*_planks'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)
