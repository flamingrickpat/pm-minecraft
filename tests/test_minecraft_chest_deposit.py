"""Live tests for minecraft_chest_deposit. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, ContainerItem, DuringAction, Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, call_mcp_during, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_chest_deposit_one(live_test):
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
            items=((
                'cobblestone',
                37,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=36,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=1,
        ),
    ))


def test_chest_deposit_partial_stack(live_test):
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
            items=((
                'cobblestone',
                37,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 17, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 17, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 17)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=20,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=17,
        ),
    ))


def test_chest_deposit_all(live_test):
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
            items=((
                'cobblestone',
                37,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': None, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': None, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 37)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=37,
        ),
    ))


def test_chest_deposit_merge_stack(live_test):
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
            items=((
                'cobblestone',
                37,
            ),),
            container_items=(ContainerItem(
                container='chest',
                slot=0,
                item='cobblestone',
                count=10,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 20, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 20, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 20)
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
            expected=30,
        ),
    ))



@pytest.mark.smoke
def test_chest_deposit_no_window(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'stone',
                1,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'stone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'stone', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_chest_window'
    assert_message(result, 'chest', 'open')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='stone',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_deposit_absent(live_test):
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
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_deposit_insufficient(live_test):
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
            items=((
                'stone',
                3,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'stone', 'count': 8, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'stone', 'count': 8, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'insufficient'
    assert_message(result, 'not enough')
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
            expected=3,
        ),
    ))
    # An insufficient deposit is a partial success: all available items moved.



@pytest.mark.contract
def test_chest_deposit_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'stone'}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_chest_deposit_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_chest_deposit', {}, timeout=660)
    assert_protocol_error(res, 'item')



@pytest.mark.contract
def test_chest_deposit_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'item')


def test_chest_deposit_chest_removed_during_approach(live_test):
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
            items=((
                'stone',
                8,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_chest_deposit',
        {'item': 'stone', 'count': 8, 'chest': '$chest'},
        DuringAction(
            wait='chest_open',
            target='chest',
            command='setblock {chest_x} {chest_y} {chest_z} air',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'stone', 'count': 8, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_chest_window'
    assert_message(result, 'chest', 'open')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='chest',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=8,
        ),
    ))


def test_chest_deposit_one__armor(live_test):
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
            items=((
                'cobblestone',
                37,
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
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=36,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=1,
        ),
    ))


def test_chest_deposit_one__damaged(live_test):
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
            items=((
                'cobblestone',
                37,
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=36,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=1,
        ),
    ))


def test_chest_deposit_one__hungry(live_test):
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
            items=((
                'cobblestone',
                37,
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=36,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=1,
        ),
    ))


def test_chest_deposit_one__night(live_test):
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
            items=((
                'cobblestone',
                37,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=36,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=1,
        ),
    ))


def test_chest_deposit_one__rain(live_test):
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
            items=((
                'cobblestone',
                37,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=36,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=1,
        ),
    ))


def test_chest_deposit_one__junk_inventory(live_test):
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
                    'cobblestone',
                    37,
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
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'cobblestone', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'item', 'cobblestone')
    assert_field(scenario, result, 'moved_count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=36,
        ),
        WorldExpectation(
            kind='container',
            target='chest:cobblestone',
            expected=1,
        ),
    ))


def test_chest_deposit_no_window__armor(live_test):
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
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'stone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'stone', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_chest_window'
    assert_message(result, 'chest', 'open')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='stone',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_deposit_no_window__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'stone',
                1,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'stone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'stone', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_chest_window'
    assert_message(result, 'chest', 'open')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='stone',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_deposit_no_window__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'stone',
                1,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'stone', 'count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'stone', 'count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_chest_window'
    assert_message(result, 'chest', 'open')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='stone',
        expected=1,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_deposit_absent__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_deposit_absent__night(live_test):
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
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_deposit_absent__rain(live_test):
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
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'diamond', 'count': 1, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_chest_deposit_insufficient__armor(live_test):
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
            items=((
                'stone',
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
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'stone', 'count': 8, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'stone', 'count': 8, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'insufficient'
    assert_message(result, 'not enough')
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
            expected=3,
        ),
    ))
    # An insufficient deposit is a partial success: all available items moved.


def test_chest_deposit_insufficient__night(live_test):
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
            items=((
                'stone',
                3,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'stone', 'count': 8, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'stone', 'count': 8, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'insufficient'
    assert_message(result, 'not enough')
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
            expected=3,
        ),
    ))
    # An insufficient deposit is a partial success: all available items moved.


def test_chest_deposit_insufficient__rain(live_test):
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
            items=((
                'stone',
                3,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_chest_deposit', {'item': 'stone', 'count': 8, 'chest': '$chest'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'stone', 'count': 8, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'insufficient'
    assert_message(result, 'not enough')
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
            expected=3,
        ),
    ))
    # An insufficient deposit is a partial success: all available items moved.


def test_chest_deposit_chest_removed_during_approach__armor(live_test):
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
            items=((
                'stone',
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
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_chest_deposit',
        {'item': 'stone', 'count': 8, 'chest': '$chest'},
        DuringAction(
            wait='chest_open',
            target='chest',
            command='setblock {chest_x} {chest_y} {chest_z} air',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'stone', 'count': 8, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_chest_window'
    assert_message(result, 'chest', 'open')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='chest',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=8,
        ),
    ))


def test_chest_deposit_chest_removed_during_approach__night(live_test):
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
            items=((
                'stone',
                8,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_chest_deposit',
        {'item': 'stone', 'count': 8, 'chest': '$chest'},
        DuringAction(
            wait='chest_open',
            target='chest',
            command='setblock {chest_x} {chest_y} {chest_z} air',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'stone', 'count': 8, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_chest_window'
    assert_message(result, 'chest', 'open')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='chest',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=8,
        ),
    ))


def test_chest_deposit_chest_removed_during_approach__rain(live_test):
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
            items=((
                'stone',
                8,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_chest_deposit',
        {'item': 'stone', 'count': 8, 'chest': '$chest'},
        DuringAction(
            wait='chest_open',
            target='chest',
            command='setblock {chest_x} {chest_y} {chest_z} air',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_chest_deposit', {'item': 'stone', 'count': 8, 'chest': '$chest'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_chest_window'
    assert_message(result, 'chest', 'open')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='chest',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=8,
        ),
    ))
