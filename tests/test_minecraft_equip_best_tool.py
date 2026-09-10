"""Live tests for minecraft_equip_best_tool. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_equip_best_tool_wood_vs_stone(live_test):
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
                    'wooden_pickaxe',
                    1,
                ),
                (
                    'stone_pickaxe',
                    1,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'target_block', 'stone')
    assert_field(scenario, result, 'equipped.name', 'stone_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_held_item',
        target='player',
        expected='stone_pickaxe',
    ),))


def test_equip_best_tool_stone_vs_iron(live_test):
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
                    'stone_pickaxe',
                    1,
                ),
                (
                    'iron_pickaxe',
                    1,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'target_block', 'stone')
    assert_field(scenario, result, 'equipped.name', 'iron_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_held_item',
        target='player',
        expected='iron_pickaxe',
    ),))


def test_equip_best_tool_iron_vs_diamond(live_test):
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
                    'diamond_pickaxe',
                    1,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'target_block', 'stone')
    assert_field(scenario, result, 'equipped.name', 'diamond_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_held_item',
        target='player',
        expected='diamond_pickaxe',
    ),))


def test_equip_best_tool_leaves_shears(live_test):
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
                block='oak_leaves[persistent=true]',
            ),),
            items=(
                (
                    'iron_axe',
                    1,
                ),
                (
                    'shears',
                    1,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'target_block', 'oak_leaves')
    assert_field(scenario, result, 'equipped.name', 'shears')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_held_item',
        target='player',
        expected='shears',
    ),))


def test_equip_best_tool_bare_hand_dirt(live_test):
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
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'target_block', 'dirt')
    assert_field(scenario, result, 'equipped', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_held_item',
        target='player',
        expected=None,
    ),))



@pytest.mark.smoke
def test_equip_best_tool_air(live_test):
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
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_equip_best_tool_bedrock(live_test):
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
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'unharvestable'
    assert_message(result, 'harvest')
    assert_field(scenario, result, 'target_block', 'bedrock')
    assert_field(scenario, result, 'best_possible_tool', None)
    assert_field(scenario, result, 'equipped', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='bedrock',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_equip_best_tool_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_equip_best_tool_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {}, timeout=660)
    assert_protocol_error(res, 'target')



@pytest.mark.contract
def test_equip_best_tool_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': {'x': {'wrong': True}, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'target')


def test_equip_best_tool_wood_vs_stone__armor(live_test):
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
                    'wooden_pickaxe',
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
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'target_block', 'stone')
    assert_field(scenario, result, 'equipped.name', 'stone_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_held_item',
        target='player',
        expected='stone_pickaxe',
    ),))


def test_equip_best_tool_wood_vs_stone__damaged(live_test):
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
                    'wooden_pickaxe',
                    1,
                ),
                (
                    'stone_pickaxe',
                    1,
                ),
            ),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'target_block', 'stone')
    assert_field(scenario, result, 'equipped.name', 'stone_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_held_item',
        target='player',
        expected='stone_pickaxe',
    ),))


def test_equip_best_tool_wood_vs_stone__hungry(live_test):
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
                    'wooden_pickaxe',
                    1,
                ),
                (
                    'stone_pickaxe',
                    1,
                ),
            ),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'target_block', 'stone')
    assert_field(scenario, result, 'equipped.name', 'stone_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_held_item',
        target='player',
        expected='stone_pickaxe',
    ),))


def test_equip_best_tool_wood_vs_stone__night(live_test):
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
                    'wooden_pickaxe',
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
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'target_block', 'stone')
    assert_field(scenario, result, 'equipped.name', 'stone_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_held_item',
        target='player',
        expected='stone_pickaxe',
    ),))


def test_equip_best_tool_wood_vs_stone__rain(live_test):
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
                    'wooden_pickaxe',
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
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'target_block', 'stone')
    assert_field(scenario, result, 'equipped.name', 'stone_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_held_item',
        target='player',
        expected='stone_pickaxe',
    ),))


def test_equip_best_tool_wood_vs_stone__junk_inventory(live_test):
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
                    'wooden_pickaxe',
                    1,
                ),
                (
                    'stone_pickaxe',
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
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'target_block', 'stone')
    assert_field(scenario, result, 'equipped.name', 'stone_pickaxe')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_held_item',
        target='player',
        expected='stone_pickaxe',
    ),))


def test_equip_best_tool_air__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_equip_best_tool_air__night(live_test):
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
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_equip_best_tool_air__rain(live_test):
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
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_equip_best_tool_bedrock__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'unharvestable'
    assert_message(result, 'harvest')
    assert_field(scenario, result, 'target_block', 'bedrock')
    assert_field(scenario, result, 'best_possible_tool', None)
    assert_field(scenario, result, 'equipped', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='bedrock',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_equip_best_tool_bedrock__night(live_test):
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
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'unharvestable'
    assert_message(result, 'harvest')
    assert_field(scenario, result, 'target_block', 'bedrock')
    assert_field(scenario, result, 'best_possible_tool', None)
    assert_field(scenario, result, 'equipped', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='bedrock',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_equip_best_tool_bedrock__rain(live_test):
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
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_equip_best_tool', {'target': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_equip_best_tool', {'target': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'unharvestable'
    assert_message(result, 'harvest')
    assert_field(scenario, result, 'target_block', 'bedrock')
    assert_field(scenario, result, 'best_possible_tool', None)
    assert_field(scenario, result, 'equipped', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='bedrock',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)
