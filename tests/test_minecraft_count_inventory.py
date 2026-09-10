"""Live tests for minecraft_count_inventory. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_count_inventory_empty(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_count_inventory', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', '*')
    assert_field(scenario, result, 'total_matching_items', 0)
    assert_response_image(res, result, False)


def test_count_inventory_one_stack(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'cobblestone',
                64,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': 'cobblestone'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_count_inventory', {'pattern': 'cobblestone'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', 'cobblestone')
    assert_field(scenario, result, 'total_matching_items', 64)
    assert_response_image(res, result, False)


def test_count_inventory_split_stacks(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'cobblestone',
                    64,
                ),
                (
                    'cobblestone',
                    37,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': 'cobblestone'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_count_inventory', {'pattern': 'cobblestone'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', 'cobblestone')
    assert_field(scenario, result, 'total_matching_items', 101)
    assert_response_image(res, result, False)


def test_count_inventory_wildcard(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'oak_log',
                    4,
                ),
                (
                    'birch_log',
                    7,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': '*_log'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_count_inventory', {'pattern': '*_log'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', '*_log')
    assert_field(scenario, result, 'total_matching_items', 11)
    assert_response_image(res, result, False)


def test_count_inventory_armor_and_offhand(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            equipment=(
                (
                    'armor.head',
                    'iron_helmet',
                ),
                (
                    'weapon.offhand',
                    'shield',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': '*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_count_inventory', {'pattern': '*'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'pattern', '*')
    assert_field(scenario, result, 'total_matching_items', 2)
    assert_response_image(res, result, False)



@pytest.mark.smoke
def test_count_inventory_absent(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': 'diamond'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_count_inventory', {'pattern': 'diamond'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'total_matching_items', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_count_inventory_typo(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'cobblestone',
                3,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': 'cobblestne'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_count_inventory', {'pattern': 'cobblestne'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_count_inventory_full_inventory(live_test):
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
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': 'dirt'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_count_inventory', {'pattern': 'dirt'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'total_matching_items', 2304)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='dirt',
        expected=2304,
    ),))



@pytest.mark.contract
def test_count_inventory_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_count_inventory', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_count_inventory_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': {'not': 'the declared type'}}, timeout=660)
    assert_protocol_error(res, 'pattern')



@pytest.mark.contract
def test_count_inventory_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'pattern')


def test_count_inventory_absent__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': 'diamond'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_count_inventory', {'pattern': 'diamond'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'total_matching_items', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_count_inventory_absent__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': 'diamond'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_count_inventory', {'pattern': 'diamond'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'total_matching_items', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_count_inventory_absent__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': 'diamond'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_count_inventory', {'pattern': 'diamond'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_field(scenario, result, 'total_matching_items', 0)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_count_inventory_typo__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'cobblestone',
                3,
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
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': 'cobblestne'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_count_inventory', {'pattern': 'cobblestne'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_count_inventory_typo__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'cobblestone',
                3,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': 'cobblestne'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_count_inventory', {'pattern': 'cobblestne'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_count_inventory_typo__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'cobblestone',
                3,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_count_inventory', {'pattern': 'cobblestne'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_count_inventory', {'pattern': 'cobblestne'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)
