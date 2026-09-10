"""Live survival checks from the iron-chestplate playtest."""

import pytest

from tests.live_case import BlockSpec, Layout, call_mcp, setup


@pytest.mark.parametrize("planks", ["oak_planks", "birch_planks", "spruce_planks"])
def test_craft_max_sticks(live_test, planks):
    scenario = setup(live_test, Layout(items=((planks, 6),)))
    response = call_mcp(scenario, "minecraft_craft_max", {"item": "stick"})
    assert not response.isError, response
    assert response.structuredContent["crafted"] == 12, response.structuredContent
    assert live_test.player_inventory_counts().get("stick", 0) == 12


def test_mining_reports_broken_tool(live_test):
    scenario = setup(live_test, Layout(
        blocks=(BlockSpec("ore", (2, 0, 0), "stone"),),
        slot_items=(("hotbar.0", "stone_pickaxe{Damage:130}", 1),),
    ))
    observed = call_mcp(scenario, "minecraft_observe", {"include_image": False})
    assert observed.structuredContent["held_item"]["durability"] == 1
    response = call_mcp(scenario, "minecraft_mine_block", {"position": "$ore"})
    assert not response.isError, response
    assert any("stone_pickaxe" in warning and "slot 0" in warning for warning in response.structuredContent["warnings"]), response.structuredContent
    assert live_test.player_inventory_counts().get("stone_pickaxe", 0) == 0


def test_explicit_equip_has_no_drift_warning(live_test):
    scenario = setup(live_test, Layout(items=(("stone_pickaxe", 1), ("cobblestone", 8))))
    response = call_mcp(scenario, "minecraft_equip", {"item": "cobblestone"})
    assert not response.isError, response
    assert response.structuredContent["warnings"] == []


def test_item_names_prefer_exact_then_match_case_insensitive_substrings(live_test):
    scenario = setup(live_test, Layout(items=(("torch", 3), ("redstone_torch", 2), ("stone_pickaxe", 1))))

    counted = call_mcp(scenario, "minecraft_count_inventory", {"pattern": "ToRcH"})
    assert not counted.isError, counted
    assert counted.structuredContent["total_matching_items"] == 3, counted.structuredContent
    assert [item["name"] for item in counted.structuredContent["matches"]] == ["torch"]

    equipped = call_mcp(scenario, "minecraft_equip", {"item": "PICK"})
    assert not equipped.isError, equipped
    assert equipped.structuredContent["equipped"]["name"] == "stone_pickaxe"


@pytest.mark.parametrize("capacity", ["empty", "partial", "full"])
def test_mined_loot_goes_to_inventory_with_overflow(live_test, capacity):
    # Glowstone produces 2–4 dust: one free space proves partial insertion.
    slots = () if capacity == "empty" else tuple(
        (f"hotbar.{i}", "dirt", 64) for i in range(9)
    ) + tuple((f"inventory.{i}", "dirt", 64) for i in range(27))
    if capacity == "partial":
        slots = (("hotbar.0", "glowstone_dust", 63),) + slots[1:]
    scenario = setup(live_test, Layout(
        blocks=(BlockSpec("ore", (3, 2, 0), "glowstone"),),
        slot_items=slots,
    ))
    response = call_mcp(scenario, "minecraft_mine_block", {"position": "$ore"})
    assert not response.isError, response
    assert response.structuredContent["ok"], response.structuredContent
    counts = live_test.player_inventory_counts()
    items = [entity for entity in live_test.entities() if entity["name"] == "item"]
    if capacity == "empty":
        assert 2 <= counts.get("glowstone_dust", 0) <= 4, counts
        assert not items, items
    elif capacity == "partial":
        assert counts["glowstone_dust"] == 64, counts
        assert items, items
    else:
        assert counts.get("glowstone_dust", 0) == 0, counts
        assert items, items
