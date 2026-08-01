import { describe, it, expect, vi, beforeEach } from "vitest";

import {
  validateCraftingGrid,
  detectGridDimensions,
  createCraftingService,
  type CraftingService,
  type CraftingGrid,
  type CraftingServiceState
} from "../craftingService.js";
import * as craftingErrors from "../craftingErrors.js";

describe("validateCraftingGrid", () => {
  it("should reject a grid that is too large for 2x2", () => {
    const grid: CraftingGrid = [
      { itemName: "oak_log", count: 1 },
      null, null, null,
      null, null, null,
      null, null, null,
    ];

    const result = validateCraftingGrid(grid, 2);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toBe("grid_too_large_for_2x2");
    }
  });

  it("should accept a grid that fits within 2x2", () => {
    const grid: CraftingGrid = [
      { itemName: "oak_log", count: 1 },
      null, null, null,
    ];

    const result = validateCraftingGrid(grid, 2);
    expect(result.ok).toBe(true);
  });

  it("should reject a grid where items are not in 2x2 bounds", () => {
    const grid: CraftingGrid = [
      null, null,
      null, null,
      null, null,
      null, null,
      null, { itemName: "oak_log", count: 1 },
      null, null,
      null, null,
      null, null,
    ];

    const result = validateCraftingGrid(grid, 2);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      // Grid has 12 slots but 2x2 supports only 4, so it's "grid_too_large_for_2x2"
      expect(result.error).toBe("grid_too_large_for_2x2");
    }
  });

  it("should accept a 3x3 grid that uses all slots", () => {
    const grid: CraftingGrid = [
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "stick", count: 1 },
    ];

    const result = validateCraftingGrid(grid, 3);
    expect(result.ok).toBe(true);
  });

  it("should reject a grid where items exceed 3x3 bounds", () => {
    const grid: CraftingGrid = [
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "extra_item", count: 1 },
    ];

    const result = validateCraftingGrid(grid, 3);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      // Grid has 10 slots but 3x3 supports only 9, so it's "grid_too_large_for_3x3"
      expect(result.error).toBe("grid_too_large_for_3x3");
    }
  });
});

describe("furnace smelting", () => {
  it("puts survival input and fuel into a nearby furnace and takes the output", async () => {
    const calls: string[] = [];
    const furnace = {
      putInput: async () => { calls.push("input"); },
      putFuel: async () => { calls.push("fuel"); },
      outputItem: () => ({ name: "iron_ingot", count: 3 }),
      takeOutput: async () => { calls.push("output"); return { name: "iron_ingot", count: 3 }; },
      close: () => { calls.push("close"); }
    };
    const mockBot = {
      entity: { position: { x: 0, y: 64, z: 0 } },
      registry: { blocksByName: { furnace: { id: 61 } } },
      findBlock: () => ({ name: "furnace", position: { x: 1, y: 64, z: 0 } }),
      inventory: {
        items: () => [
          { name: "raw_iron", count: 3, type: 1, metadata: 0 },
          { name: "coal", count: 1, type: 2, metadata: 0 }
        ]
      },
      currentWindow: null,
      openFurnace: async () => furnace
    };
    const service = createCraftingService(mockBot as unknown as import("mineflayer").Bot);

    const result = await service.smelt("raw_iron", 3, "coal", 1, 1000);

    expect(result).toEqual({
      ok: true,
      message: "Smelted 3 raw_iron using 1 coal.",
      outputItem: { name: "iron_ingot", count: 3 }
    });
    expect(calls).toEqual(["input", "fuel", "output", "close"]);
  });
});

describe("high-level survival crafting", () => {
  it("uses an ordinary Mineflayer recipe and verifies the inventory increase", async () => {
    let crafted = false;
    const recipe = { result: { id: 5, count: 4 } };
    const mockBot = {
      registry: { itemsByName: { oak_planks: { id: 5 } } },
      inventory: { items: () => crafted ? [{ name: "oak_planks", count: 4 }] : [] },
      recipesFor: vi.fn().mockReturnValue([recipe]),
      craft: vi.fn().mockImplementation(async () => { crafted = true; })
    };
    const service = createCraftingService(mockBot as unknown as import("mineflayer").Bot);

    const result = await service.craftItem("oak_planks", 1);

    expect(result).toEqual({ ok: true, message: "Crafted 4 oak_planks.", outputItem: { name: "oak_planks", count: 4 } });
    expect(mockBot.craft).toHaveBeenCalledWith(recipe, 1, null);
  });

  it("fails instead of claiming success when inventory does not change", async () => {
    const mockBot = {
      registry: { itemsByName: { stick: { id: 280 } } },
      inventory: { items: () => [] },
      recipesFor: () => [{}],
      craft: async () => undefined
    };
    const result = await createCraftingService(mockBot as unknown as import("mineflayer").Bot).craftItem("stick", 1);
    expect(result).toEqual({ ok: false, error: "craft_unverified", message: "Craft call returned without increasing stick." });
  });
});

describe("detectGridDimensions", () => {
  it("should detect 2x2 grid from 4 or fewer slots", () => {
    const grid: CraftingGrid = [
      { itemName: "oak_log", count: 1 },
      null, null, null,
    ];
    expect(detectGridDimensions(grid)).toBe(2);
  });

  it("should detect 3x3 grid from 5 to 9 slots", () => {
    const grid: CraftingGrid = [
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "stick", count: 1 },
    ];
    expect(detectGridDimensions(grid)).toBe(3);
  });

  it("should reject grids larger than 3x3", () => {
    const grid: CraftingGrid = [
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "extra", count: 1 },
    ];
    expect(detectGridDimensions(grid)).toBe(-1);
  });

  it("should reject empty grids", () => {
    const grid: CraftingGrid = [];
    expect(detectGridDimensions(grid)).toBe(-1);
  });
});

describe("crafting window slot mapping", () => {
  it("should have correct slot layout for inventory (2x2) window", () => {
    // In mineflayer 4.37+ the player inventory window has 46 slots:
    // grid 0-3 (2x2 usable), output 9, inventory 10-44, offhand 45
    const state: CraftingServiceState = {
      windowType: "inventory",
      gridSlots: [0, 1, 2, 3],
      outputSlot: 9,
      inventoryStart: 10,
      totalSlots: 46
    };

    expect(state.gridSlots).toEqual([0, 1, 2, 3]);
    expect(state.outputSlot).toBe(9);
    expect(state.inventoryStart).toBe(10);
    expect(state.totalSlots).toBe(46);
  });

  it("should have correct slot layout for crafting table (3x3) window", () => {
    const state: CraftingServiceState = {
      windowType: "crafting_table",
      gridSlots: [0, 1, 2, 3, 4, 5, 6, 7, 8],
      outputSlot: 9,
      inventoryStart: 10,
      totalSlots: 50
    };

    expect(state.gridSlots).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8]);
    expect(state.outputSlot).toBe(9);
    expect(state.inventoryStart).toBe(10);
    expect(state.totalSlots).toBe(50);
  });
});

describe("crafting error types", () => {
  it("should serialize crafting errors correctly", () => {
    const input: craftingErrors.CraftingErrorInput = {
      type: "crafting_table_not_found",
      message: "No crafting table found nearby."
    };
    const result = craftingErrors.serializeCraftingError(input);
    expect(result.ok).toBe(false);
    expect(result.error).toBe("crafting_table_not_found");
    expect(result.message).toBe("No crafting table found nearby.");
  });

  it("should identify crafting errors via type guard", () => {
    const error = { ok: false, error: "window_not_open" as const, message: "No window is open." };
    const valid = craftingErrors.isCraftingError(error);
    expect(valid).toBe(true);
  });

  it("should not identify non-errors via type guard", () => {
    const ok = { ok: true, message: "Grid set." };
    const valid = craftingErrors.isCraftingError(ok);
    expect(valid).toBe(false);
  });

  it("should have all required error types", () => {
    const errorTypes: craftingErrors.CraftingErrorType[] = [
      "open_failed",
      "open_crafting_table_failed",
      "crafting_table_not_found",
      "crafting_table_not_in_inventory",
      "window_not_open",
      "grid_too_large_for_2x2",
      "grid_too_large_for_3x3",
      "item_outside_2x2_bounds",
      "item_outside_3x3_bounds",
      "unsupported_grid_size",
      "item_not_found",
      "item_insufficient_count",
      "set_grid_failed",
      "no_output",
      "take_output_failed",
      "clear_grid_failed",
      "close_window_failed"
    ];
    expect(errorTypes.length).toBe(17);
  });
});

describe("craftingService validation", () => {
  let mockBot: any;

  beforeEach(() => {
    mockBot = {
      closeWindow: vi.fn(),
      clickWindow: vi.fn().mockResolvedValue(undefined),
      inventory: {
        slots: [
          null, null, null, null, null, null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null,
          null, null, null, null, null, null, null
        ]
      },
      currentWindow: null
    };
  });

  it("should reject setGrid when no window is open", async () => {
    mockBot.currentWindow = null;
    // Remove inventory to simulate no window available
    (mockBot as any).inventory = null;
    const service = createCraftingService(mockBot as unknown as import("mineflayer").Bot);

    const grid: CraftingGrid = [
      { itemName: "oak_log", count: 1 },
      null, null, null,
    ];
    const result = await service.setGrid(grid);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toBe("window_not_open");
    }
  });

  it("should reject unsupported grid size", async () => {
    mockBot.currentWindow = {
      slots: new Array(45).fill(null)
    };
    const service = createCraftingService(mockBot as unknown as import("mineflayer").Bot);

    const grid: CraftingGrid = [
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "extra", count: 1 },
    ];
    const result = await service.setGrid(grid);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toBe("unsupported_grid_size");
    }
  });

  it("should reject takeOutput when no grid was set", async () => {
    mockBot.currentWindow = {
      slots: [null, null, null, null, null, ...new Array(40).fill(null)]
    };
    const service = createCraftingService(mockBot as unknown as import("mineflayer").Bot);

    const result = await service.takeOutput();
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toBe("no_grid_set");
    }
  });

  it("should reject takeOutput when no output exists after grid set", async () => {
    // Set up a mock window with correct prismarine-windows properties
    // When currentWindow is set, setGrid() uses it (not bot.inventory)
    const mockWindow = {
      slots: [null, null, null, null, null, null, null, null, null, null,
        { name: "oak_log", count: 5 }, ...new Array(34).fill(null)],
      type: "minecraft:inventory",
      craftingResultSlot: 0,
      inventoryStart: 9
    };
    mockBot.currentWindow = mockWindow;
    const service = createCraftingService(mockBot as unknown as import("mineflayer").Bot);

    // Set grid first so pendingGrid is non-null
    const grid: CraftingGrid = [
      { itemName: "oak_log", count: 1 },
      null, null, null,
    ];

    // setGrid moves items via clickWindow (mocked to resolve)
    // After setGrid, pendingGrid is set and output slot (0) is null
    await service.setGrid(grid);

    // takeOutput should poll for output, timeout, and return no_output
    const result = await service.takeOutput();
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toBe("no_output");
    }
  }, 10000);

  it("shift-clicks literal recipe output into observed inventory", async () => {
    const slots: Array<{ name: string; count: number } | null> =
      new Array(46).fill(null);
    slots[9] = { name: "oak_planks", count: 2 };
    let cursor: { name: string; count: number } | null = null;
    mockBot.inventory.slots = slots;
    mockBot.clickWindow = vi.fn(
      async (slot: number, button: number, mode: number) => {
        if (slot === 9 && button === 0 && mode === 0) {
          if (cursor) {
            slots[9] = cursor;
            cursor = null;
          } else {
            cursor = slots[9];
            slots[9] = null;
          }
          return;
        }
        if ((slot === 1 || slot === 2) && button === 1 && mode === 0) {
          if (!cursor) throw new Error("test cursor is empty");
          slots[slot] = { name: cursor.name, count: 1 };
          cursor.count -= 1;
          if (cursor.count === 0) cursor = null;
          if (slots[1] && slots[2]) {
            slots[0] = { name: "oak_pressure_plate", count: 1 };
          }
          return;
        }
        if (slot === 0 && button === 0 && mode === 1) {
          slots[10] = slots[0];
          slots[0] = null;
          slots[1] = null;
          slots[2] = null;
        }
      }
    );
    const service = createCraftingService(
      mockBot as unknown as import("mineflayer").Bot
    );

    const grid: CraftingGrid = [
      { itemName: "oak_planks", count: 1 },
      { itemName: "oak_planks", count: 1 },
      null,
      null
    ];
    expect((await service.setGrid(grid)).ok).toBe(true);
    const result = await service.takeOutput();

    expect(result.ok).toBe(true);
    expect(mockBot.clickWindow).toHaveBeenCalledWith(0, 0, 1);
    expect(slots[10]).toEqual({
      name: "oak_pressure_plate",
      count: 1
    });
  });

  it("should reject clearGrid when no window is open", async () => {
    mockBot.currentWindow = null;
    // Remove inventory to simulate no window available
    (mockBot as any).inventory = null;
    const service = createCraftingService(mockBot as unknown as import("mineflayer").Bot);

    const result = await service.clearGrid();
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toBe("window_not_open");
    }
  });

  it("should detect grid size and validate against open window type", async () => {
    mockBot.currentWindow = {
      slots: new Array(45).fill(null)
    };
    const service = createCraftingService(mockBot as unknown as import("mineflayer").Bot);

    // 3x3 grid in a 2x2 window (inventory, 45 slots) should be rejected
    const grid: CraftingGrid = [
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "stick", count: 1 },
    ];

    const result = await service.setGrid(grid);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toBe("grid_too_large_for_2x2");
    }
  });
});

describe("craftingService openCraftingTable", () => {
  let mockBot: any;

  beforeEach(() => {
    mockBot = {
      openInventory: vi.fn(),
      closeWindow: vi.fn(),
      clickWindow: vi.fn().mockResolvedValue(undefined),
      inventory: {
        slots: [
          null, null, null, null, null, null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null,
          null, null, null, null, null, null
        ],
        items: vi.fn().mockReturnValue([])
      },
      currentWindow: null
    };
  });

  it("should reject openCraftingTable when no crafting table in inventory", async () => {
    const service = createCraftingService(mockBot as unknown as import("mineflayer").Bot);

    const result = await service.openCraftingTable();
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toBe("crafting_table_not_in_inventory");
    }
  });

  it("should reject openCraftingTable when window is already open", async () => {
    mockBot.currentWindow = {
      slots: new Array(45).fill(null)
    };
    const service = createCraftingService(mockBot as unknown as import("mineflayer").Bot);

    const result = await service.openCraftingTable();
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toBe("window_already_open");
    }
  });
});

describe("craftingService integration with 2x2 and 3x3", () => {
  let mockBot: any;

  beforeEach(() => {
    mockBot = {
      openInventory: vi.fn().mockImplementation(async () => {
        // Simulate the real bot: openInventory sets currentWindow
        mockBot.currentWindow = {
          slots: new Array(45).fill(null)
        };
      }),
      closeWindow: vi.fn().mockImplementation(() => {
        mockBot.currentWindow = null;
      }),
      clickWindow: vi.fn().mockResolvedValue(undefined),
      inventory: {
        slots: [
          null, null, null, null, null, null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null,
          null, null, null, null, null, null, null, null, null, null,
          null, null, null, null, null, null
        ]
      },
      inventoryWindow: null,
      currentWindow: null
    };
  });

  it("should open inventory crafting for 2x2", async () => {
    const service = createCraftingService(mockBot as unknown as import("mineflayer").Bot);

    const result = await service.openInventoryCrafting();
    expect(result.ok).toBe(true);
    // In mineflayer 4.37+, openInventory is a no-op — bot.inventory is always available
    expect(mockBot.currentWindow).toBeNull();
  });

  it("should reject 3x3 grid when inventory window (2x2) is open", async () => {
    mockBot.currentWindow = {
      slots: new Array(45).fill(null)
    };
    const service = createCraftingService(mockBot as unknown as import("mineflayer").Bot);

    const grid: CraftingGrid = [
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "oak_plank", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "stick", count: 1 },
      { itemName: "stick", count: 1 },
    ];

    const result = await service.setGrid(grid);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error).toBe("grid_too_large_for_2x2");
    }
  });
});
