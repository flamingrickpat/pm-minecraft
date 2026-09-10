"""Live tests for minecraft_pillar_up. Each test states its complete setup, MCP call, and assertions."""

import math

import pytest

from mcmcp.constants import EXACT_WALK_TOLERANCE_BLOCKS
from tests.live_case import Approx, BlockSpec, Layout, Scenario, WorldExpectation, arrange, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup


def test_pillar_up_through_mine_shaft_then_walks_to_upper_tunnel(live_test):
    context = arrange(
        live_test,
        Layout(
            points=(
                ('shaft_base', (5.0, 1.0, 8.0)),
                ('destination', (10.0, 9.0, 8.0)),
            ),
            blocks=(
                BlockSpec(key='shaft_floor', offset=(5, 0, 8), block='cobblestone'),
                BlockSpec(key='shaft_ceiling', offset=(5, 11, 8), block='cobblestone'),
                BlockSpec(key='destination_cell', offset=(10, 9, 8), block='air'),
            ),
            items=(('cobblestone', 8),),
            player_offset=(20.5, 0.0, 20.5),
            commands=(
                'execute positioned {x} {y} {z} run fill ~0 ~0 ~0 ~15 ~15 ~15 cobblestone',
                'execute positioned {x} {y} {z} run fill ~0 ~1 ~8 ~5 ~2 ~8 air',
                'execute positioned {x} {y} {z} run fill ~5 ~1 ~8 ~5 ~10 ~8 air',
                'execute positioned {x} {y} {z} run fill ~5 ~9 ~8 ~10 ~10 ~8 air',
            ),
        ),
    )
    base = context['base']
    entrance = {'x': base['x'] + 0.5, 'y': base['y'] + 1.0, 'z': base['z'] + 8.5}
    live_test.operator_command(
        f"tp {live_test.configuration.player_name} {entrance['x']} {entrance['y']} {entrance['z']}"
    )
    live_test.wait_for(
        'the player at the mine entrance',
        live_test.player_state,
        lambda state: math.dist(
            tuple(state['position'][axis] for axis in ('x', 'y', 'z')),
            tuple(entrance[axis] for axis in ('x', 'y', 'z')),
        ) < 0.1,
    )
    context['player'] = entrance
    live_test.handoff_player_to_mcp()
    scenario = Scenario(live_test, context, require_body=True, disconnect_body=False)

    first_walk_args = {
        'x': '$destination.x',
        'y': '$destination.y',
        'z': '$destination.z',
    }
    truth_before = capture_truth(scenario)
    first_walk_response = call_mcp(scenario, 'minecraft_walk_to_exact', first_walk_args, timeout=660)
    first_walk = parse_result(
        scenario,
        first_walk_response,
        'minecraft_walk_to_exact',
        first_walk_args,
        truth_before=truth_before,
    )
    assert first_walk.ok is False
    assert first_walk.status == 'partial'
    assert first_walk.reason == 'no_path'
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='shaft_base',
        expected=None,
        tolerance=1.0,
    ),))

    pillar_args = {'count': 8}
    truth_before = capture_truth(scenario)
    pillar_response = call_mcp(scenario, 'minecraft_pillar_up', pillar_args, timeout=660)
    pillar = parse_result(
        scenario,
        pillar_response,
        'minecraft_pillar_up',
        pillar_args,
        truth_before=truth_before,
    )
    assert pillar.ok is True
    assert pillar.reason is None
    assert pillar.climbed == 8
    assert pillar.blocks_placed == 8
    assert_world_state(scenario, (
        WorldExpectation(kind='inventory', target='cobblestone', expected=0),
        WorldExpectation(kind='player_data', target='Health', expected=20.0),
        WorldExpectation(kind='player_y_delta', target='player', expected=8),
    ))

    truth_before = capture_truth(scenario)
    final_walk_response = call_mcp(scenario, 'minecraft_walk_to_exact', first_walk_args, timeout=660)
    final_walk = parse_result(
        scenario,
        final_walk_response,
        'minecraft_walk_to_exact',
        first_walk_args,
        truth_before=truth_before,
    )
    assert final_walk.ok is True
    assert final_walk.reason is None
    assert final_walk.status == 'reached'
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='destination',
        expected=None,
        tolerance=EXACT_WALK_TOLERANCE_BLOCKS,
    ),))

@pytest.mark.smoke
def test_pillar_up_one_block(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='pillar_cell',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            items=((
                'cobblestone',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'climbed', 1)
    assert_field(scenario, result, 'blocks_placed', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='pillar_cell',
            expected='cobblestone',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=1,
            ),
        ),
    ))


def test_pillar_up_mixed_stacks(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='pillar_cell',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            items=(
                (
                    'cobblestone',
                    3,
                ),
                (
                    'dirt',
                    2,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'climbed', 1)
    assert_field(scenario, result, 'blocks_placed', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='pillar_cell',
            expected='cobblestone',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=2,
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=1,
            ),
        ),
    ))



@pytest.mark.smoke
def test_pillar_up_empty_hand(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_held_item'
    assert_message(result, 'hand', 'empty')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_pillar_up_non_placeable(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_placeable'
    assert_message(result, 'not', 'placeable')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_pillar_up_no_headroom(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='ceiling',
                offset=(
                    0,
                    2,
                    0,
                ),
                block='bedrock',
            ),),
            items=((
                'cobblestone',
                4,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_headroom'
    assert_message(result, 'headroom')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='ceiling',
        expected='bedrock',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_pillar_up_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_pillar_up_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_pillar_up', {'unexpected_argument': True}, timeout=660)
    assert_protocol_error(res, 'unexpected_argument')


def test_pillar_up_one_block__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='pillar_cell',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            items=((
                'cobblestone',
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
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'climbed', 1)
    assert_field(scenario, result, 'blocks_placed', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='pillar_cell',
            expected='cobblestone',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=1,
            ),
        ),
    ))


def test_pillar_up_one_block__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='pillar_cell',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            items=((
                'cobblestone',
                1,
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'climbed', 1)
    assert_field(scenario, result, 'blocks_placed', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='pillar_cell',
            expected='cobblestone',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=1,
            ),
        ),
    ))


def test_pillar_up_one_block__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='pillar_cell',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            items=((
                'cobblestone',
                1,
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'climbed', 1)
    assert_field(scenario, result, 'blocks_placed', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='pillar_cell',
            expected='cobblestone',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=1,
            ),
        ),
    ))


def test_pillar_up_one_block__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='pillar_cell',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            items=((
                'cobblestone',
                1,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'climbed', 1)
    assert_field(scenario, result, 'blocks_placed', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='pillar_cell',
            expected='cobblestone',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=1,
            ),
        ),
    ))


def test_pillar_up_one_block__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='pillar_cell',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            items=((
                'cobblestone',
                1,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'climbed', 1)
    assert_field(scenario, result, 'blocks_placed', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='pillar_cell',
            expected='cobblestone',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=1,
            ),
        ),
    ))


def test_pillar_up_one_block__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='pillar_cell',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            items=(
                (
                    'cobblestone',
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
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'climbed', 1)
    assert_field(scenario, result, 'blocks_placed', 1)
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='pillar_cell',
            expected='cobblestone',
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
        WorldExpectation(
            kind='player_y_delta',
            target='player',
            expected=Approx(
                value=1,
            ),
        ),
    ))


def test_pillar_up_empty_hand__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_held_item'
    assert_message(result, 'hand', 'empty')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_pillar_up_empty_hand__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_held_item'
    assert_message(result, 'hand', 'empty')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_pillar_up_empty_hand__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_held_item'
    assert_message(result, 'hand', 'empty')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_pillar_up_non_placeable__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
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
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_placeable'
    assert_message(result, 'not', 'placeable')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_pillar_up_non_placeable__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_placeable'
    assert_message(result, 'not', 'placeable')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_pillar_up_non_placeable__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'apple',
                1,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_placeable'
    assert_message(result, 'not', 'placeable')
    assert_response_image(res, result, result.image is not None)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_pillar_up_no_headroom__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='ceiling',
                offset=(
                    0,
                    2,
                    0,
                ),
                block='bedrock',
            ),),
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_headroom'
    assert_message(result, 'headroom')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='ceiling',
        expected='bedrock',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_pillar_up_no_headroom__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='ceiling',
                offset=(
                    0,
                    2,
                    0,
                ),
                block='bedrock',
            ),),
            items=((
                'cobblestone',
                4,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_headroom'
    assert_message(result, 'headroom')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='ceiling',
        expected='bedrock',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_pillar_up_no_headroom__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='ceiling',
                offset=(
                    0,
                    2,
                    0,
                ),
                block='bedrock',
            ),),
            items=((
                'cobblestone',
                4,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_pillar_up', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_pillar_up', {}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_headroom'
    assert_message(result, 'headroom')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='ceiling',
        expected='bedrock',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)
