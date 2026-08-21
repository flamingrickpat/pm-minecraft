import {
  requireSuccessful,
  type MinecraftContext,
  type MinecraftResponse,
  type SkillEntrypoint,
  type Vector3,
} from "../sdk/minecraft.js";

/**
 * build_house: phase-driven hut builder for the riverbank forest camp.
 *
 * House geometry (absolute world coordinates):
 *   - Footprint: x 611..615, z -452..-448 (5x5 exterior, 3x3 interior)
 *   - Walls: oak_planks at y 63, 64, 65 on the perimeter ring
 *   - Door gap: (613, 63..64, -448) south wall center (door placed in phase 3)
 *   - Roof: birch_planks ring at y 66 on top of the walls, then interior fill
 *   - Build stance: stand at the interior center (613.5, 63, -450.5); every
 *     placement is within eye-reach from there, so no walking is needed.
 *
 * Phases (input.phase): "walls" | "roof" | "door"
 *   walls: equip oak_planks, place the perimeter ring layer by layer
 *          (bottom layer against the ground's top face, higher layers
 *          against the wall block below), skipping the door column.
 *   roof:  equip birch_planks, place the y=66 ring on the wall tops, then
 *          fill the interior roof cells against already-placed roof blocks.
 *   door:  craft birch planks first if missing, place the crafting table
 *          inside, craft an oak door, then place it into the south gap.
 *
 * Idempotent: cells that are already occupied by the expected block are
 * skipped, so a timed-out run can simply be re-invoked to continue.
 */

const ORIGIN = { x: 611, y: 63, z: -452 }; // north-west corner, first wall layer
const SIZE_X = 5;
const SIZE_Z = 5;
const WALL_HEIGHT = 3; // layers at y 63..65
const DOOR = { x: 613, z: -448 }; // south wall center column
const CENTER = { x: 613, z: -450 };

const TOP_FACE: Vector3 = { x: 0, y: 1, z: 0 };

interface Input {
  phase: "walls" | "roof" | "door";
}

function isPerimeter(x: number, z: number): boolean {
  return (
    x === ORIGIN.x || x === ORIGIN.x + SIZE_X - 1 ||
    z === ORIGIN.z || z === ORIGIN.z + SIZE_Z - 1
  );
}

function isDoorColumn(x: number, z: number): boolean {
  return x === DOOR.x && z === DOOR.z;
}

const run: SkillEntrypoint = async (ctx: MinecraftContext, raw: unknown) => {
  const input = raw as Input;
  if (input.phase !== "walls" && input.phase !== "roof" && input.phase !== "door") {
    throw new Error("phase must be 'walls', 'roof', or 'door'");
  }

  // Stand at the interior center so every wall/roof cell is in placement
  // reach without further walking. walk_to_exact (not walk_to_visible) so
  // the body does not overlap any wall cell — the server refuses placements
  // intersecting the player's own bounding box.
  const stance = { x: CENTER.x + 0.5, y: 63, z: CENTER.z + 0.5 };
  await requireSuccessful(
    await ctx.call("walk_to_exact", { target: stance }, 60),
    "walk to build stance"
  );

  const placed: string[] = [];
  const skipped: string[] = [];

  if (input.phase === "walls") {
    await requireSuccessful(await ctx.equip("oak_planks"), "equip oak_planks");
    for (let layer = 0; layer < WALL_HEIGHT; layer += 1) {
      const y = ORIGIN.y + layer;
      for (let x = ORIGIN.x; x < ORIGIN.x + SIZE_X; x += 1) {
        for (let z = ORIGIN.z; z < ORIGIN.z + SIZE_Z; z += 1) {
          if (!isPerimeter(x, z)) continue;
          if (isDoorColumn(x, z)) continue; // door gap + lintel handled separately
          // Bottom layer sits on the ground; higher layers on the wall below.
          const reference: Vector3 = { x, y: y - 1, z };
          await placeCell(ctx, reference, TOP_FACE, "oak_planks", `${x},${y},${z}`, placed, skipped);
        }
      }
    }
    // Door lintel: the top block above the door gap has no wall block below
    // it (the gap is underneath), so it is placed against its west neighbour's
    // side face instead. The neighbour exists by now (lower x iterates first).
    const lintelY = ORIGIN.y + 2;
    const lintel: Vector3 = { x: DOOR.x - 1, y: lintelY, z: DOOR.z };
    await placeCell(ctx, lintel, { x: 1, y: 0, z: 0 }, "oak_planks", `${DOOR.x},${lintelY},${DOOR.z}`, placed, skipped);
  }

  if (input.phase === "roof") {
    // Birch logs are still logs at this point; turn them into roof planks.
    await requireSuccessful(await ctx.craft("birch_planks", 11), "craft birch_planks");
    await requireSuccessful(await ctx.equip("birch_planks"), "equip birch_planks");
    // Ring of roof blocks directly on the wall tops.
    const roofPlaced = new Set<string>();
    for (let x = ORIGIN.x; x < ORIGIN.x + SIZE_X; x += 1) {
      for (let z = ORIGIN.z; z < ORIGIN.z + SIZE_Z; z += 1) {
        if (!isPerimeter(x, z)) continue;
        const reference: Vector3 = { x, y: ORIGIN.y + WALL_HEIGHT - 1, z };
        await placeCell(ctx, reference, TOP_FACE, "birch_planks", `${x},${ORIGIN.y + WALL_HEIGHT},${z}`, placed, skipped);
        roofPlaced.add(`${x},${ORIGIN.y + WALL_HEIGHT},${z}`);
      }
    }
    // Interior roof cells: fill from the ring inward, each new cell placed
    // against an already-placed roof neighbour's side face. Interleaved
    // passes so every cell eventually finds a placed neighbour.
    const roofY = ORIGIN.y + WALL_HEIGHT;
    for (let pass = 0; pass < 2; pass += 1) {
      for (let x = ORIGIN.x + 1; x < ORIGIN.x + SIZE_X - 1; x += 1) {
        for (let z = ORIGIN.z + 1; z < ORIGIN.z + SIZE_Z - 1; z += 1) {
          if (roofPlaced.has(`${x},${roofY},${z}`)) continue;
          const neighbour = [
            { x: x + 1, y: roofY, z }, { x: x - 1, y: roofY, z },
            { x, y: roofY, z: z + 1 }, { x, y: roofY, z: z - 1 },
          ].find((candidate) => roofPlaced.has(`${candidate.x},${candidate.y},${candidate.z}`));
          if (!neighbour) continue;
          const face: Vector3 = {
            x: Math.sign(x - neighbour.x),
            y: 0,
            z: Math.sign(z - neighbour.z),
          };
          await placeCell(ctx, neighbour, face, "birch_planks", `${x},${roofY},${z}`, placed, skipped);
          roofPlaced.add(`${x},${roofY},${z}`);
        }
      }
    }
  }

  if (input.phase === "door") {
    // Ensure birch planks exist only for the roof story; the door itself is
    // oak. Place the crafting table inside, craft the door, then place it.
    await requireSuccessful(await ctx.equip("crafting_table"), "equip crafting_table");
    const tableReference: Vector3 = { x: CENTER.x - 1, y: 62, z: CENTER.z };
    await placeCell(ctx, tableReference, TOP_FACE, "crafting_table", "table", placed, skipped);
    await requireSuccessful(await ctx.craft("oak_door", 1), "craft oak_door");
    await requireSuccessful(await ctx.equip("oak_door"), "equip oak_door");
    const doorReference: Vector3 = { x: DOOR.x, y: 62, z: DOOR.z };
    await placeCell(ctx, doorReference, TOP_FACE, "oak_door", "door", placed, skipped);
  }

  return {
    phase: input.phase,
    placed: placed.length,
    placedCells: placed,
    skippedCells: skipped,
  };
};

/** Place the held block; treat an already-correct cell as success. */
async function placeCell(
  ctx: MinecraftContext,
  reference: Vector3,
  face: Vector3,
  expectedName: string,
  label: string,
  placed: string[],
  skipped: string[]
): Promise<void> {
  let response = await ctx.placeBlock(reference, face);
  if (response.ok === true) {
    placed.push(label);
    return;
  }
  if (response.reason === "place_target_occupied") {
    // Idempotent continuation: a previous run already built this cell.
    skipped.push(label);
    return;
  }
  if (response.reason === "no_held_item") {
    // The equipped stack ran dry; re-equip from the remaining stacks.
    await requireSuccessful(await ctx.equip(expectedName), `re-equip ${expectedName}`);
    const again = await ctx.placeBlock(reference, face);
    if (again.ok === true) {
      placed.push(label);
      return;
    }
    if (again.reason === "place_target_occupied") {
      skipped.push(label);
      return;
    }
    response = again;
  }
  if (response.reason === "place_unverified") {
    // The server refuses placements that intersect the player's bounding
    // box — and walk_to_exact's tolerance can leave the body grazing a wall
    // cell's edge by fractions of a block. Retreat: stance pushed 0.6 blocks
    // away from the failing cell, then retry.
    const cell = {
      x: reference.x + face.x,
      y: reference.y + face.y,
      z: reference.z + face.z
    };
    const stance = { x: CENTER.x + 0.5, y: 63, z: CENTER.z + 0.5 };
    const retreat = {
      x: stance.x + Math.sign(stance.x - (cell.x + 0.5)) * 0.6,
      y: 63,
      z: stance.z + Math.sign(stance.z - (cell.z + 0.5)) * 0.6
    };
    await ctx.call("walk_to_exact", { target: retreat }, 60);
    const retry = await ctx.placeBlock(reference, face);
    if (retry.ok === true) {
      placed.push(label);
      return;
    }
    if (retry.reason === "place_target_occupied") {
      skipped.push(label);
      return;
    }
    requireSuccessful(retry, `place ${expectedName} at ${label} (after retreating to ${JSON.stringify(retreat)})`);
  }
  requireSuccessful(response, `place ${expectedName} at ${label}`);
}

export default run;
