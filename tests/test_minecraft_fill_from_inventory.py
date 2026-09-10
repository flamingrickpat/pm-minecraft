"""Live tests for minecraft_fill_from_inventory. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, Layout, WorldExpectation, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_fill_from_inventory_fill(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        4,
                        1,
                        1,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'oak_planks',
                8,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'fill', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fill_from_inventory', {'shape': 'fill', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'fill')
    assert_field(scenario, result, 'material_resolved', 'oak_planks')
    assert_field(scenario, result, 'placed_count', 8)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:oak_planks',
            expected=8,
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_planks',
            expected=0,
        ),
    ))


def test_fill_from_inventory_wall(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        3,
                        2,
                        2,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'oak_planks',
                9,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'wall', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fill_from_inventory', {'shape': 'wall', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'wall')
    assert_field(scenario, result, 'material_resolved', 'oak_planks')
    assert_field(scenario, result, 'placed_count', 9)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:oak_planks',
            expected=9,
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_planks',
            expected=0,
        ),
    ))


def test_fill_from_inventory_floor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        5,
                        0,
                        2,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'oak_planks',
                9,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'floor', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fill_from_inventory', {'shape': 'floor', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'floor')
    assert_field(scenario, result, 'material_resolved', 'oak_planks')
    assert_field(scenario, result, 'placed_count', 9)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:oak_planks',
            expected=9,
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_planks',
            expected=0,
        ),
    ))


def test_fill_from_inventory_column(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        3,
                        4,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'oak_planks',
                5,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'column', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fill_from_inventory', {'shape': 'column', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'column')
    assert_field(scenario, result, 'material_resolved', 'oak_planks')
    assert_field(scenario, result, 'placed_count', 5)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:oak_planks',
            expected=5,
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_planks',
            expected=0,
        ),
    ))



@pytest.mark.smoke
def test_fill_from_inventory_insufficient_blocks(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        5,
                        0,
                        2,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'oak_planks',
                2,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'floor', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fill_from_inventory', {'shape': 'floor', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'partial'
    assert_message(result, 'partial')
    assert_field(scenario, result, 'placed_count', 2)
    assert_field(scenario, result, 'missing_material_cells', 7)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:oak_planks',
            expected=2,
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_planks',
            expected=0,
        ),
    ))



@pytest.mark.contract
def test_fill_from_inventory_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'column', 'start': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_fill_from_inventory_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {}, timeout=660)
    assert_protocol_error(res, 'shape')



@pytest.mark.contract
def test_fill_from_inventory_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': {'wrong': True}, 'start': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'shape')



@pytest.mark.contract
def test_fill_from_inventory_invalid_literal(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'not_a_valid_choice', 'start': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'shape', 'not_a_valid_choice')


def test_fill_from_inventory_fill__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        4,
                        1,
                        1,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'oak_planks',
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
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'fill', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fill_from_inventory', {'shape': 'fill', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'fill')
    assert_field(scenario, result, 'material_resolved', 'oak_planks')
    assert_field(scenario, result, 'placed_count', 8)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:oak_planks',
            expected=8,
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_planks',
            expected=0,
        ),
    ))


def test_fill_from_inventory_fill__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        4,
                        1,
                        1,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'oak_planks',
                8,
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'fill', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fill_from_inventory', {'shape': 'fill', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'fill')
    assert_field(scenario, result, 'material_resolved', 'oak_planks')
    assert_field(scenario, result, 'placed_count', 8)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:oak_planks',
            expected=8,
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_planks',
            expected=0,
        ),
    ))


def test_fill_from_inventory_fill__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        4,
                        1,
                        1,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'oak_planks',
                8,
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'fill', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fill_from_inventory', {'shape': 'fill', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'fill')
    assert_field(scenario, result, 'material_resolved', 'oak_planks')
    assert_field(scenario, result, 'placed_count', 8)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:oak_planks',
            expected=8,
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_planks',
            expected=0,
        ),
    ))


def test_fill_from_inventory_fill__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        4,
                        1,
                        1,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'oak_planks',
                8,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'fill', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fill_from_inventory', {'shape': 'fill', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'fill')
    assert_field(scenario, result, 'material_resolved', 'oak_planks')
    assert_field(scenario, result, 'placed_count', 8)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:oak_planks',
            expected=8,
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_planks',
            expected=0,
        ),
    ))


def test_fill_from_inventory_fill__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        4,
                        1,
                        1,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'oak_planks',
                8,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'fill', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fill_from_inventory', {'shape': 'fill', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'fill')
    assert_field(scenario, result, 'material_resolved', 'oak_planks')
    assert_field(scenario, result, 'placed_count', 8)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:oak_planks',
            expected=8,
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_planks',
            expected=0,
        ),
    ))


def test_fill_from_inventory_fill__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        4,
                        1,
                        1,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=(
                (
                    'oak_planks',
                    8,
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
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'fill', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fill_from_inventory', {'shape': 'fill', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'fill')
    assert_field(scenario, result, 'material_resolved', 'oak_planks')
    assert_field(scenario, result, 'placed_count', 8)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:oak_planks',
            expected=8,
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_planks',
            expected=0,
        ),
    ))


def test_fill_from_inventory_insufficient_blocks__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        5,
                        0,
                        2,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'oak_planks',
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
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'floor', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fill_from_inventory', {'shape': 'floor', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'partial'
    assert_message(result, 'partial')
    assert_field(scenario, result, 'placed_count', 2)
    assert_field(scenario, result, 'missing_material_cells', 7)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:oak_planks',
            expected=2,
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_planks',
            expected=0,
        ),
    ))


def test_fill_from_inventory_insufficient_blocks__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        5,
                        0,
                        2,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'oak_planks',
                2,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'floor', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fill_from_inventory', {'shape': 'floor', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'partial'
    assert_message(result, 'partial')
    assert_field(scenario, result, 'placed_count', 2)
    assert_field(scenario, result, 'missing_material_cells', 7)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:oak_planks',
            expected=2,
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_planks',
            expected=0,
        ),
    ))


def test_fill_from_inventory_insufficient_blocks__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        5,
                        0,
                        2,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'oak_planks',
                2,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fill_from_inventory', {'shape': 'floor', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fill_from_inventory', {'shape': 'floor', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'partial'
    assert_message(result, 'partial')
    assert_field(scenario, result, 'placed_count', 2)
    assert_field(scenario, result, 'missing_material_cells', 7)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:oak_planks',
            expected=2,
        ),
        WorldExpectation(
            kind='inventory',
            target='oak_planks',
            expected=0,
        ),
    ))
