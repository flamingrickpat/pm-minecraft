"""Live tests for minecraft_relative. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, Layout, assert_field, assert_protocol_error, assert_response_image, call_mcp, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_relative_zero(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 0}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 0}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cell', '$target')
    assert_response_image(res, result, False)


def test_relative_forward(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    0,
                    5,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_relative', {'forward': 5, 'right': 0, 'up': 0}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_relative', {'forward': 5, 'right': 0, 'up': 0}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cell', '$target')
    assert_response_image(res, result, False)


def test_relative_back(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    0,
                    -5,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_relative', {'forward': -5, 'right': 0, 'up': 0}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_relative', {'forward': -5, 'right': 0, 'up': 0}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cell', '$target')
    assert_response_image(res, result, False)


def test_relative_right(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    -5,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_relative', {'forward': 0, 'right': 5, 'up': 0}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_relative', {'forward': 0, 'right': 5, 'up': 0}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cell', '$target')
    assert_response_image(res, result, False)


def test_relative_left(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    5,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_relative', {'forward': 0, 'right': -5, 'up': 0}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_relative', {'forward': 0, 'right': -5, 'up': 0}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cell', '$target')
    assert_response_image(res, result, False)


def test_relative_up(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    5,
                    0,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 5}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 5}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cell', '$target')
    assert_response_image(res, result, False)


def test_relative_combined(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    2,
                    4,
                    3,
                ),
                block='air',
                name='air',
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_relative', {'forward': 3, 'right': -2, 'up': 4}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_relative', {'forward': 3, 'right': -2, 'up': 4}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cell', '$target')
    assert_response_image(res, result, False)



@pytest.mark.contract

@pytest.mark.smoke
def test_relative_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_relative', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_relative_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_relative', {'forward': {'not': 'the declared type'}}, timeout=660)
    assert_protocol_error(res, 'forward')



@pytest.mark.contract
def test_relative_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_relative', {'forward': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'forward')


def test_relative_zero__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
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
    res = call_mcp(scenario, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 0}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 0}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cell', '$target')
    assert_response_image(res, result, False)


def test_relative_zero__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 0}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 0}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cell', '$target')
    assert_response_image(res, result, False)


def test_relative_zero__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 0}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 0}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cell', '$target')
    assert_response_image(res, result, False)


def test_relative_zero__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 0}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 0}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cell', '$target')
    assert_response_image(res, result, False)


def test_relative_zero__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 0}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 0}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cell', '$target')
    assert_response_image(res, result, False)


def test_relative_zero__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='target',
                offset=(
                    0,
                    0,
                    0,
                ),
                block='air',
                name='air',
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
    res = call_mcp(scenario, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 0}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_relative', {'forward': 0, 'right': 0, 'up': 0}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'cell', '$target')
    assert_response_image(res, result, False)
