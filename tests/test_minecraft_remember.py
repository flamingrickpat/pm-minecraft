"""Live tests for minecraft_remember. Each test states its complete setup, MCP call, and assertions."""

import pytest

from tests.live_case import Layout, assert_field, assert_protocol_error, assert_response_image, assert_setup_success, call_mcp, parse_result, setup

@pytest.mark.smoke
def test_remember_world(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_remember', {'kind': 'world', 'markdown': 'TDD note for world: village at -32, 70, 48.'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_remember', {'kind': 'world', 'markdown': 'TDD note for world: village at -32, 70, 48.'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'kind', 'world')
    assert_field(scenario, result, 'appended_chars', 43)
    assert_response_image(res, result, False)


def test_remember_places(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_remember', {'kind': 'places', 'markdown': 'TDD note for places: village at -32, 70, 48.'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_remember', {'kind': 'places', 'markdown': 'TDD note for places: village at -32, 70, 48.'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'kind', 'places')
    assert_field(scenario, result, 'appended_chars', 44)
    assert_response_image(res, result, False)


def test_remember_routes(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_remember', {'kind': 'routes', 'markdown': 'TDD note for routes: village at -32, 70, 48.'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_remember', {'kind': 'routes', 'markdown': 'TDD note for routes: village at -32, 70, 48.'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'kind', 'routes')
    assert_field(scenario, result, 'appended_chars', 44)
    assert_response_image(res, result, False)


def test_remember_chests(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_remember', {'kind': 'chests', 'markdown': 'TDD note for chests: village at -32, 70, 48.'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_remember', {'kind': 'chests', 'markdown': 'TDD note for chests: village at -32, 70, 48.'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'kind', 'chests')
    assert_field(scenario, result, 'appended_chars', 44)
    assert_response_image(res, result, False)


def test_remember_failures(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_remember', {'kind': 'failures', 'markdown': 'TDD note for failures: village at -32, 70, 48.'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_remember', {'kind': 'failures', 'markdown': 'TDD note for failures: village at -32, 70, 48.'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'kind', 'failures')
    assert_field(scenario, result, 'appended_chars', 46)
    assert_response_image(res, result, False)


def test_remember_journal(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': 'TDD note for journal: village at -32, 70, 48.'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_remember', {'kind': 'journal', 'markdown': 'TDD note for journal: village at -32, 70, 48.'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'kind', 'journal')
    assert_field(scenario, result, 'appended_chars', 45)
    assert_response_image(res, result, False)


def test_remember_unicode(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': '基地在 -8, 64, 12. Straße. 🧭'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_remember', {'kind': 'journal', 'markdown': '基地在 -8, 64, 12. Straße. 🧭'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'appended_chars', 25)
    assert_response_image(res, result, False)


def test_remember_markdown(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': '| place | x | z |\n|---|---:|---:|\n| home | 4 | -9 |'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_remember', {'kind': 'journal', 'markdown': '| place | x | z |\n|---|---:|---:|\n| home | 4 | -9 |'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'appended_chars', 51)
    assert_response_image(res, result, False)


def test_remember_code(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': '```typescript\nawait api.observe();\n```'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_remember', {'kind': 'journal', 'markdown': '```typescript\nawait api.observe();\n```'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'appended_chars', 38)
    assert_response_image(res, result, False)


def test_remember_duplicate_append(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    setup_res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': 'same durable note'}, timeout=660)
    assert_setup_success(scenario, setup_res, 'minecraft_remember')
    res = call_mcp(scenario, 'minecraft_remember', {'kind': 'journal', 'markdown': 'same durable note'}, timeout=660)
    result = parse_result(scenario, res, 'minecraft_remember', {'kind': 'journal', 'markdown': 'same durable note'})
    assert result.ok is True
    assert result.reason is None
    assert_field(scenario, result, 'notes_in_file', 2)
    assert_field(scenario, result, 'appended_chars', 17)
    assert_response_image(res, result, False)



@pytest.mark.contract

@pytest.mark.smoke
def test_remember_invalid_arguments(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_remember', {}, timeout=660)
    assert_protocol_error(res, 'kind')



@pytest.mark.contract
def test_remember_wrong_argument_type(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_remember', {'kind': {'wrong': True}, 'markdown': 'home'}, timeout=660)
    assert_protocol_error(res, 'kind')



@pytest.mark.contract
def test_remember_invalid_literal(live_test):
    scenario = setup(
        live_test,
        layout=Layout(),
        require_body=False,
    )
    res = call_mcp(scenario, 'minecraft_remember', {'kind': 'not_a_valid_choice', 'markdown': 'home'}, timeout=660)
    assert_protocol_error(res, 'kind', 'not_a_valid_choice')
