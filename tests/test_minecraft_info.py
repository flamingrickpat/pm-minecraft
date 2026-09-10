"""Live tests for minecraft_info. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import AtLeast, Layout, NonEmpty, assert_field, assert_protocol_error, assert_response_image, assert_setup_success, call_mcp, capture_truth, parse_result, restart_mcp, setup

@pytest.mark.smoke
def test_info_connected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_info', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_info', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'username', 'tdd_player')
    assert_field(scenario, result, 'connected', True)
    assert_field(scenario, result, 'spawned', True)
    assert_field(scenario, result, 'server', '127.0.0.1:12346')
    assert_field(scenario, result, 'schema_version', NonEmpty())
    assert_field(scenario, result, 'agent_home', '$agent_home')
    assert_field(scenario, result, 'uptime_seconds', AtLeast(
        value=0,
    ))
    assert_response_image(res, result, False)


def test_info_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_info', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_info', {})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'username', 'tdd_player')
    assert_field(scenario, result, 'connected', False)
    assert_field(scenario, result, 'spawned', False)
    assert_response_image(res, result, False)



@pytest.mark.slow
def test_info_after_death_and_respawn(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    setup_res = call_mcp(scenario, 'minecraft_suicide', {'reason': 'info death counter'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_suicide')
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_info', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_info', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'connected', True)
    assert_field(scenario, result, 'spawned', True)
    assert_field(scenario, result, 'death_count', 1)
    assert_response_image(res, result, False)


def test_info_after_mcp_restart(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    restart_mcp(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_info', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_info', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'connected', True)
    assert_field(scenario, result, 'spawned', True)
    assert_field(scenario, result, 'username', 'tdd_player')
    assert_response_image(res, result, False)



@pytest.mark.contract

@pytest.mark.smoke
def test_info_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_info', {'unexpected_argument': True}, timeout=660)
    assert_protocol_error(res, 'unexpected_argument')
