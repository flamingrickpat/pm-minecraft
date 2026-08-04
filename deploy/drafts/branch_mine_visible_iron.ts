import { itemCount, responseBlock, type MinecraftContext, type MinecraftResponse, type SkillEntrypoint } from "../lib/minecraft";

function succeeded(response: MinecraftResponse): boolean {
  return response.ok === true;
}

async function mineVisibleIron(context: MinecraftContext): Promise<number> {
  let mined = 0;
  for (const oreName of ["iron_ore", "deepslate_iron_ore"]) {
    for (let attempt = 0; attempt < 12; attempt++) {
      const found = await context.findBlock(oreName, 12);
      if (!succeeded(found)) break;
      const equipped = await context.equip("stone_pickaxe");
      if (!succeeded(equipped)) throw new Error(`Cannot equip stone pickaxe: ${JSON.stringify(equipped)}`);
      const minedOre = await context.mineBlock(responseBlock(found), true, 30);
      if (!succeeded(minedOre)) throw new Error(`Cannot mine visible ${oreName}: ${JSON.stringify(minedOre)}`);
      mined++;
      await context.sleep(300);
    }
  }
  return mined;
}

const run: SkillEntrypoint = async (context) => {
  const before = await context.observe();
  const startingRawIron = itemCount(before, "raw_iron");
  let exposedOreBlocks = 0;

  for (let tunnelLength = 0; tunnelLength < 12; tunnelLength++) {
    exposedOreBlocks += await mineVisibleIron(context);
    const state = await context.observe();
    const rawIron = itemCount(state, "raw_iron");
    if (rawIron >= startingRawIron + 3) {
      return { tunnelLength, exposedOreBlocks, rawIron };
    }

    const foot = state.player.blockPosition;
    const nextX = foot.x + 1;
    for (const y of [foot.y + 1, foot.y]) {
      const equipped = await context.equip("stone_pickaxe");
      if (!succeeded(equipped)) throw new Error(`Out of stone pickaxes at tunnel length ${tunnelLength}`);
      const mined = await context.mineBlock({ x: nextX, y, z: foot.z }, false, 30);
      if (!succeeded(mined)) {
        throw new Error(`Horizontal tunnel blocked at ${nextX},${y},${foot.z}: ${JSON.stringify(mined)}`);
      }
    }

    const walked = await context.walkTo({ x: nextX + 0.5, y: foot.y, z: foot.z + 0.5 }, 0.25, 10);
    if (!succeeded(walked)) {
      throw new Error(`Cannot enter the newly mined tunnel cell: ${JSON.stringify(walked)}`);
    }
  }

  exposedOreBlocks += await mineVisibleIron(context);
  const after = await context.observe();
  throw new Error(`No three-iron yield after a 12-block untargeted branch-mine segment; raw iron ${itemCount(after, "raw_iron")}, exposed ore ${exposedOreBlocks}`);
};

export default run;
