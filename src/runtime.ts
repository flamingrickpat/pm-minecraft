import { parseRuntimeConfig, type RuntimeConfig } from "./config.js";
import { createLiveBot, type BotRuntime } from "./bot/liveBot.js";
import { CommandQueue } from "./commands/commandQueue.js";
import type { ControlStates } from "./commands/controls.js";
import { checkPaperReachable, type PaperReachability } from "./bot/paper.js";
import { createRuntimeHttpServer, type RuntimeEvent } from "./server/http.js";
import type { HealthInput } from "./server/health.js";
import { createViewerRuntime, type ViewerRuntime } from "./viewer/viewer.js";
import { createBrowserFrameImageCapture } from "./viewer/browserCapture.js";
import { createFrameBundleCapture } from "./targeting/frameBundle.js";
import { createFrameMetadataFileStore, createPixelTargeting } from "./targeting/pixelTargeting.js";
import { createInventoryService, type InventoryService } from "./inventory/inventoryService.js";
import { createCraftingService, type CraftingService } from "./crafting/craftingService.js";
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
  let viewerHooked = false;
  let stateBroadcastTimer: NodeJS.Timeout | null = null;
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
        const shot = await browserCapture.captureRaw({ url: viewer.status.url });
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
        walkTo: async (input, signal) => {
          if (!bot || !bot.status.connected) {
            throw new Error("Bot is not connected.");
          }
          return bot.actions.walkTo(input, signal);
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
      bot = createLiveBot(config.minecraft, emit, { walkSearchTimeoutMs: config.minecraft.walkSearchTimeoutMs });
      inventoryService = createInventoryService(bot.bot);
      craftingService = createCraftingService(bot.bot);
      hookViewerOnSpawn(bot, viewer, emit, () => viewerHooked, (value) => {
        viewerHooked = value;
      });
      await server.start();
      stateBroadcastTimer = setInterval(() => {
        server.broadcast({ type: "state", data: bot ? bot.getState() : disconnectedState(config.minecraft.username) });
      }, config.command.stateBroadcastIntervalMs);
      server.broadcast({ type: "log", level: "info", message: "HTTP and WebSocket server started." });
      logStartup(config, paper, viewer);
    },
    stop: async () => {
      if (stateBroadcastTimer) {
        clearInterval(stateBroadcastTimer);
        stateBroadcastTimer = null;
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
