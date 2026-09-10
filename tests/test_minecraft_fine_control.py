"""Live tests for minecraft_fine_control. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import AtLeast, Layout, WorldExpectation, assert_field, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_fine_control_forward(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fine_control', {'forward': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'forward': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': True,
        'back': False,
        'left': False,
        'right': False,
        'jump': False,
        'sneak': False,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_distance_from',
        target='player',
        expected=AtLeast(
            value=0.01,
        ),
    ),))


def test_fine_control_back(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fine_control', {'back': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'back': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': False,
        'back': True,
        'left': False,
        'right': False,
        'jump': False,
        'sneak': False,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_distance_from',
        target='player',
        expected=AtLeast(
            value=0.01,
        ),
    ),))


def test_fine_control_left(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fine_control', {'left': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'left': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': False,
        'back': False,
        'left': True,
        'right': False,
        'jump': False,
        'sneak': False,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_distance_from',
        target='player',
        expected=AtLeast(
            value=0.01,
        ),
    ),))


def test_fine_control_right(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fine_control', {'right': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'right': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': False,
        'back': False,
        'left': False,
        'right': True,
        'jump': False,
        'sneak': False,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_distance_from',
        target='player',
        expected=AtLeast(
            value=0.01,
        ),
    ),))


def test_fine_control_jump(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fine_control', {'jump': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'jump': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': False,
        'back': False,
        'left': False,
        'right': False,
        'jump': True,
        'sneak': False,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_distance_from',
        target='player',
        expected=AtLeast(
            value=0.01,
        ),
    ),))


def test_fine_control_sneak(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fine_control', {'sneak': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'sneak': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': False,
        'back': False,
        'left': False,
        'right': False,
        'jump': False,
        'sneak': True,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_fine_control_sprint_forward(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fine_control', {'forward': True, 'sprint': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'forward': True, 'sprint': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': True,
        'back': False,
        'left': False,
        'right': False,
        'jump': False,
        'sneak': False,
        'sprint': True,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_distance_from',
        target='player',
        expected=AtLeast(
            value=0.01,
        ),
    ),))


def test_fine_control_diagonal(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fine_control', {'forward': True, 'right': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'forward': True, 'right': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': True,
        'back': False,
        'left': False,
        'right': True,
        'jump': False,
        'sneak': False,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_distance_from',
        target='player',
        expected=AtLeast(
            value=0.01,
        ),
    ),))


def test_fine_control_conflicting(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fine_control', {'forward': True, 'back': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'forward': True, 'back': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': True,
        'back': True,
        'left': False,
        'right': False,
        'jump': False,
        'sneak': False,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))


def test_fine_control_none(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fine_control', {}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': False,
        'back': False,
        'left': False,
        'right': False,
        'jump': False,
        'sneak': False,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_near',
        target='player',
        expected=None,
        tolerance=0.05,
    ),))



@pytest.mark.contract

@pytest.mark.smoke
def test_fine_control_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_fine_control', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_fine_control_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_fine_control', {'forward': {'not': 'the declared type'}}, timeout=660)
    assert_protocol_error(res, 'forward')



@pytest.mark.contract
def test_fine_control_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_fine_control', {'forward': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'forward')


def test_fine_control_forward__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_fine_control', {'forward': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'forward': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': True,
        'back': False,
        'left': False,
        'right': False,
        'jump': False,
        'sneak': False,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_distance_from',
        target='player',
        expected=AtLeast(
            value=0.01,
        ),
    ),))


def test_fine_control_forward__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fine_control', {'forward': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'forward': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': True,
        'back': False,
        'left': False,
        'right': False,
        'jump': False,
        'sneak': False,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_distance_from',
        target='player',
        expected=AtLeast(
            value=0.01,
        ),
    ),))


def test_fine_control_forward__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fine_control', {'forward': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'forward': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': True,
        'back': False,
        'left': False,
        'right': False,
        'jump': False,
        'sneak': False,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_distance_from',
        target='player',
        expected=AtLeast(
            value=0.01,
        ),
    ),))


def test_fine_control_forward__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fine_control', {'forward': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'forward': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': True,
        'back': False,
        'left': False,
        'right': False,
        'jump': False,
        'sneak': False,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_distance_from',
        target='player',
        expected=AtLeast(
            value=0.01,
        ),
    ),))


def test_fine_control_forward__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_fine_control', {'forward': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'forward': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': True,
        'back': False,
        'left': False,
        'right': False,
        'jump': False,
        'sneak': False,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_distance_from',
        target='player',
        expected=AtLeast(
            value=0.01,
        ),
    ),))


def test_fine_control_forward__junk_inventory(live_test):
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
    res = call_mcp(scenario, 'minecraft_fine_control', {'forward': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_fine_control', {'forward': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'controls', {
        'forward': True,
        'back': False,
        'left': False,
        'right': False,
        'jump': False,
        'sneak': False,
        'sprint': False,
    })
    assert_field(scenario, result, 'duration_ms', AtLeast(
        value=250,
    ))
    assert_response_image(res, result, True)
    assert_world_state(scenario, (WorldExpectation(
        kind='player_distance_from',
        target='player',
        expected=AtLeast(
            value=0.01,
        ),
    ),))
