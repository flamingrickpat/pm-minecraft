"""Live tests for minecraft_look_at. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Layout, WorldExpectation, assert_failure_unchanged, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_look_at_ahead(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'target',
                (
                    0.5,
                    1.62,
                    8.5,
                ),
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_look_at', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_look_at', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_look_at_behind(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'target',
                (
                    0.5,
                    1.62,
                    -8.5,
                ),
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_look_at', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_look_at', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_look_at_above(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'target',
                (
                    0.5,
                    8.0,
                    0.5,
                ),
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_look_at', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_look_at', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_look_at_below(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'target',
                (
                    0.5,
                    -4.0,
                    0.5,
                ),
            ),),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_look_at', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_look_at', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))



@pytest.mark.smoke
def test_look_at_eye_position(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'target',
                (
                    0.5,
                    1.62,
                    0.5,
                ),
            ),),
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_look_at', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_look_at', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'same_position'
    assert_message(result, 'target', 'current')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.contract
def test_look_at_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_look_at', {'position': {'x': 0, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_look_at_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_look_at', {}, timeout=660)
    assert_protocol_error(res, 'position')



@pytest.mark.contract
def test_look_at_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_look_at', {'position': {'x': {'wrong': True}, 'y': 0, 'z': 0}}, timeout=660)
    assert_protocol_error(res, 'position')


def test_look_at_ahead__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'target',
                (
                    0.5,
                    1.62,
                    8.5,
                ),
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
    res = call_mcp(scenario, 'minecraft_look_at', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_look_at', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_look_at_ahead__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'target',
                (
                    0.5,
                    1.62,
                    8.5,
                ),
            ),),
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_look_at', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_look_at', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_look_at_ahead__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'target',
                (
                    0.5,
                    1.62,
                    8.5,
                ),
            ),),
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_look_at', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_look_at', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_look_at_ahead__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'target',
                (
                    0.5,
                    1.62,
                    8.5,
                ),
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_look_at', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_look_at', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_look_at_ahead__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'target',
                (
                    0.5,
                    1.62,
                    8.5,
                ),
            ),),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_look_at', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_look_at', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_look_at_ahead__junk_inventory(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'target',
                (
                    0.5,
                    1.62,
                    8.5,
                ),
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
    res = call_mcp(scenario, 'minecraft_look_at', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_look_at', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_look_at_eye_position__armor(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'target',
                (
                    0.5,
                    1.62,
                    0.5,
                ),
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_look_at', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_look_at', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'same_position'
    assert_message(result, 'target', 'current')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_look_at_eye_position__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'target',
                (
                    0.5,
                    1.62,
                    0.5,
                ),
            ),),
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_look_at', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_look_at', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'same_position'
    assert_message(result, 'target', 'current')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_look_at_eye_position__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            points=((
                'target',
                (
                    0.5,
                    1.62,
                    0.5,
                ),
            ),),
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_look_at', {'position': '$target'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_look_at', {'position': '$target'}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'same_position'
    assert_message(result, 'target', 'current')
    assert_response_image(res, result, result.image is not None)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))
    assert_failure_unchanged(scenario, failure_snapshot)
