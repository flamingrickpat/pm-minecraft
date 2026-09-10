"""Live tests for minecraft_chest_withdraw. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, ContainerItem, Layout, WorldExpectation, assert_failure_unchanged, assert_failure_unchanged_allow_inventory_change, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_chest_withdraw_one(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
            ),),
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='cobblestone',
                count=37,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=36,
        ),
    ))


def test_chest_withdraw_partial(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
            ),),
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='cobblestone',
                count=37,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 17, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 17, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 17)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=17,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=20,
        ),
    ))


def test_chest_withdraw_all(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
            ),),
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='cobblestone',
                count=37,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': None, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': None, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 37)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=37,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=0,
        ),
    ))



@pytest.mark.smoke
def test_chest_withdraw_no_window(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_chest_window'
    assert_message(result, 'chest', 'open')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_withdraw_absent(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_withdraw_insufficient(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
            ),),
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='stone',
                count=3,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 8, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 8, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'insufficient'
    assert_message(result, 'not enough')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=3,
        ),
        WorldExpectation(
            kind='container',
            target='chest:stone',
            expected=0,
        ),
    ))
    assert_failure_unchanged_allow_inventory_change(scenario, failure_snapshot)


def test_chest_withdraw_full_inventory_no_space(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
            ),),
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
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='stone',
                count=1,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'inventory_full'
    assert_message(result, 'inventory', 'full')
    assert_field(scenario, result, 'moved_count', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=0,
        ),
        WorldExpectation(
            kind='container',
            target='chest:stone',
            expected=1,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_chest_withdraw_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'stone'}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_chest_withdraw_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {}, timeout=660)
    assert_protocol_error(res, 'item')



@pytest.mark.contract
def test_chest_withdraw_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'item')


def test_chest_withdraw_one__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
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
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='cobblestone',
                count=37,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=36,
        ),
    ))


def test_chest_withdraw_one__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
            ),),
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='cobblestone',
                count=37,
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=36,
        ),
    ))


def test_chest_withdraw_one__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
            ),),
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='cobblestone',
                count=37,
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=36,
        ),
    ))


def test_chest_withdraw_one__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
            ),),
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='cobblestone',
                count=37,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=36,
        ),
    ))


def test_chest_withdraw_one__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
            ),),
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='cobblestone',
                count=37,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=36,
        ),
    ))


def test_chest_withdraw_one__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
            ),),
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
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='cobblestone',
                count=37,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=36,
        ),
    ))


def test_chest_withdraw_no_window__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_chest_window'
    assert_message(result, 'chest', 'open')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_withdraw_no_window__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_chest_window'
    assert_message(result, 'chest', 'open')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_withdraw_no_window__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_chest_window'
    assert_message(result, 'chest', 'open')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_withdraw_absent__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
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
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_withdraw_absent__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_withdraw_absent__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_withdraw_insufficient__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
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
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='stone',
                count=3,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 8, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 8, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'insufficient'
    assert_message(result, 'not enough')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=3,
        ),
        WorldExpectation(
            kind='container',
            target='chest:stone',
            expected=0,
        ),
    ))
    assert_failure_unchanged_allow_inventory_change(scenario, failure_snapshot)


def test_chest_withdraw_insufficient__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
            ),),
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='stone',
                count=3,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 8, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 8, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'insufficient'
    assert_message(result, 'not enough')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=3,
        ),
        WorldExpectation(
            kind='container',
            target='chest:stone',
            expected=0,
        ),
    ))
    assert_failure_unchanged_allow_inventory_change(scenario, failure_snapshot)


def test_chest_withdraw_insufficient__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
                properties={'facing': 'west'},
            ),),
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='stone',
                count=3,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 8, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 8, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'insufficient'
    assert_message(result, 'not enough')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=3,
        ),
        WorldExpectation(
            kind='container',
            target='chest:stone',
            expected=0,
        ),
    ))
    assert_failure_unchanged_allow_inventory_change(scenario, failure_snapshot)


def test_chest_withdraw_full_inventory_no_space__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
            ),),
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
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='stone',
                count=1,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'inventory_full'
    assert_message(result, 'inventory', 'full')
    assert_field(scenario, result, 'moved_count', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=0,
        ),
        WorldExpectation(
            kind='container',
            target='chest:stone',
            expected=1,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_withdraw_full_inventory_no_space__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
            ),),
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
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='stone',
                count=1,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'inventory_full'
    assert_message(result, 'inventory', 'full')
    assert_field(scenario, result, 'moved_count', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=0,
        ),
        WorldExpectation(
            kind='container',
            target='chest:stone',
            expected=1,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_withdraw_full_inventory_no_space__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='chest',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='chest[facing=west]',
            ),),
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
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='stone',
                count=1,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_withdraw', {'item': 'stone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'inventory_full'
    assert_message(result, 'inventory', 'full')
    assert_field(scenario, result, 'moved_count', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=0,
        ),
        WorldExpectation(
            kind='container',
            target='chest:stone',
            expected=1,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)
