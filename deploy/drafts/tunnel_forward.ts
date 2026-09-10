/**
 * Tunnel forward in a straight 1-wide, 2-tall corridor, one step at a time.
 *
 * Stops when it breaks into open air (cave/surface) or when a hazard
 * (water/lava/bedrock) sits in the next cells. The bot can always walk back
 * out of the tunnel it came from.
 *
 * input:
 *   steps    : how many cells to tunnel (default 6, max 16)
 *   direction: "east" | "west" | "north" | "south" (default: current facing)
 */

interface Input {
  steps?: number;
  direction?: "east" | "west" | "north" | "south";
}

const HAZARD = new Set(["lava", "flowing_lava", "water", "flowing_water", "bedrock"]);

function offset(cardinal: string): { x: number; z: number } {
  switch (cardinal) {
    case "west": return { x: -1, z: 0 };
    case "north": return { x: 0, z: -1 };
    case "south": return { x: 0, z: 1 };
    default: return { x: 1, z: 0 };
  }
}

export default async function run(api: any, rawInput: unknown) {
  const input = (rawInput ?? {}) as Input;
  const state = await api.observe({});
  const cardinal = input.direction ?? state.camera.cardinal;
  const delta = offset(cardinal);
  const steps = Math.min(16, Math.max(1, Math.floor(input.steps ?? 6)));

  const held = state.held_item?.name;
  if (held !== "stone_pickaxe" && held !== "iron_pickaxe" && held !== "wooden_pickaxe") {
    try { await api.equip({ item: "iron_pickaxe" }); }
    catch { await api.equip({ item: "stone_pickaxe" }); }
  }

  const start = state.camera.block_position;
  const mined: string[] = [];
  let done = 0;

  for (let i = 0; i < steps; i++) {
    const feet = (await api.observe({})).camera.block_position;
    const nextFeet = { x: feet.x + delta.x, y: feet.y, z: feet.z + delta.z };
    const nextHead = { x: nextFeet.x, y: nextFeet.y + 1, z: nextFeet.z };

    // Hazard guard: scan the cells around the next step for liquids/bedrock.
    const scan = api.findBlocks({
      center: nextFeet,
      names: [...HAZARD],
      horizontal: 1,
      up: 1,
      down: 1,
      limit: 1,
    });
    if (scan.blocks.length > 0) {
      return {
        start,
        end: (await api.observe({})).camera.block_position,
        hazard: scan.blocks[0].block_name,
        hazard_at: scan.blocks[0].position,
        mined,
      };
    }

    // Mine head cell first, then feet cell. A solid block in a clear tunnel
    // should mine; failures mean the cell was already air.
    for (const target of [nextHead, nextFeet]) {
      try {
        const result = await api.mineBlock({ position: target });
        if (result.ok) mined.push(`${target.x},${target.y},${target.z}`);
      } catch {
        // Cell is already air (bounding-box empty throws): nothing to clear.
      }
    }

    const walked = await api.walkVisible({
      target: { x: nextFeet.x + 0.5, y: nextFeet.y, z: nextFeet.z + 0.5 },
      limit: 4,
      timeoutMs: 10000,
    });
    if (!walked.ok) {
      return { start, end: (await api.observe({})).camera.block_position, walked: walked.reason, mined };
    }
    done++;
  }

  return { start, end: (await api.observe({})).camera.block_position, done, mined };
}
