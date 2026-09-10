"""Live tests for minecraft_add_waypoint. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Layout, Length, assert_field, assert_protocol_error, assert_response_image, assert_setup_success, call_mcp, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_add_waypoint_current(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'TDD current', 'position': None}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_add_waypoint', {'description': 'TDD current', 'position': None}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'waypoint.description', 'TDD current')
    assert_response_image(res, result, False)


def test_add_waypoint_positive(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'TDD positive', 'position': {'x': 24, 'y': 70, 'z': 32}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_add_waypoint', {'description': 'TDD positive', 'position': {'x': 24, 'y': 70, 'z': 32}})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'waypoint.description', 'TDD positive')
    assert_response_image(res, result, False)


def test_add_waypoint_negative(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'TDD negative', 'position': {'x': -24, 'y': -10, 'z': -32}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_add_waypoint', {'description': 'TDD negative', 'position': {'x': -24, 'y': -10, 'z': -32}})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'waypoint.description', 'TDD negative')
    assert_response_image(res, result, False)


def test_add_waypoint_world_top(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'TDD world_top', 'position': {'x': 0, 'y': 319, 'z': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_add_waypoint', {'description': 'TDD world_top', 'position': {'x': 0, 'y': 319, 'z': 0}})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'waypoint.description', 'TDD world_top')
    assert_response_image(res, result, False)


def test_add_waypoint_evicts_oldest_at_capacity(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'old point 0', 'position': {'x': 0, 'y': 70, 'z': 0}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'old point 1', 'position': {'x': 1, 'y': 70, 'z': 1}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'old point 2', 'position': {'x': 2, 'y': 70, 'z': 2}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'old point 3', 'position': {'x': 3, 'y': 70, 'z': 3}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'old point 4', 'position': {'x': 4, 'y': 70, 'z': 4}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'old point 5', 'position': {'x': 5, 'y': 70, 'z': 5}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'new point', 'position': {'x': 99, 'y': 70, 'z': 99}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_add_waypoint', {'description': 'new point', 'position': {'x': 99, 'y': 70, 'z': 99}})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'waypoints', Length(
        value=6,
    ))
    assert_field(scenario, result, 'evicted.description', 'old point 0')
    assert_field(scenario, result, 'waypoint.description', 'new point')
    assert_response_image(res, result, False)


def test_add_waypoint_duplicate_position_is_recorded(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'first marker', 'position': {'x': 4, 'y': 70, 'z': -8}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'second marker', 'position': {'x': 4, 'y': 70, 'z': -8}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_add_waypoint', {'description': 'second marker', 'position': {'x': 4, 'y': 70, 'z': -8}})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'waypoints', Length(
        value=2,
    ))
    assert_field(scenario, result, 'waypoints.0.description', 'first marker')
    assert_field(scenario, result, 'waypoints.1.description', 'second marker')
    assert_response_image(res, result, False)



@pytest.mark.contract

@pytest.mark.smoke
def test_add_waypoint_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'body test'}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_add_waypoint_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_add_waypoint', {}, timeout=660)
    assert_protocol_error(res, 'description')



@pytest.mark.contract
def test_add_waypoint_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'description')
