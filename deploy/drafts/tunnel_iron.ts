import { itemCount, type MinecraftContext, type Vector3, type SkillEntrypoint } from "../lib/minecraft";

const AIR = new Set(["air", "cave_air", "void_air"]);
const HAZARD = new Set(["water", "flowing_water", "lava", "flowing_lava", "bedrock"]);
const ORE_TARGETS = ["iron_ore", "deepslate_iron_ore"];
const targetItem = "raw_iron";
const want = 3;

async function nameAt(context: MinecraftContext, block: Vector3): Promise<string> {
  const res = await context.call("inspect", { block }, 4);
  if (res.ok !== true) return "air";
  return String((res.data as Record<string, unknown>)?.blockName ?? "?");
}

async function mineCell(context: MinecraftContext, block: Vector3, label: string): Promise<void> {
  // Face the cell first so digging a head/feet cell outside the current view
  // doesn't fail with "Block not in view".
  await context.call("look_at", { target: block }, 5);
  const res = await context.call("mine_block", { block, walk_into_range: false }, 25);
  if (res.ok !== true) throw new Error(`${label} ${JSON.stringify(block)}: ${res.message}`);
  // Let the physical action settle before the next one.
  await context.sleep(250);
}

const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const dirDelta: Vector3 = { x: 1, y: 0, z: 0 }; // tunnel east
  const input = (rawInput ?? {}) as { direction?: "east" | "west" | "north" | "south" };
  if (input.direction === "west") Object.assign(dirDelta, { x: -1, y: 0, z: 0 });
  else if (input.direction === "north") Object.assign(dirDelta, { x: 0, y: 0, z: -1 });
  else if (input.direction === "south") Object.assign(dirDelta, { x: 0, y: 0, z: 1 });

  const held = (await context.observe()).inventory.heldItem?.name;
  if (held !== "stone_pickaxe" && held !== "wooden_pickaxe") await context.equip("stone_pickaxe");

  const before = await context.observe();
  const start = before.player.blockPosition;
  let steps = 0;

  for (; steps < 14; steps++) {
    const state = await context.observe();
    const rawNow = itemCount(state, targetItem);
    if (rawNow >= want) return { targetItem, rawGot: rawNow, steps, done: true };

    // 1) Mine any visible iron ore around the current cell.
    let found: Vector3 | null = null;
    for (const ore of ORE_TARGETS) {
      const f = await context.findBlock(ore, 12);
      if (f.ok === true) {
        const d = (f.data as Record<string, unknown>)?.block as Record<string, unknown>;
        found = { x: d.x as number, y: d.y as number, z: d.z as number };
        break;
      }
    }
    if (found) {
      await context.equip("stone_pickaxe");
      const m = await context.call("mine_block", { block: found, walk_into_range: true }, 30);
      if (m.ok !== true) throw new Error(`mine ore ${JSON.stringify(found)}: ${m.message}`);
      await context.sleep(300);
      continue;
    }

    // 2) Tunnel one cell forward (feet + head), then walk into it.
    const foot = (await context.observe()).player.blockPosition;
    const nextFeet: Vector3 = { x: foot.x + dirDelta.x, y: foot.y, z: foot.z + dirDelta.z };
    const nextHead: Vector3 = { x: nextFeet.x, y: nextFeet.y + 1, z: nextFeet.z };
    const feetName = await nameAt(context, nextFeet);
    const headName = await nameAt(context, nextHead);
    // Never dig into a liquid or bedrock: stop cleanly instead of stranding the.
    // bot in an aquifer or lava (hazard guard).
    if (HAZARD.has(feetName) || HAZARD.has(headName)) {
      return {
        targetItem,
        rawGot: itemCount(await context.observe(), targetItem),
        steps,
        done: false,
        reason: "hazard_forward",
        hazard: feetName !== "air" ? feetName : headName,
        hazardCell: nextFeet,
      };
    }
    // Mine the head cell first (eye-level, line-of-sight), then the feet cell below it.
    if (!AIR.has(headName)) await mineCell(context, nextHead, "tunnel head");
    if (!AIR.has(feetName)) await mineCell(context, nextFeet, "tunnel feet");

    const walked = await context.walkTo(
      { x: nextFeet.x + 0.5, y: nextFeet.y, z: nextFeet.z + 0.5 },
      0.4, 10, "walk_only",
    );
    if (walked.ok !== true) throw new Error(`enter tunnel cell: ${walked.message}`);
    await context.sleep(200);
  }

  const after = await context.observe();
  return { targetItem, rawGot: itemCount(after, targetItem), steps, done: false, endPos: after.player.blockPosition };
};

export default run;
