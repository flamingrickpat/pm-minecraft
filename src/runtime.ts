import { parseRuntimeConfig, type RuntimeConfig } from "./config.js";
import { createLiveBot, type BotRuntime } from "./bot/liveBot.js";
import { CommandQueue } from "./commands/commandQueue.js";
import type { ControlStates } from "./commands/controls.js";
import { checkPaperReachable, type PaperReachability } from "./bot/paper.js";
import { createRuntimeHttpServer, type RuntimeEvent } from "./server/http.js";
import type { HealthInput } from "./server/health.js";
import { createViewerRuntime, type ViewerRuntime } from "./viewer/viewer.js";
import { createBrowserFrameImageCapture } from "./viewer/browserCapture.js";
import { botHudLines, createFrameBundleCapture } from "./targeting/frameBundle.js";
import { createFrameMetadataFileStore, createPixelTargeting } from "./targeting/pixelTargeting.js";
import { createInventoryService, type InventoryService } from "./inventory/inventoryService.js";
import { createCraftingService, type CraftingService } from "./crafting/craftingService.js";
import { reconnectDelayMs } from "./bot/reconnectPolicy.js";
import { createEvidenceStore, type EvidenceStore } from "./evidence/index.js";
import { createActionLogger } from "./logging/actionLogger.js";
import { buildLLMState } from "./state/llmState.js";
import { join } from "node:path";
import { mkdir, writeFile } from "node:fs/promises";

/**
 * Runtime parts need one product composition path; compose bot, HTTP, and viewer lifecycle behind one start call.
 *
 * @remarks
 * archetype: coordinator
 * participants: runtime config, Mineflayer connection, HTTP API, and prismarine-viewer status.
 * ordering: parse config before construction; start Paper probe, bot, viewer, and HTTP from the same runtime instance.
 * fails when: the live Paper/Mineflayer dependency is unavailable or an owned server cannot bind.
 * domain: this is the single runtime object later command, targeting, evidence, and UI work extends.
 * invariant: `npm run dev` and tests use this path rather than direct demo scripts.
 */
export interface Runtime {
  start(): Promise<void>;
  stop(): Promise<void>;
}

export interface RuntimeOptions {
  config?: RuntimeConfig;
  env?: NodeJS.ProcessEnv;
}

export function createRuntime(options: RuntimeOptions = {}): Runtime {
  const config = options.config ?? parseRuntimeConfig(options.env ?? process.env);
  const artifactRoot = process.env.MINECRAFT_BODY_LOG_DIR;
  const startedAt = new Date();
  let paper: PaperReachability = { reachable: false, checkedAt: new Date().toISOString(), error: "Paper reachability has not been checked yet" };
  let bot: BotRuntime | null = null;
  const viewer = createViewerRuntime(config.viewer, config.web.host);
  const screenshotDirectory = join(config.evidence.directory, "screenshots");
  // Auto-reconnect: how long to wait (ms) between attempts, with exponential
  // backoff. The body holds exactly ONE Mineflayer bot; when its connection
  // dies (kick, keepalive timeout, network drop) we tear it down and build a
  // fresh one so the process never sits disconnected forever.
  const RECONNECT_BASE_MS = 1000;
  const RECONNECT_MAX_MS = 15_000;
  let viewerHooked = false;
  let stateBroadcastTimer: NodeJS.Timeout | null = null;
  let reconnectTimer: NodeJS.Timeout | null = null;
  let reconnectAttempt = 0;
  let reconnecting = false;
  let stopping = false;
  const evidenceStore = createEvidenceStore(join(config.evidence.directory, "evidence.db"));
  const browserCapture = createBrowserFrameImageCapture({
    width: config.viewer.captureWidth,
    height: config.viewer.captureHeight,
    deviceScaleFactor: config.viewer.deviceScaleFactor,
    fovDegrees: config.viewer.fovDegrees
  });
  const actionLogger = createActionLogger({
    enabled: config.actionLog.enabled,
    directory: config.actionLog.directory,
    snapshotState: async () => {
      if (!bot || !bot.status.spawned) {
        return null;
      }
      return buildLLMState(bot.bot, { nearbyBlockRadius: config.actionLog.nearbyBlockRadius, messages: bot.getMessages() });
    },
    captureScreenshot: async () => {
      if (!viewer.status.started || !viewer.status.url) {
        return null;
      }
      try {
        // The before/after evidence screenshots get the same crosshair + HUD
        // overlay as the model-facing frames.
        const hud = bot && bot.status.spawned && bot.bot.entity ? botHudLines(bot.bot) : undefined;
        const shot = await browserCapture.captureRaw({ url: viewer.status.url, hud });
        return shot.png;
      } catch {
        return null;
      }
    },
    log: (level, message) => {
      server.broadcast({ type: "log", level, message });
    }
  });
  const commandQueue = new CommandQueue({
    defaultTimeoutMs: config.command.timeoutMs,
    cleanup: async () => {
      await bot?.commands.clearPhysicalState();
    },
    emit: (event) => {
      server.broadcast(event);
    },
    evidence: evidenceStore,
    hooks: actionLogger
  });
  const frameCapture = createFrameBundleCapture({
    directory: screenshotDirectory,
    viewer: viewer.status,
    bot: () => bot,
    minecraftVersion: () => bot?.bot.version ?? null,
    capturePng: (input) => browserCapture.capture(input)
  });
  const frameStore = createFrameMetadataFileStore(screenshotDirectory);
  const pixelTargeting = createPixelTargeting({
    getFrame: frameStore.getFrame,
    bot: () => bot?.bot ?? null
  });
  let inventoryService: InventoryService | undefined;
  let craftingService: CraftingService | undefined;
  const server = createRuntimeHttpServer({
    config: config.web,
    health: () => healthInput(startedAt, config, bot, paper, viewer, server.status),
    state: () => bot ? bot.getState() : disconnectedState(config.minecraft.username),
    observation: async () => bot && bot.status.spawned
      ? buildLLMState(bot.bot, { nearbyBlockRadius: config.actionLog.nearbyBlockRadius, messages: bot.getMessages() })
      : null,
    chat: {
      send: async (text) => {
        if (!bot || !bot.status.connected) {
          throw new Error("Bot is not connected.");
        }
        await bot.sendChat(text);
      }
    },
    commands: {
      queue: commandQueue,
      applyControlStates: async (controls: ControlStates) => {
        if (!bot || !bot.status.connected) {
          throw new Error("Bot is not connected.");
        }
        await bot.commands.applyControlStates(controls);
      },
      actions: {
        lookAt: async (target) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.lookAt(target);
        },
        look: async (input) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.look(input);
        },
        getOrientation: () => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.getOrientation();
        },
        syncOrientation: () => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          bot.actions.syncOrientation();
        },
        walkToVisible: async (input, signal) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.walkToVisible(input, signal);
        },
        walkToSurface: async (input, signal) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.walkToSurface(input, signal);
        },
        walkToExact: async (input, signal) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.walkToExact(input, signal);
        },
        scanHorizon: async (input) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.scanHorizon(input);
        },
        findBlock: async (input) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.findBlock(input);
        },
        findInteractables: async (input) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.findInteractables(input);
        },
        mineBlock: async (input) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.mineBlock(input);
        },
        placeBlock: async (input) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.placeBlock(input);
        },
        jumpPlaceBlock: async (input) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.jumpPlaceBlock(input);
        },
        pillarUp: async () => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.pillarUp();
        },
        useBlock: async (input) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.useBlock(input);
        },
        useHeldItem: async () => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.useHeldItem();
        },
        chestDeposit: async (input) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.chestDeposit(input);
        },
        chestWithdraw: async (input) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.chestWithdraw(input);
        },
        attackEntity: async (input) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.attackEntity(input);
        },
        inspectBlock: async (input) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.inspectBlock(input);
        },
        raycast: async (maxDistance) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.raycast(maxDistance ?? 64);
        }
      },
      maxFineControlDurationMs: config.command.maxFineControlDurationMs,
      maxChunkLimit: config.minecraft.walkMaxChunks
    },
    frames: frameCapture,
    targeting: pixelTargeting,
    get inventory() { return inventoryService; },
    get crafting() { return craftingService; },
    evidence: evidenceStore,
    broadcast: (event: RuntimeEvent) => {
      server.broadcast(event);
    }
  });
  const emit = (event: RuntimeEvent): void => {
    server.broadcast(event);
  };

  /** Build a fresh bot, then rebuild every component that snapshotted the old
   *  Mineflayer object by reference (inventory, crafting, viewer hook). The HTTP
   *  action handlers read `bot` through live arrow closures, so they pick up the
   *  new value automatically. */
  async function spawnBot(): Promise<void> {
    if (reconnecting) {
      return;
    }
    reconnecting = true;
    try {
      // If a previous bot exists, give it a clean stop so the new one can bind
      // the same viewer port and there are no lingering listeners or goals.
      const stale = bot;
      if (stale) {
        await stale.stop().catch(() => undefined);
        // Close any viewer HTTP server the old bot attached so the new viewer
        // can re-bind the same port on its next spawn.
        const viewable = (stale.bot as unknown as { viewer?: { close?: () => void } }).viewer;
        viewable?.close?.();
        viewer.status.started = false;
      }
      const nextBot = createLiveBot(config.minecraft, emit, { walkSearchTimeoutMs: config.minecraft.walkSearchTimeoutMs });
      // The Mineflayer link can die for many reasons (kick, keepalive timeout,
      // ECONNRESET). Watch both terminal events and rebuild on any of them.
      nextBot.bot.on("end", (reason?: string) => {
        if (!stopping && !reconnecting) {
          scheduleReconnect(typeof reason === "string" && reason.length > 0 ? reason : "end");
        }
      });
      nextBot.bot.on("kicked", (reason?: string) => {
        if (!stopping && !reconnecting) {
          scheduleReconnect(typeof reason === "string" && reason.length > 0 ? reason : "kicked");
        }
      });
      // Once this bot connects for real, reset the backoff so the next fault
      // starts from a short delay again.
      nextBot.bot.once("spawn", () => {
        reconnectAttempt = 0;
      });
      bot = nextBot;
      inventoryService = createInventoryService(nextBot.bot);
      craftingService = createCraftingService(nextBot.bot);
      viewerHooked = false;
      hookViewerOnSpawn(nextBot, viewer, emit, () => viewerHooked, (value) => {
        viewerHooked = value;
      });
    } finally {
      reconnecting = false;
    }
  }

  /** When the Mineflayer link dies, tear down and rebuild the bot with
   *  exponential backoff so a flaky server or a transient network drop recovers
   *  on its own instead of silently wedging the process. */
  function scheduleReconnect(reason: string): void {
    if (stopping || reconnectTimer || reconnecting) {
      return;
    }
    const delay = reconnectDelayMs(reconnectAttempt, RECONNECT_BASE_MS, RECONNECT_MAX_MS);
    reconnectAttempt += 1;
    emit({ type: "log", level: "warn", message: `Mineflayer disconnected (${reason}); reconnecting in ${delay}ms.` });
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      void spawnBot().catch((error) => {
        emit({ type: "error", message: `Bot spawn during reconnect failed: ${error instanceof Error ? error.message : String(error)}` });
        scheduleReconnect(String(error));
      });
    }, delay);
  }

  return {
    start: async () => {
      if (artifactRoot) {
        await mkdir(artifactRoot, { recursive: true });
        await writeFile(
          join(artifactRoot, "body-process.yaml"),
          [
            "schema: cog.minecraft-body-process.v1",
            `pid: ${process.pid}`,
            `username: ${config.minecraft.username}`,
            ""
          ].join("\n"),
          "utf8"
        );
      }
      paper = await checkPaperReachable(config.minecraft.host, config.minecraft.port, Math.min(config.command.timeoutMs, 5000));
      await spawnBot();
      await server.start();
      stateBroadcastTimer = setInterval(() => {
        server.broadcast({ type: "state", data: bot ? bot.getState() : disconnectedState(config.minecraft.username) });
      }, config.command.stateBroadcastIntervalMs);
      server.broadcast({ type: "log", level: "info", message: "HTTP and WebSocket server started." });
      logStartup(config, paper, viewer);
    },
    stop: async () => {
      stopping = true;
      if (stateBroadcastTimer) {
        clearInterval(stateBroadcastTimer);
        stateBroadcastTimer = null;
      }
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      await browserCapture.close().catch(() => undefined);
      await server.stop();
      if (bot) {
        await bot.stop();
      }
    }
  };
}

function healthInput(
  startedAt: Date,
  config: RuntimeConfig,
  bot: BotRuntime | null,
  paper: PaperReachability,
  viewer: ViewerRuntime,
  serverStatus: { http: HealthInput["http"]; webSocket: HealthInput["webSocket"] }
): HealthInput {
  return {
    startedAt,
    config,
    bot: bot ? bot.status : {
      connecting: false,
      connected: false,
      spawned: false,
      username: config.minecraft.username,
      version: null,
      lastError: "Mineflayer has not been started yet"
    },
    network: bot ? bot.packets.stats() : undefined,
    paper,
    http: serverStatus.http,
    webSocket: serverStatus.webSocket,
    viewer: viewer.status
  };
}

function disconnectedState(username: string) {
  return {
    connected: false,
    username,
    position: null,
    yaw: null,
    pitch: null,
    yawDegrees: null,
    pitchDegrees: null,
    facing: null,
    dimension: null,
    health: null,
    food: null,
    selectedHotbarSlot: null,
    heldItem: null,
    inventory: { totalSlots: 0, usedSlots: 0, items: [] },
    crosshairBlock: null
  };
}

function hookViewerOnSpawn(
  bot: BotRuntime,
  viewer: ViewerRuntime,
  emit: (event: RuntimeEvent) => void,
  isHooked: () => boolean,
  setHooked: (value: boolean) => void
): void {
  if (isHooked()) {
    return;
  }
  setHooked(true);
  bot.bot.once("spawn", () => {
    void viewer.start(bot.bot).then(() => {
      if (viewer.status.started) {
        emit({ type: "log", level: "info", message: `prismarine-viewer started at ${viewer.status.url}.` });
        return;
      }
      if (viewer.status.error) {
        emit({ type: "error", message: `prismarine-viewer failed: ${viewer.status.error}` });
      }
    });
  });
}

function logStartup(config: RuntimeConfig, paper: PaperReachability, viewer: ViewerRuntime): void {
  const webUrl = `http://${config.web.host}:${config.web.port}`;
  console.log(`cogarch Minecraft embodiment listening at ${webUrl}`);
  console.log(`Paper ${config.minecraft.host}:${config.minecraft.port} reachable: ${paper.reachable}`);
  if (paper.error) {
    console.error(paper.error);
  }
  console.log(`Health: ${webUrl}/api/health`);
  console.log(`State: ${webUrl}/api/state`);
  if (viewer.status.enabled) {
    console.log(`Viewer requested on port ${viewer.status.port}`);
  }
}
