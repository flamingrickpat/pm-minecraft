"""Live tests for minecraft_rotate. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Approx, Layout, WorldExpectation, assert_field, assert_protocol_error, assert_response_image, assert_setup_success, assert_world_state, call_mcp, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_rotate_absolute_south(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': 0, 'pitch_degrees': 0, 'absolute': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'yaw_degrees': 0, 'pitch_degrees': 0, 'absolute': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'camera.yaw', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_field(scenario, result, 'camera.pitch', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_rotate_absolute_west(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': 90, 'pitch_degrees': 0, 'absolute': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'yaw_degrees': 90, 'pitch_degrees': 0, 'absolute': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'camera.yaw', Approx(
        value=90,
        tolerance=0.5,
    ))
    assert_field(scenario, result, 'camera.pitch', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_rotate_absolute_north(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': 180, 'pitch_degrees': 0, 'absolute': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'yaw_degrees': 180, 'pitch_degrees': 0, 'absolute': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'camera.yaw', Approx(
        value=180,
        tolerance=0.5,
    ))
    assert_field(scenario, result, 'camera.pitch', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_rotate_absolute_east(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': 270, 'pitch_degrees': 0, 'absolute': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'yaw_degrees': 270, 'pitch_degrees': 0, 'absolute': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'camera.yaw', Approx(
        value=270,
        tolerance=0.5,
    ))
    assert_field(scenario, result, 'camera.pitch', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_rotate_straight_up(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_rotate', {'pitch_degrees': 90, 'absolute': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'pitch_degrees': 90, 'absolute': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'camera.yaw', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_field(scenario, result, 'camera.pitch', Approx(
        value=90,
        tolerance=0.5,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_rotate_straight_down(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_rotate', {'pitch_degrees': -90, 'absolute': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'pitch_degrees': -90, 'absolute': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'camera.yaw', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_field(scenario, result, 'camera.pitch', Approx(
        value=-90,
        tolerance=0.5,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_rotate_wrap_positive(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': 370, 'absolute': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'yaw_degrees': 370, 'absolute': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'camera.yaw', Approx(
        value=10,
        tolerance=0.5,
    ))
    assert_field(scenario, result, 'camera.pitch', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_rotate_relative_negative(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': -45, 'pitch_degrees': 10, 'absolute': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'yaw_degrees': -45, 'pitch_degrees': 10, 'absolute': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'camera.yaw', Approx(
        value=315,
        tolerance=0.5,
    ))
    assert_field(scenario, result, 'camera.pitch', Approx(
        value=10,
        tolerance=0.5,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_rotate_repeat_absolute_rotation(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    setup_res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': 90, 'pitch_degrees': 15, 'absolute': True}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_rotate')
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': 90, 'pitch_degrees': 15, 'absolute': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'yaw_degrees': 90, 'pitch_degrees': 15, 'absolute': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'yaw_delta', Approx(
        value=0,
        tolerance=0.1,
    ))
    assert_field(scenario, result, 'pitch_delta', Approx(
        value=0,
        tolerance=0.1,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
        WorldExpectation(
            kind='player_rotation',
            target='player',
            expected=(
                90,
                15,
            ),
            tolerance=1.5,
        ),
    ))



@pytest.mark.contract

@pytest.mark.smoke
def test_rotate_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_rotate', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_rotate_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': {'not': 'the declared type'}}, timeout=660)
    assert_protocol_error(res, 'yaw_degrees')



@pytest.mark.contract
def test_rotate_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'yaw_degrees')


def test_rotate_absolute_south__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': 0, 'pitch_degrees': 0, 'absolute': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'yaw_degrees': 0, 'pitch_degrees': 0, 'absolute': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'camera.yaw', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_field(scenario, result, 'camera.pitch', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_rotate_absolute_south__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': 0, 'pitch_degrees': 0, 'absolute': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'yaw_degrees': 0, 'pitch_degrees': 0, 'absolute': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'camera.yaw', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_field(scenario, result, 'camera.pitch', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_rotate_absolute_south__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': 0, 'pitch_degrees': 0, 'absolute': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'yaw_degrees': 0, 'pitch_degrees': 0, 'absolute': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'camera.yaw', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_field(scenario, result, 'camera.pitch', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_rotate_absolute_south__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': 0, 'pitch_degrees': 0, 'absolute': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'yaw_degrees': 0, 'pitch_degrees': 0, 'absolute': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'camera.yaw', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_field(scenario, result, 'camera.pitch', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_rotate_absolute_south__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': 0, 'pitch_degrees': 0, 'absolute': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'yaw_degrees': 0, 'pitch_degrees': 0, 'absolute': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'camera.yaw', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_field(scenario, result, 'camera.pitch', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_rotate_absolute_south__junk_inventory(live_test):
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
    res = call_mcp(scenario, 'minecraft_rotate', {'yaw_degrees': 0, 'pitch_degrees': 0, 'absolute': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_rotate', {'yaw_degrees': 0, 'pitch_degrees': 0, 'absolute': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'camera.yaw', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_field(scenario, result, 'camera.pitch', Approx(
        value=0,
        tolerance=0.5,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))
