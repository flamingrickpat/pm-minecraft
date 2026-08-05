import { itemCount, type MinecraftContext, type Vector3, type SkillEntrypoint } from "../lib/minecraft";

/**
 * Branch-mine for raw iron. Tunnels 2-tall 1-wide, collecting drops by walking
 * into each cleared cell. Unlike tunnel_iron.ts it INSPECTS every cell before
 * mining and refuses to mine water/lava; if the forward direction is blocked by
 * a hazard or a non-mineable block it rotates to the next compass direction.
 * Stops once it holds `want` raw iron (default 3 → enough for an iron pickaxe).
 *
 * input: { direction: "east"|"west"|"north"|"south", want: number, maxSteps: number }
 */
interface Input {
  direction?: "east" | "west" | "north" | "south";
  want?: number;
  maxSteps?: number;
}

const AIR = new Set(["air", "cave_air", "void_air"]);
const HAZARD = new Set(["water", "flowing_water", "lava", "flowing_lava", "bedrock", "barrier", "magma_block"]);
const ORE_TARGETS = ["iron_ore", "deepslate_iron_ore"];
const DELTAS: Record<string, Vector3> = {
  east: { x: 1, y: 0, z: 0 },
  west: { x: -1, y: 0, z: 0 },
  north: { x: 0, y: 0, z: -1 },
  south: { x: 0, y: 0, z: 1 },
};
const ORDER = ["east", "south", "west", "north"];

function clampInt(value: unknown, min: number, max: number, fallback: number): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return Math.max(min, Math.min(max, Math.floor(value)));
}

async function nameAt(context: MinecraftContext, block: Vector3): Promise<string> {
  const res = await context.call("inspect", { block }, 4);
  if (res.ok !== true) return "?";
  return String((res.data as Record<string, unknown>)?.blockName ?? "?");
}

const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const input = (rawInput ?? {}) as Input;
  const want = clampInt(input.want, 1, 64, 3);
  const maxSteps = clampInt(input.maxSteps, 1, 80, 40);
  let dir: string = ORDER.includes(input.direction ?? "") ? (input.direction as string) : "east";

  const held = (await context.observe()).inventory.heldItem?.name;
  if (held !== "stone_pickaxe" && held !== "iron_pickaxe" && held !== "diamond_pickaxe") {
    await context.equip("stone_pickaxe");
  }

  const before = await context.observe();
  const start = before.player.blockPosition as Vector3;
  let steps = 0;
  let skipped: string[] = [];

  for (; steps < maxSteps; steps++) {
    const obs = await context.observe();
    if (itemCount(obs, "raw_iron") >= want) {
      return { ok: true, done: true, reason: "iron_goal", rawIron: itemCount(obs, "raw_iron"), steps, start, end: obs.player.blockPosition as Vector3, skipped };
    }

    // 1) Mine any visible iron around us — read it straight off the fresh observe's
    //    nearbyBlocks (already visibility-filtered) instead of an extra find_block scan.
    const nb = (obs.surroundings?.nearbyBlocks ?? []) as Array<{ name: string; nearest?: { x: number; y: number; z: number } }>;
    let found: Vector3 | null = null;
    for (const b of nb) {
      if (ORE_TARGETS.includes(b.name) && b.nearest) {
        found = { x: b.nearest.x, y: b.nearest.y, z: b.nearest.z };
        break;
      }
    }
    if (found) {
      await context.equip("stone_pickaxe");
      const m = await context.call("mine_block", { block: found, walk_into_range: true }, 30);
      if (m.ok !== true) { skipped.push(`mine_ore_fail@${found.x},${found.y},${found.z}`); continue; }
      await context.sleep(300);
      continue;
    }

    // 2) Find a direction whose next 2-high cell is clear of hazards and mine.
    const foot = (await context.observe()).player.blockPosition as Vector3;
    let advanced = false;
    for (let rot = 0; rot < 4; rot++) {
      const d = DELTAS[dir];
      const nf: Vector3 = { x: foot.x + d.x, y: foot.y, z: foot.z + d.z };
      const nh: Vector3 = { x: nf.x, y: nf.y + 1, z: nf.z };
      const feetName = await nameAt(context, nf);
      const headName = await nameAt(context, nh);
      if (HAZARD.has(feetName) || HAZARD.has(headName) || feetName === "?" || headName === "?") {
        skipped.push(`${dir}@${nf.x},${nf.y},${nf.z}(${feetName}/${headName})`);
        dir = ORDER[(ORDER.indexOf(dir) + 1) % 4]; // rotate
        continue;
      }
      if (!AIR.has(headName)) {
        const mh = await context.call("mine_block", { block: nh, walk_into_range: true }, 25);
        if (mh.ok !== true) { skipped.push(`head_fail@${nh.x},${nh.y},${nh.z}`); dir = ORDER[(ORDER.indexOf(dir) + 1) % 4]; continue; }
        await context.sleep(200);
      }
      if (!AIR.has(feetName)) {
        const mf = await context.call("mine_block", { block: nf, walk_into_range: true }, 25);
        if (mf.ok !== true) { skipped.push(`feet_fail@${nf.x},${nf.y},${nf.z}`); dir = ORDER[(ORDER.indexOf(dir) + 1) % 4]; continue; }
        await context.sleep(200);
      }
      const walked = await context.walkTo(
        { x: nf.x + 0.5, y: nf.y, z: nf.z + 0.5 }, 0.4, 10, "walk_only",
      );
      if (walked.ok !== true) { skipped.push(`walk_fail@${nf.x},${nf.y},${nf.z}`); dir = ORDER[(ORDER.indexOf(dir) + 1) % 4]; continue; }
      advanced = true;
      break;
    }
    if (!advanced) {
      const after = await context.observe();
      return { ok: false, done: false, reason: "no_clear_direction", rawIron: itemCount(after, "raw_iron"), steps, start, end: after.player.blockPosition as Vector3, skipped };
    }
    await context.sleep(150);
  }

  const after = await context.observe();
  return { ok: true, done: false, reason: "max_steps", rawIron: itemCount(after, "raw_iron"), steps, start, end: after.player.blockPosition as Vector3, skipped };
};

export default run;
