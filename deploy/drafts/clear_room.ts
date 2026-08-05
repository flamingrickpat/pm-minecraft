import { type MinecraftContext, type Vector3, type SkillEntrypoint } from "../lib/minecraft";

/**
 * Expand a tight (1-wide) tunnel into a small room so block placement
 * (crafting table / furnace) has a clear floor cell. Repeats mine_block over a
 * box of non-air blocks centered a short distance ahead of the player, leaving
 * the floor (the block under the room) intact.
 *
 * width  = box width  across the tunnel (X), odd, default 3
 * depth  = box length forward (Z), default 3
 * height = box height (Y), default 2 (a 2-tall room)
 * The box is anchored in front of the bot so it can be cleared without walking
 * into a wall, then the bot can step into it.
 */
interface Input {
  width?: number;
  depth?: number;
  height?: number;
  forward?: number; // how many blocks in front of the bot the room starts (default 1)
}

function clampInt(value: number | undefined, min: number, max: number, fallback: number): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return Math.max(min, Math.min(max, Math.round(value)));
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
  const width = clampInt(input.width, 1, 9, 3);
  const depth = clampInt(input.depth, 1, 9, 3);
  const height = clampInt(input.height, 1, 5, 2);
  const forward = clampInt(input.forward, 0, 5, 1);

  const obs = await context.observe();
  const feet = obs.player.blockPosition as Vector3;

  const cleared: Array<string> = [];
  const maxCells = 120;
  let cells = 0;

  // Advance in +Z (south). The room is centered on the axis in front.
  const xCenter = feet.x;
  for (let dx = -Math.floor(width / 2); dx <= Math.floor(width / 2); dx++) {
    for (let dz = forward; dz < forward + depth; dz++) {
      for (let dy = 1; dy <= height; dy++) {
        if (cells >= maxCells) break;
        const pos = { x: xCenter + dx, y: feet.y + dy, z: feet.z + dz };
        const name = await blockNameAt(context, pos);
        if (name === "air" || name === "cave_air" || name === "void_air" || name === "inspect_failed") {
          continue;
        }
        // Face the block first: side/top cells can be outside the current view
        // frustum, and mine_block with walk_into_range=false otherwise fails
        // with "Block not in view". We use walk_into_range=true so the body
        // walks adjacent and digs reliably; the look_at is a cheap extra.
        await context.call("look_at", { target: pos }, 5);
        const res = await context.call("mine_block", { block: pos, walk_into_range: true }, 25);
        if (res.ok !== true) {
          throw new Error(`clear_room: mine ${JSON.stringify(pos)}: ${res.message}`);
        }
        cleared.push(`${pos.x},${pos.y},${pos.z}`);
        cells++;
      }
    }
  }

  const final = await context.observe();
  return {
    ok: true,
    room: { width, depth, height, forward },
    clearedCells: cleared.length,
    cleared,
    startFeet: feet,
    endPosition: (final.player.blockPosition as Vector3),
    capReached: cells >= maxCells
  };
};

export default run;
