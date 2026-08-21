import { type MinecraftContext, type Vector3, type SkillEntrypoint } from "../sdk/minecraft.js";

/**
 * Descend by carving a walkable 1-wide staircase (ramp) down, one step per
 * level, instead of a straight shaft. Each step mines THREE cells (feet, head,
 * and the clearance cell above the head — the body's standability rule needs
 * 3-block clearance above the floor) so the ramp stays walkable both ways.
 * Unlike dig-straight-down, the bot can walk back up the same ramp. Look-at is
 * used so the block is in view before mining. A no-progress guard stops the
 * run with a clear diagnostic if the body stops advancing (drop edge,
 * obstruction, water pocket).
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
    // Try every pickaxe tier; the bot usually has wooden at this stage.
    for (const pick of ["wooden_pickaxe", "stone_pickaxe", "iron_pickaxe", "diamond_pickaxe"]) {
      const e = await context.equip(pick);
      if (e.ok === true) break;
    }
  }

  const cleared: Array<string> = [];
  let lastFeetKey = "";
  let noProgressSteps = 0;
  for (let step = 0; step < maxSteps; step++) {
    const obs = await context.observe();
    const feet = obs.player.blockPosition as Vector3;
    if (feet.y <= targetY) {
      return { ok: true, reached: "target", targetY, startY: startFeet.y, reachedY: feet.y, cleared };
    }

    // No-progress guard: if the body has not moved for several steps (e.g.
    // standing at a drop edge where nothing needs mining but walk_to_visible
    // reports "already within tolerance"), stop with a clear diagnostic
    // instead of burning the whole guard budget.
    const feetKey = `${feet.x},${feet.y},${feet.z}`;
    if (feetKey === lastFeetKey) {
      noProgressSteps += 1;
      if (noProgressSteps >= 3) {
        throw new Error(
          `staircase_down: no progress for 3 steps at ${feetKey} — the body is not advancing (drop edge, obstruction, or walk tolerance too loose). Re-position to solid ground and retry.`
        );
      }
    } else {
      noProgressSteps = 0;
      lastFeetKey = feetKey;
    }

    // The next stair step needs THREE cells cleared: feet (y-1), head (y),
    // and the ceiling (y+1). The body's standability check demands 3-block
    // clearance above the floor (jump headroom), so a 2-high carve alone
    // makes the step cell "not standable" and the walk snaps back to the
    // bot's own cell.
    const forward = { x: feet.x + advance.x, y: feet.y, z: feet.z + advance.z };
    const down = { x: feet.x + advance.x, y: feet.y - 1, z: feet.z + advance.z };
    const ceiling = { x: feet.x + advance.x, y: feet.y + 1, z: feet.z + advance.z };

    for (const target of [forward, down, ceiling]) {
      const before = await context.call("inspect", { block: target }, 5);
      const name = String((before.data as Record<string, unknown>)?.blockName ?? "?");
      if (name === "air" || name === "cave_air" || name === "void_air" || name === "inspect_failed") continue;
      await context.call("look_at", { target }, 5);
      let res = await context.call("mine_block", { block: target, walk_into_range: false }, 25);
      if (res.ok !== true && String(res.reason ?? "").includes("harvest")) {
        // Picked-up drops (dirt, etc.) can end up in the hand mid-run;
        // re-equip a pickaxe and retry the block once.
        for (const pick of ["wooden_pickaxe", "stone_pickaxe", "iron_pickaxe", "diamond_pickaxe"]) {
          const e = await context.equip(pick);
          if (e.ok === true) break;
        }
        res = await context.call("mine_block", { block: target, walk_into_range: false }, 25);
      }
      if (res.ok !== true) throw new Error(`staircase_down: mine ${JSON.stringify(target)}: ${res.message}`);
      cleared.push(`${target.x},${target.y},${target.z}`);
    }

    // Step forward-down onto the carved cell. walk_to_exact (not walk_to_visible):
    // the visible variant snaps to the nearest standable cell near the target,
    // which can be the bot's own current cell on a carved stair — "success"
    // without moving. The exact walk targets the carved floor precisely.
    const stepTarget = { x: forward.x + 0.5, y: forward.y - 1, z: forward.z + 0.5 };
    // Tolerance 0.4: walk_to_exact's "already within tolerance" check is
    // horizontal-only, so a looser tolerance short-circuits while the bot is
    // still one block ABOVE the carved cell.
    const walk = await context.call("walk_to_exact", { target: stepTarget, tolerance: 0.4 }, 15);
    if (walk.ok !== true) {
      // Fallback: raw forward control. The cells are already mined; stepping
      // in is a simple 1-block walk off the edge, which fine_control handles
      // even when the pathfinder refuses (it dislikes freshly carved stairs).
      // NEVER mine extraDown here — that is the floor of the next step.
      const frame = await context.call("capture_frame", {}, 30);
      const frameId = (frame.data as Record<string, unknown> | undefined)?.frameId
        ?? (frame as unknown as Record<string, unknown>).frameId;
      if (typeof frameId === "string") {
        // Aim at the carved step cell (look_at is absolute; the body's rotate
        // is a RELATIVE delta and easy to get wrong here).
        await context.call("look_at", { target: { x: forward.x + 0.5, y: forward.y - 0.5, z: forward.z + 0.5 } }, 5);
        await context.call(
          "fine_control",
          { controls: { forward: true }, durationMs: 900, visualCheckFrameId: frameId },
          15
        );
      }
      const retry = await context.call("walk_to_exact", { target: stepTarget, tolerance: 0.6 }, 20);
      if (retry.ok !== true) {
        const after = await context.observe();
        const feetAfter = after.player.blockPosition as Vector3;
        if (feetAfter.x === feet.x && feetAfter.z === feet.z && feetAfter.y === feet.y) {
          throw new Error(
            `staircase_down: could not step down to ${JSON.stringify(forward)}: ${walk.reason ?? walk.message}`
          );
        }
        // The fine-control nudge moved the bot; continue the loop from the new position.
      }
    }
  }

  const final = await context.observe();
  const endFeet = final.player.blockPosition as Vector3;
  return { ok: true, reached: "guard", targetY, startY: startFeet.y, reachedY: endFeet.y, cleared, guardExhausted: true };
};

export default run;
