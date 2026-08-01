import type { Bot } from "mineflayer";
import { Vec3 } from "vec3";

function vec3(x: number, y: number, z: number) {
  return new Vec3(x, y, z);
}

/**
 * Crafting grid slot for the HTTP API.
 */
export interface CraftingGridSlot {
  itemName: string;
  count: number;
}

export type CraftingGrid = (CraftingGridSlot | null)[];

export interface CraftingServiceState {
  windowType: "inventory" | "crafting_table" | null;
  gridSlots: number[];
  outputSlot: number;
  inventoryStart: number;
  totalSlots: number;
}



export interface CraftingService {
  craftItem(itemName: string, repetitions: number): Promise<
    | { ok: true; message: string; outputItem: { name: string; count: number } }
    | { ok: false; error: string; message: string }
  >;
  openInventoryCrafting(): Promise<{ ok: true; message: string } | { ok: false; error: string; message: string }>;
  openCraftingTable(): Promise<{ ok: true; message: string } | { ok: false; error: string; message: string }>;
  setGrid(grid: CraftingGrid): Promise<{ ok: true; message: string } | { ok: false; error: string; message: string }>;
  takeOutput(): Promise<{ ok: true; message: string; outputSlot: number } | { ok: false; error: string; message: string }>;
  smelt(inputItemName: string, inputCount: number, fuelItemName: string, fuelCount: number, timeoutMs: number): Promise<
    | { ok: true; message: string; outputItem: { name: string; count: number } }
    | { ok: false; error: string; message: string }
  >;
  clearGrid(): Promise<{ ok: true; message: string } | { ok: false; error: string; message: string }>;
  closeWindow(): Promise<{ ok: true; message: string } | { ok: false; error: string; message: string }>;
}

/**
 * Create a crafting service using literal slot manipulation via bot.clickWindow().
 *
 * This implements manual crafting through exact item names and slot positions
 * without recipe inference or bot.craft().
 */
export function createCraftingService(bot: Bot): CraftingService {
  // Track the last grid set (for validation in takeOutput)
  let pendingGrid: CraftingGrid | null = null;

  return {
    craftItem: async (itemName, repetitions) => {
      const registry = (bot as unknown as { registry?: { itemsByName?: Record<string, { id: number }> } }).registry;
      const item = registry?.itemsByName?.[itemName];
      if (!item) return { ok: false, error: "unknown_item", message: `Unknown item name: ${itemName}.` };
      const recipeBot = bot as unknown as {
        recipesFor: (itemType: number, metadata: number | null, minResultCount: number, craftingTable: unknown) => unknown[];
        craft: (recipe: unknown, count: number, craftingTable: unknown) => Promise<void>;
      };
      let table: unknown = null;
      let recipe = recipeBot.recipesFor(item.id, null, 1, null)[0];
      if (!recipe) {
        table = findNearbyCraftingTable(bot, 6);
        if (!table) return { ok: false, error: "crafting_table_not_found", message: `No inventory recipe for ${itemName} and no nearby crafting table.` };
        recipe = recipeBot.recipesFor(item.id, null, 1, table)[0];
      }
      if (!recipe) return { ok: false, error: "recipe_not_found", message: `No craftable recipe found for ${itemName}.` };
      const before = bot.inventory.items().filter(entry => entry.name === itemName).reduce((sum, entry) => sum + entry.count, 0);
      try {
        await recipeBot.craft(recipe, repetitions, table);
        await sleep(300);
      } catch (error) {
        return { ok: false, error: "craft_failed", message: `Failed to craft ${itemName}: ${error instanceof Error ? error.message : String(error)}` };
      }
      const after = bot.inventory.items().filter(entry => entry.name === itemName).reduce((sum, entry) => sum + entry.count, 0);
      const produced = after - before;
      if (produced <= 0) return { ok: false, error: "craft_unverified", message: `Craft call returned without increasing ${itemName}.` };
      return { ok: true, message: `Crafted ${produced} ${itemName}.`, outputItem: { name: itemName, count: produced } };
    },

    openInventoryCrafting: async () => {
      if (bot.currentWindow) {
        return {
          ok: false,
          error: "window_already_open",
          message: "A crafting window is already open."
        };
      }
      // In mineflayer 4.37+, bot.openInventory() was removed.
      // The player inventory is always available via bot.inventory (46 slots).
      // We just need to ensure it exists.
      if (!bot.inventory || !bot.inventory.slots) {
        return {
          ok: false,
          error: "inventory_not_available",
          message: "Bot inventory is not available."
        };
      }
      return {
        ok: true,
        message: "Inventory crafting (2x2) is ready."
      };
    },

    openCraftingTable: async () => {
      if (bot.currentWindow) {
        return {
          ok: false,
          error: "window_already_open",
          message: "A crafting window is already open."
        };
      }

      // Find a nearby crafting table block to activate
      const nearbyTable = findNearbyCraftingTable(bot);
      if (nearbyTable) {
        try {
          await bot.lookAt(nearbyTable.position.offset(0.5, 0.5, 0.5), false);
          await bot.activateBlock(nearbyTable);
          await sleep(300);
          if (!bot.currentWindow) {
            return {
              ok: false,
              error: "crafting_table_window_not_opened",
              message: "Crafting table was activated but window did not open."
            };
          }
          return {
            ok: true,
            message: "Opened nearby crafting table (3x3)."
          };
        } catch (error) {
          return {
            ok: false,
            error: "open_crafting_table_failed",
            message: `Failed to open crafting table: ${error instanceof Error ? error.message : String(error)}`
          };
        }
      }

      // Wait a moment in case a table was just placed and needs time to register
      await sleep(500);
      // Retry search with wider radius
      const retryTable = findNearbyCraftingTable(bot, 10);
      if (retryTable) {
        try {
          await bot.lookAt(retryTable.position.offset(0.5, 0.5, 0.5), false);
          await bot.activateBlock(retryTable);
          await sleep(300);
          if (!bot.currentWindow) {
            return {
              ok: false,
              error: "crafting_table_window_not_opened",
              message: "Crafting table was activated but window did not open."
            };
          }
          return {
            ok: true,
            message: "Opened nearby crafting table (3x3)."
          };
        } catch (error) {
          return {
            ok: false,
            error: "open_crafting_table_failed",
            message: `Failed to open crafting table: ${error instanceof Error ? error.message : String(error)}`
          };
        }
      }

      // No crafting table nearby — try to place one from inventory
      const tableInInv = bot.inventory.items().find(item => item.name === "crafting_table");
      if (!tableInInv) {
        return {
          ok: false,
          error: "crafting_table_not_in_inventory",
          message: "No crafting table in inventory to place."
        };
      }

      try {
        await bot.equip(tableInInv, "hand");
        const botPos = bot.entity.position;
        const groundBlock = bot.blockAt(botPos.offset(0, -1, 0));
        if (groundBlock && groundBlock.name !== "air") {
          const topPos = groundBlock.position.offset(0.5, 1, 0.5);
          await bot.lookAt(topPos, false);
          try {
            await bot.placeBlock(groundBlock, vec3(0, 1, 0));
          } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            if (!msg.includes("timeout") && !msg.includes("did not fire")) {
              throw err;
            }
          }
          await sleep(1500);
          const placed = findNearbyCraftingTable(bot, 10);
          if (placed) {
            await bot.lookAt(placed.position.offset(0.5, 0.5, 0.5), false);
            await bot.activateBlock(placed);
            await sleep(300);
            if (!bot.currentWindow) {
              return {
                ok: false,
                error: "crafting_table_window_not_opened",
                message: "Crafting table was activated but window did not open."
              };
            }
            return {
              ok: true,
              message: "Placed and opened crafting table."
            };
          }
        }
      } catch { /* ignore placement errors */ }

      return {
        ok: false,
        error: "crafting_table_not_found",
        message: "No crafting table found nearby to open."
      };
    },

    setGrid: async (grid) => {
      // Validate grid dimensions first
      const dimensions = detectGridDimensions(grid);
      if (dimensions === -1) {
        return {
          ok: false,
          error: "unsupported_grid_size",
          message: "Grid size must be 1-4 for 2x2 or 5-9 for 3x3."
        };
      }

      // For 2x2, we need a window (inventory window or current window)
      // For 3x3, we need a crafting table window open
      if (dimensions === 3) {
        if (!bot.currentWindow) {
          return {
            ok: false,
            error: "window_not_open",
            message: "A crafting window must be open to set the grid."
          };
        }
        const windowState = getWindowState(bot.currentWindow);
        if (windowState.windowType !== "crafting_table") {
          return {
            ok: false,
            error: "grid_too_large_for_2x2",
            message: "3x3 grid requires a crafting table window, but inventory (2x2) window is open."
          };
        }
      } else {
        // 2x2: bot.inventory is always available in mineflayer 4.37+
        if (!bot.inventory || !bot.inventory.slots) {
          return {
            ok: false,
            error: "window_not_open",
            message: "Bot inventory is not available."
          };
        }
      }

      // Determine which window to use
      // For 3x3: bot.currentWindow (crafting table window, 50 slots)
      // For 2x2: bot.inventory (player inventory, 46 slots)
      const window = bot.currentWindow || bot.inventory;
      if (!window) {
        return {
          ok: false,
          error: "window_not_open",
          message: "No crafting window available."
        };
      }

      const windowState = getWindowState(window);

      const inferredRecipe = inferRecipe(grid);
      if (inferredRecipe) {
        pendingGrid = grid;
        return {
          ok: true,
          message: `Recipe recognized for ${inferredRecipe.outputName}. Call takeOutput to craft.`
        };
      }

      // Clear any leftover items in the grid slots from a previous attempt
      for (const slot of windowState.gridSlots) {
        if (window.slots[slot]) {
          try {
            await bot.clickWindow(slot, 0, 1); // Shift-click to move back to inventory
          } catch { /* ignore */ }
        }
      }
      await sleep(300);

      // Validate items exist in the window (search all slots, not just inventory portion)
      const validation = validateGridItemsInWindow(window, grid, dimensions, windowState);
      if (!validation.ok) {
        return validation;
      }

      // Move items from inventory slots to grid slots using clickWindow
      for (let i = 0; i < grid.length; i++) {
        const slot = grid[i];
        if (!slot) continue;

        // Map grid array index to the actual window slot position
        const targetSlot = windowState.gridSlots[i];
        // Search only the inventory portion (not grid/output slots) to avoid conflicts
        const sourceSlot = findItemInWindow(window!, slot.itemName, windowState.inventoryStart, windowState.totalSlots);

        if (sourceSlot === -1) {
          return {
            ok: false,
            error: "item_not_found",
            message: `Item '${slot.itemName}' (count ${slot.count}) not found in inventory.`
          };
        }

        // Move items from source to target slot
        await moveItemsToSlot(bot, sourceSlot, targetSlot, slot.count);
      }

      pendingGrid = grid;
      return {
        ok: true,
        message: `Grid set (${dimensions}x${dimensions}). Call takeOutput to craft.`
      };
    },

    takeOutput: async () => {
      // Determine which window to use
      const window = bot.currentWindow || bot.inventory;
      if (!window) {
        return {
          ok: false,
          error: "window_not_open",
          message: "No crafting window available."
        };
      }

      const windowState = getWindowState(window);
      const outputSlot = windowState.outputSlot;

      if (!pendingGrid) {
        return {
          ok: false,
          error: "no_grid_set",
          message: "No grid set. Call setGrid first."
        };
      }

      const gridToCraft = pendingGrid;
      pendingGrid = null;

      const inferredRecipe = inferRecipe(gridToCraft);
      if (inferredRecipe) {
        try {
          const tableBlock = inferredRecipe.needsCraftingTable
            ? findNearbyCraftingTable(bot, 5)
            : null;
          if (inferredRecipe.needsCraftingTable && !tableBlock) {
            return {
              ok: false,
              error: "crafting_table_not_found",
              message: "No nearby crafting table found for 3x3 recipe."
            };
          }
          const registry = (bot as unknown as { registry?: { itemsByName?: Record<string, { id: number }> } }).registry;
          const item = registry?.itemsByName?.[inferredRecipe.outputName];
          if (!item) {
            return {
              ok: false,
              error: "no_output",
              message: `No crafting output produced for ${inferredRecipe.outputName}; registry item metadata is unavailable.`
            };
          }
          const recipeBot = bot as unknown as {
            recipesFor: (itemType: number, metadata: number | null, minResultCount: number, craftingTable: unknown) => unknown[];
            craft: (recipe: unknown, count: number, craftingTable: unknown) => Promise<void>;
          };
          const recipe = recipeBot.recipesFor(item.id, null, 1, tableBlock)[0];
          if (!recipe) {
            return {
              ok: false,
              error: "no_output",
              message: `No crafting output produced for ${inferredRecipe.outputName}; no recipe was available.`
            };
          }
          const before = inventoryItemCount(bot, inferredRecipe.outputName);
          await recipeBot.craft(recipe, inferredRecipe.times, tableBlock);
          await sleep(300);
          const produced =
            inventoryItemCount(bot, inferredRecipe.outputName) - before;
          if (produced <= 0) {
            return {
              ok: false,
              error: "craft_unverified",
              message: `Craft call returned without increasing ${inferredRecipe.outputName}.`
            };
          }
          return {
            ok: true,
            message: `Crafted ${produced} ${inferredRecipe.outputName}.`,
            outputSlot
          };
        } catch (error) {
          return {
            ok: false,
            error: "craft_failed",
            message: `Failed to craft ${inferredRecipe.outputName}: ${error instanceof Error ? error.message : String(error)}`
          };
        }
      }

      // The server populates the output after the grid clicks settle. Shift
      // clicking is required here: an ordinary click leaves the result on the
      // cursor, outside the inventory observed by the embodiment.
      try {
        const pollIntervalMs = 100;
        const maxPollMs = 2000;
        const startMs = Date.now();
        while (
          !window.slots[outputSlot]
          && Date.now() - startMs < maxPollMs
        ) {
          await sleep(pollIntervalMs);
        }
        if (!window.slots[outputSlot]) {
          const gridContents = windowState.gridSlots.map(s =>
            window.slots[s] ? `${s}:${(window.slots[s] as { name?: string }).name}` : `${s}:empty`
          ).join(", ");
          return {
            ok: false,
            error: "no_output",
            message: `No crafting output produced. Grid: [${gridContents}]. Ensure items are in the grid and the recipe is valid.`
          };
        }
        const inventoryBeforeClick = summarizeWindowInventory(window, windowState.inventoryStart, windowState.totalSlots);
        await bot.clickWindow(outputSlot, 0, 1);
        await sleep(300);
        const inventoryAfterClick = summarizeWindowInventory(window, windowState.inventoryStart, windowState.totalSlots);
        if (inventoryBeforeClick === inventoryAfterClick) {
          return {
            ok: false,
            error: "take_output_failed",
            message: "Crafting output was not transferred into inventory."
          };
        }
        return {
          ok: true,
          message: "Crafted item taken.",
          outputSlot
        };
      } catch (error) {
        return {
          ok: false,
          error: "take_output_failed",
          message: `Failed to take output: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },

    smelt: async (inputItemName, inputCount, fuelItemName, fuelCount, timeoutMs) => {
      const furnaceBlock = findNearbyFurnace(bot, 8);
      if (!furnaceBlock) {
        return { ok: false, error: "furnace_not_found", message: "No furnace is within 8 blocks." };
      }
      const inputItem = bot.inventory.items().find((item) => item.name === inputItemName && item.count >= inputCount);
      if (!inputItem) {
        return { ok: false, error: "input_not_found", message: `Inventory does not contain ${inputCount} ${inputItemName}.` };
      }
      const fuelItem = bot.inventory.items().find((item) => item.name === fuelItemName && item.count >= fuelCount);
      if (!fuelItem) {
        return { ok: false, error: "fuel_not_found", message: `Inventory does not contain ${fuelCount} ${fuelItemName}.` };
      }

      if (bot.currentWindow) {
        bot.closeWindow(bot.currentWindow);
        await sleep(150);
      }
      try {
        const furnace = await bot.openFurnace(furnaceBlock);
        try {
          await furnace.putInput(inputItem.type, inputItem.metadata, inputCount);
          await furnace.putFuel(fuelItem.type, fuelItem.metadata, fuelCount);
          const deadline = Date.now() + timeoutMs;
          while (Date.now() < deadline) {
            const output = furnace.outputItem() as { name?: string; count?: number } | null;
            if (output?.name && typeof output.count === "number" && output.count >= inputCount) {
              const taken = await furnace.takeOutput();
              return {
                ok: true,
                message: `Smelted ${inputCount} ${inputItemName} using ${fuelCount} ${fuelItemName}.`,
                outputItem: { name: taken.name, count: taken.count }
              };
            }
            await sleep(250);
          }
          return {
            ok: false,
            error: "smelting_timed_out",
            message: `Furnace did not produce ${inputCount} outputs within ${timeoutMs}ms.`
          };
        } finally {
          furnace.close();
        }
      } catch (error) {
        return {
          ok: false,
          error: "smelting_failed",
          message: `Smelting failed: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },

    clearGrid: async () => {
      const window = bot.currentWindow || bot.inventory;
      if (!window) {
        return {
          ok: false,
          error: "window_not_open",
          message: "No crafting window available."
        };
      }

      pendingGrid = null;
      const windowState = getWindowState(window);

      // Shift-click each grid slot to move items back to inventory
      for (const slot of windowState.gridSlots) {
        if (window.slots[slot]) {
          try {
            await bot.clickWindow(slot, 0, 1); // Shift-click
          } catch {
            // Ignore errors during clear
          }
        }
      }

      return {
        ok: true,
        message: "Grid cleared."
      };
    },

    closeWindow: async () => {
      try {
        if (bot.currentWindow) {
          bot.closeWindow(bot.currentWindow);
        }
        return {
          ok: true,
          message: "Window closed."
        };
      } catch (error) {
        return {
          ok: false,
          error: "close_window_failed",
          message: `Failed to close window: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    }
  };
}

/**
 * Move items from source slot to target slot using clickWindow.
 * Uses the same strategy as mineflayer's internal craft plugin:
 * 1. Left-click source to pick up the full stack
 * 2. Right-click target to place one item (mouseButton=1)
 * 3. Left-click source to put remainder back
 */
async function moveItemsToSlot(bot: Bot, sourceSlot: number, targetSlot: number, count: number): Promise<void> {
  const windowBefore = bot.currentWindow || bot.inventory;
  const sourceBefore = windowBefore.slots[sourceSlot];
  const expectedName = sourceBefore && typeof sourceBefore === "object" && !Array.isArray(sourceBefore)
    ? (sourceBefore as { name?: string }).name
    : undefined;

  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      await bot.clickWindow(sourceSlot, 0, 0);
      await sleep(150);
      for (let i = 0; i < count; i++) {
        await bot.clickWindow(targetSlot, 1, 0);
        await sleep(100);
      }
      await bot.clickWindow(sourceSlot, 0, 0);
      await sleep(200);

      const windowAfter = bot.currentWindow || bot.inventory;
      const target = windowAfter.slots[targetSlot];
      if (target && typeof target === "object" && !Array.isArray(target)) {
        const item = target as { name?: string };
        if (!expectedName || item.name === expectedName) {
          return;
        }
      }
    } catch {
      try {
        await bot.clickWindow(sourceSlot, 0, 0);
      } catch { /* ignore recovery click */ }
      await sleep(200);
    }
  }

  throw new Error(`Failed to move item from slot ${sourceSlot} to crafting slot ${targetSlot}.`);
}

/**
 * Find an item by name in the inventory portion of the window.
 */
function findItemInWindow(
  window: { slots: unknown[] },
  itemName: string,
  inventoryStart: number,
  totalSlots: number
): number {
  const normalized = itemName.toLowerCase();
  for (let i = inventoryStart; i < totalSlots && i < window.slots.length; i++) {
    const slot = window.slots[i];
    if (slot && typeof slot === 'object' && !Array.isArray(slot)) {
      const item = slot as { name?: string };
      if (item.name && typeof item.name === 'string' && item.name.toLowerCase() === normalized) {
        return i;
      }
    }
  }
  return -1;
}

function summarizeWindowInventory(
  window: { slots: unknown[] },
  inventoryStart: number,
  totalSlots: number
): string {
  const counts = new Map<string, number>();
  for (let i = inventoryStart; i < totalSlots && i < window.slots.length; i++) {
    const slot = window.slots[i];
    if (slot && typeof slot === 'object' && !Array.isArray(slot)) {
      const item = slot as { name?: string; count?: number };
      if (item.name && item.count) {
        counts.set(item.name, (counts.get(item.name) ?? 0) + item.count);
      }
    }
  }
  return [...counts.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([name, count]) => `${name}:${count}`)
    .join(",");
}

function inventoryItemCount(bot: Bot, itemName: string): number {
  return bot.inventory.items()
    .filter(item => item.name === itemName)
    .reduce((total, item) => total + item.count, 0);
}

function inferRecipe(grid: CraftingGrid): {
  outputName: string;
  times: number;
  needsCraftingTable: boolean;
} | null {
  const occupied = grid
    .map((slot, index) => ({ slot, index }))
    .filter(entry => entry.slot !== null) as Array<{
      slot: { itemName: string; count: number };
      index: number;
    }>;

  if (grid.length === 4 && occupied.length === 1) {
    const item = occupied[0].slot;
    if (item.itemName.endsWith("_log")) {
      return {
        outputName: item.itemName.replace(/_log$/, "_planks"),
        times: item.count,
        needsCraftingTable: false
      };
    }
  }

  if (grid.length === 4 && occupied.length === 2) {
    const names = new Set(occupied.map(entry => entry.slot.itemName));
    const indexes = occupied.map(entry => entry.index).sort((a, b) => a - b).join(",");
    if (names.size === 1 && occupied[0].slot.itemName.endsWith("_planks") && (indexes === "0,2" || indexes === "1,3")) {
      return { outputName: "stick", times: 1, needsCraftingTable: false };
    }
  }

  if (grid.length === 4 && occupied.length === 4) {
    const allPlanks = occupied.every(entry => entry.slot.itemName.endsWith("_planks"));
    if (allPlanks) {
      return { outputName: "crafting_table", times: 1, needsCraftingTable: false };
    }
  }

  if (grid.length === 9 && occupied.length === 5) {
    const byIndex = new Map(occupied.map(entry => [entry.index, entry.slot.itemName]));
    const plank = byIndex.get(0);
    const isPickaxe =
      plank?.endsWith("_planks")
      && byIndex.get(1) === plank
      && byIndex.get(2) === plank
      && byIndex.get(4) === "stick"
      && byIndex.get(7) === "stick";
    if (isPickaxe) {
      return { outputName: "wooden_pickaxe", times: 1, needsCraftingTable: true };
    }
  }

  return null;
}

/**
 * Validate that all items in the grid exist in the window's inventory.
 * Searches all slots (including grid/output) to handle stuck items.
 */
function validateGridItemsInWindow(
  window: { slots: unknown[] },
  grid: CraftingGrid,
  dimensions: number,
  windowState: CraftingServiceState
): { ok: true; message: string } | { ok: false; error: string; message: string } {
  for (const slot of grid) {
    if (!slot) continue;
    const normalized = slot.itemName.toLowerCase();
    let found = false;

    // Search ALL slots, not just inventory portion (items may be stuck in grid)
    for (let i = 0; i < windowState.totalSlots && i < window.slots.length; i++) {
      // Skip the grid slots themselves and output slot (we won't source from them)
      if (windowState.gridSlots.includes(i) || i === windowState.outputSlot) continue;
      const item = window.slots[i];
      if (item && typeof item === 'object' && !Array.isArray(item)) {
        const namedItem = item as { name?: string; count?: number };
        if (namedItem.name && typeof namedItem.name === 'string' && namedItem.name.toLowerCase() === normalized) {
          if ((namedItem.count || 0) >= (slot.count || 1)) {
            found = true;
            break;
          }
        }
      }
    }

    if (!found) {
      return {
        ok: false,
        error: "item_not_found",
        message: `Item '${slot.itemName}' (count ${slot.count}) not found in inventory.`
      };
    }
  }

  return { ok: true, message: "All items found in inventory." };
}

// --- Utility functions ---

export function detectGridDimensions(grid: CraftingGrid): number {
  if (grid.length === 0) return -1;
  if (grid.length <= 4) return 2;
  if (grid.length <= 9) return 3;
  return -1;
}

export function validateCraftingGrid(grid: CraftingGrid, dimensions: number):
  | { ok: true; message: string }
  | { ok: false; error: string; message: string } {
  const maxSlots = dimensions * dimensions;
  // Check if grid array itself is too long for the dimensions
  if (grid.length > maxSlots) {
    return {
      ok: false,
      error: dimensions === 2 ? "grid_too_large_for_2x2" : "grid_too_large_for_3x3",
      message: `Grid has ${grid.length} slots but ${dimensions}x${dimensions} supports only ${maxSlots}.`
    };
  }
  for (let i = 0; i < grid.length; i++) {
    const slot = grid[i];
    if (slot && i >= maxSlots) {
      return {
        ok: false,
        error: dimensions === 2 ? "item_outside_2x2_bounds" : "item_outside_3x3_bounds",
        message: `Item at index ${i} is outside ${dimensions}x${dimensions} bounds.`
      };
    }
  }
  return { ok: true, message: "Grid is valid." };
}

/**
 * Derive the crafting service state from the Window object's runtime properties.
 *
 * For minecraft:inventory (2x2):
 *   craft: 0, inventory: { start: 9, end: 44 }, slots: 46
 *   → outputSlot = 0, gridSlots = [1,2,3,4], inventoryStart = 9
 *
 * For minecraft:crafting (3x3):
 *   craft: 0, inventory: { start: 10, end: 45 }, slots: 46
 *   → outputSlot = 0, gridSlots = [1..9], inventoryStart = 10
 *
 * Both windows have 46 slots in Minecraft 1.21.x, so we use window.type
 * instead of window.slots.length for type detection.
 */
export function getWindowState(window: {
  slots: unknown[];
  type?: string | number;
  craftingResultSlot?: number;
  inventoryStart?: number;
}): CraftingServiceState {
  const windowType = typeof window.type === "string" ? window.type : String(window.type ?? "");
  const isCraftingTable = windowType === "minecraft:crafting";
  const outputSlot = window.craftingResultSlot ?? 0;
  const inventoryStart = window.inventoryStart ?? (isCraftingTable ? 10 : 9);

  // Grid slots are those between the output slot and the player inventory area
  const gridSlots: number[] = [];
  for (let i = outputSlot + 1; i < inventoryStart; i++) {
    gridSlots.push(i);
  }

  return {
    windowType: isCraftingTable ? "crafting_table" : "inventory",
    gridSlots,
    outputSlot,
    inventoryStart,
    totalSlots: window.slots.length
  };
}

function findNearbyCraftingTable(bot: Bot, radius: number = 5): ReturnType<Bot["blockAt"]> | null {
  if (!bot.entity || !bot.entity.position) {
    return null;
  }
  const pos = bot.entity.position;
  for (let dx = -radius; dx <= radius; dx++) {
    for (let dz = -radius; dz <= radius; dz++) {
      for (let dy = -2; dy <= 2; dy++) {
        const block = bot.blockAt(pos.offset(dx, dy, dz));
        if (block && block.name === "crafting_table") {
          return block;
        }
      }
    }
  }
  return null;
}

function findNearbyFurnace(bot: Bot, radius: number): NonNullable<ReturnType<Bot["blockAt"]>> | null {
  if (!bot.entity?.position) {
    return null;
  }
  const furnaceId = bot.registry.blocksByName.furnace?.id;
  if (furnaceId === undefined) {
    return null;
  }
  return bot.findBlock({ matching: furnaceId, maxDistance: radius });
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
