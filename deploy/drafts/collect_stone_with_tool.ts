import { requireSuccessful, responseBlock, type SkillEntrypoint } from "../lib/minecraft";

const run: SkillEntrypoint = async (context) => {
  for (let attempt = 0; attempt < 8; attempt++) {
    const observation = await context.observe();
    const count = observation.inventory.items.find((item) => item.name === "cobblestone")?.count ?? 0;
    if (count >= 8) return { cobblestone: count, attempts: attempt };
    const found = requireSuccessful(await context.findBlock("stone", 12), "find visible stone");
    requireSuccessful(await context.equip("wooden_pickaxe"), "re-equip wooden pickaxe");
    requireSuccessful(await context.mineBlock(responseBlock(found), true, 30), "mine stone");
  }
  throw new Error("Did not collect eight cobblestone from visible stone");
};

export default run;
