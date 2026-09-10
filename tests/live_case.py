"""Run one atomic MCP case against one real Minecraft server.

The operator creates and reads the world.
The MCP owns the survival player during the tool call.
Gameplay errors use structured results.
Schema errors and a missing player body use MCP errors.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import datetime
import inspect
import json
import math
from pathlib import Path
import struct
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

from pydantic import BaseModel

from mcmcp import constants, tools


@dataclass(frozen=True)
class BlockSpec:
    key: str
    offset: tuple[int, int, int]
    block: str
    name: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FillSpec:
    start: tuple[int, int, int]
    end: tuple[int, int, int]
    block: str


@dataclass(frozen=True)
class EntitySpec:
    key: str
    entity: str
    offset: tuple[float, float, float]
    nbt: str = "{NoAI:1b,PersistenceRequired:1b}"


@dataclass(frozen=True)
class ContainerItem:
    container: str
    slot: int
    item: str
    count: int


@dataclass(frozen=True)
class Layout:
    points: tuple[tuple[str, tuple[float, float, float]], ...] = ()
    blocks: tuple[BlockSpec, ...] = ()
    fills: tuple[FillSpec, ...] = ()
    entities: tuple[EntitySpec, ...] = ()
    items: tuple[tuple[str, int], ...] = ()
    slot_items: tuple[tuple[str, str, int], ...] = ()
    equipment: tuple[tuple[str, str], ...] = ()
    held_item: str | None = None
    container_items: tuple[ContainerItem, ...] = ()
    player_offset: tuple[float, float, float] = (0.5, 0.0, 0.5)
    yaw: float = 0.0
    pitch: float = 0.0
    time: int = 1000
    weather: str = "clear"
    food: int = 20
    health: float = 20.0
    commands: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorldExpectation:
    kind: str
    target: str
    expected: Any
    tolerance: float = 3.0


@dataclass(frozen=True)
class DuringAction:
    wait: str
    target: str
    command: str
    distance: float = 4.0
    property: str | None = None


RESULT_MODELS = {
    name: get_type_hints(function)["return"]
    for name, function in inspect.getmembers(tools.MinecraftTools, inspect.isfunction)
    if name.startswith("minecraft_")
}


def assert_result_field_path(tool: str, path: str) -> None:
    """Make sure that one JSON assertion path exists in its result model."""
    annotation: Any = RESULT_MODELS[tool]
    for part in path.split("."):
        origin = get_origin(annotation)
        if origin in (Union, UnionType):
            annotation = next(value for value in get_args(annotation) if value is not type(None))
            origin = get_origin(annotation)
        if part.isdigit():
            assert origin is list, (tool, path, annotation)
            annotation = get_args(annotation)[0]
            continue
        assert isinstance(annotation, type) and issubclass(annotation, BaseModel), (tool, path, annotation)
        assert part in annotation.model_fields, (tool, path, annotation)
        annotation = annotation.model_fields[part].annotation


def assert_model_shape(value: Any, annotation: Any, path: str = "result") -> None:
    """Reject missing and extra JSON fields at each model level."""
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        if value is None and type(None) in get_args(annotation):
            return
        choices = [choice for choice in get_args(annotation) if choice is not type(None)]
        if len(choices) == 1:
            assert_model_shape(value, choices[0], path)
        return
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        assert isinstance(value, dict), f"{path} must be an object"
        expected = set(annotation.model_fields)
        actual = set(value)
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        assert not missing, f"{path} has missing fields: {missing}"
        assert not extra, f"{path} has extra fields: {extra}"
        for name, model_field in annotation.model_fields.items():
            assert_model_shape(value[name], model_field.annotation, f"{path}.{name}")
        return
    if origin is list:
        assert isinstance(value, list), f"{path} must be a list"
        item_type = get_args(annotation)[0]
        for index, item in enumerate(value):
            assert_model_shape(item, item_type, f"{path}.{index}")
        return
    if origin is dict:
        assert isinstance(value, dict), f"{path} must be an object"
        value_type = get_args(annotation)[1]
        for name, item in value.items():
            assert_model_shape(item, value_type, f"{path}.{name}")


DURATION_BUDGET_MS = {
    "minecraft_execute_typescript": (constants.SKILL_SECONDS + 5) * 1000,
    "minecraft_fine_control": constants.FINE_CONTROL_MILLISECONDS + 2000,
    "minecraft_mine_block": (constants.MINE_BLOCK_SECONDS + 5) * 1000,
    "minecraft_walk_to_exact": (constants.EXACT_WALK_SECONDS + 5) * 1000,
    "minecraft_walk_to_surface": (constants.SURFACE_WALK_SECONDS + 5) * 1000,
    "minecraft_walk_to_visible": (constants.VISIBLE_WALK_SECONDS + 5) * 1000,
}


FAILURE_MESSAGES = {
    "ambiguous": ("multiple", "exact"),
    "access_denied": ("access", "denied"),
    "bed_obstructed": ("bed", "obstructed"),
    "bed_occupied": ("bed", "occupied"),
    "cell_limit": (str(constants.BUILD_CELL_LIMIT), "cells"),
    "crafting_table_not_found": ("crafting table", "not found"),
    "entity_not_found": ("entity", "not found"),
    "food_full": ("food", "full"),
    "furnace_not_found": ("furnace", "not found"),
    "inventory_full": ("inventory", "full"),
    "insufficient": ("not enough",),
    "missing": ("missing",),
    "missing_ingredients": ("missing", "ingredient"),
    "no_bed": ("bed", "not found"),
    "no_chest_window": ("chest", "open"),
    "no_food": ("food", "not found"),
    "no_headroom": ("headroom",),
    "no_held_item": ("hand", "empty"),
    "no_path": ("path",),
    "no_standable_surface": ("standable", "surface"),
    "not_a_tree": ("not", "tree"),
    "not_found": ("not found",),
    "not_grounded": ("ground",),
    "not_interactable": ("not", "interactable"),
    "not_night": ("night",),
    "not_placeable": ("not", "placeable"),
    "not_usable": ("not", "usable"),
    "out_of_range": ("range",),
    "partial": ("partial",),
    "skill_not_found": ("skill", "not found"),
    "stopped": ("stopped",),
    "postcondition_failed": ("postcondition",),
    "same_position": ("target", "current"),
    "target_not_standable": ("target", "standable"),
    "target_changed": ("target", "changed"),
    "target_out_of_range": ("target", "range"),
    "timeout": ("time",),
    "typescript_error": ("typescript", "error"),
    "unharvestable": ("harvest",),
}


@dataclass
class Scenario:
    """One arranged live world, ready for a plainly written tool test."""

    live_test: Any
    context: dict[str, Any]
    require_body: bool
    disconnect_body: bool


def setup(
    live_test: Any,
    layout: Layout = Layout(),
    *,
    require_body: bool = True,
    disconnect_body: bool = False,
) -> Scenario:
    """Arrange the world and start MCP for one explicit test function."""
    context = arrange(live_test, layout)
    if disconnect_body:
        live_test.handoff_player_to_mcp()
        live_test.stop_mcp()
        live_test.wait_for(
            "The MCP player disconnect",
            live_test.players,
            lambda players: all(player["username"] != live_test.configuration.player_name for player in players),
        )
    elif require_body:
        live_test.handoff_player_to_mcp()
    else:
        live_test.release_setup_player()
    return Scenario(live_test, context, require_body, disconnect_body)


def call_mcp(
    scenario: Scenario,
    tool: str,
    arguments: dict[str, Any],
    *,
    timeout: float = 660,
) -> Any:
    """Call one MCP tool with references resolved from this test's setup."""
    return scenario.live_test.call_tool(tool, resolve(arguments, scenario.context), timeout=timeout)


def begin_mcp_call(
    scenario: Scenario,
    tool: str,
    arguments: dict[str, Any],
    *,
    timeout: float = 660,
) -> Any:
    """Start a call when the test needs to change the world mid-action."""
    return scenario.live_test.begin_tool(tool, resolve(arguments, scenario.context), timeout=timeout)


def finish_mcp_call(call: Any, *, timeout: float = 660) -> Any:
    """Wait for one previously started MCP call."""
    return call.result(timeout=timeout)


def call_mcp_during(
    scenario: Scenario,
    tool: str,
    arguments: dict[str, Any],
    action: DuringAction,
    *,
    timeout: float = 660,
) -> Any:
    """Call a tool, wait for its visible progress, then perform one operator action."""
    call = begin_mcp_call(scenario, tool, arguments, timeout=timeout)
    wait_for_during_action(scenario.live_test, scenario.context, action)
    if action.wait == "entity_hurt" and action.command.startswith("kill "):
        scenario.live_test.mark_entity_interrupted(scenario.context[f"{action.target}_id"])
    scenario.live_test.operator_command(format_during_command(action.command, scenario.context))
    return finish_mcp_call(call, timeout=timeout)


def run_operator_command(scenario: Scenario, command: str) -> None:
    """Run an operator command after MCP owns the player."""
    rendered = format_during_command(command, scenario.context)
    messages = scenario.live_test.operator_command(rendered)
    if rendered.startswith("playsound "):
        assert any(
            "played sound" in message.lower() or "too far away" in message.lower()
            for message in messages
        ), messages


def restart_mcp(scenario: Scenario) -> None:
    """Restart MCP without hiding whether the test needs a player body."""
    if not scenario.live_test.mcp_started:
        scenario.live_test.start_mcp()
    else:
        scenario.live_test.restart_mcp(require_player=scenario.require_body)


def assert_setup_success(scenario: Scenario, response: Any, tool: str) -> BaseModel:
    """Check an explicit setup call used by a test."""
    result = parse_result(scenario, response, tool, {}, check_truth=False, check_support=False)
    assert result.ok is True
    return result


def parse_result(
    scenario: Scenario,
    response: Any,
    tool: str,
    arguments: dict[str, Any],
    *,
    truth_before: dict[str, Any] | None = None,
    check_truth: bool = True,
    check_support: bool = True,
) -> BaseModel:
    """Validate MCP transport and common result facts, then return the typed result."""
    scenario.live_test.require_live_mcp(response)
    assert response.isError is False
    assert response.structuredContent is not None
    assert any(part.type == "text" and part.text.strip() for part in response.content)
    assert_model_shape(response.structuredContent, RESULT_MODELS[tool])
    result = RESULT_MODELS[tool].model_validate(response.structuredContent)
    payload = result.model_dump(mode="json")
    if "duration_ms" in payload:
        assert payload["duration_ms"] >= 0
        if tool in DURATION_BUDGET_MS:
            assert payload["duration_ms"] <= DURATION_BUDGET_MS[tool]
    if scenario.require_body and payload.get("camera") is not None:
        assert_camera_truth(scenario.live_test, payload["camera"])
    if payload.get("pickup") is not None:
        assert_pickup_truth(scenario.live_test, tool, payload["pickup"])
    if check_truth and scenario.require_body:
        assert truth_before is not None
        assert_result_truth(scenario.live_test, truth_before, payload)
    if check_support:
        assert_support_data_truth(scenario.live_test, tool, resolve(arguments, scenario.context), payload)
    return result


def assert_protocol_error(response: Any, *fragments: str) -> None:
    """Assert a FastMCP protocol error without converting it into a tool result."""
    assert response.isError is True
    text = "\n".join(part.text for part in response.content if part.type == "text").lower()
    for fragment in fragments:
        assert fragment.lower() in text


def assert_field(scenario: Scenario, result: BaseModel, path: str, expected: Any) -> None:
    """Assert one named result field shown directly in the test."""
    actual = read_path(result.model_dump(mode="json"), path)
    assert_value(actual, resolve(expected, scenario.context), path)


def assert_message(result: BaseModel, *fragments: str) -> None:
    """Assert that an expected gameplay failure provides a readable message."""
    message = (result.message or "").lower()
    assert message


def assert_response_image(response: Any, result: BaseModel, expected: bool | None) -> None:
    """Assert the requested image behavior after the result assertions."""
    assert_image(response, result.model_dump(mode="json").get("image"), expected)


def capture_truth(scenario: Scenario) -> dict[str, Any]:
    """Capture independent server facts immediately before the visible MCP call."""
    return capture_result_truth(scenario.live_test)


def capture_failure_snapshot(scenario: Scenario) -> dict[str, Any]:
    """Capture protected state before a failure that must leave it unchanged."""
    return capture_player_snapshot(scenario.live_test)


def assert_failure_unchanged(scenario: Scenario, snapshot: dict[str, Any]) -> None:
    """Assert that an expected failure did not mutate the player state."""
    assert_failed_action_unchanged(scenario.live_test, {"_snapshot": snapshot})


def assert_failure_unchanged_allow_inventory_change(scenario: Scenario, snapshot: dict[str, Any]) -> None:
    """Assert that a partial failure did not mutate position or vitals."""
    live_test = scenario.live_test
    player = next(
        value for value in live_test.players()
        if value["username"] == live_test.configuration.player_name
    )
    assert distance(player["position"], snapshot["position"]) <= 3.0
    assert live_test.entity_data("Health") == snapshot["health"]
    assert live_test.entity_data("foodLevel") == snapshot["food"]
    assert player["heldItem"] == snapshot["held_item"]
    assert int(live_test.entity_data("Air")) == snapshot["air"]
    assert int(live_test.entity_data("XpLevel")) == snapshot["xp_level"]


def assert_world_state(scenario: Scenario, expectations: tuple[WorldExpectation, ...]) -> None:
    """Assert visible world state after the MCP call."""
    assert_world(scenario.live_test, scenario.context, expectations)


def wait_for_action(scenario: Scenario, action: DuringAction) -> None:
    """Wait for the operator-visible action stated in the test."""
    wait_for_during_action(scenario.live_test, scenario.context, action)


def assert_background_stopped(response: Any, tool: str, reason: str) -> None:
    """Check that an explicitly started background call was stopped."""
    assert response.isError is False
    assert_model_shape(response.structuredContent, RESULT_MODELS[tool])
    result = RESULT_MODELS[tool].model_validate(response.structuredContent)
    assert result.ok is False
    assert result.reason == reason
    assert "stopped" in (result.message or "").lower()


def arrange(live_test: Any, layout: Layout) -> dict[str, Any]:
    """Create one deterministic world and inspect every setup fact."""
    base = live_test.prepare_flat_area()
    context: dict[str, Any] = {
        "base": {"x": base["x"], "y": base["y"], "z": base["z"]},
        "agent_home": str(live_test.agent_directory),
    }
    for key, point_offset in layout.points:
        context[key] = float_offset(base, point_offset)

    live_test.operator_command("kill @e[type=!minecraft:player]")
    live_test.operator_command(f"clear {live_test.configuration.player_name}")
    live_test.operator_command(f"effect clear {live_test.configuration.player_name}")
    live_test.operator_command(f"time set {layout.time}")
    live_test.operator_command(f"weather {layout.weather}")
    live_test.set_player_vitals(layout.health, layout.food)

    for fill in layout.fills:
        start = offset(base, fill.start)
        end = offset(base, fill.end)
        live_test.operator_command(
            f"fill {start['x']} {start['y']} {start['z']} {end['x']} {end['y']} {end['z']} {fill.block}"
        )

    for block in layout.blocks:
        position = offset(base, block.offset)
        context[block.key] = position

    liquid_names = {"water", "lava"}
    ordered_blocks = sorted(
        layout.blocks,
        key=lambda block: block.block.split("[", 1)[0].removeprefix("minecraft:") in liquid_names,
    )
    non_liquid = [b for b in ordered_blocks if b.block.split("[", 1)[0].removeprefix("minecraft:") not in liquid_names]
    liquid_blocks = [b for b in ordered_blocks if b.block.split("[", 1)[0].removeprefix("minecraft:") in liquid_names]
    for block in non_liquid:
        position = context[block.key]
        live_test.operator_command(f"setblock {position['x']} {position['y']} {position['z']} {block.block}")
    # Liquids go in before the player teleports into the area; a fill that is
    # placed next to the player afterwards pushes them out of position.
    for block in liquid_blocks:
        position = context[block.key]
        live_test.operator_command(f"setblock {position['x']} {position['y']} {position['z']} {block.block}")

    for entity in layout.entities:
        position = float_offset(base, entity.offset)
        context[entity.key] = position
        live_test.operator_command(
            f"summon minecraft:{entity.entity} {position['x']} {position['y']} {position['z']} {entity.nbt}"
        )

    for item, count in layout.items:
        live_test.operator_command(f"give {live_test.configuration.player_name} minecraft:{item} {count}")

    for slot, item, count in layout.slot_items:
        live_test.operator_command(
            f"item replace entity {live_test.configuration.player_name} {slot} with minecraft:{item} {count}"
        )

    for slot, item in layout.equipment:
        live_test.operator_command(
            f"item replace entity {live_test.configuration.player_name} {slot} with minecraft:{item} 1"
        )

    if layout.held_item is not None:
        live_test.operator_command(
            f"item replace entity {live_test.configuration.player_name} weapon.mainhand "
            f"with minecraft:{layout.held_item} 1"
        )

    player_position = float_offset(base, layout.player_offset)
    context["player"] = player_position
    live_test.operator_command(
        f"tp {live_test.configuration.player_name} {player_position['x']} {player_position['y']} "
        f"{player_position['z']} {layout.yaw} {layout.pitch}"
    )

    for command in layout.commands:
        live_test.operator_command(command.format(
            player=live_test.configuration.player_name,
            operator=live_test.configuration.operator_name,
            x=base["x"], y=base["y"], z=base["z"],
        ))

    for item in layout.container_items:
        position = context[item.container]
        live_test.operator_command(
            f"item replace block {position['x']} {position['y']} {position['z']} "
            f"container.{item.slot} with minecraft:{item.item} {item.count}"
        )


    arranged_state = live_test.wait_for(
        "The arranged player position",
        live_test.player_state,
        lambda state: distance(state["position"], player_position) <= 0.1
        and abs(state["health"] - layout.health) <= 0.01
        and state["food"] == layout.food
        and (layout.held_item is None or state["heldItem"] == layout.held_item),
    )
    assert arranged_state["gameMode"] == "survival"
    assert arranged_state["difficulty"] == "normal"
    operator_state = live_test.wait_for(
        "The arranged weather and time",
        live_test.operator_state,
        lambda state: state["isRaining"] is (layout.weather == "rain")
        and (state["timeOfDay"] - layout.time) % 24000 < 1200,
    )

    for block in layout.blocks:
        position = context[block.key]
        actual = live_test.block(position["x"], position["y"], position["z"])
        assert actual["name"] == (block.name or block.block.split("[")[0].removeprefix("minecraft:"))
        for name, expected in block.properties.items():
            assert actual["properties"][name] == expected

    for fill in layout.fills:
        start = offset(base, fill.start)
        end = offset(base, fill.end)
        block_name = fill.block.split("[")[0].removeprefix("minecraft:")
        cell_count = math.prod(abs(start[axis] - end[axis]) + 1 for axis in ("x", "y", "z"))
        counts = live_test.block_counts(start, end)
        assert counts.get(block_name, 0) == cell_count

    setup_inventory = aggregate_slots(live_test.player_inventory())
    expected_inventory: dict[str, int] = {}
    for item, count in layout.items:
        expected_inventory[item] = expected_inventory.get(item, 0) + count
    for _, item, count in layout.slot_items:
        item_name = item.split("{", 1)[0]
        expected_inventory[item_name] = expected_inventory.get(item_name, 0) + count
    for _, item in layout.equipment:
        expected_inventory[item] = expected_inventory.get(item, 0) + 1
    if layout.held_item is not None:
        assert layout.held_item in expected_inventory
    assert setup_inventory == expected_inventory

    for entity in layout.entities:
        position = context[entity.key]
        found = live_test.wait_for(
            f"The arranged {entity.entity}",
            live_test.entities,
            lambda entities: any(
                value["name"] == entity.entity and distance(value["position"], position) <= 0.3
                for value in entities
            ),
        )
        match = next(
            value for value in found
            if value["name"] == entity.entity and distance(value["position"], position) <= 0.3
        )
        context[f"{entity.key}_id"] = match["id"]

    for container_name in {item.container for item in layout.container_items}:
        position = context[container_name]
        live_test.operator_command(
            f"tp {live_test.configuration.operator_name} {position['x'] + 1.5} {position['y']} {position['z'] + 1.5}"
        )
        slots = live_test.container(position["x"], position["y"], position["z"])["slots"]
        expected_slots = {
            item.slot: (item.item, item.count)
            for item in layout.container_items
            if item.container == container_name
        }
        for slot, (item_name, count) in expected_slots.items():
            assert slots[slot]["name"] == item_name
            assert slots[slot]["count"] == count
        assert aggregate_slots(slots) == aggregate_container_items(expected_slots)

    return context


def assert_world(live_test: Any, context: dict[str, Any], expectations: tuple[WorldExpectation, ...]) -> None:
    """Inspect important world state without using the MCP result."""
    for expectation in expectations:
        target = resolve(f"${expectation.target}", context) if expectation.target in context else expectation.target
        if expectation.kind == "block":
            actual = live_test.block(target["x"], target["y"], target["z"])["name"]
        elif expectation.kind == "block_properties":
            actual = live_test.block(target["x"], target["y"], target["z"])["properties"]
            for name, expected in expectation.expected.items():
                assert_value(actual[name], expected, f"block property {name}")
            continue
        elif expectation.kind == "inventory":
            actual = live_test.inventory_count(expectation.target)
        elif expectation.kind == "container":
            container_name, item_name = expectation.target.split(":", 1)
            position = context[container_name]
            live_test.operator_command(
                f"tp {live_test.configuration.operator_name} {position['x'] + 1.5} {position['y']} {position['z'] + 1.5}"
            )
            actual = aggregate_slots(live_test.container(position["x"], position["y"], position["z"])["slots"]).get(item_name, 0)
        elif expectation.kind == "entity_exists":
            position = context[expectation.target]
            entity_name = expectation.expected[0]
            wanted = expectation.expected[1]
            exists = any(
                entity["name"] == entity_name and distance(entity["position"], position) <= expectation.tolerance
                for entity in live_test.entities()
            )
            assert exists is wanted
            continue
        elif expectation.kind == "item_entities":
            actual = sum(
                entity["item"]["count"]
                for entity in live_test.entities()
                if entity["item"] is not None and entity["item"]["name"] == expectation.target
            )
        elif expectation.kind == "player_data":
            actual = live_test.entity_data(expectation.target)
        elif expectation.kind == "player_near":
            player = next(
                value for value in live_test.players()
                if value["username"] == live_test.configuration.player_name
            )
            actual = distance(player["position"], context[expectation.target])
            assert actual <= expectation.tolerance
            continue
        elif expectation.kind == "player_distance_from":
            player = next(
                value for value in live_test.players()
                if value["username"] == live_test.configuration.player_name
            )
            actual = distance(player["position"], context[expectation.target])
        elif expectation.kind == "player_y_delta":
            player = next(
                value for value in live_test.players()
                if value["username"] == live_test.configuration.player_name
            )
            actual = player["position"]["y"] - context[expectation.target]["y"]
        elif expectation.kind == "player_held_item":
            player = next(
                value for value in live_test.players()
                if value["username"] == live_test.configuration.player_name
            )
            actual = player["heldItem"]
        elif expectation.kind == "player_rotation":
            player = next(
                value for value in live_test.players()
                if value["username"] == live_test.configuration.player_name
            )
            expected_yaw, expected_pitch = expectation.expected
            yaw_error = abs((player["yawDegrees"] - expected_yaw + 180) % 360 - 180)
            assert yaw_error <= expectation.tolerance
            assert math.isclose(player["pitchDegrees"], expected_pitch, abs_tol=expectation.tolerance)
            continue
        elif expectation.kind == "time_is_day":
            time_of_day = live_test.operator_state()["timeOfDay"] % 24000
            actual = time_of_day < 12000
        elif expectation.kind == "named_block_count":
            block_name, wanted_count = expectation.expected
            positions = [
                position for name, position in context.items()
                if name.startswith(expectation.target)
                and isinstance(position, dict)
                and all(axis in position for axis in ("x", "y", "z"))
            ]
            actual = sum(
                live_test.block(position["x"], position["y"], position["z"])["name"] == block_name
                for position in positions
            )
            assert_value(actual, wanted_count, expectation.kind)
            continue
        elif expectation.kind == "box_block_count":
            start_name, end_name, block_name = expectation.target.split(":", 2)
            counts = live_test.block_counts(context[start_name], context[end_name])
            actual = counts.get(block_name, 0)
        else:
            raise AssertionError(f"Unknown world expectation: {expectation.kind}")
        assert_value(actual, expectation.expected, expectation.kind)


def assert_failed_action_unchanged(live_test: Any, context: dict[str, Any]) -> None:
    """Compare protected player state after a rejected action."""
    snapshot = context["_snapshot"]
    player = next(
        value for value in live_test.players()
        if value["username"] == live_test.configuration.player_name
    )
    assert distance(player["position"], snapshot["position"]) <= 3.0
    assert live_test.entity_data("Health") == snapshot["health"]
    assert live_test.entity_data("foodLevel") == snapshot["food"]
    assert live_test.entity_data("Inventory") == snapshot["inventory"]
    assert player["heldItem"] == snapshot["held_item"]
    assert int(live_test.entity_data("Air")) == snapshot["air"]
    assert int(live_test.entity_data("XpLevel")) == snapshot["xp_level"]


def capture_player_snapshot(live_test: Any) -> dict[str, Any]:
    """Read protected state immediately before a failure request."""
    player = next(
        value for value in live_test.players()
        if value["username"] == live_test.configuration.player_name
    )
    return {
        "position": player["position"],
        "health": live_test.entity_data("Health"),
        "food": live_test.entity_data("foodLevel"),
        "inventory": live_test.entity_data("Inventory"),
        "held_item": player["heldItem"],
        "air": int(live_test.entity_data("Air")),
        "xp_level": int(live_test.entity_data("XpLevel")),
    }


def capture_result_truth(live_test: Any) -> dict[str, Any]:
    """Read independent state immediately before one MCP action."""
    player = next(
        value for value in live_test.players()
        if value["username"] == live_test.configuration.player_name
    )
    return {
        "position": player["position"],
        "inventory": live_test.player_inventory_counts(),
        **read_player_stats(live_test),
    }


def assert_result_truth(live_test: Any, before: dict[str, Any], payload: dict[str, Any]) -> None:
    """Compare common result claims with independent server state."""
    inventory_delta = payload.get("inventory_delta")
    if inventory_delta is not None:
        assert_inventory_delta_truth(live_test, before["inventory"], inventory_delta)

    stat_delta = payload.get("stat_delta")
    if stat_delta is not None:
        after_stats = read_player_stats(live_test)
        for name in ("health", "food", "oxygen", "xp_level"):
            assert_value(stat_delta[f"{name}_before"], before[name], f"stat_delta.{name}_before")
            assert_value(stat_delta[f"{name}_after"], after_stats[name], f"stat_delta.{name}_after")

    player = next(
        value for value in live_test.players()
        if value["username"] == live_test.configuration.player_name
    )
    if payload.get("pose_before") is not None:
        assert distance(payload["pose_before"], before["position"]) <= 3
    for name in ("pose_after", "final_position", "end_position", "respawn_position"):
        if payload.get(name) is not None:
            assert distance(payload[name], player["position"]) <= 3
    if payload.get("on_ground") is not None:
        assert payload["on_ground"] is bool(live_test.entity_data("OnGround"))


def read_player_stats(live_test: Any) -> dict[str, Any]:
    """Read player statistics in the units used by MCP results."""
    air_ticks = int(live_test.entity_data("Air"))
    return {
        "health": float(live_test.entity_data("Health")),
        "food": int(live_test.entity_data("foodLevel")),
        "oxygen": max(0, min(20, math.ceil(air_ticks / 15))),
        "xp_level": int(live_test.entity_data("XpLevel")),
    }


def assert_inventory_delta_truth(
    live_test: Any,
    before: dict[str, int],
    inventory_delta: dict[str, Any],
) -> None:
    """Compare one returned inventory delta with exact server counts."""
    after = live_test.player_inventory_counts()
    actual_changes = {
        item: (before.get(item, 0), after.get(item, 0))
        for item in set(before) | set(after)
        if before.get(item, 0) != after.get(item, 0)
    }
    returned_changes = {change["item"]: change for change in inventory_delta["changes"]}
    assert len(returned_changes) == len(inventory_delta["changes"])
    assert set(returned_changes) == set(actual_changes)
    for item, (count_before, count_after) in actual_changes.items():
        change = returned_changes[item]
        assert change["before"] == count_before
        assert change["after"] == count_after
        assert change["delta"] == count_after - count_before
    assert inventory_delta["total_items_before"] == sum(before.values())
    assert inventory_delta["total_items_after"] == sum(after.values())


def wait_for_during_action(live_test: Any, context: dict[str, Any], action: DuringAction) -> None:
    """Wait for operator-visible progress before a concurrent world change."""
    start = context["player"]
    target = context[action.target]

    def position() -> dict[str, float] | None:
        matches = [
            player for player in live_test.players()
            if player["username"] == live_test.configuration.player_name
        ]
        return None if not matches else matches[0]["position"]

    if action.wait == "player_moved":
        live_test.wait_for(
            "The MCP player starts the action",
            position,
            lambda value: value is not None and distance(value, start) >= 0.75,
            timeout=30,
        )
        return
    if action.wait == "player_near":
        live_test.wait_for(
            "The MCP player approaches the arranged target",
            position,
            lambda value: value is not None and distance(value, target) <= action.distance,
            timeout=30,
        )
        return
    if action.wait == "block_break_started":
        # Vanilla broadcasts dig progress only to players that track the
        # digger (~48 blocks). prepare_flat_area parks the operator ~60 blocks
        # away, so move it next to the target before watching for progress.
        live_test.operator_command(
            f"tp {live_test.configuration.operator_name} "
            f"{target['x'] - 1.5} {target['y'] + 1.5} {target['z'] + 1.5}"
        )
        live_test.wait_for(
            "The operator observes block-break progress",
            live_test.observed_events,
            lambda events: any(
                event["position"] == target and event["destroyStage"] >= 0
                for event in events["blockBreaks"]
            ),
            timeout=30,
        )
        return
    if action.wait == "entity_hurt":
        entity_id = context[f"{action.target}_id"]
        live_test.wait_for(
            "The operator observes target damage",
            live_test.observed_events,
            lambda events: entity_id in events["hurtEntities"],
            timeout=30,
        )
        return
    if action.wait == "chest_open":
        live_test.wait_for(
            "The operator observes the chest lid open",
            live_test.observed_events,
            lambda events: any(
                event["position"] == target and event["isOpen"]
                for event in events["chestLids"]
            ),
            timeout=30,
        )
        return
    if action.wait == "block_property_true":
        live_test.wait_for(
            f"The arranged block property {action.property}",
            lambda: live_test.block(target["x"], target["y"], target["z"]),
            lambda block: block["properties"][action.property] is True,
            timeout=30,
        )
        return
    raise AssertionError(f"Unknown during-action wait: {action.wait}")


def format_during_command(command: str, context: dict[str, Any]) -> str:
    """Insert arranged coordinates into one operator command."""
    values: dict[str, Any] = {}
    for key, position in context.items():
        if isinstance(position, dict) and all(axis in position for axis in ("x", "y", "z")):
            values[f"{key}_x"] = position["x"]
            values[f"{key}_y"] = position["y"]
            values[f"{key}_z"] = position["z"]
    return command.format(**values)


def assert_image(result: Any, image_ref: dict[str, Any] | None, expected: bool | None) -> None:
    """Inspect PNG structure and metadata without pixel snapshots."""
    if expected is None:
        return
    images = [part for part in result.content if part.type == "image"]
    if not expected:
        assert images == []
        assert image_ref is None
        return
    assert len(images) == 1
    assert images[0].mimeType == "image/png"
    data = base64.b64decode(images[0].data)
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    assert image_ref is not None
    assert image_ref["width"] == width
    assert image_ref["height"] == height
    assert image_ref["frame_id"]
    datetime.fromisoformat(image_ref["captured_at"].replace("Z", "+00:00"))


def assert_camera_truth(live_test: Any, camera: dict[str, Any]) -> None:
    """Compare a returned camera pose with the operator view of the player."""
    player = next(
        value for value in live_test.players()
        if value["username"] == live_test.configuration.player_name
    )
    assert distance(player["position"], camera["feet_position"]) <= 3
    feet = camera["feet_position"]
    eye = camera["eye_position"]
    assert math.isclose(eye["x"], feet["x"], abs_tol=0.01)
    assert math.isclose(eye["y"], feet["y"] + 1.62, abs_tol=0.05)
    assert math.isclose(eye["z"], feet["z"], abs_tol=0.01)
    assert camera["block_position"] == {
        "x": math.floor(feet["x"]),
        "y": math.floor(feet["y"]),
        "z": math.floor(feet["z"]),
    }


def assert_pickup_truth(live_test: Any, tool: str, pickup: dict[str, Any]) -> None:
    """Check the loot-delivery payload against the direct-collection rules."""
    assert isinstance(pickup["picked_up"], bool)
    assert isinstance(pickup["drop_items"], list)
    if not pickup["picked_up"]:
        assert pickup["drop_hint"] is not None


def assert_support_data_truth(
    live_test: Any,
    tool: str,
    arguments: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    """Inspect durable files that do not exist in the Minecraft world."""
    if tool == "minecraft_remember" and payload["ok"]:
        path = agent_path(live_test, payload["file"])
        assert path.is_file()
        assert arguments["markdown"] in path.read_text(encoding="utf-8")
    if tool == "minecraft_recall" and payload["ok"]:
        for hit in payload["hits"]:
            path = agent_path(live_test, hit["file"])
            assert path.is_file()
            assert hit["markdown"] in path.read_text(encoding="utf-8")
    if tool == "minecraft_list_capabilities" and payload["ok"]:
        for skill in payload["skills"]:
            assert agent_path(live_test, skill["path"]).is_file()
    if tool == "minecraft_execute_typescript" and payload["reason"] not in ("skill_not_found", "access_denied"):
        assert agent_path(live_test, payload["skill_path"]).is_file()


def agent_path(live_test: Any, value: str) -> Path:
    """Resolve one returned agent path against the per-test agent directory."""
    path = Path(value)
    return path if path.is_absolute() else live_test.agent_directory / path


def read_path(value: Any, path: str) -> Any:
    """Read one dotted field from a parsed result dictionary."""
    current = value
    for part in path.split("."):
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def assert_value(actual: Any, expected: Any, label: str) -> None:
    """Compare exact values and explicit approximate float values."""
    if isinstance(expected, Approx):
        assert math.isclose(actual, expected.value, abs_tol=expected.tolerance), (label, actual, expected)
    elif isinstance(expected, Length):
        assert len(actual) == expected.value, (label, actual, expected)
    elif isinstance(expected, NonEmpty):
        assert actual, (label, actual, expected)
    elif isinstance(expected, AtLeast):
        assert actual >= expected.value, (label, actual, expected)
    elif isinstance(expected, Includes):
        values = [item[expected.key] for item in actual] if expected.key else actual
        assert expected.value in values, (label, actual, expected)
    elif isinstance(expected, Excludes):
        values = [item[expected.key] for item in actual] if expected.key else actual
        assert expected.value not in values, (label, actual, expected)
    else:
        assert actual == expected, (label, actual, expected)


@dataclass(frozen=True)
class Approx:
    value: float
    tolerance: float = 0.2


@dataclass(frozen=True)
class Length:
    value: int


@dataclass(frozen=True)
class NonEmpty:
    pass


@dataclass(frozen=True)
class AtLeast:
    value: float


@dataclass(frozen=True)
class Includes:
    value: Any
    key: str | None = None


@dataclass(frozen=True)
class Excludes:
    value: Any
    key: str | None = None


def resolve(value: Any, context: dict[str, Any]) -> Any:
    """Replace a scenario reference with its arranged runtime value."""
    if isinstance(value, str) and value.startswith("$"):
        parts = value[1:].split(".")
        current: Any = context[parts[0]]
        for part in parts[1:]:
            current = current[part]
        return current
    if isinstance(value, dict):
        return {name: resolve(item, context) for name, item in value.items()}
    if isinstance(value, list):
        return [resolve(item, context) for item in value]
    if isinstance(value, tuple):
        return tuple(resolve(item, context) for item in value)
    return value


def offset(base: dict[str, Any], delta: tuple[int, int, int]) -> dict[str, int]:
    """Convert one integer offset into a block cell."""
    return {"x": int(base["x"] + delta[0]), "y": int(base["y"] + delta[1]), "z": int(base["z"] + delta[2])}


def float_offset(base: dict[str, Any], delta: tuple[float, float, float]) -> dict[str, float]:
    """Convert one float offset into a world position."""
    return {"x": base["x"] + delta[0], "y": base["y"] + delta[1], "z": base["z"] + delta[2]}


def aggregate_slots(slots: list[dict[str, Any]]) -> dict[str, int]:
    """Aggregate real inventory slots by item name."""
    totals: dict[str, int] = {}
    for slot in slots:
        if slot["name"] is not None:
            totals[slot["name"]] = totals.get(slot["name"], 0) + slot["count"]
    return totals


def aggregate_container_items(slots: dict[int, tuple[str, int]]) -> dict[str, int]:
    """Aggregate expected container slots by item name."""
    totals: dict[str, int] = {}
    for item, count in slots.values():
        totals[item] = totals.get(item, 0) + count
    return totals


def distance(a: dict[str, float], b: dict[str, float]) -> float:
    """Get the Euclidean distance between two server positions."""
    return math.sqrt(sum((a[axis] - b[axis]) ** 2 for axis in ("x", "y", "z")))
