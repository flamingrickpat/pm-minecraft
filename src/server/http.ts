import { createHash } from "node:crypto";
import { createServer, type Server, type IncomingMessage, type ServerResponse } from "node:http";
import type { Duplex } from "node:stream";
import { readFileSync, existsSync, statSync, createWriteStream, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import type { RuntimeConfig } from "../config.js";
import type { CommandQueue, CommandCompletion } from "../commands/commandQueue.js";
import type { CommandRecord } from "../evidence/evidenceStore.js";
import { controlNames, type CommandControls, type ControlStates } from "../commands/controls.js";
import type { PhysicalCommandActions } from "../bot/actions.js";
import type { Vector3 } from "../commands/types.js";
import { serializeHealth, type HealthInput } from "./health.js";
import { serializeState, type BotStateSnapshot } from "./state.js";
import type { FrameBundleCapture } from "../targeting/frameBundle.js";
import type { PixelTargeting } from "../targeting/pixelTargeting.js";
import type { InventoryService } from "../inventory/inventoryService.js";
import { createInventoryRoutes } from "./inventoryRoutes.js";
import type { CraftingService, CraftingGrid } from "../crafting/craftingService.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PUBLIC_DIR = join(__dirname, "..", "..", "public");
const LOGS_DIR = process.env.MINECRAFT_BODY_LOG_DIR || process.env.PM_LOG_DIR || join(__dirname, "..", "..", "logs");
const DEBUG_LOG_PATH = join(LOGS_DIR, "debug.log");
const ALLOWED_CHAT_COMMANDS = new Set(["help", "list", "me", "msg", "say", "tell", "w"]);

/** Async file write stream for debug logging. Created lazily to avoid blocking startup. */
let debugStream: ReturnType<typeof createWriteStream> | null = null;

function getDebugStream(): ReturnType<typeof createWriteStream> {
  if (!debugStream) {
    try {
      mkdirSync(LOGS_DIR, { recursive: true });
      debugStream = createWriteStream(DEBUG_LOG_PATH, { flags: "a" });
    } catch {
      // If we cannot create the log file, silently degrade — do not crash the server
      return null as never;
    }
  }
  return debugStream;
}

function debugLog(level: string, message: string): void {
  const stream = getDebugStream();
  if (!stream) return;
  const line = `[${new Date().toISOString()}] [${level}] ${message}\n`;
  // Fire-and-forget async write — must never block HTTP/WS processing
  stream.write(line, (err) => {
    if (err) {
      // Log write failure — do not crash
    }
  });
}

/**
 * Runtime state needs observable HTTP evidence; serve health and state JSON from supplied live snapshots.
 *
 * @remarks
 * archetype: controller
 * trigger: HTTP requests to the product runtime.
 * owns: route dispatch, JSON responses, and HTTP server lifecycle for WI-01 routes.
 * coordinates: health and state serializers plus runtime-owned status suppliers.
 * fails when: the configured web host/port cannot bind or a route is unknown.
 * invariant: `/api/state` is produced by the runtime snapshot supplier, not static JSON.
 */
export interface RuntimeHttpServer {
  start(): Promise<void>;
  stop(): Promise<void>;
  broadcast(event: RuntimeEvent): void;
  status: RuntimeServerStatus;
  publicDir: string;
}

export interface RuntimeHttpServerOptions {
  config: RuntimeConfig["web"];
  health: () => HealthInput;
  state: () => BotStateSnapshot;
  observation?: () => Promise<unknown | null>;
  chat?: { send(text: string): Promise<void> };
  commands?: {
    queue: CommandQueue;
    applyControlStates: CommandControls["applyControlStates"];
    actions: PhysicalCommandActions;
    maxFineControlDurationMs?: number;
    /** Absolute cap (chunks) on walk_to search region; larger requests are rejected. */
    maxChunkLimit?: number;
  };
  frames?: FrameBundleCapture;
  targeting?: PixelTargeting;
  inventory?: InventoryService;
  crafting?: CraftingService;
  publicDir?: string;
  evidence?: { recordCommand(cmd: { runId: string; commandId: string; command: string; status: "succeeded" | "failed" | "cancelled" | "timed_out"; input: unknown; acceptedAt: string; startedAt: string | null; finishedAt: string | null; durationMs: number; ok: boolean; reason: string | null; message: string; data: unknown }): Promise<void> };
  broadcast?: (event: RuntimeEvent) => void;
}

export type RuntimeEvent =
  | { type: "state"; data: unknown }
  | { type: "log"; level: "info" | "warn" | "error"; message: string }
  | { type: "chat"; username: string; message: string }
  | { type: "error"; message: string; data?: unknown }
  | { type: "command_started"; commandId: string; command: string; data: unknown }
  | { type: "command_finished"; commandId: string; command: string; ok: true; data: unknown }
  | { type: "command_failed"; commandId: string; command: string; ok: false; reason: string; message: string }
  | { type: "command_cancelled"; commandId: string; command: string; ok: false; reason: string; message: string }
  | { type: "crafting_window_changed"; windowType: "crafting_table" | "furnace" | null };

export interface RuntimeServerStatus {
  http: { listening: boolean; host: string; port: number; url: string | null; error: string | null };
  webSocket: { enabled: boolean; path: string; clients: number; error: string | null };
}

export function createRuntimeHttpServer(options: RuntimeHttpServerOptions): RuntimeHttpServer {
  const clients = new Set<Duplex>();
  const recentEvents: RuntimeEvent[] = [];
  const status: RuntimeServerStatus = {
    http: { listening: false, host: options.config.host, port: options.config.port, url: null, error: null },
    webSocket: { enabled: true, path: "/ws", clients: 0, error: null }
  };
  const server = createServer((request, response) => {
    void routeRequest(request, response, options);
  });
  server.on("upgrade", (request, socket) => {
    if (request.url !== "/ws") {
      socket.destroy();
      return;
    }
    acceptWebSocket(request, socket, clients, status, recentEvents);
  });

  return {
    status,
    publicDir: options.publicDir ?? PUBLIC_DIR,
    start: async () => {
      await new Promise<void>((resolve, reject) => {
        const onError = (error: Error): void => {
          status.http.error = error.message;
          reject(error);
        };
        server.once("error", onError);
        server.listen(options.config.port, options.config.host, () => {
          server.off("error", onError);
          status.http.listening = true;
          status.http.url = `http://${options.config.host}:${options.config.port}`;
          resolve();
        });
      });
    },
    stop: async () => {
      for (const client of clients) {
        client.destroy();
      }
      if (!server.listening) {
        return;
      }
      await closeServer(server);
      status.http.listening = false;
      status.http.url = null;
    },
    broadcast: (event: RuntimeEvent) => {
      recentEvents.push(event);
      if (recentEvents.length > 200) {
        recentEvents.shift();
      }
      const frame = encodeWebSocketTextFrame(JSON.stringify(event));
      for (const client of clients) {
        if (client.destroyed || !client.writable) {
          clients.delete(client);
          status.webSocket.clients = clients.size;
          continue;
        }
        client.write(frame, (error) => {
          if (error) {
            clients.delete(client);
            client.destroy();
            status.webSocket.clients = clients.size;
          }
        });
      }
    }
  };
}

async function routeRequest(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  // UI static file routes
  if (request.method === "GET" && (request.url === "/" || request.url === "/ui")) {
    serveIndexHtml(response, options.publicDir ?? PUBLIC_DIR);
    return;
  }
  if (request.method === "GET" && request.url?.startsWith("/ui/")) {
    serveStaticFile(request.url, response, options.publicDir ?? PUBLIC_DIR);
    return;
  }

  if (request.method === "GET" && request.url === "/api/health") {
    writeJson(response, 200, serializeHealth(options.health()));
    return;
  }
  if (request.method === "GET" && request.url === "/api/state") {
    writeJson(response, 200, serializeState(options.state(), options.commands?.queue.currentCommand ?? null));
    return;
  }
  if (request.method === "GET" && request.url === "/api/observation") {
    const observation = await options.observation?.() ?? null;
    if (observation === null) {
      writeJson(response, 503, {
        ok: false,
        error: "observation_unavailable",
        message: "Rich observation is unavailable because the bot has not spawned."
      });
      return;
    }
    writeJson(response, 200, observation);
    return;
  }
  if (request.method === "POST" && request.url === "/api/chat/send") {
    await sendChat(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/fine-control") {
    await fineControl(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/look-at") {
    await queuedAction(request, response, options, "look_at", parseLookAt, (actions, input) => actions.lookAt(input.target));
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/rotate") {
    await rotateCommand(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/look") {
    await queuedAction(request, response, options, "look", parseLook, (actions, input) => actions.look(input));
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/sync-orientation") {
    await syncOrientationCommand(response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/walk-to") {
    await queuedAction(request, response, options, "walk_to", (body) => parseWalkTo(body, options.commands?.maxChunkLimit), (actions, input, signal) => actions.walkTo(input, signal));
    return;
  }
  if (request.method === "POST" && request.url === "/api/world/find-block") {
    await findBlock(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/world/interactables") {
    await findInteractables(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/mine-block") {
    await queuedAction(request, response, options, "mine_block", parseMineBlock, (actions, input) => actions.mineBlock(input));
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/place-block") {
    await queuedAction(request, response, options, "place_block", parsePlaceBlock, (actions, input) => actions.placeBlock(input));
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/jump-place-block") {
    await queuedAction(request, response, options, "jump_place_block", parsePlaceBlock, (actions, input) => actions.jumpPlaceBlock(input));
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/pillar-up") {
    await queuedAction(request, response, options, "pillar_up", () => ({ ok: true, value: {} }), (actions) => actions.pillarUp());
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/use-block") {
    await handleUseBlock(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/use-item") {
    await queuedAction(request, response, options, "use_item", parseUseItem, (actions) => actions.useHeldItem());
    return;
  }
  if (request.method === "POST" && request.url === "/api/chest/deposit") {
    await queuedAction(request, response, options, "chest_deposit", parseChestInput, (actions, input) => actions.chestDeposit(input));
    return;
  }
  if (request.method === "POST" && request.url === "/api/chest/withdraw") {
    await queuedAction(request, response, options, "chest_withdraw", parseChestInput, (actions, input) => actions.chestWithdraw(input));
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/attack-entity") {
    await queuedAction(request, response, options, "attack_entity", parseAttackEntity, (actions, input) => actions.attackEntity(input));
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/inspect") {
    await inspectBlock(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/frame/capture") {
    await captureFrame(response, options);
    return;
  }
  if (request.method === "GET" && request.url === "/api/frame/current") {
    await getCurrentFrame(response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/targeting/resolve-pixel") {
    await resolvePixelTarget(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/command/stop") {
    await stopCommand(response, options);
    return;
  }
  if (request.method === "GET" && request.url === "/api/inventory") {
    handleInventoryGet(response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/hotbar/select") {
    await handleHotbarSelect(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/inventory/select") {
    await handleInventorySelect(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/inventory/equip") {
    await handleInventoryEquip(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/crafting/open-inventory") {
    await handleCraftingOpenInventory(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/crafting/open-crafting-table") {
    await handleCraftingOpenCraftingTable(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/crafting/set-grid") {
    await handleCraftingSetGrid(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/crafting/take-output") {
    await handleCraftingTakeOutput(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/crafting/clear-grid") {
    await handleCraftingClearGrid(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/crafting/close-window") {
    await handleCraftingCloseWindow(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/crafting/craft-item") {
    await handleCraftItem(request, response, options);
    return;
  }
  if (request.method === "POST" && request.url === "/api/furnace/smelt") {
    await handleFurnaceSmelt(request, response, options);
    return;
  }

  console.error('[HTTP] 404 unmatched:', request.method, request.url);
  writeJson(response, 404, { error: "not_found" });
}

async function sendChat(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }

  const text = typeof parsed.body.text === "string" ? parsed.body.text.trim() : "";
  if (text.length === 0) {
    writeJson(response, 400, {
      ok: false,
      error: "invalid_chat_text",
      message: "Chat text must be a non-empty string."
    });
    return;
  }
  const commandPolicy = validateChatCommand(text);
  if (!commandPolicy.ok) {
    writeJson(response, 403, {
      ok: false,
      error: "console_command_forbidden",
      message: commandPolicy.message,
      command: commandPolicy.command
    });
    return;
  }
  if (!options.chat) {
    writeJson(response, 503, {
      ok: false,
      error: "chat_unavailable",
      message: "Chat is unavailable because the bot runtime is not ready."
    });
    return;
  }

  try {
    await options.chat.send(text);
    writeJson(response, 200, { ok: true, message: "Chat sent.", text });
  } catch (error) {
    writeJson(response, 503, {
      ok: false,
      error: "chat_send_failed",
      message: error instanceof Error ? error.message : String(error)
    });
  }
}

export function validateChatCommand(text: string):
  | { ok: true }
  | { ok: false; command: string; message: string } {
  const trimmed = text.trim();
  if (!trimmed.startsWith("/")) {
    return { ok: true };
  }
  // Step 2 deliberately permits only the character's own, argument-free
  // death command. The MCP layer still requires observed death and respawn
  // counters before it can issue an actual-effect receipt.
  if (trimmed.toLowerCase() === "/kill") {
    return { ok: true };
  }
  const command = trimmed.slice(1).split(/\s+/, 1)[0]?.toLowerCase() ?? "";
  if (ALLOWED_CHAT_COMMANDS.has(command)) {
    return { ok: true };
  }
  return {
    ok: false,
    command,
    message:
      `Console command /${command || "<empty>"} is unavailable to this character. ` +
      "Only communication and informational commands are permitted; progression must use survival actions."
  };
}

async function fineControl(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.commands) {
    writeJson(response, 503, {
      ok: false,
      error: "commands_unavailable",
      message: "Commands are unavailable because the bot runtime is not ready."
    });
    return;
  }

  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }

  const body = parseFineControl(parsed.body, options.commands.maxFineControlDurationMs ?? 3000);
  if (!body.ok) {
    writeJson(response, 400, { ok: false, error: body.error, message: body.message });
    return;
  }

  const accepted = options.commands.queue.enqueueOrReject({
    name: "fine_control",
    input: { ...body.command, source: "browser" },
    timeoutMs: body.command.durationMs + 250,
    run: async ({ signal, log }) => {
      await options.commands?.applyControlStates(body.command.controls);
      log(`Applied fine-control states for ${body.command.durationMs} ms.`);
      await waitForDuration(body.command.durationMs, signal);
      return { ok: true, message: "Fine control completed." };
    }
  });
  if (!accepted.accepted) {
    writeJson(response, accepted.statusCode, { ok: false, error: accepted.error, message: accepted.message });
    return;
  }

  const completion = await accepted.completed;
  writeCommandCompletion(response, completion);
}

async function syncOrientationCommand(response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.commands) {
    writeJson(response, 503, {
      ok: false,
      error: "commands_unavailable",
      message: "Commands are unavailable because the bot runtime is not ready."
    });
    return;
  }

  try {
    options.commands.actions.syncOrientation();
    const orient = options.commands.actions.getOrientation();
    writeJson(response, 200, {
      ok: true,
      message: "Orientation synced.",
      yaw: orient.yaw,
      pitch: orient.pitch
    });
  } catch (error) {
    writeJson(response, 500, {
      ok: false,
      error: "sync_failed",
      message: error instanceof Error ? error.message : String(error)
    });
  }
}

async function rotateCommand(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.commands) {
    writeJson(response, 503, {
      ok: false,
      error: "commands_unavailable",
      message: "Commands are unavailable because the bot runtime is not ready."
    });
    return;
  }

  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }

  const body = parsed.body;
  const yawDelta = typeof body.yaw === "number" ? body.yaw : 0;
  const pitchDelta = typeof body.pitch === "number" ? body.pitch : 0;
  if (Math.abs(yawDelta) > 180 || Math.abs(pitchDelta) > 90) {
    writeJson(response, 400, { ok: false, error: "invalid_angles", message: "yaw must be within +/-180 and pitch within +/-90." });
    return;
  }

  const accepted = options.commands.queue.enqueueOrReject({
    name: "rotate",
    input: { yawDelta, pitchDelta },
    timeoutMs: 3000,
    run: async ({ log }) => {
      // Read yaw/pitch at execution time so queued commands rotate relative to the
      // bot's actual current orientation, not the stale values from request arrival.
      // Request convention: yaw > 0 turns right (clockwise from above), pitch > 0
      // looks up. Mineflayer yaw increases counterclockwise, hence the subtraction.
      const orient = options.commands!.actions.getOrientation();
      const result = await options.commands!.actions.look({
        yaw: orient.yaw - yawDelta,
        pitch: orient.pitch + pitchDelta
      });
      log(`Rotated by yaw=${yawDelta} pitch=${pitchDelta} (${result.message})`);
      return result;
    }
  });
  if (!accepted.accepted) {
    writeJson(response, accepted.statusCode, { ok: false, error: accepted.error, message: accepted.message });
    return;
  }

  const completion = await accepted.completed;
  writeCommandCompletion(response, completion);
}

async function queuedAction<T>(
  request: IncomingMessage,
  response: ServerResponse,
  options: RuntimeHttpServerOptions,
  name: string,
  parse: (body: Record<string, unknown>) => Parsed<T>,
  run: (actions: PhysicalCommandActions, input: T, signal?: AbortSignal) => ReturnType<PhysicalCommandActions["lookAt"]>
): Promise<void> {
  if (!options.commands) {
    writeJson(response, 503, {
      ok: false,
      error: "commands_unavailable",
      message: "Commands are unavailable because the bot runtime is not ready."
    });
    return;
  }

  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }

  const input = parse(parsed.body);
  if (!input.ok) {
    writeJson(response, 400, { ok: false, error: input.error, message: input.message });
    return;
  }

  const accepted = options.commands.queue.enqueueOrReject({
    name,
    input: { ...input.value, source: "browser" },
    timeoutMs: commandTimeout(parsed.body),
    run: async (context) => run(options.commands!.actions, input.value, context?.signal)
  });
  if (!accepted.accepted) {
    writeJson(response, accepted.statusCode, { ok: false, error: accepted.error, message: accepted.message });
    return;
  }

  writeCommandCompletion(response, await accepted.completed);
}

async function handleUseBlock(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.commands) {
    writeJson(response, 503, {
      ok: false,
      error: "commands_unavailable",
      message: "Commands are unavailable because the bot runtime is not ready."
    });
    return;
  }

  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }

  const input = parseUseBlock(parsed.body);
  if (!input.ok) {
    writeJson(response, 400, { ok: false, error: input.error, message: input.message });
    return;
  }

  const accepted = options.commands.queue.enqueueOrReject({
    name: "use_block",
    input: { ...input.value, source: "browser" },
    timeoutMs: commandTimeout(parsed.body),
    run: async () => options.commands!.actions.useBlock(input.value)
  });
  if (!accepted.accepted) {
    writeJson(response, accepted.statusCode, { ok: false, error: accepted.error, message: accepted.message });
    return;
  }

  const completion = await accepted.completed;
  writeCommandCompletion(response, completion);

  // If use-block opened a crafting/furnace window, broadcast to WebSocket clients
  if (completion.data && typeof completion.data === "object" && !Array.isArray(completion.data)) {
    const data = completion.data as Record<string, unknown>;
    const windowType = data.windowType;
    if (windowType === "crafting_table" || windowType === "furnace") {
      options.broadcast?.({ type: "crafting_window_changed", windowType });
    }
  }
}

async function inspectBlock(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.commands) {
    writeJson(response, 503, {
      ok: false,
      error: "commands_unavailable",
      message: "Commands are unavailable because the bot runtime is not ready."
    });
    return;
  }

  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }
  const input = parseBlockTarget(parsed.body, "block");
  if (!input.ok) {
    writeJson(response, 400, { ok: false, error: input.error, message: input.message });
    return;
  }

  const result = await options.commands.actions.inspectBlock(input.value);
  // Record evidence for read-only inspect (bypasses command queue)
  await recordReadonlyCommand(options, "inspect", input.value, result);
  writeJson(response, result.ok ? 200 : 404, result);
}

async function findBlock(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.commands) {
    writeJson(response, 503, {
      ok: false,
      error: "commands_unavailable",
      message: "Commands are unavailable because the bot runtime is not ready."
    });
    return;
  }

  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }
  const input = parseFindBlock(parsed.body);
  if (!input.ok) {
    writeJson(response, 400, { ok: false, error: input.error, message: input.message });
    return;
  }

  const result = await options.commands.actions.findBlock(input.value);
  await recordReadonlyCommand(options, "find_block", input.value, result);
  writeJson(response, result.ok ? 200 : 404, result);
}

async function findInteractables(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.commands) {
    writeJson(response, 503, {
      ok: false,
      error: "commands_unavailable",
      message: "Commands are unavailable because the bot runtime is not ready."
    });
    return;
  }

  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }
  const input = parseInteractables(parsed.body);
  if (!input.ok) {
    writeJson(response, 400, { ok: false, error: input.error, message: input.message });
    return;
  }

  const result = await options.commands.actions.findInteractables(input.value);
  await recordReadonlyCommand(options, "find_interactables", input.value, result);
  writeJson(response, 200, result);
}

async function stopCommand(response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.commands) {
    writeJson(response, 503, {
      ok: false,
      error: "commands_unavailable",
      message: "Commands are unavailable because the bot runtime is not ready."
    });
    return;
  }

  try {
    writeJson(response, 200, await options.commands.queue.cancelCurrent());
  } catch (error) {
    writeJson(response, 500, {
      ok: false,
      error: "command_cleanup_failed",
      message: error instanceof Error ? error.message : String(error)
    });
  }
}

async function handleInventoryGet(response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.inventory) {
    writeJson(response, 503, {
      ok: false,
      error: "inventory_unavailable",
      message: "Inventory is unavailable because the bot runtime is not ready."
    });
    return;
  }

  const inventory = options.inventory.getInventory();
  // Record evidence for read-only inventory query
  await recordReadonlyCommand(options, "get_inventory", {}, { ok: true, message: "Inventory retrieved." });
  writeJson(response, 200, inventory);
}

async function handleHotbarSelect(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.inventory) {
    writeJson(response, 503, {
      ok: false,
      error: "inventory_unavailable",
      message: "Inventory is unavailable because the bot runtime is not ready."
    });
    return;
  }

  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }

  const result = parseHotbarSelect(parsed.body);
  if (!result.ok) {
    writeJson(response, 400, { ok: false, error: result.error, message: result.message });
    return;
  }

  // Frontend sends hotbarIndex; backend service expects slot
  const outcome = await options.inventory.selectHotbar(result.value);
  writeJson(response, outcome.ok ? 200 : 400, outcome);
}

async function handleInventorySelect(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.inventory) {
    writeJson(response, 503, {
      ok: false,
      error: "inventory_unavailable",
      message: "Inventory is unavailable because the bot runtime is not ready."
    });
    return;
  }

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

  const outcome = await options.inventory.selectHotbar(result.value);
  await recordReadonlyCommand(options, "select_hotbar", { slot: result.value }, outcome);
  writeJson(response, outcome.ok ? 200 : 400, outcome);
}

async function handleInventoryEquip(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.inventory) {
    writeJson(response, 503, {
      ok: false,
      error: "inventory_unavailable",
      message: "Inventory is unavailable because the bot runtime is not ready."
    });
    return;
  }

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

  const outcome = await options.inventory.equipItem(result.value);
  await recordReadonlyCommand(options, "equip_item", { itemName: result.value }, outcome);
  writeJson(response, outcome.ok ? 200 : 404, outcome);
}

function parseHotbarSelect(body: Record<string, unknown>): { ok: true; value: number } | { ok: false; error: string; message: string } {
  const hotbarIndex = body.hotbarIndex;
  if (hotbarIndex === undefined || !Number.isInteger(hotbarIndex)) {
    return { ok: false, error: "invalid_hotbar_index", message: "hotbarIndex must be an integer." };
  }
  if ((hotbarIndex as number) < 0 || (hotbarIndex as number) > 8) {
    return { ok: false, error: "hotbar_index_out_of_range", message: `hotbarIndex ${hotbarIndex} is out of range (0-8).` };
  }
  return { ok: true, value: hotbarIndex as number };
}

function parseInventorySelect(body: Record<string, unknown>): { ok: true; value: number } | { ok: false; error: string; message: string } {
  const slot = body.slot;
  if (slot === undefined || !Number.isInteger(slot)) {
    return { ok: false, error: "invalid_slot", message: "slot must be an integer." };
  }
  if ((slot as number) < 0 || (slot as number) > 8) {
    return { ok: false, error: "slot_out_of_range", message: `Slot ${slot} is out of range (0-8).` };
  }
  return { ok: true, value: slot as number };
}

function parseInventoryEquip(body: Record<string, unknown>): { ok: true; value: string } | { ok: false; error: string; message: string } {
  const itemName = body.itemName;
  if (typeof itemName !== "string" || itemName.trim().length === 0) {
    return { ok: false, error: "invalid_item_name", message: "itemName must be a non-empty string." };
  }
  return { ok: true, value: itemName.trim() };
}

async function handleCraftingSetGrid(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.crafting) {
    writeJson(response, 503, {
      ok: false,
      error: "crafting_unavailable",
      message: "Crafting is unavailable because the bot runtime is not ready."
    });
    return;
  }

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

  const outcome = await options.crafting.setGrid(result.value);
  writeJson(response, outcome.ok ? 200 : 400, outcome);
}

async function handleCraftingTakeOutput(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.crafting) {
    writeJson(response, 503, {
      ok: false,
      error: "crafting_unavailable",
      message: "Crafting is unavailable because the bot runtime is not ready."
    });
    return;
  }

  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }

  const outcome = await options.crafting.takeOutput();
  writeJson(response, outcome.ok ? 200 : 400, outcome);
}

async function handleCraftingClearGrid(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.crafting) {
    writeJson(response, 503, {
      ok: false,
      error: "crafting_unavailable",
      message: "Crafting is unavailable because the bot runtime is not ready."
    });
    return;
  }

  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }

  const outcome = await options.crafting.clearGrid();
  writeJson(response, outcome.ok ? 200 : 400, outcome);
}

async function handleCraftingOpenInventory(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.crafting) {
    writeJson(response, 503, {
      ok: false,
      error: "crafting_unavailable",
      message: "Crafting is unavailable because the bot runtime is not ready."
    });
    return;
  }

  const outcome = await options.crafting.openInventoryCrafting();
  writeJson(response, outcome.ok ? 200 : 400, outcome);
}

async function handleCraftingOpenCraftingTable(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.crafting) {
    writeJson(response, 503, {
      ok: false,
      error: "crafting_unavailable",
      message: "Crafting is unavailable because the bot runtime is not ready."
    });
    return;
  }

  const outcome = await options.crafting.openCraftingTable();
  writeJson(response, outcome.ok ? 200 : 400, outcome);
}

async function handleCraftingCloseWindow(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.crafting) {
    writeJson(response, 503, {
      ok: false,
      error: "crafting_unavailable",
      message: "Crafting is unavailable because the bot runtime is not ready."
    });
    return;
  }

  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }

  const outcome = await options.crafting.closeWindow();
  writeJson(response, outcome.ok ? 200 : 400, outcome);
}

async function handleCraftItem(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.crafting) {
    writeJson(response, 503, { ok: false, error: "crafting_unavailable", message: "Crafting is unavailable because the bot runtime is not ready." });
    return;
  }
  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }
  const itemName = typeof parsed.body.itemName === "string" ? parsed.body.itemName.trim() : "";
  const repetitions = parsed.body.repetitions ?? 1;
  if (!itemName || !Number.isInteger(repetitions) || (repetitions as number) <= 0) {
    writeJson(response, 400, { ok: false, error: "invalid_craft_request", message: "itemName must be non-empty and repetitions must be a positive integer." });
    return;
  }
  const outcome = await options.crafting.craftItem(itemName, repetitions as number);
  writeJson(response, outcome.ok ? 200 : 400, outcome);
}

async function handleFurnaceSmelt(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.crafting) {
    writeJson(response, 503, { ok: false, error: "crafting_unavailable", message: "Smelting is unavailable because the bot runtime is not ready." });
    return;
  }
  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }
  const inputItemName = typeof parsed.body.inputItemName === "string" ? parsed.body.inputItemName.trim() : "";
  const fuelItemName = typeof parsed.body.fuelItemName === "string" ? parsed.body.fuelItemName.trim() : "";
  const inputCount = parsed.body.inputCount;
  const fuelCount = parsed.body.fuelCount;
  const timeoutMs = parsed.body.timeoutMs ?? 60000;
  if (!inputItemName || !fuelItemName || !Number.isInteger(inputCount) || (inputCount as number) <= 0 || !Number.isInteger(fuelCount) || (fuelCount as number) <= 0 || !Number.isInteger(timeoutMs) || (timeoutMs as number) <= 0) {
    writeJson(response, 400, {
      ok: false,
      error: "invalid_smelting_request",
      message: "inputItemName and fuelItemName must be non-empty; inputCount, fuelCount, and timeoutMs must be positive integers."
    });
    return;
  }
  const outcome = await options.crafting.smelt(inputItemName, inputCount as number, fuelItemName, fuelCount as number, timeoutMs as number);
  writeJson(response, outcome.ok ? 200 : 400, outcome);
}

async function captureFrame(response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  console.log('[HTTP] frame-capture: starting');
  if (!options.frames) {
    writeJson(response, 503, {
      ok: false,
      error: "frame_capture_unavailable",
      message: "Frame capture is unavailable because the runtime is not ready."
    });
    return;
  }

  const result = await options.frames.capture();
  if (!result.ok) {
    writeJson(response, result.reason === "capture_failed" ? 500 : 503, {
      ok: false,
      error: result.reason,
      message: result.message
    });
    return;
  }

  writeJson(response, 200, {
    ok: true,
    frameId: result.bundle.frameId,
    pngPath: result.bundle.pngPath,
    metadataPath: result.bundle.metadataPath,
    metadata: result.bundle.metadata
  });
}

async function getCurrentFrame(response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  if (!options.frames) {
    writeJson(response, 503, {
      ok: false,
      error: "frame_capture_unavailable",
      message: "Frame capture is unavailable because the runtime is not ready."
    });
    return;
  }

  const result = await options.frames.capture();
  if (!result.ok) {
    writeJson(response, result.reason === "capture_failed" ? 500 : 503, {
      ok: false,
      error: result.reason,
      message: result.message
    });
    return;
  }

  let pngBytes: Buffer;
  try {
    pngBytes = readFileSync(result.bundle.pngPath);
  } catch (err) {
    writeJson(response, 500, {
      ok: false,
      error: "capture_failed",
      message: err instanceof Error ? err.message : "Failed to read PNG file."
    });
    return;
  }

  writeJson(response, 200, {
    ok: true,
    frameId: result.bundle.frameId,
    pngBase64: pngBytes.toString("base64"),
    metadata: result.bundle.metadata
  });
}

/**
 * Record evidence for read-only commands (inspect, inventory) that bypass the command queue.
 * These commands don't go through enqueueOrReject so they need direct evidence recording.
 */
async function recordReadonlyCommand(
  options: RuntimeHttpServerOptions,
  commandName: string,
  input: unknown,
  result: { ok: boolean; message: string; reason?: string; data?: unknown }
): Promise<void> {
  if (!options.evidence) {
    return;
  }
  const now = new Date().toISOString();
  const cmd: CommandRecord = {
    id: null,
    runId: "default",
    evidenceType: "command",
    commandId: `cmd_${Date.now()}_readonly_${Math.random().toString(36).slice(2, 8)}`,
    command: commandName,
    status: (result.ok ? "succeeded" : "failed") as CommandRecord["status"],
    input: { ...(input as Record<string, unknown>), source: "browser" },
    acceptedAt: now,
    startedAt: now,
    finishedAt: now,
    durationMs: 0,
    ok: result.ok,
    reason: result.reason ?? null,
    message: result.message,
    data: result.data ?? null,
    recordedAt: now
  };
  try {
    await options.evidence.recordCommand(cmd);
  } catch {
    // Evidence recording must not block command responses
  }
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

async function resolvePixelTarget(request: IncomingMessage, response: ServerResponse, options: RuntimeHttpServerOptions): Promise<void> {
  console.log('[HTTP] resolve-pixel: url=', request.url);
  if (!options.targeting) {
    writeJson(response, 503, {
      ok: false,
      error: "targeting_unavailable",
      message: "Pixel targeting is unavailable because the runtime is not ready."
    });
    return;
  }

  const parsed = await readJson(request);
  if (!parsed.ok) {
    writeJson(response, 400, { ok: false, error: "invalid_json", message: parsed.message });
    return;
  }

  const input = parsePixelTarget(parsed.body);
  if (!input.ok) {
    writeJson(response, 400, { ok: false, error: input.error, message: input.message });
    return;
  }

  const result = await options.targeting.resolve(input.value);
  if (result.ok) {
    writeJson(response, 200, result);
    return;
  }

  const statusCode = result.reason === "frame_not_found" ? 404 : result.reason === "world_not_loaded" ? 424 : 404;
  writeJson(response, statusCode, { ok: false, error: result.reason, reason: result.reason, message: result.message });
}

type Parsed<T> = { ok: true; value: T } | { ok: false; error: string; message: string };

function parseFineControl(body: Record<string, unknown>, maxDurationMs: number):
  | { ok: true; command: { controls: ControlStates; durationMs: number } }
  | { ok: false; error: string; message: string } {
  const controlsInput = body.controls;
  if (!controlsInput || typeof controlsInput !== "object" || Array.isArray(controlsInput)) {
    return { ok: false, error: "invalid_controls", message: "controls must be a JSON object." };
  }

  const controls: ControlStates = {};
  for (const name of controlNames) {
    const value = (controlsInput as Record<string, unknown>)[name];
    if (value !== undefined && typeof value !== "boolean") {
      return { ok: false, error: "invalid_controls", message: `${name} must be a boolean when supplied.` };
    }
    if (typeof value === "boolean") {
      controls[name] = value;
    }
  }

  const durationMs = body.durationMs;
  if (!Number.isInteger(durationMs) || typeof durationMs !== "number" || durationMs <= 0 || durationMs > maxDurationMs) {
    return { ok: false, error: "invalid_duration", message: `durationMs must be between 1 and ${maxDurationMs}.` };
  }

  return { ok: true, command: { controls, durationMs } };
}

function parseLookAt(body: Record<string, unknown>): Parsed<{ target: Vector3 }> {
  const target = parseVector(body.target, "target", false);
  return target.ok ? { ok: true, value: { target: target.value } } : target;
}

function parseLook(body: Record<string, unknown>): Parsed<{ yaw: number; pitch: number }> {
  const yaw = body.yaw;
  const pitch = body.pitch;
  if (typeof yaw !== "number" || !Number.isFinite(yaw) || typeof pitch !== "number" || !Number.isFinite(pitch)) {
    return { ok: false, error: "invalid_angles", message: "yaw and pitch must be finite numbers in degrees." };
  }
  return { ok: true, value: { yaw, pitch } };
}

function parseWalkTo(body: Record<string, unknown>, maxChunkLimit = 8): Parsed<{ target: Vector3; tolerance: number; chunkLimit: number }> {
  const target = parseVector(body.target, "target", false);
  if (!target.ok) {
    return target;
  }
  const tolerance = optionalPositiveNumber(body.tolerance, 1.5, "invalid_tolerance", "tolerance must be a positive number.");
  if (!tolerance.ok) {
    return tolerance;
  }
  const chunkLimit = (body.chunkLimit ?? 3) as unknown;
  if (typeof chunkLimit !== "number" || !Number.isInteger(chunkLimit) || chunkLimit < 1) {
    return { ok: false, error: "invalid_chunk_limit", message: "chunkLimit must be a positive integer (chunks)." };
  }
  if (chunkLimit > maxChunkLimit) {
    return {
      ok: false,
      error: "chunk_limit_exceeded",
      message: `error: requested chunk limit (${chunkLimit}) greater than allowed (${maxChunkLimit})`
    };
  }
  return { ok: true, value: { target: target.value, tolerance: tolerance.value, chunkLimit } };
}

function parseMineBlock(body: Record<string, unknown>): Parsed<{ block: Vector3; walkIntoRange: boolean }> {
  const block = parseBlockTarget(body, "block");
  if (!block.ok) {
    return block;
  }
  return { ok: true, value: { block: block.value, walkIntoRange: booleanValue(body.walkIntoRange, false) } };
}

function parseInteractables(body: Record<string, unknown>): Parsed<{ maxDistance: number }> {
  const maxDistance = body.maxDistance ?? 16;
  if (typeof maxDistance !== "number" || !Number.isFinite(maxDistance) || maxDistance < 1 || maxDistance > 64) {
    return { ok: false, error: "invalid_max_distance", message: "maxDistance must be between 1 and 64." };
  }
  return { ok: true, value: { maxDistance } };
}

function parseFindBlock(body: Record<string, unknown>): Parsed<{ blockName: string; maxDistance: number; requireVisible: boolean }> {
  const blockName = typeof body.blockName === "string" ? body.blockName.trim() : "";
  if (!blockName) {
    return { ok: false, error: "invalid_block_name", message: "blockName must be a non-empty string." };
  }
  const maxDistance = typeof body.maxDistance === "number" ? body.maxDistance : 32;
  if (!Number.isFinite(maxDistance) || maxDistance < 1 || maxDistance > 256) {
    return { ok: false, error: "invalid_max_distance", message: "maxDistance must be between 1 and 256." };
  }
  // Anti-x-ray is hard-locked server-side: callers (including skills, which
  // talk to this HTTP API directly) cannot disable line-of-sight filtering.
  return { ok: true, value: { blockName, maxDistance, requireVisible: true } };
}

function parsePlaceBlock(body: Record<string, unknown>): Parsed<{ referenceBlock: Vector3; face: Vector3; walkIntoRange: boolean }> {
  const referenceBlock = parseVector(body.referenceBlock, "referenceBlock", true);
  if (!referenceBlock.ok) {
    return referenceBlock;
  }
  const face = parseVector(body.face, "face", true);
  if (!face.ok) {
    return face.error === "invalid_face" ? face : { ok: false, error: "invalid_face", message: "face must be an axis-aligned unit vector." };
  }
  if (!isFace(face.value)) {
    return { ok: false, error: "invalid_face", message: "face must be an axis-aligned unit vector." };
  }
  return { ok: true, value: { referenceBlock: referenceBlock.value, face: face.value, walkIntoRange: booleanValue(body.walkIntoRange, false) } };
}

function parseUseBlock(body: Record<string, unknown>): Parsed<{ block: Vector3; walkIntoRange: boolean }> {
  const block = parseBlockTarget(body, "block");
  if (!block.ok) {
    return block;
  }
  return { ok: true, value: { block: block.value, walkIntoRange: booleanValue(body.walkIntoRange, false) } };
}

function parseUseItem(body: Record<string, unknown>): Parsed<Record<string, never>> {
  return { ok: true, value: {} };
}

function parseChestInput(body: Record<string, unknown>): Parsed<{ itemName: string; count?: number }> {
  const itemName = typeof body.itemName === "string" ? body.itemName.trim() : "";
  if (!itemName) {
    return { ok: false, error: "invalid_item_name", message: "itemName must be a non-empty string." };
  }
  let count: number | undefined;
  if (body.count !== undefined && body.count !== null) {
    count = typeof body.count === "number" ? body.count : undefined;
    if (typeof count === "number" && (!Number.isInteger(count) || count < 0)) {
      return { ok: false, error: "invalid_count", message: "count must be a non-negative integer." };
    }
    if (typeof count === "number" && count === 0) count = undefined;
  }
  return { ok: true, value: { itemName, count } };
}

function parseAttackEntity(body: Record<string, unknown>): Parsed<{ entityId: number; walkIntoRange: boolean; renavigationCount: number }> {
  const entityId = body.entityId;
  if (!Number.isInteger(entityId) || typeof entityId !== "number" || entityId < 0) {
    return { ok: false, error: "invalid_entity_id", message: "entityId must be a non-negative integer from a fresh observation." };
  }
  const renavigationCount = optionalPositiveNumber(body.renavigationCount ?? 3, 3, "invalid_renavigation_count", "renavigationCount must be a positive number.");
  if (!renavigationCount.ok) {
    return renavigationCount;
  }
  return { ok: true, value: { entityId, walkIntoRange: booleanValue(body.walkIntoRange, false), renavigationCount: Math.round(renavigationCount.value) } };
}

function parsePixelTarget(body: Record<string, unknown>): Parsed<{ frameId: string; x: number; y: number; maxDistance: number }> {
  const frameId = typeof body.frameId === "string" ? body.frameId.trim() : "";
  if (!/^[A-Za-z0-9_-]+$/.test(frameId)) {
    return { ok: false, error: "invalid_frame_id", message: "frameId must be a non-empty frame identifier." };
  }
  const x = body.x;
  const y = body.y;
  if (typeof x !== "number" || typeof y !== "number" || !Number.isFinite(x) || !Number.isFinite(y) || x < 0 || y < 0) {
    return { ok: false, error: "invalid_pixel", message: "x and y must be finite non-negative pixel coordinates." };
  }
  const maxDistance = body.maxDistance;
  if (typeof maxDistance !== "number" || !Number.isFinite(maxDistance) || maxDistance <= 0) {
    return { ok: false, error: "invalid_max_distance", message: "maxDistance must be a positive number." };
  }
  return { ok: true, value: { frameId, x, y, maxDistance } };
}

function parseBlockTarget(body: Record<string, unknown>, key: string): Parsed<Vector3> {
  return parseVector(body[key], key, true);
}

function parseVector(value: unknown, key: string, integer: boolean): Parsed<Vector3> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return { ok: false, error: key === "face" ? "invalid_face" : "invalid_target", message: `${key} must be a vector object.` };
  }
  const record = value as Record<string, unknown>;
  const x = record.x;
  const y = record.y;
  const z = record.z;
  const valid = typeof x === "number" && typeof y === "number" && typeof z === "number"
    && Number.isFinite(x) && Number.isFinite(y) && Number.isFinite(z)
    && (!integer || (Number.isInteger(x) && Number.isInteger(y) && Number.isInteger(z)));
  if (!valid) {
    return {
      ok: false,
      error: key === "face" ? "invalid_face" : "invalid_target",
      message: `${key} must contain finite numeric x, y, and z values${integer ? " as integers" : ""}.`
    };
  }
  return { ok: true, value: { x, y, z } };
}

function isFace(value: Vector3): boolean {
  const components = [value.x, value.y, value.z];
  return components.filter((component) => Math.abs(component) === 1).length === 1
    && components.filter((component) => component === 0).length === 2;
}

function optionalPositiveNumber(value: unknown, defaultValue: number, error: string, message: string): Parsed<number> {
  if (value === undefined) {
    return { ok: true, value: defaultValue };
  }
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
    return { ok: false, error, message };
  }
  return { ok: true, value };
}

function booleanValue(value: unknown, defaultValue: boolean): boolean {
  return typeof value === "boolean" ? value : defaultValue;
}

function commandTimeout(body: Record<string, unknown>): number | undefined {
  return typeof body.timeoutMs === "number" && Number.isInteger(body.timeoutMs) && body.timeoutMs > 0 ? body.timeoutMs : undefined;
}

function waitForDuration(durationMs: number, signal: AbortSignal): Promise<void> {
  if (signal.aborted) {
    return Promise.reject(signal.reason);
  }

  return new Promise((resolve, reject) => {
    const timeout = setTimeout(resolve, durationMs);
    signal.addEventListener("abort", () => {
      clearTimeout(timeout);
      reject(signal.reason);
    }, { once: true });
  });
}

function writeCommandCompletion(response: ServerResponse, completion: CommandCompletion): void {
  if (completion.status === "timed_out") {
    writeJson(response, 504, completion);
    return;
  }
  if (completion.status === "failed") {
    writeJson(response, 200, completion);
    return;
  }
  writeJson(response, 200, completion);
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

async function closeServer(server: Server): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    server.close((error) => {
      if (error) {
        reject(error);
        return;
      }
      resolve();
    });
  });
}

function acceptWebSocket(
  request: IncomingMessage,
  socket: Duplex,
  clients: Set<Duplex>,
  status: RuntimeServerStatus,
  recentEvents: RuntimeEvent[]
): void {
  const key = request.headers["sec-websocket-key"];
  if (typeof key !== "string") {
    socket.destroy();
    return;
  }

  const acceptKey = createHash("sha1")
    .update(`${key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11`)
    .digest("base64");
  socket.write([
    "HTTP/1.1 101 Switching Protocols",
    "Upgrade: websocket",
    "Connection: Upgrade",
    `Sec-WebSocket-Accept: ${acceptKey}`,
    "",
    ""
  ].join("\r\n"));
  clients.add(socket);
  status.webSocket.clients = clients.size;
  debugLog("info", "WebSocket client connected");

  socket.on("error", () => {
    clients.delete(socket);
    status.webSocket.clients = clients.size;
  });

  // Frame buffer for incoming WebSocket frames
  let frameBuffer: Buffer<ArrayBufferLike> = Buffer.alloc(0);
  socket.on("data", (chunk: Buffer) => {
    frameBuffer = Buffer.concat([frameBuffer, Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)]);
    // Process complete frames from the buffer, consuming processed bytes
    const remaining = processIncomingFrames(socket, frameBuffer, clients, status);
    frameBuffer = remaining.length > 0 ? remaining : Buffer.alloc(0);
  });

  for (const event of recentEvents) {
    socket.write(encodeWebSocketTextFrame(JSON.stringify(event)));
  }
  socket.on("close", () => {
    clients.delete(socket);
    status.webSocket.clients = clients.size;
    debugLog("info", "WebSocket client disconnected");
  });
}

/**
 * Process incoming WebSocket frames from the buffer.
 * Handles ping (0x9) → pong (0xA), close (0x8) frames, and discards others.
 * Client frames are masked per RFC 6455 §5.1.
 * Returns the unconsumed tail of the buffer.
 */
function processIncomingFrames(
  socket: Duplex,
  buffer: Buffer,
  clients: Set<Duplex>,
  status: RuntimeServerStatus
): Buffer {
  let offset = 0;
  while (offset + 2 <= buffer.length) {
    const finRsvOpcode = buffer[offset];
    const opcode = finRsvOpcode & 0x0f;
    const masked = (buffer[offset + 1] & 0x80) !== 0;
    let payloadLength = buffer[offset + 1] & 0x7f;
    let headerLength = 2;

    if (payloadLength === 126) {
      if (offset + 4 > buffer.length) break;
      payloadLength = buffer.readUInt16BE(offset + 2);
      headerLength = 4;
    } else if (payloadLength === 127) {
      if (offset + 10 > buffer.length) break;
      const lo = buffer.readUInt32BE(offset + 6);
      payloadLength = lo; // We only need 32-bit for reasonable payloads
      headerLength = 10;
    }

    const maskLength = masked ? 4 : 0;
    const totalFrameLength = headerLength + maskLength + payloadLength;
    if (offset + totalFrameLength > buffer.length) break;

    let payload: Buffer;
    if (masked) {
      // Unmask the payload (RFC 6455 §5.3)
      const maskKey = buffer.subarray(offset + headerLength, offset + headerLength + 4);
      payload = Buffer.alloc(payloadLength);
      const maskedData = buffer.subarray(offset + headerLength + 4, offset + totalFrameLength);
      for (let i = 0; i < payloadLength; i++) {
        payload[i] = maskedData[i] ^ maskKey[i % 4];
      }
    } else {
      payload = buffer.subarray(offset + headerLength, offset + totalFrameLength);
    }

    // Handle control frames
    if (opcode === 0x09) {
      // Ping → respond with pong, same payload
      socket.write(encodeWebSocketPongFrame(payload));
    } else if (opcode === 0x08) {
      // Close → remove client and destroy socket
      clients.delete(socket);
      status.webSocket.clients = clients.size;
      socket.destroy();
      debugLog("info", "WebSocket close frame received");
      // Stop processing — connection is closing
      offset = buffer.length;
    }

    offset += totalFrameLength;
  }
  // Return the unconsumed tail of the buffer
  return offset > 0 ? buffer.subarray(offset) : Buffer.alloc(0);
}

function encodeWebSocketTextFrame(text: string): Buffer {
  const payload = Buffer.from(text, "utf8");
  if (payload.length > 125) {
    const frame = Buffer.alloc(4);
    frame[0] = 0x81;
    frame[1] = 126;
    frame.writeUInt16BE(payload.length, 2);
    return Buffer.concat([frame, payload]);
  }

  const frame = Buffer.alloc(2);
  frame[0] = 0x81;
  frame[1] = payload.length;
  return Buffer.concat([frame, payload]);
}

/**
 * Encode a WebSocket pong control frame (opcode 0xA).
 * Server-to-client frames are NOT masked per RFC 6455 §5.1.
 */
function encodeWebSocketPongFrame(payload: Buffer): Buffer {
  if (payload.length > 125) {
    const frame = Buffer.alloc(4 + payload.length);
    frame[0] = 0x8a; // fin=1, opcode=pong
    frame[1] = 126;
    frame.writeUInt16BE(payload.length, 2);
    payload.copy(frame, 4);
    return frame;
  }

  const frame = Buffer.alloc(2 + payload.length);
  frame[0] = 0x8a; // fin=1, opcode=pong
  frame[1] = payload.length;
  payload.copy(frame, 2);
  return frame;
}

function serveIndexHtml(response: ServerResponse, publicDir: string): void {
  const indexPath = join(publicDir, "index.html");
  if (!existsSync(indexPath)) {
    writeJson(response, 404, { error: "UI not found", message: "index.html not found in public directory." });
    return;
  }
  try {
    const content = readFileSync(indexPath, "utf8");
    response.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    response.end(content);
  } catch {
    writeJson(response, 500, { error: "read_failed", message: "Failed to read index.html." });
  }
}

function serveStaticFile(url: string, response: ServerResponse, publicDir: string): void {
  const relativePath = url.startsWith("/ui/") ? url.slice(4) : url.slice(1);
  // Prevent directory traversal
  const normalized = relativePath.replace(/\.\.[\/\\]/g, "");
  const filePath = join(publicDir, normalized);
  if (!filePath.startsWith(publicDir)) {
    writeJson(response, 403, { error: "forbidden" });
    return;
  }
  if (!existsSync(filePath)) {
    writeJson(response, 404, { error: "not_found", message: normalized });
    return;
  }
  try {
    const stats = statSync(filePath);
    if (!stats.isFile()) {
      writeJson(response, 403, { error: "forbidden" });
      return;
    }
    const ext = filePath.split(".").pop() ?? "";
    const contentType = getStaticContentType(ext);
    const content = readFileSync(filePath);
    response.writeHead(200, { "content-type": contentType });
    response.end(content);
  } catch {
    writeJson(response, 500, { error: "read_failed", message: normalized });
  }
}

function getStaticContentType(ext: string): string {
  const map: Record<string, string> = {
    html: "text/html; charset=utf-8",
    css: "text/css; charset=utf-8",
    js: "application/javascript; charset=utf-8",
    json: "application/json; charset=utf-8",
    png: "image/png",
    jpg: "image/jpeg",
    gif: "image/gif",
    svg: "image/svg+xml",
    ico: "image/x-icon",
    woff: "font/woff",
    woff2: "font/woff2",
    ttf: "font/ttf",
    txt: "text/plain; charset=utf-8"
  };
  return map[ext] ?? "application/octet-stream";
}
