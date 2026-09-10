"""Live tests for minecraft_recall. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Layout, Length, NonEmpty, assert_field, assert_message, assert_protocol_error, assert_response_image, assert_setup_success, call_mcp, parse_result, restart_mcp, setup

@pytest.mark.smoke
def test_recall_empty(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_recall', {'pattern': 'village'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recall', {'pattern': 'village'})
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)



@pytest.mark.smoke
def test_recall_unicode(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'places', 'markdown': '基地 village at -32, 70, 48.'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    res = call_mcp(scenario, 'minecraft_recall', {'pattern': '基地'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recall', {'pattern': '基地'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hits', NonEmpty())
    assert_field(scenario, result, 'total_notes', 1)
    assert_response_image(res, result, False)


def test_recall_coordinates(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'places', 'markdown': '基地 village at -32, 70, 48.'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    res = call_mcp(scenario, 'minecraft_recall', {'pattern': '-32'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recall', {'pattern': '-32'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hits', NonEmpty())
    assert_field(scenario, result, 'total_notes', 1)
    assert_response_image(res, result, False)


def test_recall_partial(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'places', 'markdown': '基地 village at -32, 70, 48.'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    res = call_mcp(scenario, 'minecraft_recall', {'pattern': 'vill'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recall', {'pattern': 'vill'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hits', NonEmpty())
    assert_field(scenario, result, 'total_notes', 1)
    assert_response_image(res, result, False)


def test_recall_no_match(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_recall', {'pattern': 'nonexistent-memory-token'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recall', {'pattern': 'nonexistent-memory-token'})
    assert result.ok is False
    assert result.reason == 'not_found'
    assert_message(result, 'not found')
    assert_response_image(res, result, False)


def test_recall_result_limit_newest_first(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': 'recall-limit-note-00 shared-limit-token'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': 'recall-limit-note-01 shared-limit-token'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': 'recall-limit-note-02 shared-limit-token'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': 'recall-limit-note-03 shared-limit-token'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': 'recall-limit-note-04 shared-limit-token'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': 'recall-limit-note-05 shared-limit-token'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': 'recall-limit-note-06 shared-limit-token'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': 'recall-limit-note-07 shared-limit-token'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': 'recall-limit-note-08 shared-limit-token'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': 'recall-limit-note-09 shared-limit-token'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': 'recall-limit-note-10 shared-limit-token'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    res = call_mcp(scenario, 'minecraft_recall', {'pattern': '*shared-limit-token*'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recall', {'pattern': '*shared-limit-token*'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hits', Length(
        value=10,
    ))
    assert_field(scenario, result, 'hits.0.markdown', 'recall-limit-note-10 shared-limit-token')
    assert_field(scenario, result, 'hits.9.markdown', 'recall-limit-note-01 shared-limit-token')
    assert_field(scenario, result, 'total_notes', 11)
    assert_response_image(res, result, False)


def test_recall_persistent_after_restart(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'places', 'markdown': 'durable-base at 9, 70, -12'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    restart_mcp(scenario)
    res = call_mcp(scenario, 'minecraft_recall', {'pattern': 'durable-base'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_recall', {'pattern': 'durable-base'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'hits', Length(
        value=1,
    ))
    assert_field(scenario, result, 'hits.0.markdown', 'durable-base at 9, 70, -12')
    assert_field(scenario, result, 'total_notes', 1)
    assert_response_image(res, result, False)



@pytest.mark.contract
def test_recall_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_recall', {}, timeout=660)
    assert_protocol_error(res, 'pattern')



@pytest.mark.contract
def test_recall_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_recall', {'pattern': {'wrong': True}}, timeout=660)
    assert_protocol_error(res, 'pattern')
