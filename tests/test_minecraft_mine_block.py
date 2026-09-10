"""Live tests for minecraft_mine_block. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, DuringAction, FillSpec, Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, call_mcp_during, capture_failure_snapshot, capture_truth, parse_result, setup


def test_mine_block_autocollects_ore_across_ledge(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(5, 5, 0),
                block='iron_ore',
            ),),
            fills=(FillSpec(
                start=(0, 4, 0),
                end=(1, 4, 0),
                block='cobblestone',
            ),),
            items=(('iron_pickaxe', 1),),
            player_offset=(0.5, 5.0, 0.5),
        ),
    )
    arguments = {'position': '$target'}
    truth_before = capture_truth(scenario)
    response = call_mcp(scenario, 'minecraft_mine_block', arguments, timeout=660)
    result = parse_result(
        scenario,
        response,
        'minecraft_mine_block',
        arguments,
        truth_before=truth_before,
    )

    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block.block_name', 'iron_ore')
    assert_field(scenario, result, 'tool_used', 'iron_pickaxe')
    assert_field(scenario, result, 'can_harvest', True)
    assert_field(scenario, result, 'pickup.picked_up', True)
    assert_field(scenario, result, 'pickup.drop_hint', None)
    assert_world_state(scenario, (
        WorldExpectation(kind='block', target='target', expected='air'),
        WorldExpectation(kind='inventory', target='raw_iron', expected=1),
    ))


def test_mine_block_stone_iron_pickaxe(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
            items=((
                'iron_pickaxe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block.block_name', 'stone')
    assert_field(scenario, result, 'tool_used', 'iron_pickaxe')
    assert_field(scenario, result, 'can_harvest', True)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
    ))



@pytest.mark.smoke
def test_mine_block_iron_ore_iron_pickaxe(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='iron_ore',
            ),),
            items=((
                'iron_pickaxe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block.block_name', 'iron_ore')
    assert_field(scenario, result, 'tool_used', 'iron_pickaxe')
    assert_field(scenario, result, 'can_harvest', True)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='raw_iron',
            expected=1,
        ),
    ))


def test_mine_block_dirt_shovel(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='dirt',
            ),),
            items=((
                'iron_shovel',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block.block_name', 'dirt')
    assert_field(scenario, result, 'tool_used', 'iron_shovel')
    assert_field(scenario, result, 'can_harvest', True)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='dirt',
            expected=1,
        ),
    ))


def test_mine_block_oak_log_axe(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='oak_log',
            ),),
            items=((
                'iron_axe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block.block_name', 'oak_log')
    assert_field(scenario, result, 'tool_used', 'iron_axe')
    assert_field(scenario, result, 'can_harvest', True)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_log',
            expected=1,
        ),
    ))


def test_mine_block_underwater_stone(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
            items=((
                'iron_pickaxe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block.block_name', 'stone')
    assert_field(scenario, result, 'tool_used', 'iron_pickaxe')
    assert_field(scenario, result, 'can_harvest', True)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
    ))



@pytest.mark.smoke
def test_mine_block_air(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_bedrock(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='bedrock',
            ),),
            items=((
                'diamond_pickaxe',
                1,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'unharvestable'
    assert_message(result, 'harvest')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='bedrock',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_iron_with_bare_hand(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='iron_ore',
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'unharvestable'
    assert_message(result, 'harvest')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_distant(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    35,
                    0,
                    0,
                ),
                block='stone',
            ),),
            items=((
                'iron_pickaxe',
                1,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'target_out_of_range'
    assert_message(result, 'target', 'range')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_breaks_last_pickaxe_use(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
            slot_items=((
                'hotbar.0',
                'iron_pickaxe{Damage:249}',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'tool_used', 'iron_pickaxe')
    assert_field(scenario, result, 'can_harvest', True)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
    ))


def test_mine_block_efficiency_enchantment(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
            slot_items=((
                'hotbar.0',
                'iron_pickaxe{Enchantments:[{id:"minecraft:efficiency",lvl:5s}]}',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'tool_used', 'iron_pickaxe')
    assert_field(scenario, result, 'can_harvest', True)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
    ))


def test_mine_block_full_inventory_drop_not_collected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
            slot_items=(
                (
                    'hotbar.0',
                    'iron_pickaxe',
                    1,
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
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'can_harvest', True)
    assert_field(scenario, result, 'pickup.picked_up', False)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))



@pytest.mark.contract
def test_mine_block_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_mine_block_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_mine_block', {}, timeout=660)
    assert_protocol_error(res, 'position')



@pytest.mark.contract
def test_mine_block_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': {'x': {'wrong': True}, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'position')


def test_mine_block_target_replaced_during_action(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='iron_ore',
            ),),
            items=((
                'iron_pickaxe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_mine_block',
        {'position': '$target'},
        DuringAction(
            wait='block_break_started',
            target='target',
            command='setblock {target_x} {target_y} {target_z} bedrock',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    # The swap races the break, so both outcomes are valid. The invariant
    # under test: the tool never reports success for a target_changed abort,
    # and the operator swap always landed.
    if result.ok is False:
        assert result.reason == 'target_changed'
        assert_message(result, 'target', 'changed')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='bedrock',
        ),
    ))


def test_mine_block_stone_iron_pickaxe__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
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
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block.block_name', 'stone')
    assert_field(scenario, result, 'tool_used', 'iron_pickaxe')
    assert_field(scenario, result, 'can_harvest', True)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
    ))


def test_mine_block_stone_iron_pickaxe__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
            items=((
                'iron_pickaxe',
                1,
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block.block_name', 'stone')
    assert_field(scenario, result, 'tool_used', 'iron_pickaxe')
    assert_field(scenario, result, 'can_harvest', True)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
    ))


def test_mine_block_stone_iron_pickaxe__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
            items=((
                'iron_pickaxe',
                1,
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block.block_name', 'stone')
    assert_field(scenario, result, 'tool_used', 'iron_pickaxe')
    assert_field(scenario, result, 'can_harvest', True)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
    ))


def test_mine_block_stone_iron_pickaxe__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
            items=((
                'iron_pickaxe',
                1,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block.block_name', 'stone')
    assert_field(scenario, result, 'tool_used', 'iron_pickaxe')
    assert_field(scenario, result, 'can_harvest', True)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
    ))


def test_mine_block_stone_iron_pickaxe__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
            items=((
                'iron_pickaxe',
                1,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block.block_name', 'stone')
    assert_field(scenario, result, 'tool_used', 'iron_pickaxe')
    assert_field(scenario, result, 'can_harvest', True)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
    ))


def test_mine_block_stone_iron_pickaxe__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='stone',
            ),),
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
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'block.block_name', 'stone')
    assert_field(scenario, result, 'tool_used', 'iron_pickaxe')
    assert_field(scenario, result, 'can_harvest', True)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=1,
        ),
    ))


def test_mine_block_air__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='air',
                name='air',
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
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_air__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_air__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_bedrock__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='bedrock',
            ),),
            items=((
                'diamond_pickaxe',
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
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'unharvestable'
    assert_message(result, 'harvest')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='bedrock',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_bedrock__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='bedrock',
            ),),
            items=((
                'diamond_pickaxe',
                1,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'unharvestable'
    assert_message(result, 'harvest')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='bedrock',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_bedrock__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='bedrock',
            ),),
            items=((
                'diamond_pickaxe',
                1,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'unharvestable'
    assert_message(result, 'harvest')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='bedrock',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_iron_with_bare_hand__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='iron_ore',
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
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'unharvestable'
    assert_message(result, 'harvest')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_iron_with_bare_hand__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='iron_ore',
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'unharvestable'
    assert_message(result, 'harvest')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_iron_with_bare_hand__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='iron_ore',
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'unharvestable'
    assert_message(result, 'harvest')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='iron_ore',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_distant__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    35,
                    0,
                    0,
                ),
                block='stone',
            ),),
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
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'target_out_of_range'
    assert_message(result, 'target', 'range')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_distant__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    35,
                    0,
                    0,
                ),
                block='stone',
            ),),
            items=((
                'iron_pickaxe',
                1,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'target_out_of_range'
    assert_message(result, 'target', 'range')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_distant__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    35,
                    0,
                    0,
                ),
                block='stone',
            ),),
            items=((
                'iron_pickaxe',
                1,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_mine_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'target_out_of_range'
    assert_message(result, 'target', 'range')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_mine_block_target_replaced_during_action__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='iron_ore',
            ),),
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
    res = call_mcp_during(
        scenario,
        'minecraft_mine_block',
        {'position': '$target'},
        DuringAction(
            wait='block_break_started',
            target='target',
            command='setblock {target_x} {target_y} {target_z} bedrock',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    # The swap races the break, so both outcomes are valid. The invariant
    # under test: the tool never reports success for a target_changed abort,
    # and the operator swap always landed.
    if result.ok is False:
        assert result.reason == 'target_changed'
        assert_message(result, 'target', 'changed')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='bedrock',
        ),
    ))


def test_mine_block_target_replaced_during_action__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='iron_ore',
            ),),
            items=((
                'iron_pickaxe',
                1,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_mine_block',
        {'position': '$target'},
        DuringAction(
            wait='block_break_started',
            target='target',
            command='setblock {target_x} {target_y} {target_z} bedrock',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    # The swap races the break, so both outcomes are valid. The invariant
    # under test: the tool never reports success for a target_changed abort,
    # and the operator swap always landed.
    if result.ok is False:
        assert result.reason == 'target_changed'
        assert_message(result, 'target', 'changed')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='bedrock',
        ),
    ))


def test_mine_block_target_replaced_during_action__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='iron_ore',
            ),),
            items=((
                'iron_pickaxe',
                1,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_mine_block',
        {'position': '$target'},
        DuringAction(
            wait='block_break_started',
            target='target',
            command='setblock {target_x} {target_y} {target_z} bedrock',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_mine_block', {'position': '$target'}, truth_before=truth_before)
    # The swap races the break, so both outcomes are valid. The invariant
    # under test: the tool never reports success for a target_changed abort,
    # and the operator swap always landed.
    if result.ok is False:
        assert result.reason == 'target_changed'
        assert_message(result, 'target', 'changed')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='bedrock',
        ),
    ))
