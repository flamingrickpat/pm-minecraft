import {
  itemCount,
  responseBlock,
  type MinecraftContext,
  type MinecraftObservation,
  type MinecraftResponse,
  type SkillEntrypoint,
  type Vector3,
} from "../lib/minecraft";

type Direction = "north" | "south" | "east" | "west";

interface Input {
  direction?: Direction;
  maxSteps?: number;
  maxDurationMs?: number;
  minY?: number;
  tool?: string;
  targetBlocks?: string[];
  targetItem?: string;
  targetCount?: number;
}

const DELTAS: Record<Direction, Vector3> = {
  north: { x: 0, y: 0, z: -1 },
  south: { x: 0, y: 0, z: 1 },
  east: { x: 1, y: 0, z: 0 },
  west: { x: -1, y: 0, z: 0 },
};

const FLUIDS = new Set(["water", "lava", "bubble_column"]);
const NEVER_MINE = new Set(["bedrock", "barrier", "end_portal", "end_portal_frame"]);

function succeeded(response: MinecraftResponse): boolean {
  return response.ok === true;
}

function boundedInteger(value: unknown, fallback: number, minimum: number, maximum: number): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return Math.max(minimum, Math.min(maximum, Math.floor(value)));
}

function blockName(response: MinecraftResponse): string {
  const value = response.data?.blockName;
  if (typeof value !== "string") {
    throw new Error(`Inspect response has no blockName: ${JSON.stringify(response)}`);
  }
  return value;
}

async function inspect(context: MinecraftContext, block: Vector3): Promise<string> {
  const response = await context.call("inspect", { block }, 5);
  if (!succeeded(response)) throw new Error(`Cannot inspect ${JSON.stringify(block)}: ${JSON.stringify(response)}`);
  return blockName(response);
}

function assertHealthy(state: MinecraftObservation): void {
  if (state.player.health < 18) throw new Error(`Health guard stopped tunnel at ${state.player.health}/20`);
  if (state.player.food < 6) throw new Error(`Food guard stopped tunnel at ${state.player.food}/20`);
}

async function mineVisibleTargets(
  context: MinecraftContext,
  targetBlocks: string[],
  targetItem: string,
  desiredCount: number,
  tool: string,
  deadline: number,
): Promise<number> {
  let mined = 0;
  while (Date.now() < deadline) {
    const state = await context.observe();
    assertHealthy(state);
    if (itemCount(state, targetItem) >= desiredCount) return mined;

    let found: MinecraftResponse | null = null;
    for (const name of targetBlocks) {
      const candidate = await context.findBlock(name, 8);
      if (succeeded(candidate)) {
        found = candidate;
        break;
      }
    }
    if (!found) return mined;

    const equipped = await context.equip(tool);
    if (!succeeded(equipped)) throw new Error(`Cannot equip ${tool}: ${JSON.stringify(equipped)}`);
    const minedTarget = await context.mineBlock(responseBlock(found), true, 15);
    if (!succeeded(minedTarget)) throw new Error(`Cannot mine visible target: ${JSON.stringify(minedTarget)}`);
    mined++;
    await context.sleep(150);
  }
  return mined;
}

const run: SkillEntrypoint = async (context, rawInput) => {
  const input = (rawInput ?? {}) as Input;
  const direction = input.direction ?? "east";
  const delta = DELTAS[direction];
  if (!delta) throw new Error(`Unsupported direction ${String(input.direction)}`);

  const maxSteps = boundedInteger(input.maxSteps, 8, 1, 16);
  const maxDurationMs = boundedInteger(input.maxDurationMs, 45_000, 5_000, 90_000);
  const minY = boundedInteger(input.minY, -55, -63, 319);
  const tool = input.tool ?? "iron_pickaxe";
  const targetBlocks = input.targetBlocks?.length ? input.targetBlocks.slice(0, 4) : ["gold_ore", "deepslate_gold_ore"];
  const targetItem = input.targetItem ?? "raw_gold";
  const targetCount = boundedInteger(input.targetCount, 1, 1, 64);
  const deadline = Date.now() + maxDurationMs;

  const before = await context.observe();
  assertHealthy(before);
  const start = before.player.blockPosition;
  if (start.y < minY) throw new Error(`Start Y ${start.y} is below configured minimum ${minY}`);
  const currentFeet = await inspect(context, start);
  const currentHead = await inspect(context, { x: start.x, y: start.y + 1, z: start.z });
  if (FLUIDS.has(currentFeet) || FLUIDS.has(currentHead)) {
    throw new Error(`Fluid guard refused to start in ${currentFeet}/${currentHead}`);
  }

  const startingTargetItems = itemCount(before, targetItem);
  let minedTargets = await mineVisibleTargets(
    context,
    targetBlocks,
    targetItem,
    startingTargetItems + targetCount,
    tool,
    deadline,
  );
  let completedSteps = 0;
  let stopReason = "step_limit";

  for (let step = 0; step < maxSteps && Date.now() < deadline; step++) {
    const state = await context.observe();
    assertHealthy(state);
    if (itemCount(state, targetItem) >= startingTargetItems + targetCount) {
      stopReason = "target_collected";
      break;
    }
    if (Math.abs(state.player.blockPosition.y - start.y) > 1) {
      throw new Error(`Vertical-drift guard stopped tunnel at Y ${state.player.blockPosition.y}; start Y was ${start.y}`);
    }

    const player = state.player.blockPosition;
    const nextFeet = { x: player.x + delta.x, y: player.y, z: player.z + delta.z };
    const nextHead = { x: nextFeet.x, y: nextFeet.y + 1, z: nextFeet.z };
    const nextFloor = { x: nextFeet.x, y: nextFeet.y - 1, z: nextFeet.z };
    if (nextFeet.y < minY) throw new Error(`Minimum-Y guard stopped tunnel before Y ${nextFeet.y}`);

    const [feetName, headName, floorName] = await Promise.all([
      inspect(context, nextFeet),
      inspect(context, nextHead),
      inspect(context, nextFloor),
    ]);
    if (FLUIDS.has(feetName) || FLUIDS.has(headName) || FLUIDS.has(floorName)) {
      stopReason = `fluid_ahead:${feetName}/${headName}/${floorName}`;
      break;
    }
    if (floorName === "air") {
      stopReason = "drop_or_cave_ahead";
      break;
    }
    if (NEVER_MINE.has(feetName) || NEVER_MINE.has(headName) || NEVER_MINE.has(floorName)) {
      stopReason = `protected_block_ahead:${feetName}/${headName}/${floorName}`;
      break;
    }

    const equipped = await context.equip(tool);
    if (!succeeded(equipped)) throw new Error(`Cannot equip ${tool}: ${JSON.stringify(equipped)}`);
    for (const [position, name] of [[nextHead, headName], [nextFeet, feetName]] as const) {
      if (name === "air" || name === "cave_air" || name === "void_air") continue;
      const mined = await context.mineBlock(position, false, 15);
      if (!succeeded(mined)) throw new Error(`Cannot mine tunnel cell ${JSON.stringify(position)} (${name}): ${JSON.stringify(mined)}`);
    }

    const walked = await context.walkTo(
      { x: nextFeet.x + 0.5, y: nextFeet.y, z: nextFeet.z + 0.5 },
      0.45,
      8,
      "walk_only",
    );
    if (!succeeded(walked)) throw new Error(`Cannot enter cleared tunnel cell: ${JSON.stringify(walked)}`);
    completedSteps++;

    minedTargets += await mineVisibleTargets(
      context,
      targetBlocks,
      targetItem,
      startingTargetItems + targetCount,
      tool,
      deadline,
    );
  }

  if (Date.now() >= deadline) stopReason = "time_limit";
  const after = await context.observe();
  assertHealthy(after);
  return {
    direction,
    completedSteps,
    minedTargets,
    stopReason,
    start,
    end: after.player.blockPosition,
    targetItem,
    targetItemDelta: itemCount(after, targetItem) - startingTargetItems,
    health: after.player.health,
  };
};

export default run;
