import { type MinecraftContext, type Vector3, type SkillEntrypoint } from "../lib/minecraft";

/**
 * Long-distance patrol to find a village. Walks in a set heading, hopping to
 * successive waypoints and checking `nearbyEntities` (and a few village blocks)
 * at each stop, and returns once a villager is sighted OR after a time budget so
 * the skill always finishes within the caller's request window and reports where
 * it got to.
 *
 * input:
 *   heading : "north"|"south"|"east"|"west" (default east)
 *   budgetMs: wall-clock run time before reporting (default 185000)
 *   hop     : blocks per waypoint (default 30)
 *   maxHops : hard cap (default 60)
 */
interface Input {
  heading?: string;
  budgetMs?: number;
  hop?: number;
  maxHops?: number;
}

const DELTA: Record<string, { x: number; z: number }> = {
  north: { x: 0, z: -1 },
  south: { x: 0, z: 1 },
  east: { x: 1, z: 0 },
  west: { x: -1, z: 0 },
};

const VILLAGE_BLOCKS = new Set([
  "hay_bale",
  "dirt_path",
  "wheat",
  "carrots",
  "potatoes",
  "barrel",
  "composter",
  "bee_nest",
  "black_bed",
  "blue_bed",
  "red_bed",
  "cobblestone",
  "oak_log",
  "spruce_log",
]);

const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const input = (rawInput ?? {}) as Input;
  const d = DELTA[input.heading ?? "east"] ?? DELTA.east;
  const budgetMs = typeof input.budgetMs === "number" ? Math.min(input.budgetMs, 190000) : 185000;
  const hop = typeof input.hop === "number" ? Math.max(12, Math.min(input.hop, 80)) : 30;
  const maxHops = typeof input.maxHops === "number" ? Math.max(1, input.maxHops) : 60;

  const obs0 = await context.observe();
  const start = obs0.player.blockPosition as Vector3;
  const visited: string[] = [`${start.x},${start.y},${start.z}`];
  const deadline = Date.now() + budgetMs;
  let waypoint = { x: start.x, y: start.y, z: start.z };

  let pos = start;
  for (let i = 0; i < maxHops && Date.now() < deadline; i++) {
    const obs = await context.observe();
    pos = obs.player.blockPosition as Vector3;

    // Anyone home? A villager in render distance means a village.
    const entities = (obs.surroundings?.nearbyEntities ?? []) as Array<{ name: string; position?: Vector3; distance?: number }>;
    for (const e of entities) {
      if (e.name === "villager") {
        return { ok: true, found: "villager", entityPosition: e.position, distance: e.distance, pos, heading: input.heading ?? "east", hops: i, visited };
      }
    }
    // Village structure blocks close by also count.
    const blocks = (obs.surroundings?.nearbyBlocks ?? []) as Array<{ name: string; distance?: number }>;
    for (const b of blocks) {
      if (VILLAGE_BLOCKS.has(b.name) && (b.distance ?? 99) <= 20) {
        return { ok: true, found: `block:${b.name}`, distance: b.distance, pos, heading: input.heading ?? "east", hops: i, visited };
      }
    }

    // Hop toward the next waypoint along the heading.
    waypoint = { x: waypoint.x + d.x * hop, y: waypoint.y, z: waypoint.z + d.z * hop };
    const w = await context.walkTo(waypoint, 12, 45);
    if (w.ok === true) {
      const after = await context.observe();
      pos = after.player.blockPosition as Vector3;
      visited.push(`${pos.x},${pos.y},${pos.z}`);
      waypoint = { x: pos.x, y: pos.y, z: pos.z };
    } else {
      visited.push(`stall@${pos.x},${pos.z}`);
    }
  }

  const end = await context.observe();
  return { ok: true, found: null, pos: end.player.blockPosition as Vector3, heading: input.heading ?? "east", hops: visited.length, visited, timedOutInStep: true };
};

export default run;
