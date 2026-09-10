"""Test the real server, Mineflayer clients, MCP process, and teardown."""

import json
import math
import time

import pytest

from mcmcp import constants
from test_infrastructure import LiveMinecraftTest
from test_infrastructure.live_test import port_listening
from tests.conftest import CONFIGURATION
from tests.live_case import Layout, RESULT_MODELS, arrange


pytestmark = pytest.mark.infrastructure

PUBLIC_TOOLS = frozenset(RESULT_MODELS)


def test_new_world_is_superflat_survival_on_normal(live_test):
    assert (live_test.agent_directory / "skills" / "success.ts").is_file()
    assert (live_test.agent_directory / "drafts").is_dir()
    player = live_test.player_state()
    assert player["username"] == "tdd_player"
    assert player["gameMode"] == "survival"
    assert player["difficulty"] == "normal"

    x = math.floor(player["position"]["x"])
    y = math.floor(player["position"]["y"])
    z = math.floor(player["position"]["z"])
    assert live_test.block(x, y - 1, z)["name"] == "grass_block"
    assert live_test.block(x, y - 2, z)["name"] == "dirt"
    assert live_test.block(x, y - 5, z)["name"] == "stone"
    assert live_test.block(x, -64, z)["name"] == "bedrock"


def test_operator_can_change_and_inspect_the_world(live_test):
    player = live_test.player_state()
    x = math.floor(player["position"]["x"]) + 2
    y = math.floor(player["position"]["y"])
    z = math.floor(player["position"]["z"])

    live_test.operator_command(f"setblock {x} {y} {z} gold_block")
    live_test.operator_command(f"setblock {x + 1} {y} {z} diamond_block")
    assert live_test.block(x, y, z)["name"] == "gold_block"
    assert live_test.block_counts(
        {"x": x, "y": y, "z": z},
        {"x": x + 1, "y": y, "z": z},
    ) == {"gold_block": 1, "diamond_block": 1}

    position = player["position"]
    live_test.operator_command(
        f"tp {live_test.configuration.player_name} "
        f"{position['x']} {position['y']} {position['z']} 90 15"
    )
    observed_player = live_test.wait_for(
        "The operator view of the player rotation",
        live_test.players,
        lambda players: any(
            value["username"] == live_test.configuration.player_name
            and value["yawDegrees"] is not None
            and abs(value["yawDegrees"] - 90) <= 0.1
            and abs(value["pitchDegrees"] + 15) <= 1.5
            for value in players
        ),
    )
    assert any(value["username"] == live_test.configuration.player_name for value in observed_player)


def test_operator_commands_create_reliable_ground_truth(live_test):
    player = live_test.player_state()
    ground_y = math.floor(player["position"]["y"]) - 1
    x = math.floor(player["position"]["x"]) + 8
    z = math.floor(player["position"]["z"]) + 8
    bedrock_y = next(
        block_y for block_y in range(ground_y, -65, -1)
        if live_test.block(x, block_y, z)["name"] == "bedrock"
    )

    live_test.operator_command(f"fill {x - 2} {ground_y + 1} {z - 2} {x + 32} {ground_y + 8} {z + 12} air")
    live_test.operator_command(f"fill {x - 2} {ground_y} {z - 2} {x + 32} {ground_y} {z + 12} stone")

    staircase = (
        (x + 1, ground_y + 1, z),
        (x + 1, ground_y + 2, z + 1),
        (x, ground_y + 3, z + 1),
        (x, ground_y + 4, z),
    )
    for block_x, block_y, block_z in staircase:
        live_test.operator_command(f"setblock {block_x} {block_y} {block_z} polished_andesite")

    ore = (x + 6, ground_y + 2, z + 2)
    live_test.operator_command(f"setblock {ore[0]} {ore[1]} {ore[2]} iron_ore")
    for offset_x, offset_y, offset_z in (
        (-1, 0, 0), (1, 0, 0), (0, -1, 0),
        (0, 1, 0), (0, 0, -1), (0, 0, 1),
    ):
        live_test.operator_command(
            f"setblock {ore[0] + offset_x} {ore[1] + offset_y} {ore[2] + offset_z} deepslate"
        )

    pit = (x + 10, z + 2)
    live_test.operator_command(f"fill {pit[0]} {bedrock_y + 1} {pit[1]} {pit[0]} {ground_y} {pit[1]} air")
    live_test.operator_command(f"setblock {x + 14} {ground_y + 1} {z + 2} chest[facing=north]")
    live_test.operator_command(f"setblock {x + 16} {ground_y + 1} {z + 2} oak_door[half=lower,facing=north,open=false]")
    live_test.operator_command(f"setblock {x + 16} {ground_y + 2} {z + 2} oak_door[half=upper,facing=north,open=false]")
    live_test.operator_command(f"setblock {x + 18} {ground_y + 1} {z + 2} oak_fence")
    live_test.operator_command(f"setblock {x + 24} {ground_y + 1} {z + 2} bell[attachment=floor,facing=north]")
    live_test.operator_command(f"setblock {x + 25} {ground_y + 1} {z + 2} hay_block")
    live_test.operator_command(f"setblock {x + 26} {ground_y + 1} {z + 2} composter[level=5]")

    live_test.operator_command(f"clear {live_test.configuration.player_name}")
    live_test.operator_command(f"give {live_test.configuration.player_name} iron_sword 1")
    live_test.operator_command(f"give {live_test.configuration.player_name} cobblestone 37")
    live_test.operator_command(f"give {live_test.configuration.player_name} apple 5")
    live_test.operator_command(f"give {live_test.configuration.player_name} torch 64")

    live_test.operator_command("kill @e[type=minecraft:cow]")
    cow = (x + 6.5, ground_y + 1, z + 7.5)
    live_test.operator_command(
        f"summon minecraft:cow {cow[0]} {cow[1]} {cow[2]} "
        "{NoAI:1b,PersistenceRequired:1b,Tags:[\"tdd_target\"]}"
    )
    live_test.operator_command(f"tp {live_test.configuration.operator_name} {x - 2.5} {ground_y + 1} {z - 2.5}")
    live_test.operator_command(f"tp {live_test.configuration.player_name} {x + 0.5} {ground_y + 1} {z + 0.5}")

    moved_player = live_test.wait_for(
        "The player teleport",
        live_test.player_state,
        lambda state: abs(state["position"]["x"] - (x + 0.5)) < 0.1
        and abs(state["position"]["z"] - (z + 0.5)) < 0.1,
    )
    assert moved_player["gameMode"] == "survival"
    assert moved_player["difficulty"] == "normal"

    held_player = live_test.wait_for(
        "The operator view of the held item",
        live_test.players,
        lambda players: any(
            value["username"] == live_test.configuration.player_name
            and value["heldItem"] == "iron_sword"
            for value in players
        ),
    )
    assert any(value["heldItem"] == "iron_sword" for value in held_player)

    inventory = live_test.wait_for(
        "The player inventory",
        live_test.player_inventory,
        lambda items: sum(item["count"] for item in items) == 107,
    )
    counts = {item["name"]: item["count"] for item in inventory if item["name"] is not None}
    assert counts == {"iron_sword": 1, "cobblestone": 37, "apple": 5, "torch": 64}

    for block_x, block_y, block_z in staircase:
        assert live_test.block(block_x, block_y, block_z)["name"] == "polished_andesite"
    assert live_test.block(*ore)["name"] == "iron_ore"
    for offset_x, offset_y, offset_z in (
        (-1, 0, 0), (1, 0, 0), (0, -1, 0),
        (0, 1, 0), (0, 0, -1), (0, 0, 1),
    ):
        assert live_test.block(
            ore[0] + offset_x,
            ore[1] + offset_y,
            ore[2] + offset_z,
        )["name"] == "deepslate"
    assert live_test.block(pit[0], ground_y, pit[1])["name"] == "air"
    assert live_test.block(pit[0], bedrock_y, pit[1])["name"] == "bedrock"
    assert live_test.block(x + 14, ground_y + 1, z + 2)["name"] == "chest"

    lower_door = live_test.block(x + 16, ground_y + 1, z + 2)
    upper_door = live_test.block(x + 16, ground_y + 2, z + 2)
    assert lower_door["name"] == "oak_door"
    assert lower_door["properties"]["half"] == "lower"
    assert lower_door["properties"]["open"] is False
    assert upper_door["properties"]["half"] == "upper"
    assert live_test.block(x + 18, ground_y + 1, z + 2)["name"] == "oak_fence"
    assert live_test.block(x + 24, ground_y + 1, z + 2)["name"] == "bell"
    assert live_test.block(x + 25, ground_y + 1, z + 2)["name"] == "hay_block"
    assert live_test.block(x + 26, ground_y + 1, z + 2)["properties"]["level"] == "5"

    entities = live_test.wait_for(
        "The target cow",
        live_test.entities,
        lambda values: any(
            entity["name"] == "cow"
            and abs(entity["position"]["x"] - cow[0]) < 0.2
            and abs(entity["position"]["z"] - cow[2]) < 0.2
            for entity in values
        ),
    )
    target_cows = [
        entity for entity in entities
        if entity["name"] == "cow"
        and abs(entity["position"]["x"] - cow[0]) < 0.2
        and abs(entity["position"]["z"] - cow[2]) < 0.2
    ]
    assert len(target_cows) == 1


def test_mcp_process_accepts_a_real_client(live_test):
    live_test.release_setup_player()
    live_test.start_mcp()
    result = live_test.call_tool("minecraft_info", {})
    assert result.isError is False
    assert result.structuredContent is not None
    assert result.meta["mode"] == "live"
    assert result.meta["tool"] == "minecraft_info"


def test_operator_reads_player_data_after_setup(live_test):
    live_test.set_player_vitals(7.0, 3)
    live_test.operator_command("give tdd_player minecraft:apple 11")

    assert live_test.entity_data("Health") == 7.0
    assert live_test.entity_data("foodLevel") == 3
    assert live_test.inventory_count("apple") == 11
    assert live_test.player_inventory_counts() == {"apple": 11}

    live_test.operator_command("clear tdd_player")
    live_test.operator_command("give tdd_player minecraft:dirt 2304")
    assert live_test.player_inventory_counts() == {"dirt": 2304}


def test_operator_reads_real_container_slots(live_test):
    base = live_test.prepare_flat_area()
    x = int(base["x"] + 3)
    y = int(base["y"])
    z = int(base["z"])
    live_test.operator_command(f"setblock {x} {y} {z} chest[facing=west]")
    live_test.operator_command(f"item replace block {x} {y} {z} container.0 with minecraft:diamond 7")
    live_test.operator_command(f"tp tdd_operator {x + 1.5} {y} {z + 1.5}")

    slots = live_test.container(x, y, z)["slots"]
    diamonds = sum(slot["count"] for slot in slots if slot["name"] == "diamond")
    assert diamonds == 7


def test_arrange_verifies_one_exact_player_loadout(live_test):
    arrange(
        live_test,
        Layout(
            items=(("apple", 1), ("string", 7)),
            equipment=(
                ("armor.head", "iron_helmet"),
                ("armor.chest", "iron_chestplate"),
                ("armor.legs", "iron_leggings"),
                ("armor.feet", "iron_boots"),
            ),
            held_item="apple",
        ),
    )


def test_setup_player_releases_the_mcp_username(live_test):
    assert any(player["username"] == "tdd_player" for player in live_test.players())
    live_test.release_setup_player()
    assert all(player["username"] != "tdd_player" for player in live_test.players())


def test_mcp_advertises_every_frozen_tool_schema(live_test):
    live_test.release_setup_player()
    live_test.start_mcp()
    advertised = live_test.list_tools()

    assert {tool.name for tool in advertised} == PUBLIC_TOOLS
    for tool in advertised:
        assert tool.description
        assert "{{" not in tool.description
        assert tool.inputSchema["type"] == "object"
        assert tool.outputSchema is not None

    descriptions = {tool.name: tool.description for tool in advertised}
    documented_limits = {
        "minecraft_observe": (constants.OBSERVE_RADIUS_BLOCKS,),
        "minecraft_find_block": (
            constants.FIND_BLOCK_HORIZONTAL_BLOCKS,
            constants.FIND_BLOCK_UP_BLOCKS,
            constants.FIND_BLOCK_DOWN_BLOCKS,
            constants.FIND_BLOCK_RESULT_LIMIT,
        ),
        "minecraft_find_interactables": (
            constants.INTERACTABLE_RADIUS_BLOCKS,
            constants.INTERACTABLE_RESULT_LIMIT,
        ),
        "minecraft_raytrace": (constants.RAYTRACE_DISTANCE_BLOCKS,),
        "minecraft_scan_horizon": (
            constants.HORIZON_HEADING_COUNT,
            constants.HORIZON_PITCHES_DEGREES,
        ),
        "minecraft_recipe_search": (constants.RECIPE_RESULT_LIMIT,),
        "minecraft_smelt_item": (constants.FURNACE_DISTANCE_BLOCKS,),
        "minecraft_mine_block": (
            constants.MINE_BLOCK_SECONDS,
        ),
        "minecraft_build": (
            constants.BUILD_DISTANCE_BLOCKS,
            constants.BUILD_CELL_LIMIT,
        ),
        "minecraft_fine_control": (constants.FINE_CONTROL_MILLISECONDS,),
        "minecraft_pillar_up": (constants.PILLAR_UP_BLOCK_LIMIT,),
        "minecraft_walk_to_visible": (
            constants.LOCAL_PATH_DISTANCE_BLOCKS,
            constants.VISIBLE_WALK_SECONDS,
        ),
        "minecraft_walk_to_surface": (constants.SURFACE_WALK_SECONDS,),
        "minecraft_walk_to_exact": (
            constants.EXACT_WALK_TOLERANCE_BLOCKS,
            constants.EXACT_WALK_SECONDS,
        ),
        "minecraft_attack_entity": (constants.ATTACK_HIT_LIMIT,),
        "minecraft_add_waypoint": (constants.WAYPOINT_CAPACITY,),
        "minecraft_list_waypoints": (constants.WAYPOINT_CAPACITY,),
        "minecraft_execute_typescript": (constants.SKILL_SECONDS,),
        "minecraft_mine_vein": (constants.MINE_VEIN_BLOCK_LIMIT,),
        "minecraft_analyze_area": (
            constants.VISIBLE_AREA_HORIZONTAL_BLOCKS,
            constants.VISIBLE_AREA_UP_BLOCKS,
            constants.VISIBLE_AREA_DOWN_BLOCKS,
        ),
        "minecraft_find_path": (constants.LOCAL_PATH_DISTANCE_BLOCKS,),
        "minecraft_is_safe_to_dig": (constants.DIG_SOUND_RADIUS_BLOCKS,),
        "minecraft_recall": (constants.RECALL_RESULT_LIMIT,),
    }
    for tool_name, values in documented_limits.items():
        for value in values:
            assert str(value) in descriptions[tool_name], (tool_name, value)


def test_babymode_mod_is_live(live_test):
    """Require canonical Babymode; no natural regeneration or pickup magnet."""
    assert any("Agentic Babymode v0.5.0" in line for line in live_test.operator_command("babymode version"))
    configuration_path = live_test.configuration.server_template / "config" / "agentic_babymode.json"
    mod_configuration = json.loads(configuration_path.read_text(encoding="utf-8"))
    assert mod_configuration["player"]["naturalRegeneration"] is False

    base = live_test.prepare_flat_area()
    live_test.set_player_vitals(6.0, 20)
    time.sleep(12)
    assert abs(live_test.entity_data("Health") - 6.0) < 0.01

    x = int(base["x"])
    y = float(base["y"])
    z = float(base["z"])
    live_test.operator_command(
        f"summon minecraft:item {x + 3.5} {y + 0.4} {z + 0.5} "
        '{Item:{id:"minecraft:diamond",Count:1b},PickupDelay:0b,Motion:[0d,0d,0d]}'
    )
    time.sleep(1)
    assert live_test.inventory_count("diamond") == 0


def test_teardown_releases_owned_processes():
    instance = LiveMinecraftTest(CONFIGURATION, "manual_teardown_test")
    with instance:
        if CONFIGURATION.use_server_checkpointing:
            assert not (instance.run_directory / "world").exists()
        else:
            assert (instance.run_directory / "world").is_dir()
    assert not instance.run_directory.exists()
    assert instance.driver_process.poll() is not None
    if CONFIGURATION.use_server_checkpointing:
        assert not hasattr(instance, "server_process")
        assert port_listening(CONFIGURATION.minecraft_host, CONFIGURATION.minecraft_port)
    else:
        assert instance.server_process.poll() is not None
        assert not port_listening(CONFIGURATION.minecraft_host, CONFIGURATION.minecraft_port)
    assert port_listening(CONFIGURATION.mcp_host, CONFIGURATION.mcp_port)
