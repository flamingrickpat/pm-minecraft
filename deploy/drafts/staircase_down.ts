/**
 * Descend by carving a walkable 1-wide, 2-tall staircase (ramp) down, one step
 * per level, instead of a straight shaft. The bot can walk back up the same
 * ramp. The body also exposes this natively (minecraft_staircase_down); this
 * draft is the readable reference for a step-per-level descent.
 *
 * input:
 *   targetY  : stop descending when feet.y <= targetY (default feet.y - 8)
 *   direction: "east" | "west" | "north" | "south" (default: current facing)
 *   maxSteps : hard guard on steps (default 60)
 */

interface Input {
  targetY?: number;
  direction?: "east" | "west" | "north" | "south";
  maxSteps?: number;
}

function offset(cardinal: string): { x: number; z: number } {
  switch (cardinal) {
    case "west": return { x: -1, z: 0 };
    case "north": return { x: 0, z: -1 };
    case "south": return { x: 0, z: 1 };
    default: return { x: 1, z: 0 };
  }
}

export default async function run(api: any, rawInput: unknown) {
  const input = (rawInput ?? {}) as Input;
  const startState = await api.observe({});
  const startFeet = startState.camera.block_position;
  const targetY = Number.isFinite(input.targetY) ? Math.floor(input.targetY!) : startFeet.y - 8;
  const maxSteps = Math.min(160, Math.max(1, Math.floor(input.maxSteps ?? 60)));
  const delta = offset(input.direction ?? startState.camera.cardinal);

  const held = startState.held_item?.name;
  if (!held || !held.endsWith("_pickaxe")) {
    try { await api.equip({ item: "iron_pickaxe" }); }
    catch { await api.equip({ item: "stone_pickaxe" }); }
  }

  const cleared: string[] = [];
  for (let step = 0; step < maxSteps; step++) {
    const feet = (await api.observe({})).camera.block_position;
    if (feet.y <= targetY) {
      return { ok: true, reached: "target", startY: startFeet.y, reachedY: feet.y, cleared };
    }

    // The next step is the cell ahead at head height plus the cell below it.
    const forward = { x: feet.x + delta.x, y: feet.y, z: feet.z + delta.z };
    const down = { x: forward.x, y: forward.y - 1, z: forward.z };

    for (const target of [forward, down]) {
      const safety = await api.safeToDig({ position: target });
      if (safety.risk === "warning") {
        return { ok: false, reached: "hazard", at: target, safety, cleared };
      }
      try {
        const result = await api.mineBlock({ position: target });
        if (result.ok) cleared.push(`${target.x},${target.y},${target.z}`);
      } catch {
        // Already air.
      }
    }

    const walked = await api.walkVisible({
      target: { x: forward.x + 0.5, y: forward.y, z: forward.z + 0.5 },
      limit: 6,
      timeoutMs: 15000,
    });
    if (!walked.ok) {
      return { ok: false, reached: "blocked", at: forward, reason: walked.reason, cleared };
    }
  }

  const finalFeet = (await api.observe({})).camera.block_position;
  return { ok: true, reached: "guard", startY: startFeet.y, reachedY: finalFeet.y, cleared };
}
