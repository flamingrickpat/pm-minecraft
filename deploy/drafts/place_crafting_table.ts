import {
  requireSuccessful,
  type MinecraftContext,
  type MinecraftResponse,
  type SkillEntrypoint,
  type Vector3,
} from "../lib/minecraft";

interface Input {
  /** Block the table is placed against. Defaults to the floor beside the character. */
  referenceBlock?: Vector3;
  /** Face of the reference block that receives the table. Defaults to the top face. */
  face?: Vector3;
}

const TOP_FACE: Vector3 = { x: 0, y: 1, z: 0 };
const CARDINALS: Vector3[] = [
  { x: 1, y: 0, z: 0 },
  { x: -1, y: 0, z: 0 },
  { x: 0, y: 0, z: 1 },
  { x: 0, y: 0, z: -1 },
];
const AIR = new Set(["air", "cave_air", "void_air"]);

function blockCell(value: unknown, label: string): Vector3 {
  const candidate = value as Partial<Vector3> | undefined;
  if (
    typeof candidate?.x !== "number"
    || typeof candidate?.y !== "number"
    || typeof candidate?.z !== "number"
  ) {
    throw new Error(`${label} must be {x,y,z}: ${JSON.stringify(value)}`);
  }
  return { x: Math.floor(candidate.x), y: Math.floor(candidate.y), z: Math.floor(candidate.z) };
}

function offset(block: Vector3, delta: Vector3): Vector3 {
  return { x: block.x + delta.x, y: block.y + delta.y, z: block.z + delta.z };
}

async function inspect(context: MinecraftContext, block: Vector3): Promise<Record<string, unknown>> {
  const inspected: MinecraftResponse = requireSuccessful(
    await context.call("inspect", { block }, 5),
    `inspect ${JSON.stringify(block)}`,
  );
  return inspected.data ?? {};
}

/** A foundation must be a full solid block, and the cell that receives the table must be empty. */
async function foundationRefusal(
  context: MinecraftContext,
  reference: Vector3,
  target: Vector3,
): Promise<string | null> {
  const foundation = await inspect(context, reference);
  if (foundation.boundingBox !== "block") {
    return `${String(foundation.blockName)} at ${JSON.stringify(reference)} is not a full solid block`;
  }
  const destination = await inspect(context, target);
  if (!AIR.has(String(destination.blockName))) {
    return `${JSON.stringify(target)} is occupied by ${String(destination.blockName)}`;
  }
  return null;
}

const run: SkillEntrypoint = async (context, rawInput) => {
  const input = (rawInput ?? {}) as Input;
  const face = input.face === undefined ? TOP_FACE : blockCell(input.face, "face");
  let reference: Vector3 | null = null;

  if (input.referenceBlock !== undefined) {
    reference = blockCell(input.referenceBlock, "referenceBlock");
    const refusal = await foundationRefusal(context, reference, offset(reference, face));
    if (refusal !== null) throw new Error(`Unsafe foundation: ${refusal}`);
  } else {
    // No coordinates given: stay put and use the floor of a cell beside the character.
    const feet = (await context.observe()).player.blockPosition;
    const refusals: string[] = [];
    for (const cardinal of CARDINALS) {
      const candidate = offset(feet, { x: cardinal.x, y: -1, z: cardinal.z });
      const refusal = await foundationRefusal(context, candidate, offset(candidate, face));
      if (refusal === null) {
        reference = candidate;
        break;
      }
      refusals.push(refusal);
    }
    if (reference === null) {
      throw new Error(`No cell beside ${JSON.stringify(feet)} can hold a table: ${refusals.join("; ")}`);
    }
  }

  const target = offset(reference, face);
  requireSuccessful(await context.equip("crafting_table"), "equip crafting table");
  requireSuccessful(await context.placeBlock(reference, face, true), "place crafting table");

  const placed = await inspect(context, target);
  if (placed.blockName !== "crafting_table") {
    throw new Error(`Placement unverified: ${JSON.stringify(target)} holds ${String(placed.blockName)}`);
  }
  return { referenceBlock: reference, face, craftingTable: target };
};

export default run;
