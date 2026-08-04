import { type MinecraftContext, type Vector3, type SkillEntrypoint } from "../lib/minecraft";

const AIR = new Set(["air", "cave_air", "void_air"]);

interface Input {
  steps?: number;
  direction?: "east" | "west" | "north" | "south";
}

async function nameAt(context: MinecraftContext, block: Vector3): Promise<string> {
  const res = await context.call("inspect", { block }, 4);
  if (res.ok !== true) return "air";
  return String((res.data as Record<string, unknown>)?.blockName ?? "?");
}

async function mineCell(context: MinecraftContext, block: Vector3, label: string): Promise<boolean> {
  const name = await nameAt(context, block);
  if (AIR.has(name)) return false;
  const res = await context.call("mine_block", { block, walk_into_range: false }, 25);
  if (res.ok !== true) throw new Error(`${label} ${JSON.stringify(block)}: ${res.message}`);
  await context.sleep(250);
  return true;
}

const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const input = (rawInput ?? {}) as Input;
  const steps = typeof input.steps === "number" ? Math.min(10, Math.max(1, Math.floor(input.steps))) : 6;
  const delta: Vector3 =
    input.direction === "west" ? { x: -1, y: 0, z: 0 }
    : input.direction === "north" ? { x: 0, y: 0, z: -1 }
    : input.direction === "south" ? { x: 0, y: 0, z: 1 }
    : { x: 1, y: 0, z: 0 };

  const held = (await context.observe()).inventory.heldItem?.name;
  if (held !== "stone_pickaxe" && held !== "wooden_pickaxe") await context.equip("stone_pickaxe");

  const start = (await context.observe()).player.blockPosition;
  const mined: Array<string> = [];
  let done = 0;

  for (let i = 0; i < steps; i++) {
    const foot = (await context.observe()).player.blockPosition;
    const nextFeet: Vector3 = { x: foot.x + delta.x, y: foot.y, z: foot.z + delta.z };
    const nextHead: Vector3 = { x: nextFeet.x, y: nextFeet.y + 1, z: nextFeet.z };

    // Stop if we've broken into open air (a cave / surface).
    const [hf, hh] = await Promise.all([nameAt(context, nextFeet), nameAt(context, nextHead)]);
    if (AIR.has(hf) && AIR.has(hh)) {
      return { start, end: (await context.observe()).player.blockPosition, brokenIntoOpen: true, mined };
    }

    // Mine head cell (eye-level) first, then feet cell.
    if (!AIR.has(hh)) {
      await mineCell(context, nextHead, "head");
      mined.push(`head ${nextHead.x},${nextHead.y},${nextHead.z}`);
    }
    if (!AIR.has(hf)) {
      await mineCell(context, nextFeet, "feet");
      mined.push(`feet ${nextFeet.x},${nextFeet.y},${nextFeet.z}`);
    }

    const walked = await context.walkTo(
      { x: nextFeet.x + 0.5, y: nextFeet.y, z: nextFeet.z + 0.5 }, 0.4, 10, "walk_only",
    );
    if (walked.ok !== true) throw new Error(`enter cell ${JSON.stringify(nextFeet)}: ${walked.message}`);
    await context.sleep(200);
    done++;
  }
  return { start, end: (await context.observe()).player.blockPosition, done };
};

export default run;
