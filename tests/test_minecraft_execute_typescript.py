"""Live tests for minecraft_execute_typescript. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Layout, WorldExpectation, assert_failure_unchanged, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_world_state, call_mcp, capture_failure_snapshot, capture_truth, parse_result, setup

@pytest.mark.slow

@pytest.mark.smoke
def test_execute_typescript_success(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/success.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/success.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'skill_path', 'skills/success.ts')
    assert_field(scenario, result, 'postcondition.passed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))



@pytest.mark.slow
def test_execute_typescript_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/arguments.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/arguments.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'skill_path', 'skills/arguments.ts')
    assert_field(scenario, result, 'postcondition.passed', True)
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))



@pytest.mark.slow

@pytest.mark.smoke
def test_execute_typescript_false_postcondition(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/success.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/success.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'postcondition_failed'
    assert_message(result, 'postcondition')
    assert_field(scenario, result, 'skill_path', 'skills/success.ts')
    assert_field(scenario, result, 'postcondition.passed', False)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.slow
def test_execute_typescript_throws(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/throws.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/throws.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'typescript_error'
    assert_message(result, 'typescript', 'error')
    assert_field(scenario, result, 'skill_path', 'skills/throws.ts')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.slow

@pytest.mark.security
def test_execute_typescript_filesystem_denied(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/filesystem.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/filesystem.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/filesystem.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.slow

@pytest.mark.security
def test_execute_typescript_network_denied(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/network.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/network.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/network.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.slow

@pytest.mark.security
def test_execute_typescript_command_denied(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/command.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/command.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/command.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.slow

@pytest.mark.security
def test_execute_typescript_teleport_denied(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/teleport.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/teleport.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/teleport.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.slow

@pytest.mark.security
def test_execute_typescript_give_item_denied(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/give_item.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/give_item.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/give_item.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_missing_skill(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'skills/missing.ts', 'postcondition': {'position_changed_min': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'skills/missing.ts', 'postcondition': {'position_changed_min': 0}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'skill_not_found'
    assert_message(result, 'skill', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.slow

@pytest.mark.security
def test_execute_typescript_absolute_path_denied(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'C:/Windows/win.ini', 'postcondition': {'position_changed_min': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'C:/Windows/win.ini', 'postcondition': {'position_changed_min': 0}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'C:/Windows/win.ini')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.slow

@pytest.mark.security
def test_execute_typescript_parent_path_denied(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'skills/../../server.log', 'postcondition': {'position_changed_min': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'skills/../../server.log', 'postcondition': {'position_changed_min': 0}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/../../server.log')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)



@pytest.mark.slow
def test_execute_typescript_fixed_timeout(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'skills/forever.ts', 'postcondition': {'position_changed_min': 10000}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'skills/forever.ts', 'postcondition': {'position_changed_min': 10000}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'timeout'
    assert_message(result, 'time')
    assert_field(scenario, result, 'skill_path', 'skills/forever.ts')
    assert_response_image(res, result, False)



@pytest.mark.contract
def test_execute_typescript_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'missing.ts', 'postcondition': {}}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_execute_typescript_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_execute_typescript', {}, timeout=660)
    assert_protocol_error(res, 'path')



@pytest.mark.contract
def test_execute_typescript_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': {'wrong': True}, 'postcondition': {}}, timeout=660)
    assert_protocol_error(res, 'path')


def test_execute_typescript_false_postcondition__armor(live_test):
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/success.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/success.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'postcondition_failed'
    assert_message(result, 'postcondition')
    assert_field(scenario, result, 'skill_path', 'skills/success.ts')
    assert_field(scenario, result, 'postcondition.passed', False)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_false_postcondition__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/success.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/success.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'postcondition_failed'
    assert_message(result, 'postcondition')
    assert_field(scenario, result, 'skill_path', 'skills/success.ts')
    assert_field(scenario, result, 'postcondition.passed', False)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_false_postcondition__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/success.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/success.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'postcondition_failed'
    assert_message(result, 'postcondition')
    assert_field(scenario, result, 'skill_path', 'skills/success.ts')
    assert_field(scenario, result, 'postcondition.passed', False)
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_throws__armor(live_test):
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/throws.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/throws.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'typescript_error'
    assert_message(result, 'typescript', 'error')
    assert_field(scenario, result, 'skill_path', 'skills/throws.ts')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_throws__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/throws.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/throws.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'typescript_error'
    assert_message(result, 'typescript', 'error')
    assert_field(scenario, result, 'skill_path', 'skills/throws.ts')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_throws__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/throws.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/throws.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'typescript_error'
    assert_message(result, 'typescript', 'error')
    assert_field(scenario, result, 'skill_path', 'skills/throws.ts')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_filesystem_denied__armor(live_test):
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/filesystem.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/filesystem.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/filesystem.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_filesystem_denied__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/filesystem.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/filesystem.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/filesystem.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_filesystem_denied__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/filesystem.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/filesystem.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/filesystem.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_network_denied__armor(live_test):
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/network.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/network.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/network.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_network_denied__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/network.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/network.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/network.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_network_denied__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/network.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/network.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/network.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_command_denied__armor(live_test):
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/command.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/command.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/command.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_command_denied__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/command.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/command.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/command.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_command_denied__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/command.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/command.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/command.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_teleport_denied__armor(live_test):
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/teleport.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/teleport.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/teleport.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_teleport_denied__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/teleport.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/teleport.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/teleport.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_teleport_denied__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/teleport.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/teleport.ts',
        'postcondition': {'position_changed_min': 0},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/teleport.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_give_item_denied__armor(live_test):
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/give_item.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/give_item.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/give_item.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_give_item_denied__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/give_item.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/give_item.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/give_item.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_give_item_denied__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {
        'path': 'skills/give_item.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {
        'path': 'skills/give_item.ts',
        'postcondition': {'inventory_min': {'diamond': 64}},
        'arguments': {'steps': 2},
    }, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/give_item.ts')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_missing_skill__armor(live_test):
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'skills/missing.ts', 'postcondition': {'position_changed_min': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'skills/missing.ts', 'postcondition': {'position_changed_min': 0}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'skill_not_found'
    assert_message(result, 'skill', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_missing_skill__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'skills/missing.ts', 'postcondition': {'position_changed_min': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'skills/missing.ts', 'postcondition': {'position_changed_min': 0}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'skill_not_found'
    assert_message(result, 'skill', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_missing_skill__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'skills/missing.ts', 'postcondition': {'position_changed_min': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'skills/missing.ts', 'postcondition': {'position_changed_min': 0}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'skill_not_found'
    assert_message(result, 'skill', 'not found')
    assert_response_image(res, result, False)
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_absolute_path_denied__armor(live_test):
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'C:/Windows/win.ini', 'postcondition': {'position_changed_min': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'C:/Windows/win.ini', 'postcondition': {'position_changed_min': 0}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'C:/Windows/win.ini')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_absolute_path_denied__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'C:/Windows/win.ini', 'postcondition': {'position_changed_min': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'C:/Windows/win.ini', 'postcondition': {'position_changed_min': 0}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'C:/Windows/win.ini')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_absolute_path_denied__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'C:/Windows/win.ini', 'postcondition': {'position_changed_min': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'C:/Windows/win.ini', 'postcondition': {'position_changed_min': 0}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'C:/Windows/win.ini')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_parent_path_denied__armor(live_test):
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
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'skills/../../server.log', 'postcondition': {'position_changed_min': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'skills/../../server.log', 'postcondition': {'position_changed_min': 0}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/../../server.log')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_parent_path_denied__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'skills/../../server.log', 'postcondition': {'position_changed_min': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'skills/../../server.log', 'postcondition': {'position_changed_min': 0}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/../../server.log')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_parent_path_denied__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    failure_snapshot = capture_failure_snapshot(scenario)
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'skills/../../server.log', 'postcondition': {'position_changed_min': 0}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'skills/../../server.log', 'postcondition': {'position_changed_min': 0}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'access_denied'
    assert_message(result, 'access', 'denied')
    assert_field(scenario, result, 'skill_path', 'skills/../../server.log')
    assert_response_image(res, result, False)
    assert_world_state(scenario, (
        WorldExpectation(
            kind='inventory',
            target='diamond',
            expected=0,
        ),
        WorldExpectation(
            kind='player_near',
            target='player',
            expected=None,
            tolerance=0.05,
        ),
    ))
    assert_failure_unchanged(scenario, failure_snapshot)


def test_execute_typescript_fixed_timeout__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'skills/forever.ts', 'postcondition': {'position_changed_min': 10000}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'skills/forever.ts', 'postcondition': {'position_changed_min': 10000}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'timeout'
    assert_message(result, 'time')
    assert_field(scenario, result, 'skill_path', 'skills/forever.ts')
    assert_response_image(res, result, False)


def test_execute_typescript_fixed_timeout__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'skills/forever.ts', 'postcondition': {'position_changed_min': 10000}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'skills/forever.ts', 'postcondition': {'position_changed_min': 10000}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'timeout'
    assert_message(result, 'time')
    assert_field(scenario, result, 'skill_path', 'skills/forever.ts')
    assert_response_image(res, result, False)


def test_execute_typescript_fixed_timeout__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_execute_typescript', {'path': 'skills/forever.ts', 'postcondition': {'position_changed_min': 10000}}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_execute_typescript', {'path': 'skills/forever.ts', 'postcondition': {'position_changed_min': 10000}}, truth_before=truth_before)
    assert result.ok is False
    assert result.reason == 'timeout'
    assert_message(result, 'time')
    assert_field(scenario, result, 'skill_path', 'skills/forever.ts')
    assert_response_image(res, result, False)
