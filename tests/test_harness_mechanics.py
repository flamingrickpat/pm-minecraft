"""Prove the harness plumbing that behavior cases rely on.

The behavior cases stay red until the live MCP backend lands. Their
orchestration mechanics (concurrent tool calls, during-action waits, MCP
restart, coordinate formatting) must not be proven for the first time on
that day. This module exercises every branch that can run against the MCP
server and the real Mineflayer clients.

Each test boots one fresh world. The tests cover the driver events, result
checks, and MCP process lifecycle.
"""

from __future__ import annotations

import pytest

from mcmcp import constants
from test_infrastructure.live_test import port_listening
from tests.conftest import CONFIGURATION
from tests.live_case import (
    Approx,
    AtLeast,
    DuringAction,
    Excludes,
    Includes,
    Length,
    NonEmpty,
    RESULT_MODELS,
    aggregate_slots,
    assert_model_shape,
    assert_result_truth,
    assert_value,
    capture_result_truth,
    distance,
    float_offset,
    format_during_command,
    offset,
    read_path,
    resolve,
    wait_for_during_action,
)


PUBLIC_TOOLS = frozenset(RESULT_MODELS)

pytestmark = [pytest.mark.infrastructure, pytest.mark.usefixtures("live_test")]


# ---------------------------------------------------------------------------
# Scenario helpers
# ---------------------------------------------------------------------------


def test_resolve_reads_scenario_references():
    context = {
        "player": {"x": 1, "y": 2, "z": 3},
        "target": {"x": 4, "y": 5, "z": 6},
        "plain": "text",
    }
    assert resolve("$player.x", context) == 1
    assert resolve("$target.z", context) == 6
    assert resolve("$plain", context) == "text"
    assert resolve({"pos": "$player", "list": ["$player.y", 7]}, context) == {
        "pos": {"x": 1, "y": 2, "z": 3},
        "list": [2, 7],
    }
    assert resolve(("$player.x", "$player.y"), context) == (1, 2)


def test_offset_and_float_offset():
    base = {"x": 10, "y": 64, "z": -8}
    assert offset(base, (2, -1, 3)) == {"x": 12, "y": 63, "z": -5}
    assert float_offset(base, (0.5, 0.0, -0.5)) == {"x": 10.5, "y": 64.0, "z": -8.5}


def test_format_during_command_replaces_coordinates():
    context = {
        "base": {"x": 10, "y": 64, "z": -8},
        "target": {"x": 12, "y": 63, "z": -5},
        "player": {"x": 10.5, "y": 64.0, "z": -8.5},
    }
    command = format_during_command(
        "setblock {target_x} {target_y} {target_z} stone", context
    )
    assert command == "setblock 12 63 -5 stone"
    with pytest.raises(KeyError):
        format_during_command("tp {missing_x} 0 0", context)


def test_read_path_and_value_matchers():
    payload = {"player": {"health": 7.0, "food": 20}, "results": [{"name": "a"}, {"name": "b"}]}
    assert read_path(payload, "player.health") == 7.0
    assert read_path(payload, "results.1.name") == "b"
    assert_value(7.01, Approx(7.0, 0.1), "health")
    assert_value(7.0, Approx(7.0), "health")
    with pytest.raises(AssertionError):
        assert_value(8.0, Approx(7.0), "health")
    assert_value([1, 2], Length(2), "list")
    assert_value("x", NonEmpty(), "value")
    assert_value(5, AtLeast(5), "count")
    assert_value([{"key": "v1"}, {"key": "v2"}], Includes("v2", "key"), "items")
    assert_value([{"key": "v1"}, {"key": "v2"}], Excludes("v3", "key"), "items")
    assert_value("exact", "exact", "label")


def test_result_shape_rejects_missing_and_extra_fields():
    from mcmcp.models import DistanceResult

    valid = {
        "ok": True,
        "reason": None,
        "message": None,
        "distance": 5.0,
        "manhattan": 7.0,
        "dx": 3.0,
        "dy": 4.0,
        "dz": 0.0,
    }
    assert_model_shape(valid, DistanceResult)
    with pytest.raises(AssertionError, match="missing"):
        assert_model_shape({name: value for name, value in valid.items() if name != "dz"}, DistanceResult)
    with pytest.raises(AssertionError, match="extra"):
        assert_model_shape({**valid, "surprise": 1}, DistanceResult)


def test_aggregate_slots_merges_stack_sizes():
    slots = [
        {"name": None, "count": 0},
        {"name": "diamond", "count": 3},
        {"name": "diamond", "count": 5},
        {"name": "apple", "count": 64},
    ]
    assert aggregate_slots(slots) == {"diamond": 8, "apple": 64}


def test_duration_budgets_stay_within_the_documented_limits():
    from tests.live_case import DURATION_BUDGET_MS

    assert DURATION_BUDGET_MS["minecraft_mine_block"] == (constants.MINE_BLOCK_SECONDS + 5) * 1000
    assert DURATION_BUDGET_MS["minecraft_execute_typescript"] == (constants.SKILL_SECONDS + 5) * 1000


# ---------------------------------------------------------------------------
# Live driver events behind the during-action waits (one world)
# ---------------------------------------------------------------------------


def test_observed_events_support_the_during_waits(live_test):
    base = live_test.prepare_flat_area()
    x = int(base["x"])
    y = int(base["y"])
    z = int(base["z"])

    live_test.operator_command(f"setblock {x + 1} {y - 1} {z} dirt")
    live_test.operator_command(f"setblock {x + 3} {y} {z} chest[facing=west]")
    live_test.operator_command(f"setblock {x + 5} {y} {z} oak_door[half=lower,facing=north,open=false]")
    live_test.operator_command(f"setblock {x + 5} {y + 1} {z} oak_door[half=upper,facing=north,open=false]")
    live_test.operator_command(
        f"summon minecraft:cow {x + 3.5} {y} {z + 2.5} "
        '{NoAI:1b,PersistenceRequired:1b,Tags:["tdd_target"]}'
    )
    live_test.operator_command(f"tp {live_test.configuration.operator_name} {x + 1.5} {y} {z + 1.5}")

    found = live_test.wait_for(
        "the frozen cow", live_test.entities, lambda values: any(v["name"] == "cow" for v in values)
    )
    cow = next(value for value in found if value["name"] == "cow")

    context = {
        "base": {"x": x, "y": y, "z": z},
        "player": {"x": x + 0.5, "y": float(y), "z": z + 0.5},
        "dig_target": {"x": x + 1, "y": y - 1, "z": z},
        "cow_target": cow["position"],
        "cow_target_id": cow["id"],
        "chest_target": {"x": x + 3, "y": y, "z": z},
        "door_target": {"x": x + 5, "y": y, "z": z},
        "near_target": {"x": x + 2.5, "y": float(y), "z": z + 0.5},
    }

    # blockBreakProgressObserved
    live_test.driver("dig_block", position=context["dig_target"])
    live_test.wait_for(
        "the observed dig progress",
        live_test.observed_events,
        lambda events: any(event["position"] == context["dig_target"] for event in events["blockBreaks"]),
    )
    wait_for_during_action(live_test, context, DuringAction("block_break_started", "dig_target", ""))

    # entityHurt: the setup player attacks the cow (command damage does not
    # broadcast the hurt animation to clients)
    live_test.operator_command(
        f"tp {live_test.configuration.player_name} {x + 2.5} {float(y)} {z + 1.5}"
    )
    live_test.wait_for(
        "the setup-player attack position",
        live_test.player_state,
        lambda state: distance(state["position"], {"x": x + 2.5, "y": float(y), "z": z + 1.5}) <= 0.1,
    )
    health_before = live_test.entity_data("Health", "@e[tag=tdd_target,limit=1]")
    attacked = live_test.driver("attack_entity", entityId=context["cow_target_id"])
    assert attacked == {"attacked": "cow", "id": context["cow_target_id"]}
    live_test.wait_for(
        "the observed cow damage",
        live_test.observed_events,
        lambda events: context["cow_target_id"] in events["hurtEntities"],
    )
    health_after = live_test.entity_data("Health", "@e[tag=tdd_target,limit=1]")
    assert health_after < health_before
    wait_for_during_action(live_test, context, DuringAction("entity_hurt", "cow_target", ""))

    # chestLidMove
    live_test.driver("container", position=context["chest_target"])
    live_test.wait_for(
        "the observed chest lid",
        live_test.observed_events,
        lambda events: any(
            event["position"] == context["chest_target"] and event["isOpen"]
            for event in events["chestLids"]
        ),
    )
    wait_for_during_action(live_test, context, DuringAction("chest_open", "chest_target", ""))

    # block_property_true: fresh door placement with open=true. Vanilla
    # cancels a setblock when the door's derived upper half is occupied, so
    # break the door first in a separate command, then place it open.
    live_test.operator_command(
        format_during_command("setblock {door_target_x} {door_target_y} {door_target_z} air", context)
    )
    live_test.operator_command(
        format_during_command(
            "setblock {door_target_x} {door_target_y} {door_target_z} "
            "oak_door[half=lower,facing=north,open=true]",
            context,
        )
    )
    wait_for_during_action(
        live_test, context, DuringAction("block_property_true", "door_target", "", property="open")
    )
    assert live_test.block(x + 5, y, z)["properties"]["open"] is True

    # player_moved and player_near through a real teleport
    live_test.operator_command(
        f"tp {live_test.configuration.player_name} {x + 2.5} {float(y)} {z + 0.5}"
    )
    wait_for_during_action(live_test, context, DuringAction("player_moved", "player", ""))
    wait_for_during_action(live_test, context, DuringAction("player_near", "near_target", ""))

    with pytest.raises(AssertionError, match="Unknown during-action wait"):
        wait_for_during_action(live_test, context, DuringAction("bogus", "player", ""))


def test_common_result_oracles_read_server_truth(live_test):
    base = live_test.prepare_flat_area()
    live_test.set_player_vitals(10.0, 10)
    live_test.operator_command(f"give {live_test.configuration.player_name} minecraft:apple 2")
    before = capture_result_truth(live_test)

    live_test.operator_command(f"give {live_test.configuration.player_name} minecraft:apple 3")
    live_test.operator_command(f"clear {live_test.configuration.player_name} minecraft:apple 1")
    live_test.operator_command(f"give {live_test.configuration.player_name} minecraft:stone 1")
    live_test.set_player_vitals(8.0, 7)
    destination = {"x": base["x"] + 1.5, "y": float(base["y"]), "z": base["z"] + 0.5}
    live_test.operator_command(
        f"tp {live_test.configuration.player_name} "
        f"{destination['x']} {destination['y']} {destination['z']}"
    )
    live_test.wait_for(
        "the result-oracle destination",
        live_test.players,
        lambda players: any(
            player["username"] == live_test.configuration.player_name
            and distance(player["position"], destination) <= 0.1
            for player in players
        ),
    )

    assert_result_truth(
        live_test,
        before,
        {
            "inventory_delta": {
                "changes": [
                    {"item": "apple", "before": 2, "after": 4, "delta": 2},
                    {"item": "stone", "before": 0, "after": 1, "delta": 1},
                ],
                "total_items_before": 2,
                "total_items_after": 5,
            },
            "stat_delta": {
                "health_before": 10.0,
                "health_after": 8.0,
                "food_before": 10,
                "food_after": 7,
                "oxygen_before": 20,
                "oxygen_after": 20,
                "xp_level_before": 0,
                "xp_level_after": 0,
            },
            "pose_before": before["position"],
            "pose_after": destination,
            "on_ground": True,
        },
    )


# ---------------------------------------------------------------------------
# MCP process lifecycle and concurrent calls (one world)
# ---------------------------------------------------------------------------


def test_mcp_restart_and_concurrent_tool_calls(live_test):
    live_test.release_setup_player()
    live_test.start_mcp()

    first = live_test.list_tools()
    first_names = {tool.name for tool in first}
    assert first_names == PUBLIC_TOOLS

    future_a = live_test.begin_tool("minecraft_observe", {"include_image": False}, timeout=60)
    future_b = live_test.begin_tool("minecraft_info", {}, timeout=60)
    sequential = live_test.call_tool("minecraft_observe", {"include_image": False}, timeout=60)
    for result in (sequential, future_a.result(timeout=60), future_b.result(timeout=60)):
        assert result.isError is False
        assert result.meta["mode"] == "live"
        assert result.structuredContent is not None

    assert_model_shape(sequential.structuredContent, RESULT_MODELS["minecraft_observe"])

    live_test.restart_mcp(require_player=False)
    second = live_test.list_tools()
    assert {tool.name for tool in second} == first_names
    restarted_call = live_test.call_tool("minecraft_info", {}, timeout=60)
    assert restarted_call.isError is False

    live_test.stop_mcp()
    assert port_listening(CONFIGURATION.mcp_host, CONFIGURATION.mcp_port)
    stopped = live_test.call_tool("minecraft_info", {}, timeout=60)
    assert stopped.isError is False
    assert stopped.structuredContent["connected"] is False
    assert stopped.structuredContent["spawned"] is False
