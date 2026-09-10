"""Live tests for minecraft_screenshot. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, Layout, assert_protocol_error, assert_response_image, call_mcp, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_screenshot_day(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_screenshot', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_screenshot', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)


def test_screenshot_night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_screenshot', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_screenshot', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)


def test_screenshot_rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_screenshot', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_screenshot', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)


def test_screenshot_water(live_test):
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
    res = call_mcp(scenario, 'minecraft_screenshot', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_screenshot', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)


def test_screenshot_cave(live_test):
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
    res = call_mcp(scenario, 'minecraft_screenshot', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_screenshot', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)



@pytest.mark.contract

@pytest.mark.smoke
def test_screenshot_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_screenshot', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_screenshot_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_screenshot', {'unexpected_argument': True}, timeout=660)
    assert_protocol_error(res, 'unexpected_argument')


def test_screenshot_day__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_screenshot', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_screenshot', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)


def test_screenshot_day__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_screenshot', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_screenshot', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)


def test_screenshot_day__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_screenshot', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_screenshot', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)


def test_screenshot_day__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_screenshot', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_screenshot', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)


def test_screenshot_day__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_screenshot', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_screenshot', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)


def test_screenshot_day__junk_inventory(live_test):
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
    res = call_mcp(scenario, 'minecraft_screenshot', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_screenshot', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)
