"""Live tests for minecraft_distance. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Approx, Layout, assert_field, assert_protocol_error, assert_response_image, call_mcp, parse_result, setup

@pytest.mark.smoke
def test_distance_same_point(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_distance', {'a': {'x': 0, 'y': 0, 'z': 0}, 'b': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_distance', {'a': {'x': 0, 'y': 0, 'z': 0}, 'b': {'x': 0, 'y': 0, 'z': 0}})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'distance', Approx(
        value=0.0,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'manhattan', Approx(
        value=0.0,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dx', Approx(
        value=0,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dy', Approx(
        value=0,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dz', Approx(
        value=0,
        tolerance=1e-06,
    ))
    assert_response_image(res, result, False)


def test_distance_axis(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_distance', {'a': {'x': 0, 'y': 0, 'z': 0}, 'b': {'x': 7, 'y': 0, 'z': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_distance', {'a': {'x': 0, 'y': 0, 'z': 0}, 'b': {'x': 7, 'y': 0, 'z': 0}})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'distance', Approx(
        value=7.0,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'manhattan', Approx(
        value=7.0,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dx', Approx(
        value=7,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dy', Approx(
        value=0,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dz', Approx(
        value=0,
        tolerance=1e-06,
    ))
    assert_response_image(res, result, False)


def test_distance_three_four_five(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_distance', {'a': {'x': 0, 'y': 0, 'z': 0}, 'b': {'x': 3, 'y': 4, 'z': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_distance', {'a': {'x': 0, 'y': 0, 'z': 0}, 'b': {'x': 3, 'y': 4, 'z': 0}})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'distance', Approx(
        value=5.0,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'manhattan', Approx(
        value=7.0,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dx', Approx(
        value=3,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dy', Approx(
        value=4,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dz', Approx(
        value=0,
        tolerance=1e-06,
    ))
    assert_response_image(res, result, False)


def test_distance_negative(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_distance', {'a': {'x': -5, 'y': -2, 'z': -3}, 'b': {'x': 1, 'y': 2, 'z': 3}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_distance', {'a': {'x': -5, 'y': -2, 'z': -3}, 'b': {'x': 1, 'y': 2, 'z': 3}})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'distance', Approx(
        value=9.38083151964686,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'manhattan', Approx(
        value=16.0,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dx', Approx(
        value=6,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dy', Approx(
        value=4,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dz', Approx(
        value=6,
        tolerance=1e-06,
    ))
    assert_response_image(res, result, False)


def test_distance_fractional(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_distance', {'a': {'x': 0.25, 'y': 1.5, 'z': -2.75}, 'b': {'x': 1.25, 'y': 3.5, 'z': 0.25}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_distance', {'a': {'x': 0.25, 'y': 1.5, 'z': -2.75}, 'b': {'x': 1.25, 'y': 3.5, 'z': 0.25}})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'distance', Approx(
        value=3.7416573867739413,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'manhattan', Approx(
        value=6.0,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dx', Approx(
        value=1.0,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dy', Approx(
        value=2.0,
        tolerance=1e-06,
    ))
    assert_field(scenario, result, 'dz', Approx(
        value=3.0,
        tolerance=1e-06,
    ))
    assert_response_image(res, result, False)



@pytest.mark.contract

@pytest.mark.smoke
def test_distance_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_distance', {}, timeout=660)
    assert_protocol_error(res, 'a')



@pytest.mark.contract
def test_distance_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_distance', {'a': {'x': {'wrong': True}, 'y': 0, 'z': 0}, 'b': {'x': 1, 'y': 1, 'z': 1}}, timeout=660)
    assert_protocol_error(res, 'a')
