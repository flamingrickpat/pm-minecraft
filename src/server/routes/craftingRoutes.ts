import type { IncomingMessage, ServerResponse } from "node:http";
import type { CraftingService, CraftingGrid } from "../../crafting/craftingService.js";

/**
 * Crafting HTTP routes need validation and serialization; parse and respond to crafting commands.
 *
 * @remarks
 * archetype: controller
 * trigger: HTTP requests to the product runtime.
 * owns: route dispatch, JSON responses for crafting operations.
 * coordinates: crafting service for literal grid manipulation.
 * fails when: the crafting service is unavailable or the request is malformed.
 * invariant: grid slots are literal Mineflayer window positions with no recipe substitution.
 */
export interface CraftingRouteHandler {
  handleCraftingSetGrid(request: IncomingMessage, response: ServerResponse): Promise<void>;
  handleCraftingTakeOutput(request: IncomingMessage, response: ServerResponse): Promise<void>;
  handleCraftingClearGrid(request: IncomingMessage, response: ServerResponse): Promise<void>;
  handleCraftingCloseWindow(request: IncomingMessage, response: ServerResponse): Promise<void>;
}

export interface CraftingRouteOptions {
  service: CraftingService;
}

export function createCraftingRoutes(options: CraftingRouteOptions): CraftingRouteHandler {
  const service = options.service;

  return {
    handleCraftingSetGrid: async (request: IncomingMessage, response: ServerResponse) => {
      const parsed = await readJson(request);
      if (!parsed.ok) {
        writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
        return;
      }

      const result = parseCraftingGrid(parsed.body);
      if (!result.ok) {
        writeJson(response, 400, { ok: false, error: result.error, message: result.message });
        return;
      }

      const outcome = await service.setGrid(result.value);
      writeJson(response, outcome.ok ? 200 : 400, outcome);
    },

    handleCraftingTakeOutput: async (request: IncomingMessage, response: ServerResponse) => {
      const parsed = await readJson(request);
      if (!parsed.ok) {
        writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
        return;
      }

      const outcome = await service.takeOutput();
      writeJson(response, outcome.ok ? 200 : 400, outcome);
    },

    handleCraftingClearGrid: async (request: IncomingMessage, response: ServerResponse) => {
      const parsed = await readJson(request);
      if (!parsed.ok) {
        writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
        return;
      }

      const outcome = await service.clearGrid();
      writeJson(response, outcome.ok ? 200 : 400, outcome);
    },

    handleCraftingCloseWindow: async (request: IncomingMessage, response: ServerResponse) => {
      const parsed = await readJson(request);
      if (!parsed.ok) {
        writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
        return;
      }

      const outcome = await service.closeWindow();
      writeJson(response, outcome.ok ? 200 : 400, outcome);
    }
  };
}

export type ParsedCraftingGrid = { ok: true; value: CraftingGrid } | { ok: false; error: string; message: string };

export function parseCraftingGrid(body: Record<string, unknown>): ParsedCraftingGrid {
  const grid = body.grid;
  if (!Array.isArray(grid)) {
    return { ok: false, error: "invalid_grid", message: "grid must be an array." };
  }

  const parsed: CraftingGrid = grid.map((slot: unknown) => {
    if (!slot || typeof slot !== "object" || Array.isArray(slot)) {
      return null;
    }

    const record = slot as Record<string, unknown>;
    const itemName = record.itemName;
    const count = record.count;

    if (typeof itemName !== "string" || itemName.trim().length === 0) {
      return null;
    }

    if (!Number.isInteger(count) || typeof count !== "number" || count <= 0) {
      return null;
    }

    return {
      itemName: itemName.trim(),
      count: count as number
    };
  });

  return { ok: true, value: parsed };
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
