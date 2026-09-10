/**
 * Collect a target count of one block type (e.g. stone, deepslate, logs):
 * find the nearest exposed block, equip the best tool for it, mine it, and
 * repeat until the inventory holds the requested count.
 *
 * input:
 *   block : the block name to collect (default "stone")
 *   count : how many items to end up with (default 32, max 128)
 *   range : horizontal search range in blocks (default 24, max 48)
 */

interface Input {
  block?: string;
  count?: number;
  range?: number;
}

function inventoryCount(inventory: Array<{ name: string; count: number }>, names: string[]): number {
  return inventory
    .filter((item) => names.includes(item.name))
    .reduce((total, item) => total + item.count, 0);
}

export default async function run(api: any, rawInput: unknown) {
  const input = (rawInput ?? {}) as Input;
  const block = input.block ?? "stone";
  const count = Math.min(128, Math.max(1, Math.floor(input.count ?? 32)));
  const range = Math.min(48, Math.max(4, Math.floor(input.range ?? 24)));

  // Whole family names: "stone" also accepts its dropped variants.
  const wanted: Record<string, string[]> = {
    stone: ["stone", "cobblestone"],
    deepslate: ["deepslate", "cobbled_deepslate"],
  };
  const names = wanted[block] ?? [block];

  const startCount = inventoryCount((await api.observe({})).inventory, names);
  const mined: string[] = [];
  let misses = 0;

  while (startCount + mined.length < count) {
    const feet = (await api.observe({})).camera.feet_position;
    const scan = api.findBlocks({
      center: feet,
      names: [block],
      horizontal: range,
      up: 16,
      down: 24,
      limit: 1,
    });
    if (scan.blocks.length === 0) {
      misses++;
      if (misses >= 3) {
        return {
          ok: false,
          reason: "no_more_blocks",
          collected: mined.length,
          mined,
        };
      }
      // Nothing in range: wander toward the last mined cell's neighborhood.
      continue;
    }
    misses = 0;

    const target = scan.blocks[0];
    await api.equipBestTool({ target: target.position });
    const result = await api.mineBlock({ position: target.position });
    if (result.ok) {
      mined.push(`${target.position.x},${target.position.y},${target.position.z}`);
    } else {
      // Unharvestable or changed: skip this cell by walking near the next one.
      mined.push(`skipped:${target.block_name}`);
    }
  }

  const inventory = (await api.observe({})).inventory;
  return {
    ok: true,
    collected: inventoryCount(inventory, names),
    mines: mined.length,
    mined,
  };
}
