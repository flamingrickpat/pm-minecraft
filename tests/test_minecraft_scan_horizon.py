"""Live tests for minecraft_scan_horizon. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import BlockSpec, Includes, Layout, Length, NonEmpty, assert_field, assert_protocol_error, assert_response_image, call_mcp, capture_truth, parse_result, setup

@pytest.mark.smoke
def test_scan_horizon_empty_horizon(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_scan_horizon', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_scan_horizon', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'rays', Length(
        value=72,
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=15,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=0,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=-15,
        key='pitch',
    ))
    assert_field(scenario, result, 'origin.x', '$player.x')
    assert_response_image(res, result, False)


def test_scan_horizon_village_evidence(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='bell',
                    offset=(
                        20,
                        1,
                        0,
                    ),
                    block='bell[attachment=floor,facing=north]',
                ),
                BlockSpec(
                    key='hay',
                    offset=(
                        21,
                        0,
                        0,
                    ),
                    block='hay_block',
                ),
                BlockSpec(
                    key='bed',
                    offset=(
                        20,
                        0,
                        2,
                    ),
                    block='red_bed[part=foot,facing=south]',
                ),
                BlockSpec(
                    key='path',
                    offset=(
                        19,
                        -1,
                        0,
                    ),
                    block='dirt_path',
                ),
                BlockSpec(
                    key='roof',
                    offset=(
                        20,
                        3,
                        0,
                    ),
                    block='oak_stairs[facing=east]',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_scan_horizon', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_scan_horizon', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'rays', Length(
        value=72,
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=15,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=0,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=-15,
        key='pitch',
    ))
    assert_field(scenario, result, 'origin.x', '$player.x')
    assert_field(scenario, result, 'landmarks', NonEmpty())
    assert_field(scenario, result, 'landmarks.0.kind', 'possible_village')
    assert_response_image(res, result, False)


def test_scan_horizon_village_evidence_image(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='bell',
                    offset=(
                        20,
                        1,
                        0,
                    ),
                    block='bell[attachment=floor,facing=north]',
                ),
                BlockSpec(
                    key='hay',
                    offset=(
                        21,
                        0,
                        0,
                    ),
                    block='hay_block',
                ),
                BlockSpec(
                    key='bed',
                    offset=(
                        20,
                        0,
                        2,
                    ),
                    block='red_bed[part=foot,facing=south]',
                ),
                BlockSpec(
                    key='path',
                    offset=(
                        19,
                        -1,
                        0,
                    ),
                    block='dirt_path',
                ),
                BlockSpec(
                    key='roof',
                    offset=(
                        20,
                        3,
                        0,
                    ),
                    block='oak_stairs[facing=east]',
                ),
            ),
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_scan_horizon', {'include_image': True}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_scan_horizon', {'include_image': True}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'rays', Length(
        value=72,
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=15,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=0,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=-15,
        key='pitch',
    ))
    assert_field(scenario, result, 'origin.x', '$player.x')
    assert_field(scenario, result, 'landmarks', NonEmpty())
    assert_field(scenario, result, 'landmarks.0.kind', 'possible_village')
    assert_response_image(res, result, True)


def test_scan_horizon_rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(
                BlockSpec(
                    key='bell',
                    offset=(
                        20,
                        1,
                        0,
                    ),
                    block='bell[attachment=floor,facing=north]',
                ),
                BlockSpec(
                    key='hay',
                    offset=(
                        21,
                        0,
                        0,
                    ),
                    block='hay_block',
                ),
                BlockSpec(
                    key='bed',
                    offset=(
                        20,
                        0,
                        2,
                    ),
                    block='red_bed[part=foot,facing=south]',
                ),
                BlockSpec(
                    key='path',
                    offset=(
                        19,
                        -1,
                        0,
                    ),
                    block='dirt_path',
                ),
                BlockSpec(
                    key='roof',
                    offset=(
                        20,
                        3,
                        0,
                    ),
                    block='oak_stairs[facing=east]',
                ),
            ),
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_scan_horizon', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_scan_horizon', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'rays', Length(
        value=72,
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=15,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=0,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=-15,
        key='pitch',
    ))
    assert_field(scenario, result, 'origin.x', '$player.x')
    assert_response_image(res, result, False)


def test_scan_horizon_night_light(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            blocks=(BlockSpec(
                key='torch',
                offset=(
                    18,
                    1,
                    0,
                ),
                block='torch',
            ),),
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_scan_horizon', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_scan_horizon', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'rays', Length(
        value=72,
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=15,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=0,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=-15,
        key='pitch',
    ))
    assert_field(scenario, result, 'origin.x', '$player.x')
    assert_response_image(res, result, False)



@pytest.mark.contract

@pytest.mark.smoke
def test_scan_horizon_player_body_disconnected(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        disconnect_body=True,
    )
    res = call_mcp(scenario, 'minecraft_scan_horizon', {}, timeout=660)
    assert_protocol_error(res, 'player body', 'not available')



@pytest.mark.contract
def test_scan_horizon_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_scan_horizon', {'include_image': {'not': 'the declared type'}}, timeout=660)
    assert_protocol_error(res, 'include_image')



@pytest.mark.contract
def test_scan_horizon_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_scan_horizon', {'include_image': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'include_image')


def test_scan_horizon_empty_horizon__armor(live_test):
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
    res = call_mcp(scenario, 'minecraft_scan_horizon', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_scan_horizon', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'rays', Length(
        value=72,
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=15,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=0,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=-15,
        key='pitch',
    ))
    assert_field(scenario, result, 'origin.x', '$player.x')
    assert_response_image(res, result, False)


def test_scan_horizon_empty_horizon__damaged(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            food=3,
            health=6.0,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_scan_horizon', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_scan_horizon', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'rays', Length(
        value=72,
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=15,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=0,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=-15,
        key='pitch',
    ))
    assert_field(scenario, result, 'origin.x', '$player.x')
    assert_response_image(res, result, False)


def test_scan_horizon_empty_horizon__hungry(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            food=3,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_scan_horizon', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_scan_horizon', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'rays', Length(
        value=72,
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=15,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=0,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=-15,
        key='pitch',
    ))
    assert_field(scenario, result, 'origin.x', '$player.x')
    assert_response_image(res, result, False)


def test_scan_horizon_empty_horizon__night(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            time=18000,
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_scan_horizon', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_scan_horizon', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'rays', Length(
        value=72,
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=15,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=0,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=-15,
        key='pitch',
    ))
    assert_field(scenario, result, 'origin.x', '$player.x')
    assert_response_image(res, result, False)


def test_scan_horizon_empty_horizon__rain(live_test):
    scenario = setup(
        live_test,
        layout=Layout(
            weather='rain',
        ),
    )
    truth_before = capture_truth(scenario)
    res = call_mcp(scenario, 'minecraft_scan_horizon', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_scan_horizon', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'rays', Length(
        value=72,
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=15,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=0,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=-15,
        key='pitch',
    ))
    assert_field(scenario, result, 'origin.x', '$player.x')
    assert_response_image(res, result, False)


def test_scan_horizon_empty_horizon__junk_inventory(live_test):
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
    res = call_mcp(scenario, 'minecraft_scan_horizon', {'include_image': False}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_scan_horizon', {'include_image': False}, truth_before=truth_before)
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'rays', Length(
        value=72,
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=15,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=0,
        key='pitch',
    ))
    assert_field(scenario, result, 'rays', Includes(
        value=-15,
        key='pitch',
    ))
    assert_field(scenario, result, 'origin.x', '$player.x')
    assert_response_image(res, result, False)
