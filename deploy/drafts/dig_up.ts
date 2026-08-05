import { type MinecraftContext, type Vector3, type SkillEntrypoint } from "../lib/minecraft";

/**
 * Climb straight UP one block at a time out of a 1-wide shaft, clearing exactly
 * the single-block headroom each hop needs and immediately pillaring up.
 *
 * Why one block at a time: clearing 2–3 blocks above the head in a tight shaft
 * reliably trips "Command timed out" (reach/line-of-sight) and "pillar_up ... no
 * headroom" (cleared too little). Mining the ONE block that becomes headroom
 * (2 above the feet) each hop is always directly overhead and within reach, so
 * the climb succeeds even from a cramped shaft.
 *
 * Each hop also re-asserts the pickaxe just before digging and a placeable
 * block just before pillaring. `mine_block`'s walk may consume a placeable
 * block (dirt/cobblestone) as scaffolding and leave it in hand, so the pickaxe
 * is verified (not just requested) right before each dig.
 *
 * input: { targetY?: number } (default 76)
 */
interface Input {
  targetY?: number;
}

const AIR = new Set(["air", "cave_air", "void_air"]);

async function blockNameAt(context: MinecraftContext, block: Vector3): Promise<string> {
  const res = await context.call("inspect", { block }, 5);
  if (res.ok !== true) return "?";
  return String((res.data as Record<string, unknown>)?.blockName ?? "?");
}

const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const input = (rawInput ?? {}) as Input;
  const targetY = typeof input.targetY === "number" ? input.targetY : 76;

  // Verify-and-retry: equip may report ok but leave the previous block in hand;
  // confirm the held item really changed to a pickaxe before digging.
  async function ensurePickaxe(): Promise<void> {
    for (let attempt = 0; attempt < 4; attempt++) {
      const held = (await context.observe()).inventory.heldItem?.name;
      if (held === "stone_pickaxe" || held === "wooden_pickaxe" || held === "iron_pickaxe") return;
      const e = await context.equip("stone_pickaxe");
      if (e.ok !== true) await context.equip("wooden_pickaxe");
      await context.sleep(150);
    }
    const still = (await context.observe()).inventory.heldItem?.name;
    throw new Error(`dig_up: could not equip a pickaxe (still holding ${still ?? "nothing"})`);
  }

  // Get a placeable solid block in hand for pilillaring.
  async function ensurePlaceable(): Promise<void> {
    for (let attempt = 0; attempt < 4; attempt++) {
      const held = (await context.observe()).inventory.heldItem?.name;
      if (held === "cobblestone" || held === "dirt") return;
      const e = await context.equip("cobblestone");
      if (e.ok !== true) await context.equip("dirt");
      await context.sleep(150);
    }
  }

  const cleared: Array<string> = [];
  let hops = 0;
  const maxHops = 200;
  for (; hops < maxHops; hops++) {
    const obs = await context.observe();
    const feet = obs.player.blockPosition as Vector3;
    if (feet.y >= targetY) return { reachedY: feet.y, cleared: cleared.length, open: true, hops };

    // Clear the single block that becomes headroom after this hop (2 above feet).
    const above: Vector3 = { x: feet.x, y: feet.y + 2, z: feet.z };
    const name = await blockNameAt(context, above);
    if (!AIR.has(name)) {
      await ensurePickaxe();
      await context.call("look_at", { target: above }, 5);
      let mined = await context.call("mine_block", { block: above, walk_into_range: false }, 30);
      if (mined.ok !== true) {
        // Fallback: let the body walk/facing take over (it may place scaffold).
        mined = await context.call("mine_block", { block: above, walk_into_range: true }, 30);
      }
      if (mined.ok !== true) throw new Error(`dig_up: clear ${JSON.stringify(above)}: ${mined.message}`);
      cleared.push(`${above.x},${above.y},${above.z}`);
    }

    // Hop up one block and verify we actually gained altitude.
    await ensurePlaceable();
    const climbRes = await context.call("pillar_up", {}, 15);
    if (climbRes.ok !== true) throw new Error(`dig_up: ascend @ ${feet.y}: ${climbRes.message}`);
    const after = await context.observe();
    const afterY = (after.player.blockPosition as Vector3).y;
    if (afterY <= feet.y) {
      throw new Error(`dig_up: pillar_up did not gain altitude (${feet.y} -> ${afterY})`);
    }
  }
  const end = await context.observe();
  return {
    reachedY: (end.player.blockPosition as Vector3).y,
    cleared: cleared.length,
    open: (end.player.blockPosition as Vector3).y >= targetY,
    guardExhausted: true,
    hops,
  };
};

export default run;
