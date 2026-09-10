"""Live tests for minecraft_suicide. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, Layout, WorldExpectation, assert_field, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_truth, parse_result, setup

@pytest.mark.slow

@pytest.mark.smoke
def test_suicide_empty_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=(
                (
                    'spawn',
                    (
                        0.5,
                        0,
                        0.5,
                    ),
                ),
                (
                    'death',
                    (
                        20.5,
                        0,
                        0.5,
                    ),
                ),
            ),
            player_offset=(
                20.5,
                0,
                0.5,
            ),
            commands=(
                'gamerule keepInventory false',
                'gamerule spawnRadius 0',
                'setworldspawn {x} {y} {z}',
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_suicide', {'reason': 'TDD empty_inventory'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_suicide', {'reason': 'TDD empty_inventory'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cause', 'TDD empty_inventory')
    assert_field(scenario, result, 'deaths', 1)
    assert_field(scenario, result, 'inventory_lost', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='spawn',
        expected=None,
        tolerance=2.0,
    ),))



@pytest.mark.slow
def test_suicide_full_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=(
                (
                    'spawn',
                    (
                        0.5,
                        0,
                        0.5,
                    ),
                ),
                (
                    'death',
                    (
                        20.5,
                        0,
                        0.5,
                    ),
                ),
            ),
            items=(
                (
                    'cobblestone',
                    64,
                ),
                (
                    'apple',
                    16,
                ),
                (
                    'iron_pickaxe',
                    1,
                ),
            ),
            player_offset=(
                20.5,
                0,
                0.5,
            ),
            commands=(
                'gamerule keepInventory false',
                'gamerule spawnRadius 0',
                'setworldspawn {x} {y} {z}',
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_suicide', {'reason': 'TDD full_inventory'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_suicide', {'reason': 'TDD full_inventory'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cause', 'TDD full_inventory')
    assert_field(scenario, result, 'deaths', 1)
    assert_field(scenario, result, 'inventory_lost', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='player_near',
            target='spawn',
            expected=None,
            tolerance=2.0,
        ),
        WorldExpectation(
            kind='inventory',
            target='cobblestone',
            expected=0,
        ),
        WorldExpectation(
            kind='item_entities',
            target='cobblestone',
            expected=64,
        ),
        WorldExpectation(
            kind='inventory',
            target='apple',
            expected=0,
        ),
        WorldExpectation(
            kind='item_entities',
            target='apple',
            expected=16,
        ),
        WorldExpectation(
            kind='inventory',
            target='iron_pickaxe',
            expected=0,
        ),
        WorldExpectation(
            kind='item_entities',
            target='iron_pickaxe',
            expected=1,
        ),
    ))



@pytest.mark.slow
def test_suicide_bed_spawn(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=(
                (
                    'spawn',
                    (
                        0.5,
                        0,
                        0.5,
                    ),
                ),
                (
                    'death',
                    (
                        20.5,
                        0,
                        0.5,
                    ),
                ),
            ),
            blocks=(
                BlockSpec(
                    key='bed',
                    offset=(
                        0,
                        0,
                        0,
                    ),
                    block='red_bed[part=foot,facing=east,occupied=false]',
                ),
                BlockSpec(
                    key='bed_head',
                    offset=(
                        1,
                        0,
                        0,
                    ),
                    block='red_bed[part=head,facing=east,occupied=false]',
                ),
            ),
            items=((
                'torch',
                8,
            ),),
            player_offset=(
                20.5,
                0,
                0.5,
            ),
            commands=(
                'gamerule keepInventory false',
                'gamerule spawnRadius 0',
                'setworldspawn {x} {y} {z}',
                'spawnpoint {player} {x} {y} {z}',
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_suicide', {'reason': 'TDD bed_spawn'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_suicide', {'reason': 'TDD bed_spawn'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cause', 'TDD bed_spawn')
    assert_field(scenario, result, 'deaths', 1)
    assert_field(scenario, result, 'inventory_lost', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='player_near',
            target='spawn',
            expected=None,
            tolerance=2.0,
        ),
        WorldExpectation(
            kind='inventory',
            target='torch',
            expected=0,
        ),
        WorldExpectation(
            kind='item_entities',
            target='torch',
            expected=8,
        ),
        WorldExpectation(
            kind='block',
            target='bed',
            expected='red_bed',
        ),
    ))



@pytest.mark.contract

@pytest.mark.smoke
def test_suicide_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_suicide', {'reason': 'body test'}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_suicide_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_suicide', {}, timeout=660)
    assert_protocol_error(res, 'reason')



@pytest.mark.contract
def test_suicide_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_suicide', {'reason': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'reason')
