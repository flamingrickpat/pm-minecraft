"""Live tests for minecraft_use_block. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_setup_success, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_use_block_open_door(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='door_upper',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_door[half=upper,facing=west,open=false]',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_door[half=lower,facing=west,open=false]',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'door_opened')
    assert_field(scenario, result, 'block.block_name', 'oak_door')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block_properties',
        target='target',
        expected={'open': True},
    ),))


def test_use_block_open_gate(live_test):
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
                block='oak_fence_gate[facing=west,open=false]',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'gate_opened')
    assert_field(scenario, result, 'block.block_name', 'oak_fence_gate')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block_properties',
        target='target',
        expected={'open': True},
    ),))


def test_use_block_open_trapdoor(live_test):
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
                block='oak_trapdoor[facing=west,half=bottom,open=false]',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'trapdoor_opened')
    assert_field(scenario, result, 'block.block_name', 'oak_trapdoor')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block_properties',
        target='target',
        expected={'open': True},
    ),))


def test_use_block_toggle_lever(live_test):
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
                block='lever[face=floor,facing=north,powered=false]',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'lever_toggled')
    assert_field(scenario, result, 'block.block_name', 'lever')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block_properties',
        target='target',
        expected={'powered': True},
    ),))


def test_use_block_press_button(live_test):
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
                block='oak_button[face=wall,facing=west,powered=false]',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'button_pressed')
    assert_field(scenario, result, 'block.block_name', 'oak_button')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block_properties',
        target='target',
        expected={'powered': True},
    ),))


def test_use_block_open_chest(live_test):
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
                block='chest[facing=west]',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'container_opened')
    assert_field(scenario, result, 'block.block_name', 'chest')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='chest',
    ),))


def test_use_block_open_furnace(live_test):
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
                block='furnace[facing=west]',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'furnace_opened')
    assert_field(scenario, result, 'block.block_name', 'furnace')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='furnace',
    ),))


def test_use_block_open_table(live_test):
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
                block='crafting_table',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'crafting_table_opened')
    assert_field(scenario, result, 'block.block_name', 'crafting_table')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='crafting_table',
    ),))



@pytest.mark.smoke
def test_use_block_air(live_test):
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
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_block_stone(live_test):
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
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_interactable'
    assert_message(result, 'not', 'interactable')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_block_out_of_range(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    20,
                    0,
                    0,
                ),
                block='chest',
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='chest',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_block_second_toggle_closes_door(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_door[half=lower,facing=west,open=false]',
                ),
                BlockSpec(
                    key='door_upper',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_door[half=upper,facing=west,open=false]',
                ),
            ),
        ),
    )
    setup_res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_use_block')
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'door_closed')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block_properties',
        target='target',
        expected={'open': False},
    ),))



@pytest.mark.contract
def test_use_block_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_use_block', {'position': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_use_block_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_use_block', {}, timeout=660)
    assert_protocol_error(res, 'position')



@pytest.mark.contract
def test_use_block_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_use_block', {'position': {'x': {'wrong': True}, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'position')


def test_use_block_open_door__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='door_upper',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_door[half=upper,facing=west,open=false]',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_door[half=lower,facing=west,open=false]',
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
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'door_opened')
    assert_field(scenario, result, 'block.block_name', 'oak_door')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block_properties',
        target='target',
        expected={'open': True},
    ),))


def test_use_block_open_door__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='door_upper',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_door[half=upper,facing=west,open=false]',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_door[half=lower,facing=west,open=false]',
                ),
            ),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'door_opened')
    assert_field(scenario, result, 'block.block_name', 'oak_door')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block_properties',
        target='target',
        expected={'open': True},
    ),))


def test_use_block_open_door__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='door_upper',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_door[half=upper,facing=west,open=false]',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_door[half=lower,facing=west,open=false]',
                ),
            ),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'door_opened')
    assert_field(scenario, result, 'block.block_name', 'oak_door')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block_properties',
        target='target',
        expected={'open': True},
    ),))


def test_use_block_open_door__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='door_upper',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_door[half=upper,facing=west,open=false]',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_door[half=lower,facing=west,open=false]',
                ),
            ),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'door_opened')
    assert_field(scenario, result, 'block.block_name', 'oak_door')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block_properties',
        target='target',
        expected={'open': True},
    ),))


def test_use_block_open_door__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='door_upper',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_door[half=upper,facing=west,open=false]',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_door[half=lower,facing=west,open=false]',
                ),
            ),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'door_opened')
    assert_field(scenario, result, 'block.block_name', 'oak_door')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block_properties',
        target='target',
        expected={'open': True},
    ),))


def test_use_block_open_door__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='door_upper',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='oak_door[half=upper,facing=west,open=false]',
                ),
                BlockSpec(
                    key='target',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='oak_door[half=lower,facing=west,open=false]',
                ),
            ),
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
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'action', 'door_opened')
    assert_field(scenario, result, 'block.block_name', 'oak_door')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block_properties',
        target='target',
        expected={'open': True},
    ),))


def test_use_block_air__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_block_air__night(live_test):
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
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_block_air__rain(live_test):
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
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_block_stone__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_interactable'
    assert_message(result, 'not', 'interactable')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_block_stone__night(live_test):
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
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_interactable'
    assert_message(result, 'not', 'interactable')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_block_stone__rain(live_test):
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
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_interactable'
    assert_message(result, 'not', 'interactable')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='stone',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_block_out_of_range__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    20,
                    0,
                    0,
                ),
                block='chest',
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
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='chest',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_block_out_of_range__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    20,
                    0,
                    0,
                ),
                block='chest',
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='chest',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_use_block_out_of_range__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    20,
                    0,
                    0,
                ),
                block='chest',
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_use_block', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_use_block', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='chest',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)
