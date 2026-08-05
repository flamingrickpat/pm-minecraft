import { type MinecraftContext, type Vector3, type SkillEntrypoint } from "../lib/minecraft";

/**
 * Dig a walkable 2-tall, 1-wide staircase instead of a 1-wide straight-down
 * shaft (which the pathfinder cannot climb back out of). Each "step" clears a
 * run of `distance` blocks forward and one block down, so the result is a ramp
 * the bot can walk down and back up.
 *
 * Default advances in the +X direction; pass `direction` ("x+"|"x-"|"z+"|"z-")
 * to change it.
 *
 * stop:
 *   "cave"         stop as soon as the next carved cell is any non-solid block
 *                  (air, cave air, lava, or water).
 *   "cave_and_ore" stop at a cave too, but keep going a little further when any
 *                  carved cell was ore so a vein is not abandoned at the very
 *                  mouth of the tunnel.
 */
interface Input {
  height?: number;   // how many blocks to descend total (default 2)
  distance?: number; // horizontal run per step, 1..12 (default 6)
  stop?: "cave" | "cave_and_ore";
  direction?: "x+" | "x-" | "z+" | "z-";
}

const NON_SOLID = new Set(["air", "cave_air", "void_air", "lava", "water", "flowing_lava", "flowing_water"]);

function clampInt(value: number | undefined, min: number, max: number, fallback: number): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return Math.max(min, Math.min(max, Math.round(value)));
}

function isNonSolid(name: string): boolean {
  return NON_SOLID.has(name);
}

function isOre(name: string): boolean {
  return name.endsWith("_ore") || name === "ancient_debris";
}

async function blockNameAt(context: MinecraftContext, block: Vector3): Promise<string> {
  const res = await context.call("inspect", { block }, 5);
  if (res.ok !== true) return "inspect_failed";
  return String((res.data as Record<string, unknown>)?.blockName ?? "?");
}

async function ensurePickaxe(context: MinecraftContext): Promise<void> {
  const held = (await context.observe()).inventory.heldItem?.name;
  if (!held || !held.endsWith("_pickaxe")) {
    const equipped = await context.equip("stone_pickaxe");
    if (equipped.ok !== true) await context.equip("wooden_pickaxe");
  }
}

const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const input = (rawInput ?? {}) as Input;
  const height = clampInt(input.height, 1, 64, 2);
  const distance = clampInt(input.distance, 1, 12, 6);
  const stop = input.stop === "cave_and_ore" ? "cave_and_ore" : "cave";
  const advance = {
    x: input.direction === "x-" ? -1 : input.direction === "z+" || input.direction === "z-" ? 0 : 1,
    z: input.direction === "z+" ? 1 : input.direction === "z-" ? -1 : 0
  };

  const startObs = await context.observe();
  const feet = startObs.player.blockPosition as Vector3;
  const cleared: Array<string> = [];
  let oreFound: string | null = null;
  let caveHit: string | null = null;
  let guard = 0;

  for (let step = 0; step < height; step++) {
    await ensurePickaxe(context);
    const floorY = feet.y - step; // lower level of this step's carved cell
    for (let d = 0; d < distance; d++) {
      const originX = feet.x + advance.x * (step * distance + d);
      const originZ = feet.z + advance.z * (step * distance + d);
      for (const dy of [1, 0]) { // head cell first, then feet cell (tunnel-friendly order)
        const pos = { x: originX, y: floorY + dy, z: originZ };
        const name = await blockNameAt(context, pos);
        if (isNonSolid(name)) {
          caveHit = name;
        } else {
          if (isOre(name)) {
            oreFound = oreFound ?? name;
          }
          // Face the cell so digging a head/feet cell outside the current view
          // doesn't fail with "Block not in view".
          await context.call("look_at", { target: pos }, 5);
          const res = await context.call("mine_block", { block: pos, walk_into_range: false }, 25);
          if (res.ok !== true) throw new Error(`dig_staircase: mine ${JSON.stringify(pos)}: ${res.message}`);
          cleared.push(`${pos.x},${pos.y},${pos.z}`);
          guard++;
        }
      }
      if (caveHit !== null) {
        break;
      }
    }
    if (caveHit !== null || guard > 400) {
      break;
    }
  }

  const obs = await context.observe();
  return {
    ok: true,
    descended: height,
    clearedCells: cleared.length,
    cleared,
    caveHit,
    oreFound,
    stop,
    startFeet: feet,
    endPosition: (obs.player.blockPosition as Vector3),
    guardExhausted: guard > 400
  };
};

export default run;
