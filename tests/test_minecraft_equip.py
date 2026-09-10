"""Live tests for minecraft_equip. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_setup_success, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_equip_iron_pickaxe(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'iron_pickaxe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'iron_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'iron_pickaxe'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'iron_pickaxe')
    assert_field(scenario, result, 'equipped.name', 'iron_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_data',
        target='SelectedItem.id',
        expected='minecraft:iron_pickaxe',
    ),))


def test_equip_iron_sword(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'iron_sword',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'iron_sword'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'iron_sword'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'iron_sword')
    assert_field(scenario, result, 'equipped.name', 'iron_sword')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_data',
        target='SelectedItem.id',
        expected='minecraft:iron_sword',
    ),))


def test_equip_shield(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'shield',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'shield'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'shield'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'shield')
    assert_field(scenario, result, 'equipped.name', 'shield')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_data',
        target='SelectedItem.id',
        expected='minecraft:shield',
    ),))


def test_equip_apple(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'apple'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'apple'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'apple')
    assert_field(scenario, result, 'equipped.name', 'apple')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_data',
        target='SelectedItem.id',
        expected='minecraft:apple',
    ),))


def test_equip_cobblestone(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'cobblestone',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'cobblestone'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'cobblestone'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'cobblestone')
    assert_field(scenario, result, 'equipped.name', 'cobblestone')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_data',
        target='SelectedItem.id',
        expected='minecraft:cobblestone',
    ),))


def test_equip_iron_helmet(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'iron_helmet',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'iron_helmet'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'iron_helmet'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'iron_helmet')
    assert_field(scenario, result, 'equipped.name', 'iron_helmet')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_data',
        target='SelectedItem.id',
        expected='minecraft:iron_helmet',
    ),))



@pytest.mark.smoke
def test_equip_absent(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'iron_pickaxe',
                1,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'diamond_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'diamond_pickaxe'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_pickaxe',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_equip_ambiguous(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'iron_pickaxe',
                    1,
                ),
                (
                    'stone_pickaxe',
                    1,
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': '*_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': '*_pickaxe'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_equip_second_equip_is_stable(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'iron_pickaxe',
                1,
            ),),
        ),
    )
    setup_res = call_mcp(scenario, 'minecraft_equip', {'item': 'iron_pickaxe'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_equip')
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'iron_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'iron_pickaxe'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'equipped.name', 'iron_pickaxe')
    assert_field(scenario, result, 'previous_held.name', 'iron_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_data',
        target='SelectedItem.id',
        expected='minecraft:iron_pickaxe',
    ),))



@pytest.mark.contract
def test_equip_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'stone'}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_equip_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_equip', {}, timeout=660)
    assert_protocol_error(res, 'item')



@pytest.mark.contract
def test_equip_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_equip', {'item': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'item')


def test_equip_iron_pickaxe__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
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
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'iron_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'iron_pickaxe'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'iron_pickaxe')
    assert_field(scenario, result, 'equipped.name', 'iron_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_data',
        target='SelectedItem.id',
        expected='minecraft:iron_pickaxe',
    ),))


def test_equip_iron_pickaxe__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'iron_pickaxe',
                1,
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'iron_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'iron_pickaxe'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'iron_pickaxe')
    assert_field(scenario, result, 'equipped.name', 'iron_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_data',
        target='SelectedItem.id',
        expected='minecraft:iron_pickaxe',
    ),))


def test_equip_iron_pickaxe__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'iron_pickaxe',
                1,
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'iron_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'iron_pickaxe'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'iron_pickaxe')
    assert_field(scenario, result, 'equipped.name', 'iron_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_data',
        target='SelectedItem.id',
        expected='minecraft:iron_pickaxe',
    ),))


def test_equip_iron_pickaxe__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'iron_pickaxe',
                1,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'iron_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'iron_pickaxe'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'iron_pickaxe')
    assert_field(scenario, result, 'equipped.name', 'iron_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_data',
        target='SelectedItem.id',
        expected='minecraft:iron_pickaxe',
    ),))


def test_equip_iron_pickaxe__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'iron_pickaxe',
                1,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'iron_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'iron_pickaxe'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'iron_pickaxe')
    assert_field(scenario, result, 'equipped.name', 'iron_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_data',
        target='SelectedItem.id',
        expected='minecraft:iron_pickaxe',
    ),))


def test_equip_iron_pickaxe__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
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
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'iron_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'iron_pickaxe'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'requested', 'iron_pickaxe')
    assert_field(scenario, result, 'equipped.name', 'iron_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_data',
        target='SelectedItem.id',
        expected='minecraft:iron_pickaxe',
    ),))


def test_equip_absent__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
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
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'diamond_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'diamond_pickaxe'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_pickaxe',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_equip_absent__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'iron_pickaxe',
                1,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'diamond_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'diamond_pickaxe'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_pickaxe',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_equip_absent__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'iron_pickaxe',
                1,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': 'diamond_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': 'diamond_pickaxe'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_pickaxe',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_equip_ambiguous__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'iron_pickaxe',
                    1,
                ),
                (
                    'stone_pickaxe',
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
    res = call_mcp(scenario, 'minecraft_equip', {'item': '*_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': '*_pickaxe'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_equip_ambiguous__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'iron_pickaxe',
                    1,
                ),
                (
                    'stone_pickaxe',
                    1,
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': '*_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': '*_pickaxe'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_equip_ambiguous__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'iron_pickaxe',
                    1,
                ),
                (
                    'stone_pickaxe',
                    1,
                ),
            ),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip', {'item': '*_pickaxe'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip', {'item': '*_pickaxe'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'ambiguous'
    assert_message(result, 'multiple', 'exact')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)
