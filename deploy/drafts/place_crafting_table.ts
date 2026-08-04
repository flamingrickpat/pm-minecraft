import { requireSuccessful, type SkillEntrypoint } from "../lib/minecraft";

const run: SkillEntrypoint = async (context) => {
  requireSuccessful(await context.equip("crafting_table"), "equip crafting table");
  const target = { x: -8, y: 87, z: 10 };
  const inspected = requireSuccessful(await context.call("inspect", { block: target }), "inspect table foundation");
  if (inspected.data?.blockName !== "grass_block") throw new Error(`unsafe foundation: ${JSON.stringify(inspected.data)}`);
  return requireSuccessful(await context.placeBlock(target, { x: 0, y: 1, z: 0 }, true), "place crafting table");
};

export default run;
