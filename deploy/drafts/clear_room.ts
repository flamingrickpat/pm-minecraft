/**
 * Clear a rectangular room of blocks around an origin cell, e.g. to make space
 * for a base. Skips air cells, refuses to start when hazards touch the area,
 * and re-equips the best tool every few cells.
 *
 * input:
 *   origin : {x,y,z} corner of the room (default: feet cell)
 *   width  : x extent (default 3, max 9)
 *   height : y extent (default 3, max 6)
 *   depth  : z extent (default 3, max 9)
 */

interface Input {
  origin?: { x: number; y: number; z: number };
  width?: number;
  height?: number;
  depth?: number;
}

export default async function run(api: any, rawInput: unknown) {
  const input = (rawInput ?? {}) as Input;
  const feet = (await api.observe({})).camera.block_position;
  const origin = input.origin ?? feet;
  const width = Math.min(9, Math.max(1, Math.floor(input.width ?? 3)));
  const height = Math.min(6, Math.max(1, Math.floor(input.height ?? 3)));
  const depth = Math.min(9, Math.max(1, Math.floor(input.depth ?? 3)));

  // Refuse to dig into a hazard: scan the whole volume once before starting.
  const hazards = api.findBlocks({
    center: { x: origin.x + width / 2, y: origin.y + height / 2, z: origin.z + depth / 2 },
    names: ["lava", "flowing_lava", "water", "flowing_water"],
    horizontal: Math.ceil(width / 2) + 1,
    up: Math.ceil(height / 2) + 1,
    down: Math.ceil(depth / 2) + 1,
    limit: 1,
  });
  if (hazards.blocks.length > 0) {
    return { ok: false, reason: "hazard_in_area", hazard: hazards.blocks[0] };
  }

  const mined: string[] = [];
  let cell = 0;
  for (let dx = 0; dx < width; dx++) {
    for (let dy = 0; dy < height; dy++) {
      for (let dz = 0; dz < depth; dz++) {
        const target = { x: origin.x + dx, y: origin.y + dy, z: origin.z + dz };
        if (target.x === feet.x && target.y === feet.y && target.z === feet.z) continue;
        try {
          const result = await api.mineBlock({ position: target });
          if (result.ok) {
            mined.push(`${target.x},${target.y},${target.z}`);
            cell++;
          }
        } catch {
          // Air cell.
        }
        // Re-equip the best tool for the next cell every 8 mined blocks.
        if (cell > 0 && cell % 8 === 0 && mined.length > 0) {
          const last = mined[mined.length - 1].split(",").map(Number);
          await api.equipBestTool({ target: { x: last[0], y: last[1], z: last[2] } });
        }
      }
    }
  }

  return { ok: true, origin, mined_count: cell, mined };
}
