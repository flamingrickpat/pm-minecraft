import { requireSuccessful, type MinecraftContext, type Vector3, type SkillEntrypoint } from "../lib/minecraft";

interface Input {
  targetY: number;
  blockToHold?: string;
}

const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const input = (rawInput ?? {}) as Input;
  if (typeof input.targetY !== "number") throw new Error("targetY is required");
  const blockToHold = input.blockToHold ?? "cobblestone";

  // Make sure we hold a placeable block.
  const equipRes = await context.equip(blockToHold);
  if (equipRes.ok !== true) throw new Error(`could not equip ${blockToHold}: ${equipRes.message}`);

  const climbed: number[] = [];
  let guard = 0;
  for (; guard < 40; guard++) {
    const obs = await context.observe();
    const pos = obs.player.position as Vector3;
    if (pos.y >= input.targetY - 0.5) break;
    const res = requireSuccessful(await context.call("pillar_up", {}, 20), `pillar_up @ y=${pos.y}`);
    const afterY = Number(((res.data as Record<string, unknown>)?.position as Record<string, unknown>)?.y ?? pos.y);
    climbed.push(afterY);
    if (afterY <= pos.y) throw new Error(`pillar_up did not gain altitude (${pos.y} -> ${afterY})`);
  }
  const obs = await context.observe();
  return {
    targetY: input.targetY,
    reachedY: (obs.player.position as Vector3).y,
    pillars: climbed.length,
  };
};

export default run;
