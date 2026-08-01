import type { IncomingMessage, ServerResponse } from "node:http";
import type { InventoryService } from "../inventory/inventoryService.js";

/**
 * Inventory HTTP routes need validation and serialization; parse and respond to inventory commands.
 *
 * @remarks
 * archetype: controller
 * trigger: HTTP requests to the product runtime.
 * owns: route dispatch, JSON responses for inventory operations.
 * coordinates: inventory service for live inventory reads and operations.
 * fails when: the inventory service is unavailable or the request is malformed.
 * invariant: item names are exact Mineflayer/Minecraft names with no synonym substitution.
 */
export interface InventoryRouteHandler {
  handleInventoryGet(response: ServerResponse): void;
  handleInventorySelect(request: IncomingMessage, response: ServerResponse): Promise<void>;
  handleInventoryEquip(request: IncomingMessage, response: ServerResponse): Promise<void>;
}

export interface InventoryRouteOptions {
  service: InventoryService;
}

export function createInventoryRoutes(options: InventoryRouteOptions): InventoryRouteHandler {
  const service = options.service;

  return {
    handleInventoryGet: (response: ServerResponse) => {
      const inventory = service.getInventory();
      writeJson(response, 200, inventory);
    },

    handleInventorySelect: async (request: IncomingMessage, response: ServerResponse) => {
      const parsed = await readJson(request);
      if (!parsed.ok) {
        writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
        return;
      }

      const result = parseInventorySelect(parsed.body);
      if (!result.ok) {
        writeJson(response, 400, { ok: false, error: result.error, message: result.message });
        return;
      }

      const outcome = await service.selectHotbar(result.value);
      writeJson(response, outcome.ok ? 200 : 400, outcome);
    },

    handleInventoryEquip: async (request: IncomingMessage, response: ServerResponse) => {
      const parsed = await readJson(request);
      if (!parsed.ok) {
        writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
        return;
      }

      const result = parseInventoryEquip(parsed.body);
      if (!result.ok) {
        writeJson(response, 400, { ok: false, error: result.error, message: result.message });
        return;
      }

      const outcome = await service.equipItem(result.value);
      writeJson(response, outcome.ok ? 200 : 404, outcome);
    }
  };
}

export type ParsedSelect = { ok: true; value: number } | { ok: false; error: string; message: string };
export type ParsedEquip = { ok: true; value: string } | { ok: false; error: string; message: string };

export function parseInventorySelect(body: Record<string, unknown>): ParsedSelect {
  const slot = body.slot;
  if (slot === undefined || !Number.isInteger(slot)) {
    return { ok: false, error: "invalid_slot", message: "slot must be an integer." };
  }
  if ((slot as number) < 0 || (slot as number) > 8) {
    return { ok: false, error: "slot_out_of_range", message: `Slot ${slot} is out of range (0-8).` };
  }
  return { ok: true, value: slot as number };
}

export function parseInventoryEquip(body: Record<string, unknown>): ParsedEquip {
  const itemName = body.itemName;
  if (typeof itemName !== "string" || itemName.trim().length === 0) {
    return { ok: false, error: "invalid_item_name", message: "itemName must be a non-empty string." };
  }
  return { ok: true, value: itemName.trim() };
}

export function serializeInventoryError(error: { type: string; message: string }): { ok: false; error: string; message: string } {
  return {
    ok: false,
    error: error.type,
    message: error.message
  };
}

async function readJson(request: IncomingMessage): Promise<{ ok: true; body: Record<string, unknown> } | { ok: false; message: string }> {
  const chunks: Buffer[] = [];
  for await (const chunk of request) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }

  try {
    const parsed = JSON.parse(Buffer.concat(chunks).toString("utf8")) as unknown;
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return { ok: false, message: "Request body must be a JSON object." };
    }
    return { ok: true, body: parsed as Record<string, unknown> };
  } catch {
    return { ok: false, message: "Request body must be valid JSON." };
  }
}

function writeJson(response: ServerResponse, statusCode: number, body: unknown): void {
  response.writeHead(statusCode, { "content-type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(body));
}