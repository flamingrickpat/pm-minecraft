"""Live tests for minecraft_analyze_area. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import AtLeast, BlockSpec, Excludes, Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_analyze_area_one_air_cell(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {
        'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
        'end': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {
        'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
        'end': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'total_cells', 1)
    assert_field(scenario, result, 'air_cells', 1)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_response_image(res, result, False)


def test_analyze_area_mixed_visible_box(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='stone',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='glass',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='glass',
                ),
                BlockSpec(
                    key='water',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='water',
                ),
                BlockSpec(
                    key='hidden_ore',
                    offset=(
                        4,
                        -2,
                        0,
                    ),
                    block='diamond_ore',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$stone', 'end': '$water'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$stone', 'end': '$water'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'total_cells', 2)
    assert_response_image(res, result, False)


def test_analyze_area_reversed_corners(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='stone',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='glass',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='glass',
                ),
                BlockSpec(
                    key='water',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='water',
                ),
                BlockSpec(
                    key='hidden_ore',
                    offset=(
                        4,
                        -2,
                        0,
                    ),
                    block='diamond_ore',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$water', 'end': '$stone'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$water', 'end': '$stone'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'total_cells', 2)
    assert_response_image(res, result, False)


def test_analyze_area_hidden_ore_excluded(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='stone',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='stone',
                ),
                BlockSpec(
                    key='glass',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='glass',
                ),
                BlockSpec(
                    key='water',
                    offset=(
                        3,
                        1,
                        0,
                    ),
                    block='water',
                ),
                BlockSpec(
                    key='hidden_ore',
                    offset=(
                        4,
                        -2,
                        0,
                    ),
                    block='diamond_ore',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'}, 'end': '$hidden_ore'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'}, 'end': '$hidden_ore'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'blocks', Excludes(
        value='diamond_ore',
        key='block_name',
    ))
    assert_field(scenario, result, 'unseen_cells', AtLeast(
        value=1,
    ))
    assert_response_image(res, result, False)


def test_analyze_area_east_limit(live_test):
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
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'bounds.min', '$target')
    assert_field(scenario, result, 'bounds.max', '$target')
    assert_field(scenario, result, 'total_cells', 1)
    assert_response_image(res, result, False)



@pytest.mark.smoke
def test_analyze_area_east_outside(live_test):
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
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'bounds', None)
    assert_field(scenario, result, 'total_cells', 0)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_field(scenario, result, 'air_cells', 0)
    assert_field(scenario, result, 'unseen_cells', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_analyze_area_up_limit(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    16,
                    0,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'bounds.min', '$target')
    assert_field(scenario, result, 'bounds.max', '$target')
    assert_field(scenario, result, 'total_cells', 1)
    assert_response_image(res, result, False)


def test_analyze_area_up_outside(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    17,
                    0,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'bounds', None)
    assert_field(scenario, result, 'total_cells', 0)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_field(scenario, result, 'air_cells', 0)
    assert_field(scenario, result, 'unseen_cells', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_analyze_area_down_limit(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    -24,
                    0,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'bounds.min', '$target')
    assert_field(scenario, result, 'bounds.max', '$target')
    assert_field(scenario, result, 'total_cells', 1)
    assert_response_image(res, result, False)


def test_analyze_area_down_outside(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    -25,
                    0,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'bounds', None)
    assert_field(scenario, result, 'total_cells', 0)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_field(scenario, result, 'air_cells', 0)
    assert_field(scenario, result, 'unseen_cells', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_analyze_area_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': {'x': 0, 'y': 0, 'z': 0}, 'end': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_analyze_area_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_analyze_area', {}, timeout=660)
    assert_protocol_error(res, 'start')



@pytest.mark.contract
def test_analyze_area_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': {'x': {'wrong': True}, 'y': 0, 'z': 0}, 'end': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'start')


def test_analyze_area_one_air_cell__armor(live_test):
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
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {
        'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
        'end': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {
        'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
        'end': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'total_cells', 1)
    assert_field(scenario, result, 'air_cells', 1)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_response_image(res, result, False)


def test_analyze_area_one_air_cell__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {
        'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
        'end': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {
        'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
        'end': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'total_cells', 1)
    assert_field(scenario, result, 'air_cells', 1)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_response_image(res, result, False)


def test_analyze_area_one_air_cell__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {
        'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
        'end': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {
        'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
        'end': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'total_cells', 1)
    assert_field(scenario, result, 'air_cells', 1)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_response_image(res, result, False)


def test_analyze_area_one_air_cell__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {
        'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
        'end': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {
        'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
        'end': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'total_cells', 1)
    assert_field(scenario, result, 'air_cells', 1)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_response_image(res, result, False)


def test_analyze_area_one_air_cell__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {
        'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
        'end': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {
        'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
        'end': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'total_cells', 1)
    assert_field(scenario, result, 'air_cells', 1)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_response_image(res, result, False)


def test_analyze_area_one_air_cell__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
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
    res = call_mcp(scenario, 'minecraft_analyze_area', {
        'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
        'end': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {
        'start': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
        'end': {'x': '$base.x', 'y': '$base.y', 'z': '$base.z'},
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'total_cells', 1)
    assert_field(scenario, result, 'air_cells', 1)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_response_image(res, result, False)


def test_analyze_area_east_outside__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'bounds', None)
    assert_field(scenario, result, 'total_cells', 0)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_field(scenario, result, 'air_cells', 0)
    assert_field(scenario, result, 'unseen_cells', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_analyze_area_east_outside__night(live_test):
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
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'bounds', None)
    assert_field(scenario, result, 'total_cells', 0)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_field(scenario, result, 'air_cells', 0)
    assert_field(scenario, result, 'unseen_cells', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_analyze_area_east_outside__rain(live_test):
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
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'bounds', None)
    assert_field(scenario, result, 'total_cells', 0)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_field(scenario, result, 'air_cells', 0)
    assert_field(scenario, result, 'unseen_cells', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_analyze_area_up_outside__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    17,
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
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'bounds', None)
    assert_field(scenario, result, 'total_cells', 0)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_field(scenario, result, 'air_cells', 0)
    assert_field(scenario, result, 'unseen_cells', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_analyze_area_up_outside__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    17,
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
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'bounds', None)
    assert_field(scenario, result, 'total_cells', 0)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_field(scenario, result, 'air_cells', 0)
    assert_field(scenario, result, 'unseen_cells', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_analyze_area_up_outside__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    17,
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
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'bounds', None)
    assert_field(scenario, result, 'total_cells', 0)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_field(scenario, result, 'air_cells', 0)
    assert_field(scenario, result, 'unseen_cells', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_analyze_area_down_outside__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    -25,
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
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'bounds', None)
    assert_field(scenario, result, 'total_cells', 0)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_field(scenario, result, 'air_cells', 0)
    assert_field(scenario, result, 'unseen_cells', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_analyze_area_down_outside__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    -25,
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
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'bounds', None)
    assert_field(scenario, result, 'total_cells', 0)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_field(scenario, result, 'air_cells', 0)
    assert_field(scenario, result, 'unseen_cells', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_analyze_area_down_outside__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    -25,
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
    res = call_mcp(scenario, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_analyze_area', {'start': '$target', 'end': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'bounds', None)
    assert_field(scenario, result, 'total_cells', 0)
    assert_field(scenario, result, 'solid_cells', 0)
    assert_field(scenario, result, 'air_cells', 0)
    assert_field(scenario, result, 'unseen_cells', 0)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='air',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)
