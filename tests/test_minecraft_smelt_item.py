"""Live tests for minecraft_smelt_item. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, DuringAction, Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, call_mcp_during, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.slow

@pytest.mark.smoke
def test_smelt_item_coal_one(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'input_item', 'raw_iron')
    assert_field(scenario, result, 'fuel_item', 'coal')
    assert_field(scenario, result, 'input_consumed', 1)
    assert_field(scenario, result, 'output.count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_ingot',
        expected=1,
    ),))



@pytest.mark.slow
def test_smelt_item_coal_many(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    4,
                ),
                (
                    'coal',
                    1,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 4, 'fuel': 'coal', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 4, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'input_item', 'raw_iron')
    assert_field(scenario, result, 'fuel_item', 'coal')
    assert_field(scenario, result, 'input_consumed', 4)
    assert_field(scenario, result, 'output.count', 4)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_ingot',
        expected=4,
    ),))



@pytest.mark.slow
def test_smelt_item_charcoal(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    2,
                ),
                (
                    'charcoal',
                    1,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 2, 'fuel': 'charcoal', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 2, 'fuel': 'charcoal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'input_item', 'raw_iron')
    assert_field(scenario, result, 'fuel_item', 'charcoal')
    assert_field(scenario, result, 'input_consumed', 2)
    assert_field(scenario, result, 'output.count', 2)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_ingot',
        expected=2,
    ),))



@pytest.mark.slow
def test_smelt_item_lava_bucket(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    8,
                ),
                (
                    'lava_bucket',
                    1,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 8, 'fuel': 'lava_bucket', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 8, 'fuel': 'lava_bucket', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'input_item', 'raw_iron')
    assert_field(scenario, result, 'fuel_item', 'lava_bucket')
    assert_field(scenario, result, 'input_consumed', 8)
    assert_field(scenario, result, 'output.count', 8)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_ingot',
        expected=8,
    ),))



@pytest.mark.smoke
def test_smelt_item_no_furnace(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'furnace_not_found'
    assert_message(result, 'furnace', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_smelt_item_missing_fuel(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace',
            ),),
            items=((
                'raw_iron',
                1,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'missing'
    assert_message(result, 'missing')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_smelt_item_missing_input(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace',
            ),),
            items=((
                'coal',
                1,
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'missing'
    assert_message(result, 'missing')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.slow
def test_smelt_item_furnace_distance_boundary(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    8,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
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
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'furnace', '$furnace')
    assert_field(scenario, result, 'input_consumed', 1)
    assert_field(scenario, result, 'output.name', 'iron_ingot')
    assert_field(scenario, result, 'output.count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_ingot',
        expected=1,
    ),))


def test_smelt_item_outside_furnace_distance(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    9,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
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
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'furnace_not_found'
    assert_message(result, 'furnace', 'not found')
    assert_field(scenario, result, 'furnace', None)
    assert_field(scenario, result, 'input_consumed', 0)
    assert_field(scenario, result, 'output', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='furnace',
            expected='furnace',
        ),
        WorldExpectation(
            kind='inventory',
            target='raw_iron',
            expected=1,
        ),
        WorldExpectation(
            kind='inventory',
            target='coal',
            expected=1,
        ),
        WorldExpectation(
            kind='inventory',
            target='iron_ingot',
            expected=0,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_smelt_item_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron'}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_smelt_item_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_smelt_item', {}, timeout=660)
    assert_protocol_error(res, 'input')



@pytest.mark.contract
def test_smelt_item_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'input')


def test_smelt_item_furnace_removed_during_action(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_smelt_item',
        {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1},
        DuringAction(
            wait='block_property_true',
            target='furnace',
            command='setblock {furnace_x} {furnace_y} {furnace_z} air',
            property='lit',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'target_changed'
    assert_message(result, 'target', 'changed')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='furnace',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='iron_ingot',
            expected=0,
        ),
    ))


def test_smelt_item_coal_one__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
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
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'input_item', 'raw_iron')
    assert_field(scenario, result, 'fuel_item', 'coal')
    assert_field(scenario, result, 'input_consumed', 1)
    assert_field(scenario, result, 'output.count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_ingot',
        expected=1,
    ),))


def test_smelt_item_coal_one__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
                ),
            ),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'input_item', 'raw_iron')
    assert_field(scenario, result, 'fuel_item', 'coal')
    assert_field(scenario, result, 'input_consumed', 1)
    assert_field(scenario, result, 'output.count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_ingot',
        expected=1,
    ),))


def test_smelt_item_coal_one__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
                ),
            ),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'input_item', 'raw_iron')
    assert_field(scenario, result, 'fuel_item', 'coal')
    assert_field(scenario, result, 'input_consumed', 1)
    assert_field(scenario, result, 'output.count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_ingot',
        expected=1,
    ),))


def test_smelt_item_coal_one__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
                ),
            ),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'input_item', 'raw_iron')
    assert_field(scenario, result, 'fuel_item', 'coal')
    assert_field(scenario, result, 'input_consumed', 1)
    assert_field(scenario, result, 'output.count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_ingot',
        expected=1,
    ),))


def test_smelt_item_coal_one__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
                ),
            ),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'input_item', 'raw_iron')
    assert_field(scenario, result, 'fuel_item', 'coal')
    assert_field(scenario, result, 'input_consumed', 1)
    assert_field(scenario, result, 'output.count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_ingot',
        expected=1,
    ),))


def test_smelt_item_coal_one__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
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
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'input_item', 'raw_iron')
    assert_field(scenario, result, 'fuel_item', 'coal')
    assert_field(scenario, result, 'input_consumed', 1)
    assert_field(scenario, result, 'output.count', 1)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='inventory',
        target='iron_ingot',
        expected=1,
    ),))


def test_smelt_item_no_furnace__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'furnace_not_found'
    assert_message(result, 'furnace', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_smelt_item_no_furnace__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'furnace_not_found'
    assert_message(result, 'furnace', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_smelt_item_no_furnace__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
                ),
            ),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'furnace_not_found'
    assert_message(result, 'furnace', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_smelt_item_missing_fuel__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace',
            ),),
            items=((
                'raw_iron',
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
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'missing'
    assert_message(result, 'missing')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_smelt_item_missing_fuel__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace',
            ),),
            items=((
                'raw_iron',
                1,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'missing'
    assert_message(result, 'missing')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_smelt_item_missing_fuel__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace',
            ),),
            items=((
                'raw_iron',
                1,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'missing'
    assert_message(result, 'missing')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_smelt_item_missing_input__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace',
            ),),
            items=((
                'coal',
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
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'missing'
    assert_message(result, 'missing')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_smelt_item_missing_input__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace',
            ),),
            items=((
                'coal',
                1,
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'missing'
    assert_message(result, 'missing')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_smelt_item_missing_input__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace',
            ),),
            items=((
                'coal',
                1,
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'fuel': 'coal'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'missing'
    assert_message(result, 'missing')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_smelt_item_outside_furnace_distance__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    9,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
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
            player_offset=(
                0.0,
                0.0,
                0.0,
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'furnace_not_found'
    assert_message(result, 'furnace', 'not found')
    assert_field(scenario, result, 'furnace', None)
    assert_field(scenario, result, 'input_consumed', 0)
    assert_field(scenario, result, 'output', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='furnace',
            expected='furnace',
        ),
        WorldExpectation(
            kind='inventory',
            target='raw_iron',
            expected=1,
        ),
        WorldExpectation(
            kind='inventory',
            target='coal',
            expected=1,
        ),
        WorldExpectation(
            kind='inventory',
            target='iron_ingot',
            expected=0,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_smelt_item_outside_furnace_distance__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    9,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
                ),
            ),
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
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'furnace_not_found'
    assert_message(result, 'furnace', 'not found')
    assert_field(scenario, result, 'furnace', None)
    assert_field(scenario, result, 'input_consumed', 0)
    assert_field(scenario, result, 'output', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='furnace',
            expected='furnace',
        ),
        WorldExpectation(
            kind='inventory',
            target='raw_iron',
            expected=1,
        ),
        WorldExpectation(
            kind='inventory',
            target='coal',
            expected=1,
        ),
        WorldExpectation(
            kind='inventory',
            target='iron_ingot',
            expected=0,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_smelt_item_outside_furnace_distance__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    9,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
                ),
            ),
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
    res = call_mcp(scenario, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'furnace_not_found'
    assert_message(result, 'furnace', 'not found')
    assert_field(scenario, result, 'furnace', None)
    assert_field(scenario, result, 'input_consumed', 0)
    assert_field(scenario, result, 'output', None)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='furnace',
            expected='furnace',
        ),
        WorldExpectation(
            kind='inventory',
            target='raw_iron',
            expected=1,
        ),
        WorldExpectation(
            kind='inventory',
            target='coal',
            expected=1,
        ),
        WorldExpectation(
            kind='inventory',
            target='iron_ingot',
            expected=0,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_smelt_item_furnace_removed_during_action__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
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
    res = call_mcp_during(
        scenario,
        'minecraft_smelt_item',
        {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1},
        DuringAction(
            wait='block_property_true',
            target='furnace',
            command='setblock {furnace_x} {furnace_y} {furnace_z} air',
            property='lit',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'target_changed'
    assert_message(result, 'target', 'changed')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='furnace',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='iron_ingot',
            expected=0,
        ),
    ))


def test_smelt_item_furnace_removed_during_action__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
                ),
            ),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_smelt_item',
        {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1},
        DuringAction(
            wait='block_property_true',
            target='furnace',
            command='setblock {furnace_x} {furnace_y} {furnace_z} air',
            property='lit',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'target_changed'
    assert_message(result, 'target', 'changed')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='furnace',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='iron_ingot',
            expected=0,
        ),
    ))


def test_smelt_item_furnace_removed_during_action__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='furnace',
                offset=(
                    3,
                    0,
                    0,
                ),
                block='furnace[facing=west]',
            ),),
            items=(
                (
                    'raw_iron',
                    1,
                ),
                (
                    'coal',
                    1,
                ),
            ),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp_during(
        scenario,
        'minecraft_smelt_item',
        {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1},
        DuringAction(
            wait='block_property_true',
            target='furnace',
            command='setblock {furnace_x} {furnace_y} {furnace_z} air',
            property='lit',
        ),
        timeout=660,
    )
    result = parse_result(scenario, res, 'minecraft_smelt_item', {'input': 'raw_iron', 'input_count': 1, 'fuel': 'coal', 'fuel_count': 1}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'target_changed'
    assert_message(result, 'target', 'changed')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='block',
            target='furnace',
            expected='air',
        ),
        WorldExpectation(
            kind='inventory',
            target='iron_ingot',
            expected=0,
        ),
    ))
