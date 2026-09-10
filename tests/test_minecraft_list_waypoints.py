"""Live tests for minecraft_list_waypoints. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Layout, Length, assert_field, assert_protocol_error, assert_response_image, assert_setup_success, call_mcp, parse_result, restart_mcp, setup

@pytest.mark.smoke
def test_list_waypoints_count_0(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_list_waypoints', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_list_waypoints', {})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'capacity', 6)
    assert_field(scenario, result, 'waypoints', Length(
        value=0,
    ))
    assert_response_image(res, result, False)


def test_list_waypoints_count_1(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'point 0', 'position': {'x': 0, 'y': 70, 'z': 0}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    res = call_mcp(scenario, 'minecraft_list_waypoints', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_list_waypoints', {})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'capacity', 6)
    assert_field(scenario, result, 'waypoints', Length(
        value=1,
    ))
    assert_response_image(res, result, False)


def test_list_waypoints_count_6(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'point 0', 'position': {'x': 0, 'y': 70, 'z': 0}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'point 1', 'position': {'x': 1, 'y': 70, 'z': -1}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'point 2', 'position': {'x': 2, 'y': 70, 'z': -2}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'point 3', 'position': {'x': 3, 'y': 70, 'z': -3}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'point 4', 'position': {'x': 4, 'y': 70, 'z': -4}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'point 5', 'position': {'x': 5, 'y': 70, 'z': -5}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    res = call_mcp(scenario, 'minecraft_list_waypoints', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_list_waypoints', {})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'capacity', 6)
    assert_field(scenario, result, 'waypoints', Length(
        value=6,
    ))
    assert_response_image(res, result, False)


def test_list_waypoints_persistent_after_restart(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    setup_res = call_mcp(scenario, 'minecraft_add_waypoint', {'description': 'durable point', 'position': {'x': 9, 'y': 70, 'z': -12}}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_add_waypoint')
    restart_mcp(scenario)
    res = call_mcp(scenario, 'minecraft_list_waypoints', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_list_waypoints', {})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'capacity', 6)
    assert_field(scenario, result, 'waypoints', Length(
        value=1,
    ))
    assert_field(scenario, result, 'waypoints.0.description', 'durable point')
    assert_response_image(res, result, False)



@pytest.mark.contract

@pytest.mark.smoke
def test_list_waypoints_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_list_waypoints', {'unexpected_argument': True}, timeout=660)
    assert_protocol_error(res, 'unexpected_argument')
