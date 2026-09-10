"""Live tests for minecraft_build. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, Layout, Length, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup


def test_build_fill_skips_blocks_occupied_by_player(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(key='player_feet', offset=(0, 0, 0), block='air'),
                BlockSpec(key='player_head', offset=(0, 1, 0), block='air'),
            ),
            items=(('cobblestone', 2),),
        ),
    )
    arguments = {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$player_feet',
        'end': '$player_head',
        'include_image': False,
    }
    truth_before = capture_truth(scenario)
    response = call_mcp(scenario, 'minecraft_build', arguments, timeout=660)
    result = parse_result(
        scenario,
        response,
        'minecraft_build',
        arguments,
        truth_before=truth_before,
    )

    assert result.placed_count == 0
    assert result.placed == []
    assert_world_state(scenario, (
        WorldExpectation(kind='block', target='player_feet', expected='air'),
        WorldExpectation(kind='block', target='player_head', expected='air'),
        WorldExpectation(kind='inventory', target='cobblestone', expected=2),
    ))


def test_build_fill(live_test):
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
                'cobblestone',
                8,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'fill')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 8)
    assert_field(scenario, result, 'placed_count', 8)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=8,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_wall(live_test):
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
                'cobblestone',
                9,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'wall',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'wall',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'wall')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 9)
    assert_field(scenario, result, 'placed_count', 9)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=9,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_floor(live_test):
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
                'cobblestone',
                9,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'floor',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'floor',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'floor')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 9)
    assert_field(scenario, result, 'placed_count', 9)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=9,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_ceiling(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        3,
                        2,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        5,
                        2,
                        2,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'cobblestone',
                9,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'ceiling',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'ceiling',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'ceiling')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 9)
    assert_field(scenario, result, 'placed_count', 9)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=9,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_column(live_test):
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
                'cobblestone',
                5,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'column',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'column',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'column')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 5)
    assert_field(scenario, result, 'placed_count', 5)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=5,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_staircase(live_test):
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
                        7,
                        4,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'cobblestone',
                5,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'staircase',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'staircase',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'staircase')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 5)
    assert_field(scenario, result, 'placed_count', 5)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=5,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))



@pytest.mark.smoke
def test_build_bridge(live_test):
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
                        8,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'cobblestone',
                6,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'bridge',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'bridge',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'bridge')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 6)
    assert_field(scenario, result, 'placed_count', 6)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=6,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_frame(live_test):
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
                        6,
                        3,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'cobblestone',
                12,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'frame',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'frame',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'frame')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 12)
    assert_field(scenario, result, 'placed_count', 12)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=12,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_shell(live_test):
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
                        2,
                        2,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'cobblestone',
                26,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'shell',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'shell',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'shell')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 26)
    assert_field(scenario, result, 'placed_count', 26)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=26,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))



@pytest.mark.smoke
def test_build_missing_material(live_test):
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
                'cobblestone',
                4,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {'shape': 'floor', 'material': 'cobblestone', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {'shape': 'floor', 'material': 'cobblestone', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'partial'
    assert_message(result, 'partial')
    assert_field(scenario, result, 'planned_cells', 9)
    assert_field(scenario, result, 'placed_count', 4)
    assert_field(scenario, result, 'missing_material_cells', 5)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=4,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_all_out_of_range(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        34,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        34,
                        2,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'stone',
                3,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {'shape': 'column', 'material': 'stone', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {'shape': 'column', 'material': 'stone', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='stone',
        expected=3,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_build_unknown_material(live_test):
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
    res = call_mcp(scenario, 'minecraft_build', {'shape': 'column', 'material': 'cobblestne', 'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {'shape': 'column', 'material': 'cobblestne', 'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_build_distance_boundary(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    32,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            items=((
                'stone',
                1,
            ),),
            player_offset=(
                0.0,
                0.0,
                0.0,
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'column',
        'material': 'stone',
        'start': '$target',
        'end': '$target',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'column',
        'material': 'stone',
        'start': '$target',
        'end': '$target',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'planned_cells', 1)
    assert_field(scenario, result, 'placed_count', 1)
    assert_field(scenario, result, 'out_of_range', [])
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='stone',
        ),
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=0,
        ),
    ))


def test_build_outside_distance_boundary(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    33,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            items=((
                'stone',
                1,
            ),),
            player_offset=(
                0.0,
                0.0,
                0.0,
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'column',
        'material': 'stone',
        'start': '$target',
        'end': '$target',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'column',
        'material': 'stone',
        'start': '$target',
        'end': '$target',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'planned_cells', 1)
    assert_field(scenario, result, 'placed_count', 0)
    assert_field(scenario, result, 'out_of_range', Length(
        value=1,
    ))
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=1,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.slow
def test_build_cell_limit_boundary(live_test):
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
                        10,
                        7,
                        7,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'stone',
                512,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'fill',
        'material': 'stone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'fill',
        'material': 'stone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'planned_cells', 512)
    assert_field(scenario, result, 'placed_count', 512)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:stone',
            expected=512,
        ),
        WorldExpectation(
            kind='block',
            target='start',
            expected='stone',
        ),
        WorldExpectation(
            kind='block',
            target='end',
            expected='stone',
        ),
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=0,
        ),
    ))


def test_build_cell_limit_exceeded(live_test):
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
                        11,
                        2,
                        18,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'stone',
                513,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'fill',
        'material': 'stone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'fill',
        'material': 'stone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'cell_limit'
    assert_message(result, '512', 'cells')
    assert_field(scenario, result, 'planned_cells', 513)
    assert_field(scenario, result, 'placed_count', 0)
    assert_field(scenario, result, 'placed', [])
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='start',
            expected='air',
        ),
        WorldExpectation(
            kind='block',
            target='end',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=513,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_build_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_build', {'shape': 'column', 'material': 'stone', 'start': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_build_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_build', {}, timeout=660)
    assert_protocol_error(res, 'shape')



@pytest.mark.contract
def test_build_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_build', {'shape': {'wrong': True}, 'material': 'stone', 'start': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'shape')



@pytest.mark.contract
def test_build_invalid_literal(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_build', {'shape': 'not_a_valid_choice', 'material': 'stone', 'start': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'shape', 'not_a_valid_choice')


def test_build_fill__armor(live_test):
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
                'cobblestone',
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
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'fill')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 8)
    assert_field(scenario, result, 'placed_count', 8)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=8,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_fill__damaged(live_test):
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
                'cobblestone',
                8,
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'fill')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 8)
    assert_field(scenario, result, 'placed_count', 8)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=8,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_fill__hungry(live_test):
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
                'cobblestone',
                8,
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'fill')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 8)
    assert_field(scenario, result, 'placed_count', 8)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=8,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_fill__night(live_test):
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
                'cobblestone',
                8,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'fill')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 8)
    assert_field(scenario, result, 'placed_count', 8)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=8,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_fill__rain(live_test):
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
                'cobblestone',
                8,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'fill')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 8)
    assert_field(scenario, result, 'placed_count', 8)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=8,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_fill__junk_inventory(live_test):
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
                    'cobblestone',
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
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'fill',
        'material': 'cobblestone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'shape', 'fill')
    assert_field(scenario, result, 'material_resolved', 'cobblestone')
    assert_field(scenario, result, 'planned_cells', 8)
    assert_field(scenario, result, 'placed_count', 8)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=8,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_missing_material__armor(live_test):
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
                'cobblestone',
                4,
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
    res = call_mcp(scenario, 'minecraft_build', {'shape': 'floor', 'material': 'cobblestone', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {'shape': 'floor', 'material': 'cobblestone', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'partial'
    assert_message(result, 'partial')
    assert_field(scenario, result, 'planned_cells', 9)
    assert_field(scenario, result, 'placed_count', 4)
    assert_field(scenario, result, 'missing_material_cells', 5)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=4,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_missing_material__night(live_test):
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
                'cobblestone',
                4,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {'shape': 'floor', 'material': 'cobblestone', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {'shape': 'floor', 'material': 'cobblestone', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'partial'
    assert_message(result, 'partial')
    assert_field(scenario, result, 'planned_cells', 9)
    assert_field(scenario, result, 'placed_count', 4)
    assert_field(scenario, result, 'missing_material_cells', 5)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=4,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_missing_material__rain(live_test):
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
                'cobblestone',
                4,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {'shape': 'floor', 'material': 'cobblestone', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {'shape': 'floor', 'material': 'cobblestone', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'partial'
    assert_message(result, 'partial')
    assert_field(scenario, result, 'planned_cells', 9)
    assert_field(scenario, result, 'placed_count', 4)
    assert_field(scenario, result, 'missing_material_cells', 5)
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='box_block_count',
            target='start:end:cobblestone',
            expected=4,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
    ))


def test_build_all_out_of_range__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        34,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        34,
                        2,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
            ),
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
    res = call_mcp(scenario, 'minecraft_build', {'shape': 'column', 'material': 'stone', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {'shape': 'column', 'material': 'stone', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='stone',
        expected=3,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_build_all_out_of_range__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        34,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        34,
                        2,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'stone',
                3,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {'shape': 'column', 'material': 'stone', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {'shape': 'column', 'material': 'stone', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='stone',
        expected=3,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_build_all_out_of_range__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='start',
                    offset=(
                        34,
                        0,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
                BlockSpec(
                    key='end',
                    offset=(
                        34,
                        2,
                        0,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'stone',
                3,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {'shape': 'column', 'material': 'stone', 'start': '$start', 'end': '$end'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {'shape': 'column', 'material': 'stone', 'start': '$start', 'end': '$end'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='stone',
        expected=3,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_build_unknown_material__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_build', {'shape': 'column', 'material': 'cobblestne', 'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {'shape': 'column', 'material': 'cobblestne', 'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_build_unknown_material__night(live_test):
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
    res = call_mcp(scenario, 'minecraft_build', {'shape': 'column', 'material': 'cobblestne', 'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {'shape': 'column', 'material': 'cobblestne', 'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_build_unknown_material__rain(live_test):
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
    res = call_mcp(scenario, 'minecraft_build', {'shape': 'column', 'material': 'cobblestne', 'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {'shape': 'column', 'material': 'cobblestne', 'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_build_outside_distance_boundary__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    33,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
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
            player_offset=(
                0.0,
                0.0,
                0.0,
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'column',
        'material': 'stone',
        'start': '$target',
        'end': '$target',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'column',
        'material': 'stone',
        'start': '$target',
        'end': '$target',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'planned_cells', 1)
    assert_field(scenario, result, 'placed_count', 0)
    assert_field(scenario, result, 'out_of_range', Length(
        value=1,
    ))
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=1,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_build_outside_distance_boundary__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    33,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            items=((
                'stone',
                1,
            ),),
            player_offset=(
                0.0,
                0.0,
                0.0,
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'column',
        'material': 'stone',
        'start': '$target',
        'end': '$target',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'column',
        'material': 'stone',
        'start': '$target',
        'end': '$target',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'planned_cells', 1)
    assert_field(scenario, result, 'placed_count', 0)
    assert_field(scenario, result, 'out_of_range', Length(
        value=1,
    ))
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=1,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_build_outside_distance_boundary__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    33,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            items=((
                'stone',
                1,
            ),),
            player_offset=(
                0.0,
                0.0,
                0.0,
            ),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'column',
        'material': 'stone',
        'start': '$target',
        'end': '$target',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'column',
        'material': 'stone',
        'start': '$target',
        'end': '$target',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'planned_cells', 1)
    assert_field(scenario, result, 'placed_count', 0)
    assert_field(scenario, result, 'out_of_range', Length(
        value=1,
    ))
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='target',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=1,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_build_cell_limit_exceeded__armor(live_test):
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
                        11,
                        2,
                        18,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'stone',
                513,
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
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'fill',
        'material': 'stone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'fill',
        'material': 'stone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'cell_limit'
    assert_message(result, '512', 'cells')
    assert_field(scenario, result, 'planned_cells', 513)
    assert_field(scenario, result, 'placed_count', 0)
    assert_field(scenario, result, 'placed', [])
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='start',
            expected='air',
        ),
        WorldExpectation(
            kind='block',
            target='end',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=513,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_build_cell_limit_exceeded__night(live_test):
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
                        11,
                        2,
                        18,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'stone',
                513,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'fill',
        'material': 'stone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'fill',
        'material': 'stone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'cell_limit'
    assert_message(result, '512', 'cells')
    assert_field(scenario, result, 'planned_cells', 513)
    assert_field(scenario, result, 'placed_count', 0)
    assert_field(scenario, result, 'placed', [])
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='start',
            expected='air',
        ),
        WorldExpectation(
            kind='block',
            target='end',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=513,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_build_cell_limit_exceeded__rain(live_test):
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
                        11,
                        2,
                        18,
                    ),
                    block='air',
                    name='air',
                ),
            ),
            items=((
                'stone',
                513,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_build', {
        'shape': 'fill',
        'material': 'stone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_build', {
        'shape': 'fill',
        'material': 'stone',
        'start': '$start',
        'end': '$end',
        'include_image': False,
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'cell_limit'
    assert_message(result, '512', 'cells')
    assert_field(scenario, result, 'planned_cells', 513)
    assert_field(scenario, result, 'placed_count', 0)
    assert_field(scenario, result, 'placed', [])
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='start',
            expected='air',
        ),
        WorldExpectation(
            kind='block',
            target='end',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='stone',
            expected=513,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)
