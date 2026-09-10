"""Live tests for minecraft_list_capabilities. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Layout, NonEmpty, assert_field, assert_protocol_error, assert_response_image, call_mcp, parse_result, restart_mcp, setup

@pytest.mark.contract

@pytest.mark.smoke
def test_list_capabilities_complete_registry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_list_capabilities', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_list_capabilities', {})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'skills', NonEmpty())
    assert_field(scenario, result, 'skills.0.name', NonEmpty())
    assert_field(scenario, result, 'skills.0.description', NonEmpty())
    assert_field(scenario, result, 'skills.0.path', NonEmpty())
    assert_response_image(res, result, False)



@pytest.mark.contract
def test_list_capabilities_registry_after_restart(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    restart_mcp(scenario)
    res = call_mcp(scenario, 'minecraft_list_capabilities', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_list_capabilities', {})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'skills', NonEmpty())
    assert_field(scenario, result, 'skills.0.name', NonEmpty())
    assert_field(scenario, result, 'skills.0.path', NonEmpty())
    assert_response_image(res, result, False)



@pytest.mark.contract

@pytest.mark.smoke
def test_list_capabilities_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_list_capabilities', {'unexpected_argument': True}, timeout=660)
    assert_protocol_error(res, 'unexpected_argument')
