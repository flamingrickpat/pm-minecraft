import { type MinecraftContext, type Vector3, type SkillEntrypoint } from "../sdk/minecraft.js";

/**
 * Tunnel horizontally at the current level, harvesting ores exposed in the
 * tunnel walls/face. Mines a 3-high face (feet, head, and the clearance cell
 * the body's standability rule needs above the head), inspects the wall, floor
 * and ceiling cells each step, and mines any coal/copper ore found. Falling
 * gravel/sand that refills a mined cell is re-mined automatically (mineStable
 * re-checks each cell after a settle delay). Each step forward is verified
 * against the bot's real position, so the script cannot advance its internal
 * feet counter while the bot stays behind.
 *
 * input:
 *   length     : tunnel length in blocks (default 12)
 *   direction  : "x+" | "x-" | "z+" | "z-" (default x+)
 *   wantIron   : also harvest iron_ore (needs stone pickaxe held by caller)
 */
interface Input {
  length?: number;
  direction?: "x+" | "x-" | "z+" | "z-";
  wantIron?: boolean;
}

const ORES = ["coal_ore", "deepslate_coal_ore", "copper_ore", "deepslate_copper_ore"];

function clampInt(value: unknown, min: number, max: number, fallback: number): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return Math.max(min, Math.min(max, Math.floor(value)));
}

  const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const input = (rawInput ?? {}) as Input;
  const length = clampInt(input.length, 1, 64, 12);
  const wantIron = input.wantIron === true;
  const ores = wantIron ? [...ORES, "iron_ore", "deepslate_iron_ore"] : ORES;
  const advance = {
    x: input.direction === "x-" ? -1 : input.direction === "x+" || !input.direction ? 1 : 0,
    z: input.direction === "z+" ? 1 : input.direction === "z-" ? -1 : 0,
  };

  const startObs = await context.observe();
  const startFeet = startObs.player.blockPosition as Vector3;
  const mined: string[] = [];

  const nameOf = async (target: Vector3): Promise<string> => {
    const before = await context.call("inspect", { block: target }, 5);
    return String((before.data as Record<string, unknown>)?.blockName ?? "?");
  };

  const mine = async (target: Vector3, label: string): Promise<boolean> => {
    const name = await nameOf(target);
    if (name === "air" || name === "cave_air" || name === "void_air") return false;
    await context.call("look_at", { target }, 5);
    let res = await context.call("mine_block", { block: target, walk_into_range: false }, 30);
    if (res.ok !== true && String(res.reason ?? "").includes("harvest")) {
      for (const pick of ["stone_pickaxe", "iron_pickaxe", "wooden_pickaxe"]) {
        const e = await context.equip(pick);
        if (e.ok === true) break;
      }
      res = await context.call("mine_block", { block: target, walk_into_range: false }, 30);
    }
    if (res.ok !== true) throw new Error(`tunnel_and_mine: mine ${label} at ${JSON.stringify(target)}: ${res.message}`);
    mined.push(`${name}@${target.x},${target.y},${target.z}`);
    return true;
  };

  // Mine a cell and make sure it STAYS air: falling gravel/sand cascades refill
  // the freshly mined cell from above (mining top-down invites this), so
  // re-check and re-mine up to 3 times with a short settle delay.
  const mineStable = async (target: Vector3, label: string): Promise<void> => {
    for (let attempt = 0; attempt < 3; attempt += 1) {
      const minedNow = await mine(target, label);
      if (!minedNow) return;
      await new Promise((resolve) => setTimeout(resolve, 600));
      const after = await nameOf(target);
      if (after === "air" || after === "cave_air" || after === "void_air") return;
      // Block refilled (gravel/sand fell in): loop and mine the refill.
    }
    throw new Error(`tunnel_and_mine: ${label} at ${JSON.stringify(target)} keeps refilling (falling gravel/sand column)`);
  };

  // Hold the best pickaxe available.
  for (const pick of ["stone_pickaxe", "iron_pickaxe", "wooden_pickaxe"]) {
    const e = await context.equip(pick);
    if (e.ok === true) break;
  }

  let feet = startFeet;
  for (let step = 0; step < length; step += 1) {
    const forward: Vector3 = { x: feet.x + advance.x, y: feet.y, z: feet.z + advance.z };
    const forwardUp: Vector3 = { x: feet.x + advance.x, y: feet.y + 1, z: feet.z + advance.z };

    // Mine the tunnel face (3 high: feet, head, and the clearance cell the
    // body's standability check requires above the head). mineStable handles
    // gravel/sand cascades that refill the cell from above.
    await mineStable(forwardUp, "face-head");
    await mineStable({ x: forward.x, y: forward.y + 2, z: forward.z }, "face-clearance");
    await mineStable(forward, "face-feet");

    // Scan the freshly exposed cells around the new position for ores:
    // side walls (perpendicular), floor dips, and the face-ahead cells.
    const perp = advance.x !== 0 ? { x: 0, z: 1 } : { x: 1, z: 0 };
    const scanCells: Vector3[] = [
      { x: forward.x, y: forward.y, z: forward.z }, // face feet (already mined -> air)
      { x: forward.x, y: forward.y + 1, z: forward.z },
      { x: forward.x + perp.x, y: forward.y, z: forward.z + perp.z },
      { x: forward.x - perp.x, y: forward.y, z: forward.z - perp.z },
      { x: forward.x + perp.x, y: forward.y + 1, z: forward.z + perp.z },
      { x: forward.x - perp.x, y: forward.y + 1, z: forward.z - perp.z },
      { x: forward.x, y: forward.y - 1, z: forward.z }, // floor (ore in the floor)
      { x: forward.x, y: forward.y + 2, z: forward.z }, // ceiling
    ];
    for (const cell of scanCells) {
      const name = await nameOf(cell);
      if (ores.includes(name)) {
        await mine(cell, `ore-${name}`);
        // Ore neighbors often cluster: check the cells adjacent to the ore too.
        for (const d of [{ x: 1, y: 0, z: 0 }, { x: -1, y: 0, z: 0 }, { x: 0, y: 1, z: 0 }, { x: 0, y: -1, z: 0 }, { x: 0, y: 0, z: 1 }, { x: 0, y: 0, z: -1 }]) {
          const n = { x: cell.x + d.x, y: cell.y + d.y, z: cell.z + d.z };
          const nn = await nameOf(n);
          if (ores.includes(nn)) await mine(n, `ore-${nn}`);
        }
      }
    }

    // Step forward into the tunnel. Verify the bot actually arrived:
    // walk_to_exact can report an instant "success" with an empty path when
    // the goal is mis-snapped, which would desync this script's feet tracking.
    let arrived = false;
    for (let walkAttempt = 0; walkAttempt < 2 && !arrived; walkAttempt += 1) {
      const walk = await context.call(
        "walk_to_exact",
        { target: { x: forward.x + 0.5, y: forward.y, z: forward.z + 0.5 }, tolerance: 0.4 },
        15
      );
      if (walk.ok !== true) {
        throw new Error(`tunnel_and_mine: could not advance to ${JSON.stringify(forward)}: ${walk.reason ?? walk.message}`);
      }
      const posObs = await context.observe();
      const pos = posObs.player.blockPosition as Vector3;
      arrived = pos.x === forward.x && pos.y === forward.y && pos.z === forward.z;
    }
    if (!arrived) {
      throw new Error(`tunnel_and_mine: walk reported success but bot is not at ${JSON.stringify(forward)} (empty-path desync)`);
    }
    feet = forward;
  }

  const finalObs = await context.observe();
  return {
    ok: true,
    start: startFeet,
    end: finalObs.player.blockPosition,
    minedCount: mined.length,
    mined
  };
};

export default run;
