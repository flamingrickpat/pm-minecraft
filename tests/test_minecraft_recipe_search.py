"""Live tests for minecraft_recipe_search. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import AtLeast, Layout, Length, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_recipe_search_planks_exact(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                2,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', 'oak_planks')
    assert_response_image(res, result, False)


def test_recipe_search_pickaxes_glob(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                2,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': '*_pickaxe', 'craftable_now': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': '*_pickaxe', 'craftable_now': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', '*_pickaxe')
    assert_response_image(res, result, False)


def test_recipe_search_craftable_only(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                2,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', 'oak_planks')
    assert_response_image(res, result, False)


def test_recipe_search_uncraftable_only(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                2,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': 'iron_pickaxe', 'craftable_now': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': 'iron_pickaxe', 'craftable_now': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', 'iron_pickaxe')
    assert_response_image(res, result, False)


def test_recipe_search_all_limited(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                2,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': '*', 'craftable_now': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': '*', 'craftable_now': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', '*')
    assert_response_image(res, result, False)



@pytest.mark.smoke
def test_recipe_search_unknown(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': 'definitely_not_an_item'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': 'definitely_not_an_item'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_recipe_search_result_limit(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': '*', 'craftable_now': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': '*', 'craftable_now': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'matches', Length(
        value=32,
    ))
    assert_field(scenario, result, 'total_recipes', AtLeast(
        value=33,
    ))
    assert_response_image(res, result, False)



@pytest.mark.contract
def test_recipe_search_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_recipe_search', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_recipe_search_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': {'not': 'the declared type'}}, timeout=660)
    assert_protocol_error(res, 'pattern')



@pytest.mark.contract
def test_recipe_search_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'pattern')


def test_recipe_search_planks_exact__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                2,
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
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', 'oak_planks')
    assert_response_image(res, result, False)


def test_recipe_search_planks_exact__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                2,
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', 'oak_planks')
    assert_response_image(res, result, False)


def test_recipe_search_planks_exact__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                2,
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', 'oak_planks')
    assert_response_image(res, result, False)


def test_recipe_search_planks_exact__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                2,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', 'oak_planks')
    assert_response_image(res, result, False)


def test_recipe_search_planks_exact__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'oak_log',
                2,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', 'oak_planks')
    assert_response_image(res, result, False)


def test_recipe_search_planks_exact__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'oak_log',
                    2,
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
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': 'oak_planks', 'craftable_now': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', 'oak_planks')
    assert_response_image(res, result, False)


def test_recipe_search_unknown__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': 'definitely_not_an_item'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': 'definitely_not_an_item'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_recipe_search_unknown__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': 'definitely_not_an_item'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': 'definitely_not_an_item'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_recipe_search_unknown__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_recipe_search', {'pattern': 'definitely_not_an_item'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recipe_search', {'pattern': 'definitely_not_an_item'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)
