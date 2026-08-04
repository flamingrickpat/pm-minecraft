import { requireSuccessful, type MinecraftContext, type Vector3, type SkillEntrypoint } from "../lib/minecraft";

const run: SkillEntrypoint = async (context: MinecraftContext) => {
  // Mining stone/cobblestone requires a pickaxe; ensure one is held.
  const obs0 = await context.observe();
  const held0 = obs0.inventory.heldItem?.name;
  if (held0 !== "stone_pickaxe" && held0 !== "wooden_pickaxe") {
    const equip = await context.equip("stone_pickaxe");
    if (equip.ok !== true) await context.equip("wooden_pickaxe");
  }
  const mined: Array<{ pos: string; name: string }> = [];
  let guard = 0;
  while (guard < 14) {
    guard++;
    const obs = await context.observe();
    const feet = obs.player.blockPosition as Vector3;
    const below: Vector3 = { x: feet.x, y: feet.y - 1, z: feet.z };
    const minedRes = requireSuccessful(
      await context.call("mine_block", { block: below }, 30),
      `mine ${JSON.stringify(below)}`,
    );
    const blockName = String((minedRes.data as Record<string, unknown>)?.blockName ?? "unknown");
    mined.push({ pos: `${below.x},${below.y},${below.z}`, name: blockName });
    // Stop the moment we expose a stone layer (we already gained a cobblestone from it).
    if (blockName === "stone") break;
  }
  if (mined.length === 0) throw new Error("No block mined while digging down");
  return { mined, last: mined[mined.length - 1] };
};

export default run;
