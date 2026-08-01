/**
 * Inventory errors need consistent serialization; map domain error shapes to HTTP responses.
 *
 * @remarks
 * archetype: service-provider
 * owns: error type mapping and serialization for inventory operations.
 * not own: HTTP transport or live bot state reads.
 * domain: this module defines the canonical error types for inventory operations.
 * invariant: errors carry exact Mineflayer/Minecraft names with no synonym substitution.
 */

export type InventoryErrorType =
  | "slot_out_of_range"
  | "select_failed"
  | "invalid_item_name"
  | "equip_failed"
  | "item_not_found";

export interface InventoryErrorInput {
  type: InventoryErrorType;
  message: string;
  slot?: number;
  itemName?: string;
}

export interface InventoryErrorResponse {
  ok: false;
  error: InventoryErrorType;
  message: string;
}

export function serializeInventoryError(input: InventoryErrorInput): InventoryErrorResponse {
  return {
    ok: false,
    error: input.type,
    message: input.message
  };
}

export function isInventoryError(response: { ok?: boolean }): response is InventoryErrorResponse {
  return !response.ok && "error" in response && typeof response.error === "string";
}
