import { type MinecraftContext, type Vector3, type SkillEntrypoint } from "../lib/minecraft";

interface Input {
  targetY?: number;
}

const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const input = (rawInput ?? {}) as Input;
  const targetY = typeof input.targetY === "number" ? input.targetY : 74;

  async function ensurePickaxe(): Promise<void> {
    const held = (await context.observe()).inventory.heldItem?.name;
    if (held !== "stone_pickaxe" && held !== "wooden_pickaxe") {
      await context.equip("stone_pickaxe");
    }
  }

  const descended: Array<string> = [];
  let guard = 0;
  for (; guard < 60; guard++) {
    const obs = await context.observe();
    const feet = obs.player.blockPosition as Vector3;
    if (feet.y <= targetY) return { reachedY: feet.y, descended, onGround: true };

    // Mine the block directly below the feet to drop one level.
    await ensurePickaxe();
    const below: Vector3 = { x: feet.x, y: feet.y - 1, z: feet.z };
    const res = await context.call("mine_block", { block: below, walk_into_range: false }, 25);
    if (res.ok !== true) throw new Error(`descend: mine below ${JSON.stringify(below)}: ${res.message}`);
    descended.push(`${below.x},${below.y},${below.z}`);
  }
  const obs = await context.observe();
  return { reachedY: (obs.player.blockPosition as Vector3).y, descended, guardExhausted: true };
};

export default run;
