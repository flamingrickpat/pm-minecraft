import { type MinecraftContext, type Vector3, type SkillEntrypoint } from "../lib/minecraft";

interface Input {
  targetY?: number;
}

const AIR = new Set(["air", "cave_air", "void_air"]);

async function blockNameAt(context: MinecraftContext, block: Vector3): Promise<string> {
  const res = await context.call("inspect", { block }, 5);
  if (res.ok !== true) return "inspect_failed";
  return String((res.data as Record<string, unknown>)?.blockName ?? "?");
}

const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const input = (rawInput ?? {}) as Input;
  const targetY = typeof input.targetY === "number" ? input.targetY : 76;

  async function ensurePickaxe(): Promise<void> {
    const held = (await context.observe()).inventory.heldItem?.name;
    if (held !== "stone_pickaxe" && held !== "wooden_pickaxe") {
      await context.equip("stone_pickaxe");
    }
  }

  const cleared: Array<string> = [];
  let guard = 0;
  for (; guard < 18; guard++) {
    const obs = await context.observe();
    const feet = obs.player.blockPosition as Vector3;
    if (feet.y >= targetY) return { reachedY: feet.y, cleared, open: true };

    // Clear three blocks above the head so a pillar landing has headroom.
    await ensurePickaxe();
    for (const dy of [1, 2, 3]) {
      const pos: Vector3 = { x: feet.x, y: feet.y + dy, z: feet.z };
      const name = await blockNameAt(context, pos);
      if (AIR.has(name)) continue;
      const mined = await context.call("mine_block", { block: pos, walk_into_range: false }, 25);
      if (mined.ok !== true) throw new Error(`dig_up: clear ${JSON.stringify(pos)}: ${mined.message}`);
      cleared.push(`${pos.x},${pos.y},${pos.z}`);
    }

    // Ascend one block by jumping and placing a block below.
    const heldName = (await context.observe()).inventory.heldItem?.name;
    if (heldName !== "cobblestone" && heldName !== "dirt") {
      const e = await context.equip("cobblestone");
      if (e.ok !== true) await context.equip("dirt");
    }
    const climbed = await context.call("pillar_up", {}, 12);
    if (climbed.ok !== true) throw new Error(`dig_up: ascend: ${climbed.message}`);
  }
  const obs = await context.observe();
  return { reachedY: (obs.player.blockPosition as Vector3).y, cleared, guardExhausted: true };
};

export default run;
