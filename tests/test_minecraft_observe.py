"""Live tests for minecraft_observe. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, EntitySpec, Excludes, Includes, Layout, Length, NonEmpty, WorldExpectation, assert_field, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_truth, parse_result, setup
def test_observe_empty_day(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_observe', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_observe', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'player.health', 20.0)
    assert_field(scenario, result, 'player.food', 20)
    assert_field(scenario, result, 'camera.feet_position.x', '$player.x')
    assert_response_image(res, result, False)



@pytest.mark.smoke
def test_observe_mixed_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='chest',
                    offset=(
                        2,
                        0,
                        2,
                    ),
                    block='chest',
                ),
                BlockSpec(
                    key='lava',
                    offset=(
                        -2,
                        0,
                        2,
                    ),
                    block='lava',
                ),
            ),
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
            ),),
            items=(
                (
                    'iron_sword',
                    1,
                ),
                (
                    'cobblestone',
                    37,
                ),
                (
                    'apple',
                    5,
                ),
                (
                    'torch',
                    64,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_observe', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_observe', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'player.health', 20.0)
    assert_field(scenario, result, 'player.food', 20)
    assert_field(scenario, result, 'camera.feet_position.x', '$player.x')
    assert_response_image(res, result, False)


def test_observe_water(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='water',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='water',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_observe', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_observe', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'player.health', 20.0)
    assert_field(scenario, result, 'player.food', 20)
    assert_field(scenario, result, 'camera.feet_position.x', '$player.x')
    assert_response_image(res, result, False)


def test_observe_dark(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='roof',
                offset=(
                    0,
                    2,
                    0,
                ),
                block='stone',
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_observe', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_observe', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'player.health', 20.0)
    assert_field(scenario, result, 'player.food', 20)
    assert_field(scenario, result, 'camera.feet_position.x', '$player.x')
    assert_response_image(res, result, False)


def test_observe_damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=((
                'wooden_pickaxe',
                1,
            ),),
            food=4,
            health=7.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_observe', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_observe', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'player.health', 7.0)
    assert_field(scenario, result, 'player.food', 4)
    assert_field(scenario, result, 'camera.feet_position.x', '$player.x')
    assert_response_image(res, result, False)


def test_observe_png_image(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_observe', {'include_image': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_observe', {'include_image': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)


def test_observe_fixed_radius_boundary(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='inside_block',
                    offset=(
                        8,
                        0,
                        0,
                    ),
                    block='diamond_block',
                ),
                BlockSpec(
                    key='outside_block',
                    offset=(
                        9,
                        0,
                        0,
                    ),
                    block='emerald_block',
                ),
            ),
            entities=(
                EntitySpec(
                    key='inside_entity',
                    entity='pig',
                    offset=(
                        0.0,
                        0,
                        8.0,
                    ),
                    nbt='{NoAI:1b,PersistenceRequired:1b}',
                ),
                EntitySpec(
                    key='outside_entity',
                    entity='cow',
                    offset=(
                        0.0,
                        0,
                        9.0,
                    ),
                    nbt='{NoAI:1b,PersistenceRequired:1b}',
                ),
            ),
            player_offset=(
                0.0,
                0.0,
                0.0,
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_observe', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_observe', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'nearby_blocks', Includes(
        value='diamond_block',
        key='block_name',
    ))
    assert_field(scenario, result, 'nearby_blocks', Excludes(
        value='emerald_block',
        key='block_name',
    ))
    assert_field(scenario, result, 'nearby_entities', Includes(
        value='pig',
        key='entity_type',
    ))
    assert_field(scenario, result, 'nearby_entities', Excludes(
        value='cow',
        key='entity_type',
    ))
    assert_response_image(res, result, False)


def test_observe_full_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            slot_items=(
                (
                    'hotbar.0',
                    'dirt',
                    64,
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
    res = call_mcp(scenario, 'minecraft_observe', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_observe', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'inventory', NonEmpty())
    assert_field(scenario, result, 'hotbar', Length(
        value=9,
    ))
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='dirt',
        expected=2304,
    ),))



@pytest.mark.contract

@pytest.mark.smoke
def test_observe_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_observe', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_observe_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_observe', {'include_image': {'not': 'the declared type'}}, timeout=660)
    assert_protocol_error(res, 'include_image')



@pytest.mark.contract
def test_observe_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_observe', {'include_image': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'include_image')


def test_observe_empty_day__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_observe', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_observe', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'player.health', 20.0)
    assert_field(scenario, result, 'player.food', 20)
    assert_field(scenario, result, 'camera.feet_position.x', '$player.x')
    assert_response_image(res, result, False)


def test_observe_empty_day__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_observe', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_observe', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'player.health', 20.0)
    assert_field(scenario, result, 'player.food', 20)
    assert_field(scenario, result, 'camera.feet_position.x', '$player.x')
    assert_response_image(res, result, False)


def test_observe_empty_day__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_observe', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_observe', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'player.health', 20.0)
    assert_field(scenario, result, 'player.food', 20)
    assert_field(scenario, result, 'camera.feet_position.x', '$player.x')
    assert_response_image(res, result, False)


def test_observe_empty_day__junk_inventory(live_test):
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
    res = call_mcp(scenario, 'minecraft_observe', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_observe', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'player.health', 20.0)
    assert_field(scenario, result, 'player.food', 20)
    assert_field(scenario, result, 'camera.feet_position.x', '$player.x')
    assert_response_image(res, result, False)
