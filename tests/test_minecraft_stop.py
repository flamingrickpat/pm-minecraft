"""Live tests for minecraft_stop. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, DuringAction, Layout, assert_background_stopped, assert_field, assert_protocol_error, assert_response_image, assert_setup_success, begin_mcp_call, call_mcp, capture_truth, finish_mcp_call, parse_result, setup, wait_for_action

@pytest.mark.smoke
def test_stop_idle_command(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_stop', {'scope': 'command'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_stop', {'scope': 'command'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'scope', 'command')
    assert_field(scenario, result, 'stopped_command', None)
    assert_field(scenario, result, 'stopped_skill', None)
    assert_response_image(res, result, False)


def test_stop_idle_skill(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_stop', {'scope': 'skill'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_stop', {'scope': 'skill'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'scope', 'skill')
    assert_field(scenario, result, 'stopped_command', None)
    assert_field(scenario, result, 'stopped_skill', None)
    assert_response_image(res, result, False)


def test_stop_idle_both(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_stop', {'scope': 'both'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_stop', {'scope': 'both'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'scope', 'both')
    assert_field(scenario, result, 'stopped_command', None)
    assert_field(scenario, result, 'stopped_skill', None)
    assert_response_image(res, result, False)


def test_stop_second_idle_stop(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    setup_res = call_mcp(scenario, 'minecraft_stop', {'scope': 'both'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_stop')
    res = call_mcp(scenario, 'minecraft_stop', {'scope': 'both'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_stop', {'scope': 'both'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'scope', 'both')
    assert_field(scenario, result, 'stopped_command', None)
    assert_field(scenario, result, 'stopped_skill', None)
    assert_response_image(res, result, False)



@pytest.mark.contract

@pytest.mark.smoke
def test_stop_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_stop', {'scope': {'not': 'the declared type'}}, timeout=660)
    assert_protocol_error(res, 'scope')



@pytest.mark.contract
def test_stop_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_stop', {'scope': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'scope')



@pytest.mark.contract
def test_stop_invalid_literal(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_stop', {'scope': 'not_a_valid_choice'}, timeout=660)
    assert_protocol_error(res, 'scope', 'not_a_valid_choice')



@pytest.mark.slow
def test_stop_active_walk(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='destination',
                offset=(
                    30,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    background = begin_mcp_call(scenario, 'minecraft_walk_to_exact', {'x': '$destination.x', 'y': '$destination.y', 'z': '$destination.z'}, timeout=660)
    wait_for_action(scenario, DuringAction('player_moved', 'player', ''))
    res = call_mcp(scenario, 'minecraft_stop', {'scope': 'command'}, timeout=660)
    assert_background_stopped(finish_mcp_call(background, timeout=660), 'minecraft_walk_to_exact', 'stopped')
    result = parse_result(scenario, res, 'minecraft_stop', {'scope': 'command'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'scope', 'command')
    assert_field(scenario, result, 'stopped_command', 'minecraft_walk_to_exact')
    assert_response_image(res, result, False)



@pytest.mark.slow
def test_stop_active_skill(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    background = begin_mcp_call(scenario, 'minecraft_execute_typescript', {'path': 'skills/forever.ts', 'postcondition': {'position_changed_min': 10000}}, timeout=660)
    wait_for_action(scenario, DuringAction('player_moved', 'player', ''))
    res = call_mcp(scenario, 'minecraft_stop', {'scope': 'skill'}, timeout=660)
    assert_background_stopped(finish_mcp_call(background, timeout=660), 'minecraft_execute_typescript', 'stopped')
    result = parse_result(scenario, res, 'minecraft_stop', {'scope': 'skill'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'scope', 'skill')
    assert_field(scenario, result, 'stopped_skill', 'skills/forever.ts')
    assert_response_image(res, result, False)
