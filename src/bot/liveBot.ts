import mineflayer from "mineflayer";
import type { Bot } from "mineflayer";
import type { RuntimeConfig } from "../config.js";
import type { BotStateSnapshot } from "../server/state.js";
import { createBotStateSnapshot } from "../state/botState.js";
import { createChatInbox, type MinecraftMessage } from "../state/chatInbox.js";
import type { RuntimeEvent } from "../server/http.js";
import { controlNames, type CommandControls, type ControlName, type ControlStates } from "../commands/controls.js";
import { createPhysicalCommandActions, installPathfinder, type PhysicalCommandActions } from "./actions.js";

/**
 * Runtime state needs a live Mineflayer source; own one bot connection and expose its current status.
 *
 * @remarks
 * archetype: service-provider
 * owns: Mineflayer bot creation, connection/spawn status, error capture, and minimal state snapshot reads.
 * not own: command execution, HTTP serialization, Paper process startup, or fake state generation.
 * fails when: Mineflayer emits connection, login, kick, or end errors from the live server path.
 * domain: this is the only bot connection created by the product runtime.
 * invariant: state snapshots are read from the live bot object when connected and null otherwise.
 */
export interface BotRuntime {
  bot: Bot;
  status: BotStatus;
  commands: CommandControls;
  actions: PhysicalCommandActions;
  getState(): BotStateSnapshot;
  getMessages(): MinecraftMessage[];
  sendChat(text: string): Promise<void>;
  stop(): Promise<void>;
}

export interface BotStatus {
  connecting: boolean;
  connected: boolean;
  spawned: boolean;
  username: string;
  version: string | null;
  deathCount: number;
  spawnCount: number;
  lastDeathAt: string | null;
  lastSpawnAt: string | null;
  lastError: string | null;
}

export function createLiveBot(config: RuntimeConfig["minecraft"], emit: (event: RuntimeEvent) => void = () => undefined): BotRuntime {
  const chatInbox = createChatInbox();
  const bot = mineflayer.createBot({
    host: config.host,
    port: config.port,
    username: config.username,
    auth: "offline",
    viewDistance: config.viewDistance ?? 12
  });
  bot.once("inject_allowed", () => {
    (bot.physics as typeof bot.physics & { stepHeight: number }).stepHeight = 1.1;
    emit({ type: "log", level: "info", message: "Set Mineflayer physics step height to 1.1." });
  });
  installPathfinder(bot);
  const status: BotStatus = {
    connecting: true,
    connected: false,
    spawned: false,
    username: config.username,
    version: null,
    deathCount: 0,
    spawnCount: 0,
    lastDeathAt: null,
    lastSpawnAt: null,
    lastError: null
  };

  bot.once("login", () => {
    status.connecting = false;
    status.connected = true;
    status.username = bot.username;
    status.version = bot.version;
    emit({ type: "log", level: "info", message: `Mineflayer logged in as ${bot.username}.` });
  });
  bot.on("spawn", () => {
    const respawn = status.spawnCount > 0;
    status.connecting = false;
    status.connected = true;
    status.spawned = true;
    status.username = bot.username;
    status.version = bot.version;
    status.spawnCount += 1;
    status.lastSpawnAt = new Date().toISOString();
    emit({
      type: "log",
      level: "info",
      message: (
        `Mineflayer ${respawn ? "respawned" : "spawned"} as ${bot.username}.`
      )
    });
  });
  bot.on("death", () => {
    status.deathCount += 1;
    status.lastDeathAt = new Date().toISOString();
    status.spawned = false;
    emit({
      type: "log",
      level: "warn",
      message: `Mineflayer death observed for ${bot.username}.`
    });
  });
  bot.on("error", (error) => {
    status.connecting = false;
    status.lastError = error.message;
    emit({ type: "error", message: error.message });
  });
  bot.on("kicked", (reason) => {
    status.connecting = false;
    status.connected = false;
    status.spawned = false;
    status.lastError = typeof reason === "string" ? reason : JSON.stringify(reason);
    emit({ type: "error", message: `Mineflayer kicked: ${status.lastError}` });
  });
  bot.on("end", (reason) => {
    status.connecting = false;
    status.connected = false;
    status.spawned = false;
    if (reason) {
      status.lastError = String(reason);
    }
    emit({ type: "log", level: "warn", message: `Mineflayer connection ended${reason ? `: ${String(reason)}` : "."}` });
  });
  bot.on("chat", (username, message) => {
    emit({ type: "chat", username, message });
  });
  bot.on("messagestr", (message, position) => {
    chatInbox.add(message, position);
  });

  return {
    bot,
    status,
    commands: createCommandControls(bot, emit),
    actions: createPhysicalCommandActions(bot, {
      mineVisibilityIgnoreDistance: config.mineVisibilityIgnoreDistance,
      walkToMaxDistance: config.walkToMaxDistance
    }),
    getState: () => createBotStateSnapshot(bot, status),
    getMessages: () => chatInbox.messages(),
    sendChat: async (text: string) => {
      bot.chat(text);
      emit({ type: "chat", username: status.username, message: text });
      emit({ type: "log", level: "info", message: `Sent chat: ${text}` });
    },
    stop: async () => {
      bot.end();
    }
  };
}

function createCommandControls(bot: Bot, emit: (event: RuntimeEvent) => void): CommandControls {
  return {
    applyControlStates: (controls: ControlStates) => {
      for (const name of controlNames) {
        if (controls[name] !== undefined) {
          bot.setControlState(name, controls[name] === true);
        }
      }
    },
    clearPhysicalState: () => {
      const pathfinder = (bot as Bot & { pathfinder?: { setGoal(goal: unknown): void } }).pathfinder;
      pathfinder?.setGoal(null);
      if (typeof bot.clearControlStates === "function") {
        bot.clearControlStates();
      } else {
        for (const name of controlNames) {
          bot.setControlState(name as ControlName, false);
        }
      }
      emit({ type: "log", level: "info", message: "Cleared pathfinder goal and Mineflayer control states." });
    }
  };
}
