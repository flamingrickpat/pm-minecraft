"""Live tests for minecraft_attack_entity. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import DuringAction, EntitySpec, Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, call_mcp_during, capture_failure_snapshot, capture_truth, parse_result, setup
def test_attack_entity_bare_hand(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': '$target_id'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'entity_id', '$target_id')
    assert_field(scenario, result, 'entity_type', 'cow')
    assert_field(scenario, result, 'killed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='entity_exists',
        target='target',
        expected=(
            'cow',
            False,
        ),
        tolerance=0.8,
    ),))


def test_attack_entity_wooden_sword(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
            items=((
                'wooden_sword',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': '$target_id'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'entity_id', '$target_id')
    assert_field(scenario, result, 'entity_type', 'cow')
    assert_field(scenario, result, 'killed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='entity_exists',
        target='target',
        expected=(
            'cow',
            False,
        ),
        tolerance=0.8,
    ),))


def test_attack_entity_stone_sword(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
            items=((
                'stone_sword',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': '$target_id'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'entity_id', '$target_id')
    assert_field(scenario, result, 'entity_type', 'cow')
    assert_field(scenario, result, 'killed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='entity_exists',
        target='target',
        expected=(
            'cow',
            False,
        ),
        tolerance=0.8,
    ),))



@pytest.mark.smoke
def test_attack_entity_iron_sword(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
            items=((
                'iron_sword',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': '$target_id'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'entity_id', '$target_id')
    assert_field(scenario, result, 'entity_type', 'cow')
    assert_field(scenario, result, 'killed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='entity_exists',
        target='target',
        expected=(
            'cow',
            False,
        ),
        tolerance=0.8,
    ),))


def test_attack_entity_diamond_sword(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
            items=((
                'diamond_sword',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': '$target_id'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'entity_id', '$target_id')
    assert_field(scenario, result, 'entity_type', 'cow')
    assert_field(scenario, result, 'killed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='entity_exists',
        target='target',
        expected=(
            'cow',
            False,
        ),
        tolerance=0.8,
    ),))


def test_attack_entity_iron_axe(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
            items=((
                'iron_axe',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': '$target_id'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'entity_id', '$target_id')
    assert_field(scenario, result, 'entity_type', 'cow')
    assert_field(scenario, result, 'killed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='entity_exists',
        target='target',
        expected=(
            'cow',
            False,
        ),
        tolerance=0.8,
    ),))



@pytest.mark.smoke
def test_attack_entity_unknown_entity_id(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': 2147483647}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': 2147483647}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'entity_not_found'
    assert_message(result, 'entity', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_attack_entity_hit_budget_exhausted(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
            items=((
                'wooden_sword',
                1,
            ),),
            commands=('effect give @e[tag=tdd_target] minecraft:resistance infinite 255 true',),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': '$target_id'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'entity_id', '$target_id')
    assert_field(scenario, result, 'hits', 25)
    assert_field(scenario, result, 'killed', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='entity_exists',
        target='target',
        expected=(
            'cow',
            True,
        ),
        tolerance=0.8,
    ),))


def test_attack_entity_armored_zombie(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='zombie',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"],ArmorItems:[{id:"diamond_boots",Count:1b},{id:"diamond_leggings",Count:1b},{id:"diamond_chestplate",Count:1b},{id:"diamond_helmet",Count:1b}]}',
            ),),
            items=((
                'diamond_sword',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': '$target_id'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'entity_type', 'zombie')
    assert_field(scenario, result, 'killed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='entity_exists',
        target='target',
        expected=(
            'zombie',
            False,
        ),
        tolerance=0.8,
    ),))



@pytest.mark.contract
def test_attack_entity_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': 1}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_attack_entity_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_attack_entity', {}, timeout=660)
    assert_protocol_error(res, 'entity_id')



@pytest.mark.contract
def test_attack_entity_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'entity_id')


def test_attack_entity_target_killed_during_approach(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
            items=((
                'iron_sword',
                1,
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_attack_entity',
        {'entity_id': '$target_id'},
        DuringAction(
            wait='entity_hurt',
            target='target',
            command='kill @e[tag=tdd_target]',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'entity_not_found'
    assert_message(result, 'entity', 'not found')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='entity_exists',
            target='target',
            expected=(
                'cow',
                False,
            ),
            tolerance=0.8,
        ),
        WorldExpectation(
            kind='inventory',
            target='iron_sword',
            expected=1,
        ),
    ))


def test_attack_entity_bare_hand__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
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
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': '$target_id'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'entity_id', '$target_id')
    assert_field(scenario, result, 'entity_type', 'cow')
    assert_field(scenario, result, 'killed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='entity_exists',
        target='target',
        expected=(
            'cow',
            False,
        ),
        tolerance=0.8,
    ),))


def test_attack_entity_bare_hand__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': '$target_id'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'entity_id', '$target_id')
    assert_field(scenario, result, 'entity_type', 'cow')
    assert_field(scenario, result, 'killed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='entity_exists',
        target='target',
        expected=(
            'cow',
            False,
        ),
        tolerance=0.8,
    ),))


def test_attack_entity_bare_hand__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': '$target_id'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'entity_id', '$target_id')
    assert_field(scenario, result, 'entity_type', 'cow')
    assert_field(scenario, result, 'killed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='entity_exists',
        target='target',
        expected=(
            'cow',
            False,
        ),
        tolerance=0.8,
    ),))


def test_attack_entity_bare_hand__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': '$target_id'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'entity_id', '$target_id')
    assert_field(scenario, result, 'entity_type', 'cow')
    assert_field(scenario, result, 'killed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='entity_exists',
        target='target',
        expected=(
            'cow',
            False,
        ),
        tolerance=0.8,
    ),))


def test_attack_entity_bare_hand__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': '$target_id'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'entity_id', '$target_id')
    assert_field(scenario, result, 'entity_type', 'cow')
    assert_field(scenario, result, 'killed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='entity_exists',
        target='target',
        expected=(
            'cow',
            False,
        ),
        tolerance=0.8,
    ),))


def test_attack_entity_bare_hand__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
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
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': '$target_id'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'entity_id', '$target_id')
    assert_field(scenario, result, 'entity_type', 'cow')
    assert_field(scenario, result, 'killed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='entity_exists',
        target='target',
        expected=(
            'cow',
            False,
        ),
        tolerance=0.8,
    ),))


def test_attack_entity_unknown_entity_id__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': 2147483647}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': 2147483647}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'entity_not_found'
    assert_message(result, 'entity', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_attack_entity_unknown_entity_id__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': 2147483647}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': 2147483647}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'entity_not_found'
    assert_message(result, 'entity', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_attack_entity_unknown_entity_id__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_attack_entity', {'entity_id': 2147483647}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': 2147483647}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'entity_not_found'
    assert_message(result, 'entity', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_attack_entity_target_killed_during_approach__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
            items=((
                'iron_sword',
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
        'minecraft_attack_entity',
        {'entity_id': '$target_id'},
        DuringAction(
            wait='entity_hurt',
            target='target',
            command='kill @e[tag=tdd_target]',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'entity_not_found'
    assert_message(result, 'entity', 'not found')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='entity_exists',
            target='target',
            expected=(
                'cow',
                False,
            ),
            tolerance=0.8,
        ),
        WorldExpectation(
            kind='inventory',
            target='iron_sword',
            expected=1,
        ),
    ))


def test_attack_entity_target_killed_during_approach__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
            items=((
                'iron_sword',
                1,
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_attack_entity',
        {'entity_id': '$target_id'},
        DuringAction(
            wait='entity_hurt',
            target='target',
            command='kill @e[tag=tdd_target]',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'entity_not_found'
    assert_message(result, 'entity', 'not found')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='entity_exists',
            target='target',
            expected=(
                'cow',
                False,
            ),
            tolerance=0.8,
        ),
        WorldExpectation(
            kind='inventory',
            target='iron_sword',
            expected=1,
        ),
    ))


def test_attack_entity_target_killed_during_approach__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            entities=(EntitySpec(
                key='target',
                entity='cow',
                offset=(
                    3.5,
                    0,
                    0.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}',
            ),),
            items=((
                'iron_sword',
                1,
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_attack_entity',
        {'entity_id': '$target_id'},
        DuringAction(
            wait='entity_hurt',
            target='target',
            command='kill @e[tag=tdd_target]',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_attack_entity', {'entity_id': '$target_id'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'entity_not_found'
    assert_message(result, 'entity', 'not found')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='entity_exists',
            target='target',
            expected=(
                'cow',
                False,
            ),
            tolerance=0.8,
        ),
        WorldExpectation(
            kind='inventory',
            target='iron_sword',
            expected=1,
        ),
    ))
