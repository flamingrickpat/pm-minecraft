"""Live tests for minecraft_raytrace. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Approx, BlockSpec, EntitySpec, Layout, WorldExpectation, assert_field, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_raytrace_solid_center(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    1,
                    4,
                ),
                block='stone',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', True)
    assert_field(scenario, result, 'hit_block', 'stone')
    assert_field(scenario, result, 'hit_position', '$target')
    assert_response_image(res, result, False)


def test_raytrace_water(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    1,
                    4,
                ),
                block='water',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', True)
    assert_field(scenario, result, 'hit_block', 'water')
    assert_field(scenario, result, 'hit_position', '$target')
    assert_response_image(res, result, False)


def test_raytrace_glass(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    1,
                    4,
                ),
                block='glass',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', True)
    assert_field(scenario, result, 'hit_block', 'glass')
    assert_field(scenario, result, 'hit_position', '$target')
    assert_response_image(res, result, False)


def test_raytrace_leaves(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    1,
                    4,
                ),
                block='oak_leaves[persistent=true]',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', True)
    assert_field(scenario, result, 'hit_block', 'oak_leaves')
    assert_field(scenario, result, 'hit_position', '$target')
    assert_response_image(res, result, False)


def test_raytrace_open_sky(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', False)
    assert_field(scenario, result, 'hit_block', None)
    assert_response_image(res, result, False)


def test_raytrace_png_image(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    1,
                    4,
                ),
                block='stone',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', True)
    assert_response_image(res, result, True)


def test_raytrace_fixed_range_boundary(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    1,
                    256,
                ),
                block='diamond_block',
            ),),
            player_offset=(
                0.5,
                0.0,
                0.0,
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', True)
    assert_field(scenario, result, 'hit_block', 'diamond_block')
    assert_field(scenario, result, 'hit_position', '$target')
    assert_field(scenario, result, 'distance', Approx(
        value=256,
        tolerance=0.01,
    ))
    assert_response_image(res, result, False)


def test_raytrace_outside_fixed_range(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    1,
                    257,
                ),
                block='emerald_block',
            ),),
            player_offset=(
                0.5,
                0.0,
                0.0,
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', False)
    assert_field(scenario, result, 'hit_block', None)
    assert_field(scenario, result, 'hit_position', None)
    assert_field(scenario, result, 'distance', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='target',
        expected='emerald_block',
    ),))


def test_raytrace_entity_before_block(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    1,
                    6,
                ),
                block='stone',
            ),),
            entities=(EntitySpec(
                key='cow',
                entity='cow',
                offset=(
                    0.5,
                    0,
                    3.5,
                ),
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', True)
    assert_field(scenario, result, 'hit_block', 'stone')
    assert_field(scenario, result, 'hit_position', '$target')
    assert_response_image(res, result, False)



@pytest.mark.contract

@pytest.mark.smoke
def test_raytrace_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_raytrace', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_raytrace_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': {'not': 'the declared type'}}, timeout=660)
    assert_protocol_error(res, 'include_image')



@pytest.mark.contract
def test_raytrace_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'include_image')


def test_raytrace_solid_center__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    1,
                    4,
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
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', True)
    assert_field(scenario, result, 'hit_block', 'stone')
    assert_field(scenario, result, 'hit_position', '$target')
    assert_response_image(res, result, False)


def test_raytrace_solid_center__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    1,
                    4,
                ),
                block='stone',
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', True)
    assert_field(scenario, result, 'hit_block', 'stone')
    assert_field(scenario, result, 'hit_position', '$target')
    assert_response_image(res, result, False)


def test_raytrace_solid_center__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    1,
                    4,
                ),
                block='stone',
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', True)
    assert_field(scenario, result, 'hit_block', 'stone')
    assert_field(scenario, result, 'hit_position', '$target')
    assert_response_image(res, result, False)


def test_raytrace_solid_center__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    1,
                    4,
                ),
                block='stone',
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', True)
    assert_field(scenario, result, 'hit_block', 'stone')
    assert_field(scenario, result, 'hit_position', '$target')
    assert_response_image(res, result, False)


def test_raytrace_solid_center__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    1,
                    4,
                ),
                block='stone',
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', True)
    assert_field(scenario, result, 'hit_block', 'stone')
    assert_field(scenario, result, 'hit_position', '$target')
    assert_response_image(res, result, False)


def test_raytrace_solid_center__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    1,
                    4,
                ),
                block='stone',
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
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_raytrace', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_raytrace', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hit', True)
    assert_field(scenario, result, 'hit_block', 'stone')
    assert_field(scenario, result, 'hit_position', '$target')
    assert_response_image(res, result, False)
