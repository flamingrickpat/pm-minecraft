import { type MinecraftContext, type Vector3, type SkillEntrypoint } from "../lib/minecraft";

/**
 * Ascend through low-headroom / enclosed space by repeatedly clearing the two
 * cells above the feet (head + above-head) and stepping up one level. Works
 * indoors where pillar_up alone fails for lack of headroom (it first carves the
 * headroom, then climbs). The result climbs a shaft the bot can descend again
 * with staircase_down / dig_staircase.
 *
 * input:
 *   targetY  : stop ascending when feet.y >= targetY (default feet.y + 8)
 *   maxSteps : hard guard on upward steps (default 40)
 */
interface Input {
  targetY?: number;
  maxSteps?: number;
}

function clampInt(value: unknown, min: number, max: number, fallback: number): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return Math.max(min, Math.min(max, Math.floor(value)));
}

async function clearCellIfSolid(context: MinecraftContext, target: Vector3, cleared: string[]): Promise<void> {
  const before = await context.call("inspect", { block: target }, 5);
  const name = String((before.data as Record<string, unknown>)?.blockName ?? "?");
  if (name === "air" || name === "cave_air" || name === "void_air" || name === "inspect_failed") return;
  const res = await context.call("mine_block", { block: target, walk_into_range: false }, 25);
  if (res.ok !== true) {
    throw new Error(`staircase_up: could not clear ${name} at ${JSON.stringify(target)}: ${res.message}`);
  }
  cleared.push(`${target.x},${target.y},${target.z}`);
}

const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const input = (rawInput ?? {}) as Input;
  const startObs = await context.observe();
  const startFeet = startObs.player.blockPosition as Vector3;
  const startY = startFeet.y;
  const targetY = clampInt(input.targetY, -60, 320, startFeet.y + 8);
  const maxSteps = clampInt(input.maxSteps, 1, 120, 40);

  // Hold a pickaxe so clearing harder ceilings works.
  const held = startObs.inventory.heldItem?.name;
  if (held && !held.endsWith("_pickaxe")) {
    const e = await context.equip("stone_pickaxe");
    if (e.ok !== true) await context.equip("wooden_pickaxe");
  }

  const cleared: Array<string> = [];
  const climbed: Array<number> = [startY];
  let guard = 0;
  for (; guard < maxSteps; guard++) {
    const obs = await context.observe();
    const feet = obs.player.blockPosition as Vector3;
    if (feet.y >= targetY) {
      return { ok: true, reached: "target", targetY, startY, reachedY: feet.y, climbed };
    }

    // Clear headroom: the two cells the player's body occupies at the next level.
    const above1: Vector3 = { x: feet.x, y: feet.y + 1, z: feet.z };
    const above2: Vector3 = { x: feet.x, y: feet.y + 2, z: feet.z };
    await clearCellIfSolid(context, above1, cleared);
    await clearCellIfSolid(context, above2, cleared);

    // Step up one level. pillar_up places a block beneath and jumps; with the
    // headroom just carved it now has clearance indoors too.
    const climb = await context.call("pillar_up", {}, 15);
    const afterObs = await context.observe();
    const afterY = (afterObs.player.blockPosition as Vector3).y;
    if (climb.ok !== true || afterY <= feet.y) {
      // Headroom may be insufficient; try to widen by clearing one more above
      // and retry once before giving up on this level.
      await clearCellIfSolid(context, { x: feet.x, y: feet.y + 2, z: feet.z }, cleared);
      await clearCellIfSolid(context, { x: feet.x, y: feet.y + 3, z: feet.z }, cleared);
      const retry = await context.call("pillar_up", {}, 15);
      const retryObs = await context.observe();
      const retryY = (retryObs.player.blockPosition as Vector3).y;
      if (retry.ok !== true || retryY <= feet.y) {
        throw new Error(
          `staircase_up: could not ascend from y=${feet.y} (${climb.reason ?? climb.message}); ` +
          "the shaft may be too tight or blocked above."
        );
      }
      climbed.push(retryY);
      continue;
    }
    climbed.push(afterY);
  }

  const final = await context.observe();
  const endFeet = final.player.blockPosition as Vector3;
  return {
    ok: true,
    reached: "guard",
    targetY,
    startY,
    reachedY: endFeet.y,
    climbed,
    guardExhausted: true,
  };
};

export default run;
