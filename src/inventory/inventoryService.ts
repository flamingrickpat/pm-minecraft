import type { Bot } from "mineflayer";
import type { BotRuntime } from "../bot/liveBot.js";
import type { InventoryItemSummary } from "../server/state.js";
import { globResolve, globSuggest } from "../bot/nameMatching.js";

/**
 * Inventory operations need a live Mineflayer source; read and select slots through one service.
 *
 * @remarks
 * archetype: service-provider
 * owns: live inventory read, hotbar selection, and exact item-name equip.
 * not own: recipe logic, crafting windows, or autonomous item selection.
 * fails when: Mineflayer rejects the action, item is absent, or slot is out of range.
 * domain: this is the only inventory service created by the product runtime.
 * invariant: item names are exact Mineflayer/Minecraft names with no synonym substitution.
 */
export interface InventoryService {
  getInventory(): InventoryServiceOptions;
  selectHotbar(slot: number): Promise<{ ok: true; slot: number; message: string } | { ok: false; error: string; message: string }>;
  equipItem(itemName: string): Promise<{ ok: true; slot: number; message: string } | { ok: false; error: string; message: string }>;
}

export interface InventoryServiceOptions {
  selectedHotbarSlot: number | null;
  heldItem: InventoryItemSummary | null;
  hotbar: InventoryItemSummary[];
  main: InventoryItemSummary[];
  totalSlots: number;
  usedSlots: number;
}

export interface InventoryResponse {
  selectedHotbarSlot: number | null;
  heldItem: InventoryItemSummary | null;
  hotbar: InventoryItemSummary[];
  main: InventoryItemSummary[];
  totalSlots: number;
  usedSlots: number;
}

export function createInventoryService(bot: Bot): InventoryService {
  return {
    getInventory: () => {
      const slots = bot.inventory.slots ?? [];
      const hotbar: InventoryItemSummary[] = [];
      const main: InventoryItemSummary[] = [];

      for (let i = 0; i < slots.length; i++) {
        const item = slots[i];
        if (!item || !item.name || typeof item.count !== "number" || item.count === 0) {
          continue;
        }

        const summary: InventoryItemSummary = {
          slot: i,
          name: item.name,
          displayName: item.displayName ?? null,
          count: item.count
        };

        if (i >= 36 && i <= 45) {
          hotbar.push(summary);
        } else {
          main.push(summary);
        }
      }

      return {
        selectedHotbarSlot: bot.quickBarSlot ?? 0,
        heldItem: bot.heldItem ? {
          slot: bot.heldItem.slot,
          name: bot.heldItem.name,
          displayName: bot.heldItem.displayName ?? null,
          count: bot.heldItem.count
        } : null,
        hotbar,
        main,
        totalSlots: slots.length,
        usedSlots: hotbar.length + main.length
      };
    },

    selectHotbar: async (slot: number) => {
      if (!Number.isInteger(slot) || slot < 0 || slot > 8) {
        return {
          ok: false,
          error: "slot_out_of_range",
          message: `Slot ${slot} is out of range (0-8).`
        };
      }

      try {
        bot.setQuickBarSlot(slot);
        return {
          ok: true,
          slot,
          message: `Selected hotbar slot ${slot}.`
        };
      } catch (error) {
        return {
          ok: false,
          error: "select_failed",
          message: `Failed to select slot ${slot}: ${error instanceof Error ? error.message : String(error)}`
        };
      }
    },

    equipItem: async (itemName: string) => {
      if (!itemName || typeof itemName !== "string" || itemName.trim().length === 0) {
        return {
          ok: false,
          error: "invalid_item_name",
          message: "Item name must be a non-empty string."
        };
      }

      const slots = bot.inventory.slots ?? [];
      const normalized = itemName.trim().toLowerCase();

      // Exact name wins outright; wildcards ('*log*') resolve against what is
      // actually in the inventory. Ambiguous patterns are a cheap, teaching
      // failure: they list the matches so the next call is exact.
      const inventoryNames = [...new Set(
        slots
          .filter((item): item is NonNullable<typeof item> => !!item?.name)
          .map((item) => item.name as string)
      )];
      const matches = globResolve(normalized, inventoryNames);
      if (matches.length > 1) {
        const counts = new Map<string, number>();
        for (const item of slots) {
          if (item?.name) counts.set(item.name, (counts.get(item.name) ?? 0) + (item.count ?? 1));
        }
        return {
          ok: false,
          error: "ambiguous_item_pattern",
          message: `Ambiguous item pattern '${itemName}': matching inventory items are ${matches.map((name) => `${name} x${counts.get(name) ?? 0}`).join(", ")}. Pass an exact name.`
        };
      }
      const targetName = matches.length === 1 ? matches[0] : normalized;

      // Search for the item
      for (let i = 0; i < slots.length; i++) {
        const item = slots[i];
        if (item && item.name && typeof item.name === "string" && item.name.toLowerCase() === targetName) {
          try {
            // Use bot.equip() which handles hotbar/main inventory correctly
            console.log("[EQUIP] Before equip - heldItem:", bot.heldItem?.name, "quickBarSlot:", bot.quickBarSlot);
            await bot.equip(item, "hand");
            // Wait a bit for the inventory update to propagate
            await new Promise(r => setTimeout(r, 100));
            console.log("[EQUIP] After equip - heldItem:", bot.heldItem?.name, "quickBarSlot:", bot.quickBarSlot);
            console.log("[EQUIP] Hotbar slots:", bot.inventory.slots.slice(36, 45).map((s, i) => s?.name || "empty").join(", "));
            return {
              ok: true,
              slot: bot.heldItem?.slot ?? i,
              message: `Equipped ${item.name}.`
            };
          } catch (error) {
            return {
              ok: false,
              error: "equip_failed",
              message: `Failed to equip ${item.name}: ${error instanceof Error ? error.message : String(error)}`
            };
          }
        }
      }

      const suggestions = globSuggest(`*${normalized}*`, inventoryNames, 10);
      const registryNames = Object.keys(
        (bot as unknown as { registry?: { itemsByName?: Record<string, unknown> } }).registry?.itemsByName ?? {}
      );
      const registrySuggestions = suggestions.length > 0 ? suggestions : globSuggest(`*${normalized}*`, registryNames, 10);
      return {
        ok: false,
        error: "item_not_found",
        message: `No item matching '${itemName}' in inventory.${registrySuggestions.length > 0 ? ` Known items close to that: ${registrySuggestions.join(", ")}.` : ""} Patterns with * are allowed, e.g. '*log*' for any wood. Inventory: ${inventoryNames.join(", ") || "empty"}.`
      };
    }
  };
}

export function serializeInventory(options: InventoryServiceOptions): InventoryResponse {
  return {
    selectedHotbarSlot: options.selectedHotbarSlot,
    heldItem: options.heldItem,
    hotbar: options.hotbar,
    main: options.main,
    totalSlots: options.totalSlots,
    usedSlots: options.usedSlots
  };
}