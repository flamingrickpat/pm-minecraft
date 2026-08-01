import { readFile, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import type {
  MinecraftContext,
  MinecraftObservation,
  MinecraftResponse,
  SkillEntrypoint,
  SkillResult
} from "./sdk/minecraft.js";

interface RunnerArguments {
  skill: string;
  input: string;
  result: string;
}

const routes: Record<string, ["GET" | "POST", string]> = {
  health: ["GET", "/api/health"],
  state: ["GET", "/api/state"],
  observe: ["GET", "/api/observation"],
  capture_frame: ["GET", "/api/frame/current"],
  find_block: ["POST", "/api/world/find-block"],
  walk_to: ["POST", "/api/command/walk-to"],
  mine_block: ["POST", "/api/command/mine-block"],
  place_block: ["POST", "/api/command/place-block"],
  jump_place_block: ["POST", "/api/command/jump-place-block"],
  pillar_up: ["POST", "/api/command/pillar-up"],
  use_block: ["POST", "/api/command/use-block"],
  inspect: ["POST", "/api/command/inspect"],
  rotate: ["POST", "/api/command/rotate"],
  look_at: ["POST", "/api/command/look-at"],
  fine_control: ["POST", "/api/command/fine-control"],
  sync_orientation: ["POST", "/api/command/sync-orientation"],
  stop: ["POST", "/api/command/stop"],
  hotbar_select: ["POST", "/api/hotbar/select"],
  inventory_select: ["POST", "/api/inventory/select"],
  inventory_equip: ["POST", "/api/inventory/equip"],
  open_inventory: ["POST", "/api/crafting/open-inventory"],
  craft_item: ["POST", "/api/crafting/craft-item"],
  open_crafting_table: ["POST", "/api/crafting/open-crafting-table"],
  set_crafting_grid: ["POST", "/api/crafting/set-grid"],
  take_crafting_output: ["POST", "/api/crafting/take-output"],
  clear_crafting_grid: ["POST", "/api/crafting/clear-grid"],
  close_crafting_window: ["POST", "/api/crafting/close-window"],
  smelt: ["POST", "/api/furnace/smelt"],
  resolve_pixel: ["POST", "/api/targeting/resolve-pixel"],
  chat: ["POST", "/api/chat/send"]
};

function parseArguments(argv: string[]): RunnerArguments {
  const values = new Map<string, string>();
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith("--") || value === undefined) {
      throw new Error(`Invalid runner arguments: ${argv.join(" ")}`);
    }
    values.set(key.slice(2), value);
  }
  const skill = values.get("skill");
  const input = values.get("input");
  const result = values.get("result");
  if (!skill || !input || !result) {
    throw new Error("Runner requires --skill, --input, and --result");
  }
  return { skill, input, result };
}

function createContext(bodyUrl: string): MinecraftContext {
  const visualFrames = new Map<string, number>();
  const call = async (action: string, parameters: Record<string, unknown> = {}, timeoutSeconds = 30): Promise<MinecraftResponse> => {
    const route = routes[action];
    if (!route) {
      throw new Error(`Unknown Minecraft action ${JSON.stringify(action)}. Available: ${Object.keys(routes).sort().join(", ")}`);
    }
    const [method, path] = route;
    const body = { ...parameters };
    if (action === "fine_control") {
      const frameId = body.visualCheckFrameId;
      if (typeof frameId !== "string" || !visualFrames.has(frameId) || Date.now() - visualFrames.get(frameId)! > 60_000) {
        throw new Error("fine_control requires visualCheckFrameId from ctx.call('capture_frame') within the last 60 seconds");
      }
      delete body.visualCheckFrameId;
    }
    if (path.startsWith("/api/command/") && !["stop", "sync_orientation"].includes(action)) {
      body.timeoutMs = Math.round(timeoutSeconds * 1000);
    }
    const response = await fetch(`${bodyUrl}${path}`, {
      method,
      headers: method === "POST" ? { "content-type": "application/json" } : undefined,
      body: method === "POST" ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout((timeoutSeconds + 5) * 1000)
    });
    const payload: unknown = await response.json();
    if (!response.ok) {
      if (payload && typeof payload === "object" && !Array.isArray(payload) && (payload as Record<string, unknown>).ok === false) {
        return { ...(payload as MinecraftResponse), httpStatus: response.status };
      }
      throw new Error(`Minecraft body ${method} ${path} returned HTTP ${response.status}: ${JSON.stringify(payload)}`);
    }
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error(`Minecraft body ${method} ${path} returned a non-object response`);
    }
    if (action === "capture_frame") {
      const frameId = frameIdentifier(payload as Record<string, unknown>);
      if (frameId) visualFrames.set(frameId, Date.now());
    }
    return payload as MinecraftResponse;
  };

  return {
    username: process.env.MINECRAFT_USERNAME!,
    bodyUrl,
    agentHome: process.env.MINECRAFT_AGENT_HOME!,
    executionId: process.env.MINECRAFT_EXECUTION_ID!,
    call,
    observe: () => call("observe") as unknown as Promise<MinecraftObservation>,
    findBlock: (blockName, maxDistance = 64) => call("find_block", { blockName, maxDistance }, 15),
    walkTo: (target, tolerance = 1.5, timeoutSeconds = 60) => call("walk_to", { target, tolerance }, timeoutSeconds),
    mineBlock: (block, walkIntoRange = true, timeoutSeconds = 60) => call("mine_block", { block, walkIntoRange }, timeoutSeconds),
    placeBlock: (referenceBlock, face, walkIntoRange = true, timeoutSeconds = 60) => call("place_block", { referenceBlock, face, walkIntoRange }, timeoutSeconds),
    useBlock: (block, walkIntoRange = true, timeoutSeconds = 30) => call("use_block", { block, walkIntoRange }, timeoutSeconds),
    equip: (itemName) => call("inventory_equip", { itemName }, 15),
    craft: (itemName, repetitions = 1) => call("craft_item", { itemName, repetitions }, 60),
    smelt: (inputItemName, inputCount, fuelItemName, fuelCount = 1, timeoutSeconds = 60) => call(
      "smelt",
      { inputItemName, inputCount, fuelItemName, fuelCount, timeoutMs: Math.round(timeoutSeconds * 1000) },
      timeoutSeconds
    ),
    rotate: (yaw, pitch = 0) => call("rotate", { yaw, pitch }, 10),
    stop: () => call("stop", {}, 10),
    chat: (text) => call("chat", { text }, 10),
    sleep: (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds))
  };
}

function frameIdentifier(payload: Record<string, unknown>): string | null {
  if (typeof payload.frameId === "string") return payload.frameId;
  const metadata = payload.metadata;
  return metadata && typeof metadata === "object" && !Array.isArray(metadata) && typeof (metadata as Record<string, unknown>).frameId === "string"
    ? (metadata as Record<string, unknown>).frameId as string
    : null;
}

async function main(): Promise<void> {
  const args = parseArguments(process.argv.slice(2));
  const bodyUrl = process.env.MINECRAFT_BODY_URL;
  if (!bodyUrl) {
    throw new Error("MINECRAFT_BODY_URL is required");
  }
  const input: unknown = JSON.parse(await readFile(args.input, "utf-8"));
  const imported = await import(`${pathToFileURL(args.skill).href}?execution=${Date.now()}`) as { run?: SkillEntrypoint; default?: SkillEntrypoint };
  const entrypoint = imported.run ?? imported.default;
  if (typeof entrypoint !== "function") {
    throw new TypeError(`${args.skill} must export async function run(ctx, input) or a default async function`);
  }
  const startedAt = new Date().toISOString();
  try {
    const value = await entrypoint(createContext(bodyUrl), input);
    const result: SkillResult = {
      ok: true,
      startedAt,
      finishedAt: new Date().toISOString(),
      value: value ?? null
    };
    await writeFile(args.result, JSON.stringify(result, null, 2));
  } catch (error) {
    const rendered = error instanceof Error
      ? { name: error.name, message: error.message, stack: error.stack ?? `${error.name}: ${error.message}` }
      : { name: "ThrownValue", message: String(error), stack: String(error) };
    const result: SkillResult = {
      ok: false,
      startedAt,
      finishedAt: new Date().toISOString(),
      error: rendered
    };
    await writeFile(args.result, JSON.stringify(result, null, 2));
    console.error(rendered.stack);
    process.exitCode = 1;
  }
}

await main();
