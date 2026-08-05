import {
  itemCount,
  type MinecraftContext,
  type MinecraftResponse,
  type SkillEntrypoint,
  type Vector3,
} from "../lib/minecraft";

/**
 * Safely descend a straight 1-wide shaft to a target Y while collecting
 * cobblestone. Before each step it inspects the block below the feet and stops
 * (without mining) if that block is lava, water, or bedrock. It also records
 * any ore it notices in the fresh after-state and stops early if requested.
 *
 * input:
 *   targetY        : stop descending when feet.y <= targetY (default 40)
 *   stopOnOre      : if true, stop as soon as an ore appears in surroundings
 *   oreNames       : which ores count (default iron_ore, deepslate_iron_ore)
 *   maxSteps       : hard guard on downward steps (default 80)
 */
interface Input {
  targetY?: number;
  stopOnOre?: boolean;
  oreNames?: string[];
  maxSteps?: number;
}

const HAZARD = new Set(["lava", "flowing_lava", "water", "flowing_water", "bedrock", "void_air"]);
const DEFAULT_ORES = ["iron_ore", "deepslate_iron_ore"];

function clampInt(value: unknown, min: number, max: number, fallback: number): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return Math.max(min, Math.min(max, Math.floor(value)));
}

async function inspectName(context: MinecraftContext, block: Vector3): Promise<string> {
  const res = await context.call("inspect", { block }, 5);
  if (res.ok !== true) return "inspect_failed";
  return String((res.data as Record<string, unknown>)?.blockName ?? "?");
}

const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const input = (rawInput ?? {}) as Input;
  const targetY = clampInt(input.targetY, -60, 319, 40);
  const stopOnOre = input.stopOnOre === true;
  const oreNames = input.oreNames && input.oreNames.length > 0 ? input.oreNames : DEFAULT_ORES;
  const maxSteps = clampInt(input.maxSteps, 1, 160, 80);

  // Ensure a pickaxe is held.
  const held = (await context.observe()).inventory.heldItem?.name;
  if (!held || !held.endsWith("_pickaxe")) {
    const e = await context.equip("stone_pickaxe");
    if (e.ok !== true) await context.equip("iron_pickaxe");
  }

  const startRaw = itemCount(await context.observe(), "cobblestone");
  const descended: Array<string> = [];
  let oreSeen: string | null = null;

  for (let step = 0; step < maxSteps; step++) {
    const obs = await context.observe();
    const feet = obs.player.blockPosition as Vector3;
    if (feet.y <= targetY) break;

    // Early stop if we are asked to look for ore and one is in view.
    if (stopOnOre && obs.surroundings?.nearbyBlocks) {
      for (const b of obs.surroundings.nearbyBlocks as Array<{ name: string; distance: number }>) {
        if (oreNames.includes(b.name)) {
          oreSeen = `${b.name}@(${obs.player.blockPosition.x},${obs.player.blockPosition.y},${obs.player.blockPosition.z}) d=${b.distance.toFixed(1)}`;
          break;
        }
      }
      if (oreSeen) break;
    }

    const below: Vector3 = { x: feet.x, y: feet.y - 1, z: feet.z };
    const name = await inspectName(context, below);
    if (HAZARD.has(name)) {
      return { ok: true, stopped: "hazard", hazard: name, block: below, feetY: feet.y, descended };
    }

    const res = await context.call("mine_block", { block: below, walk_into_range: true }, 25);
    if (res.ok !== true) {
      return { ok: false, stopped: "mine_failed", hazard: name, reason: res.message, block: below, descended };
    }
    descended.push(`${below.x},${below.y},${below.z}`);
  }

  const final = await context.observe();
  const endFeet = final.player.blockPosition as Vector3;
  return {
    ok: true,
    stopped: oreSeen ? "ore" : endFeet.y <= targetY ? "reached_target" : "guard",
    reachedY: endFeet.y,
    descended,
    cobblestoneGained: itemCount(final, "cobblestone") - startRaw,
    oreSeen,
  };
};

export default run;
