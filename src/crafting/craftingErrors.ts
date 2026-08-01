/**
 * Crafting errors need consistent serialization; map domain error shapes to HTTP responses.
 *
 * @remarks
 * archetype: service-provider
 * owns: error type mapping and serialization for crafting operations.
 * not own: HTTP transport or live bot state reads.
 * domain: this module defines the canonical error types for crafting operations.
 * invariant: errors carry exact Mineflayer/Minecraft names with no synonym substitution.
 */

export type CraftingErrorType =
  | "open_failed"
  | "open_crafting_table_failed"
  | "crafting_table_not_found"
  | "crafting_table_not_in_inventory"
  | "window_not_open"
  | "grid_too_large_for_2x2"
  | "grid_too_large_for_3x3"
  | "item_outside_2x2_bounds"
  | "item_outside_3x3_bounds"
  | "unsupported_grid_size"
  | "item_not_found"
  | "item_insufficient_count"
  | "set_grid_failed"
  | "no_output"
  | "take_output_failed"
  | "clear_grid_failed"
  | "close_window_failed";

export interface CraftingErrorInput {
  type: CraftingErrorType;
  message: string;
  itemName?: string;
  slotIndex?: number;
}

export interface CraftingErrorResponse {
  ok: false;
  error: CraftingErrorType;
  message: string;
}

export function serializeCraftingError(input: CraftingErrorInput): CraftingErrorResponse {
  return {
    ok: false,
    error: input.type,
    message: input.message
  };
}

export function isCraftingError(response: { ok?: boolean }): response is CraftingErrorResponse {
  return !response.ok && "error" in response && typeof response.error === "string";
}
