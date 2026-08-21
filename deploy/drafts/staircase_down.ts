import { type MinecraftContext, type Vector3, type SkillEntrypoint } from "../lib/minecraft";

/**
 * Descend by carving a walkable 1-wide, 2-tall staircase (ramp) down, one step
 * per level, instead of a straight shaft. Unlike dig-straight-down, the bot can
 * walk back up the same ramp. Each step mines forward-down cells; look-at is
 * used so the block is in view before mining.
 *
 * input:
 *   targetY  : stop descending when feet.y <= targetY (default feet.y - 8)
 *   direction: "x+" | "x-" | "z+" | "z-" (default x+)
 *   maxSteps : hard guard on steps (default 60)
 */
interface Input {
  targetY?: number;
  direction?: "x+" | "x-" | "z+" | "z-";
  maxSteps?: number;
}

function clampInt(value: unknown, min: number, max: number, fallback: number): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return Math.max(min, Math.min(max, Math.floor(value)));
}

const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const input = (rawInput ?? {}) as Input;
  const startObs = await context.observe();
  const startFeet = startObs.player.blockPosition as Vector3;
  const targetY = clampInt(input.targetY, -60, 320, startFeet.y - 8);
  const maxSteps = clampInt(input.maxSteps, 1, 160, 60);
  const advance = {
    x: input.direction === "x-" ? -1 : input.direction === "x+" || !input.direction ? 1 : 0,
    z: input.direction === "z+" ? 1 : input.direction === "z-" ? -1 : 0,
  };

  const held = startObs.inventory.heldItem?.name;
  if (!held || !held.endsWith("_pickaxe")) {
    const e = await context.equip("stone_pickaxe");
    if (e.ok !== true) await context.equip("iron_pickaxe");
  }

  const cleared: Array<string> = [];
  for (let step = 0; step < maxSteps; step++) {
    const obs = await context.observe();
    const feet = obs.player.blockPosition as Vector3;
    if (feet.y <= targetY) {
      return { ok: true, reached: "target", targetY, startY: startFeet.y, reachedY: feet.y, cleared };
    }

    // The cell ahead-and-down is the next step: head then feet cells.
    const forward = { x: feet.x + advance.x, y: feet.y, z: feet.z + advance.z };
    const down = { x: feet.x + advance.x, y: feet.y - 1, z: feet.z + advance.z };

    for (const target of [forward, down]) {
      const before = await context.call("inspect", { block: target }, 5);
      const name = String((before.data as Record<string, unknown>)?.blockName ?? "?");
      if (name === "air" || name === "cave_air" || name === "void_air" || name === "inspect_failed") continue;
      await context.call("look_at", { target }, 5);
      const res = await context.call("mine_block", { block: target, walk_into_range: false }, 25);
      if (res.ok !== true) throw new Error(`staircase_down: mine ${JSON.stringify(target)}: ${res.message}`);
      cleared.push(`${target.x},${target.y},${target.z}`);
    }

    // Step forward-down onto the carved cell.
    const walk = await context.walkTo(
      { x: forward.x + 0.5, y: forward.y, z: forward.z + 0.5 },
      0.9,
      15,
    );
    if (walk.ok !== true) {
      // Moving the body may be blocked; mine one lower level and retry.
      const extraDown = { x: down.x, y: down.y - 1, z: down.z };
      const b = await context.call("inspect", { block: extraDown }, 5);
      const n = String((b.data as Record<string, unknown>)?.blockName ?? "?");
      if (n !== "air" && n !== "inspect_failed") {
        await context.call("look_at", { target: extraDown }, 5);
        await context.call("mine_block", { block: extraDown, walk_into_range: false }, 25);
        cleared.push(`${extraDown.x},${extraDown.y},${extraDown.z}`);
      }
      const retry = await context.walkTo(
        { x: forward.x + 0.5, y: forward.y, z: forward.z + 0.5 },
        1.2,
        20,
      );
      if (retry.ok !== true) {
        throw new Error(`staircase_down: could not step down to ${JSON.stringify(forward)}: ${walk.reason ?? walk.message}`);
      }
    }
  }

  const final = await context.observe();
  const endFeet = final.player.blockPosition as Vector3;
  return { ok: true, reached: "guard", targetY, startY: startFeet.y, reachedY: endFeet.y, cleared, guardExhausted: true };
};

export default run;
