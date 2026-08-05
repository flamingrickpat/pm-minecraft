import type { MinecraftContext } from "../sdk/minecraft.js";
import {
  itemCount,
  requireSuccessful,
  responseBlock,
} from "../sdk/minecraft.js";

export async function run(ctx: MinecraftContext, raw: unknown): Promise<unknown> {
  const input = raw as { blockName: string; itemName?: string; count: number; maxDistance?: number };
  if (!input.blockName || !Number.isInteger(input.count) || input.count <= 0) throw new Error("blockName and positive integer count are required");
  const itemName = input.itemName ?? input.blockName;
  const start = itemCount(await ctx.observe(), itemName);
  const attempts: unknown[] = [];

  // Equip the cheapest tool that harvests this block up front so the run does
  // not die mid-way with an unharvestable rejection (see playtest finding 4).
  await ensureHarvestTool(ctx, input.blockName);

  while (itemCount(await ctx.observe(), itemName) - start < input.count) {
    const found = requireSuccessful(await ctx.findBlock(input.blockName, input.maxDistance ?? 48), `find ${input.blockName}`);
    await ensureHarvestTool(ctx, input.blockName);
    const mined = requireSuccessful(await ctx.mineBlock(responseBlock(found), true, 60), `mine ${input.blockName}`);
    attempts.push({ found: found.data, mined: mined.data });
    if (mined.data?.canHarvest === false) {
      const held = mined.data.heldItemBefore as { name?: unknown } | null | undefined;
      const heldName = held && typeof held.name === "string" ? held.name : "empty hand";
      throw new Error(`${heldName} cannot harvest drops from ${input.blockName}; collected ${itemCount(await ctx.observe(), itemName) - start}`);
    }
  }
  const final = await ctx.observe();
  return { blockName: input.blockName, itemName, collected: itemCount(final, itemName) - start, attempts };
}

/**
 * Inspect the nearest block of interest and, when the held item cannot
 * harvest it, equip the cheapest working tool reported by the body.
 */
async function ensureHarvestTool(ctx: MinecraftContext, blockName: string): Promise<void> {
  const observation = await ctx.observe();
  const held = observation.inventory.heldItem?.name ?? null;
  const entry = observation.surroundings?.nearbyBlocks?.find((block) => block.name === blockName);
  if (!entry) {
    // No visible block of this kind in the scan; cannot decide a tool.
    return;
  }
  if (entry.canHarvestWithHeldItem === false && Array.isArray(entry.harvestToolOptions) && entry.harvestToolOptions.length > 0) {
    const wanted = entry.harvestToolOptions[0];
    if (wanted !== held) {
      const equipped = await ctx.equip(wanted);
      if (equipped.ok !== true) {
        throw new Error(`collect_blocks: could not equip ${wanted} to harvest ${blockName}: ${equipped.message}`);
      }
    }
  }
}
