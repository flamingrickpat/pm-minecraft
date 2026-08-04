import {
  requireSuccessful,
  type MinecraftContext,
  type Vector3,
  type SkillEntrypoint,
} from "../lib/minecraft";

interface Input {
  itemName?: string;
}

const TOP_FACE: Vector3 = { x: 0, y: 1, z: 0 };
const CARDINALS: Vector3[] = [
  { x: 1, y: 0, z: 0 },
  { x: -1, y: 0, z: 0 },
  { x: 0, y: 0, z: 1 },
  { x: 0, y: 0, z: -1 },
];
const AIR = new Set(["air", "cave_air", "void_air"]);

async function inspectName(context: MinecraftContext, block: Vector3): Promise<string> {
  const inspected = requireSuccessful(await context.call("inspect", { block }, 5), `inspect ${JSON.stringify(block)}`);
  return String((inspected.data as Record<string, unknown>)?.blockName ?? "?");
}

const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const input = (rawInput ?? {}) as Input;
  const itemName = input.itemName ?? "furnace";
  const feet = (await context.observe()).player.blockPosition;

  let reference: Vector3 | null = null;
  let target: Vector3 | null = null;
  for (const cardinal of CARDINALS) {
    const candidate = { x: feet.x + cardinal.x, y: feet.y - 1, z: feet.z + cardinal.z };
    const foundation = await inspectName(context, candidate);
    if (foundation === "air" || foundation === "cave_air") continue; // floor below the side cell must be solid
    const dest = { x: candidate.x, y: candidate.y + TOP_FACE.y, z: candidate.z };
    const destName = await inspectName(context, dest);
    if (AIR.has(destName)) {
      reference = candidate;
      target = dest;
      break;
    }
  }
  if (reference === null || target === null) {
    throw new Error(`No clear floor cell beside ${JSON.stringify(feet)} for ${itemName}`);
  }

  requireSuccessful(await context.equip(itemName), `equip ${itemName}`);
  requireSuccessful(await context.placeBlock(reference, TOP_FACE, true), `place ${itemName}`);

  const placed = await inspectName(context, target);
  if (placed !== itemName) {
    throw new Error(`Placement unverified: ${JSON.stringify(target)} holds ${placed}`);
  }
  return { referenceBlock: reference, placedBlock: target };
};

export default run;
