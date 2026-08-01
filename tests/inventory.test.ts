import { describe, expect, it } from "vitest";
import { serializeInventory, type InventoryResponse, type InventoryServiceOptions } from "../src/inventory/inventoryService.js";
import { parseInventorySelect, parseInventoryEquip } from "../src/server/inventoryRoutes.js";
import { serializeInventoryError } from "../src/inventory/inventoryErrors.js";

describe("inventory serializer", () => {
  it("serializes a live inventory with hotbar, main, selected slot, and held item", () => {
    const options: InventoryServiceOptions = {
      selectedHotbarSlot: 2,
      heldItem: { slot: 38, name: "oak_log", displayName: "Oak Log", count: 5 },
      hotbar: [
        { slot: 36, name: "oak_log", displayName: "Oak Log", count: 10 },
        { slot: 37, name: "stone_pickaxe", displayName: "Stone Pickaxe", count: 1 },
        { slot: 38, name: "oak_log", displayName: "Oak Log", count: 5 }
      ],
      main: [
        { slot: 10, name: "crafting_table", displayName: "Crafting Table", count: 1 }
      ],
      totalSlots: 46,
      usedSlots: 4
    };

    const response: InventoryResponse = serializeInventory(options);

    expect(response).toMatchObject({
      selectedHotbarSlot: 2,
      heldItem: { slot: 38, name: "oak_log", displayName: "Oak Log", count: 5 },
      hotbar: expect.any(Array),
      main: expect.any(Array),
      totalSlots: 46,
      usedSlots: 4
    });

    expect(response.hotbar.length).toBe(3);
    expect(response.main.length).toBe(1);
  });

  it("serializes an empty inventory", () => {
    const options: InventoryServiceOptions = {
      selectedHotbarSlot: 0,
      heldItem: null,
      hotbar: [],
      main: [],
      totalSlots: 46,
      usedSlots: 0
    };

    const response: InventoryResponse = serializeInventory(options);

    expect(response).toMatchObject({
      selectedHotbarSlot: 0,
      heldItem: null,
      hotbar: [],
      main: [],
      totalSlots: 46,
      usedSlots: 0
    });
  });
});

describe("hotbar validation", () => {
  it("accepts valid slot 0", () => {
    const result = parseInventorySelect({ slot: 0 });
    expect(result.ok).toBe(true);
  });

  it("accepts valid slot 8", () => {
    const result = parseInventorySelect({ slot: 8 });
    expect(result.ok).toBe(true);
  });

  it("rejects slot -1", () => {
    const result = parseInventorySelect({ slot: -1 });
    expect(result.ok).toBe(false);
  });

  it("rejects slot 9", () => {
    const result = parseInventorySelect({ slot: 9 });
    expect(result.ok).toBe(false);
  });

  it("rejects non-integer slot", () => {
    const result = parseInventorySelect({ slot: 2.5 });
    expect(result.ok).toBe(false);
  });

  it("rejects non-numeric slot", () => {
    const result = parseInventorySelect({ slot: "two" });
    expect(result.ok).toBe(false);
  });
});

describe("exact item-name matching", () => {
  it("matches exact item name", () => {
    const result = parseInventoryEquip({ itemName: "oak_log" });
    expect(result.ok).toBe(true);
  });

  it("rejects empty item name", () => {
    const result = parseInventoryEquip({ itemName: "" });
    expect(result.ok).toBe(false);
  });

  it("rejects blank item name", () => {
    const result = parseInventoryEquip({ itemName: "  " });
    expect(result.ok).toBe(false);
  });

  it("rejects missing item name", () => {
    const result = parseInventoryEquip({});
    expect(result.ok).toBe(false);
  });
});

describe("inventory error serialization", () => {
  it("serializes slot_out_of_range error", () => {
    const error = serializeInventoryError({
      type: "slot_out_of_range",
      message: "Slot 9 is out of range (0-8).",
      slot: 9
    });

    expect(error).toMatchObject({
      ok: false,
      error: "slot_out_of_range",
      message: "Slot 9 is out of range (0-8)."
    });
  });

  it("serializes item_not_found error", () => {
    const error = serializeInventoryError({
      type: "item_not_found",
      message: "No item named 'stone_sword' in inventory.",
      itemName: "stone_sword"
    });

    expect(error).toMatchObject({
      ok: false,
      error: "item_not_found",
      message: "No item named 'stone_sword' in inventory."
    });
  });
});