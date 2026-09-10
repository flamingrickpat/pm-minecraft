"""Live tests for minecraft_sleep. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, EntitySpec, Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.slow

@pytest.mark.smoke
def test_sleep_safe_night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='bed',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='red_bed[part=foot,facing=east,occupied=false]',
                ),
                BlockSpec(
                    key='bed_head',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='red_bed[part=head,facing=east,occupied=false]',
                ),
            ),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_sleep', {'bed': '$bed'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_sleep', {'bed': '$bed'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'slept', True)
    assert_field(scenario, result, 'is_day_now', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='time_is_day',
            target='world',
            expected=True,
        ),
        WorldExpectation(
            kind='block',
            target='bed',
            expected='red_bed',
        ),
    ))



@pytest.mark.smoke
def test_sleep_no_bed(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_sleep', {'bed': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_sleep', {'bed': None}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'no_bed'
    assert_message(result, 'bed', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_sleep_day(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='bed',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='red_bed[part=foot,facing=east,occupied=false]',
                ),
                BlockSpec(
                    key='bed_head',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='red_bed[part=head,facing=east,occupied=false]',
                ),
            ),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_sleep', {'bed': '$bed'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_sleep', {'bed': '$bed'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'not_night'
    assert_message(result, 'night')
    assert_field(scenario, result, 'slept', False)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_sleep_monster_nearby(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='bed',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='red_bed[part=foot,facing=east,occupied=false]',
                ),
                BlockSpec(
                    key='bed_head',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='red_bed[part=head,facing=east,occupied=false]',
                ),
            ),
            entities=(EntitySpec(
                key='monster',
                entity='zombie',
                offset=(
                    4.5,
                    0,
                    3.5,
                ),
                nbt='{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_monster"]}',
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_sleep', {'bed': '$bed'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_sleep', {'bed': '$bed'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'slept', False)
    assert_field(scenario, result, 'blocking_entity.entity_type', 'zombie')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='time_is_day',
            target='world',
            expected=False,
        ),
        WorldExpectation(
            kind='entity_exists',
            target='monster',
            expected=(
                'zombie',
                True,
            ),
            tolerance=0.8,
        ),
        WorldExpectation(
            kind='block',
            target='bed',
            expected='red_bed',
        ),
    ))


def test_sleep_occupied_bed(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='bed',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='red_bed[part=foot,facing=east,occupied=true]',
                ),
                BlockSpec(
                    key='bed_head',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='red_bed[part=head,facing=east,occupied=true]',
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_sleep', {'bed': '$bed'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_sleep', {'bed': '$bed'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'bed_occupied'
    assert_message(result, 'bed', 'occupied')
    assert_field(scenario, result, 'slept', False)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_sleep_obstructed_bed(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='bed',
                    offset=(
                        3,
                        0,
                        0,
                    ),
                    block='red_bed[part=foot,facing=east,occupied=false]',
                ),
                BlockSpec(
                    key='bed_head',
                    offset=(
                        4,
                        0,
                        0,
                    ),
                    block='red_bed[part=head,facing=east,occupied=false]',
                ),
                BlockSpec(
                    key='obstruction',
                    offset=(
                        4,
                        1,
                        0,
                    ),
                    block='bedrock',
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_sleep', {'bed': '$bed'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_sleep', {'bed': '$bed'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'bed_obstructed'
    assert_message(result, 'bed', 'obstructed')
    assert_field(scenario, result, 'slept', False)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (WorldExpectation(
        kind='block',
        target='obstruction',
        expected='bedrock',
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_sleep_bed_out_of_range(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='bed',
                    offset=(
                        20,
                        0,
                        0,
                    ),
                    block='red_bed[part=foot,facing=east,occupied=false]',
                ),
                BlockSpec(
                    key='bed_head',
                    offset=(
                        21,
                        0,
                        0,
                    ),
                    block='red_bed[part=head,facing=east,occupied=false]',
                ),
            ),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_sleep', {'bed': '$bed'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_sleep', {'bed': '$bed'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'out_of_range'
    assert_message(result, 'range')
    assert_field(scenario, result, 'slept', False)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_sleep_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_sleep', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_sleep_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_sleep', {'bed': {'not': 'the declared type'}}, timeout=660)
    assert_protocol_error(res, 'bed')



@pytest.mark.contract
def test_sleep_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_sleep', {'bed': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'bed')
