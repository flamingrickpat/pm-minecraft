"""Live tests for minecraft_discard_items. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_setup_success, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_discard_items_count_1(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'cobblestone',
                16,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'discarded_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=15,
        ),
        WorldExpectation(
            kind='item_entities',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_discard_items_count_7(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'cobblestone',
                16,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 7}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 7}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'discarded_count', 7)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=9,
        ),
        WorldExpectation(
            kind='item_entities',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_discard_items_all(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'cobblestone',
                16,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'cobblestone', 'count': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'cobblestone', 'count': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'discarded_count', 16)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
        WorldExpectation(
            kind='item_entities',
            target='cobblestone',
            expected=0,
        ),
    ))



@pytest.mark.smoke
def test_discard_items_absent(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'diamond', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'diamond', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_discard_items_ambiguous(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'oak_log',
                    1,
                ),
                (
                    'birch_log',
                    1,
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': '*_log', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': '*_log', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_discard_items_second_discard_reports_absent(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'dirt',
                8,
            ),),
        ),
    )
    setup_res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'dirt', 'count': None}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_discard_items')
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'dirt', 'count': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'dirt', 'count': None}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'discarded_count', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_discard_items_full_inventory_all_stacks(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            slot_items=(
                (
                    'hotbar.0',
                    'dirt',
                    64,
                ),
                (
                    'hotbar.1',
                    'dirt',
                    64,
                ),
                (
                    'hotbar.2',
                    'dirt',
                    64,
                ),
                (
                    'hotbar.3',
                    'dirt',
                    64,
                ),
                (
                    'hotbar.4',
                    'dirt',
                    64,
                ),
                (
                    'hotbar.5',
                    'dirt',
                    64,
                ),
                (
                    'hotbar.6',
                    'dirt',
                    64,
                ),
                (
                    'hotbar.7',
                    'dirt',
                    64,
                ),
                (
                    'hotbar.8',
                    'dirt',
                    64,
                ),
                (
                    'inventory.0',
                    'dirt',
                    64,
                ),
                (
                    'inventory.1',
                    'dirt',
                    64,
                ),
                (
                    'inventory.2',
                    'dirt',
                    64,
                ),
                (
                    'inventory.3',
                    'dirt',
                    64,
                ),
                (
                    'inventory.4',
                    'dirt',
                    64,
                ),
                (
                    'inventory.5',
                    'dirt',
                    64,
                ),
                (
                    'inventory.6',
                    'dirt',
                    64,
                ),
                (
                    'inventory.7',
                    'dirt',
                    64,
                ),
                (
                    'inventory.8',
                    'dirt',
                    64,
                ),
                (
                    'inventory.9',
                    'dirt',
                    64,
                ),
                (
                    'inventory.10',
                    'dirt',
                    64,
                ),
                (
                    'inventory.11',
                    'dirt',
                    64,
                ),
                (
                    'inventory.12',
                    'dirt',
                    64,
                ),
                (
                    'inventory.13',
                    'dirt',
                    64,
                ),
                (
                    'inventory.14',
                    'dirt',
                    64,
                ),
                (
                    'inventory.15',
                    'dirt',
                    64,
                ),
                (
                    'inventory.16',
                    'dirt',
                    64,
                ),
                (
                    'inventory.17',
                    'dirt',
                    64,
                ),
                (
                    'inventory.18',
                    'dirt',
                    64,
                ),
                (
                    'inventory.19',
                    'dirt',
                    64,
                ),
                (
                    'inventory.20',
                    'dirt',
                    64,
                ),
                (
                    'inventory.21',
                    'dirt',
                    64,
                ),
                (
                    'inventory.22',
                    'dirt',
                    64,
                ),
                (
                    'inventory.23',
                    'dirt',
                    64,
                ),
                (
                    'inventory.24',
                    'dirt',
                    64,
                ),
                (
                    'inventory.25',
                    'dirt',
                    64,
                ),
                (
                    'inventory.26',
                    'dirt',
                    64,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'dirt', 'count': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'dirt', 'count': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'discarded_count', 2304)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='dirt',
            expected=0,
        ),
        WorldExpectation(
            kind='item_entities',
            target='dirt',
            expected=0,
        ),
    ))



@pytest.mark.contract
def test_discard_items_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'stone'}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_discard_items_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_discard_items', {}, timeout=660)
    assert_protocol_error(res, 'item')



@pytest.mark.contract
def test_discard_items_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'item')


def test_discard_items_count_1__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'cobblestone',
                16,
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
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'discarded_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=15,
        ),
        WorldExpectation(
            kind='item_entities',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_discard_items_count_1__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'cobblestone',
                16,
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'discarded_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=15,
        ),
        WorldExpectation(
            kind='item_entities',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_discard_items_count_1__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'cobblestone',
                16,
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'discarded_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=15,
        ),
        WorldExpectation(
            kind='item_entities',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_discard_items_count_1__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'cobblestone',
                16,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'discarded_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=15,
        ),
        WorldExpectation(
            kind='item_entities',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_discard_items_count_1__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'cobblestone',
                16,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'discarded_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=15,
        ),
        WorldExpectation(
            kind='item_entities',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_discard_items_count_1__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'cobblestone',
                    16,
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
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'cobblestone', 'count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'discarded_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=15,
        ),
        WorldExpectation(
            kind='item_entities',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_discard_items_absent__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'diamond', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'diamond', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_discard_items_absent__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'diamond', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'diamond', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_discard_items_absent__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'diamond', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'diamond', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_discard_items_ambiguous__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'oak_log',
                    1,
                ),
                (
                    'birch_log',
                    1,
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
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': '*_log', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': '*_log', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_discard_items_ambiguous__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'oak_log',
                    1,
                ),
                (
                    'birch_log',
                    1,
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': '*_log', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': '*_log', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_discard_items_ambiguous__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'oak_log',
                    1,
                ),
                (
                    'birch_log',
                    1,
                ),
            ),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': '*_log', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': '*_log', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_discard_items_second_discard_reports_absent__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'dirt',
                8,
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
    setup_res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'dirt', 'count': None}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_discard_items')
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'dirt', 'count': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'dirt', 'count': None}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'discarded_count', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_discard_items_second_discard_reports_absent__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'dirt',
                8,
            ),),
            time=18000,
        ),
    )
    setup_res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'dirt', 'count': None}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_discard_items')
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'dirt', 'count': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'dirt', 'count': None}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'discarded_count', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_discard_items_second_discard_reports_absent__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'dirt',
                8,
            ),),
            weather='rain',
        ),
    )
    setup_res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'dirt', 'count': None}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_discard_items')
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_discard_items', {'item': 'dirt', 'count': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_discard_items', {'item': 'dirt', 'count': None}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'discarded_count', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)
