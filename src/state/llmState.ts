import type { Bot } from "mineflayer";
import { Vec3 } from "vec3";
import { compassFacing } from "./botState.js";
import { isVisibleFromHead } from "../perception/visibility.js";
import type { MinecraftMessage } from "./chatInbox.js";
import { fetchBabymodeStatus, type BabymodeStatus } from "./babymode.js";

/**
 * Action evidence needs a complete world/agent snapshot; build one LLM-parseable state object from the live bot.
 *
 * @remarks
 * archetype: service-provider
 * owns: the action-log state.json shape — player transform, world info, inventory, nearby blocks/entities.
 * not own: file persistence, screenshots, command execution, or the minimal `/api/state` shape.
 * fails when: never fatally; sections that cannot be read from the live bot degrade to null/empty.
 * domain: consumed by agents to verify command effects (compare before/after snapshots).
 * invariant: angles are degrees (yaw [0,360) counterclockwise from north, pitch positive up); positions are absolute world coordinates.
 * invariant: every non-integer coordinate, distance, and angle is rounded to one decimal — sub-decimeter precision
 * carries no decision value for an agent and only inflates the state it has to read.
 */
export interface LLMStateSnapshot {
  capturedAt: string;
  chat: { messages: MinecraftMessage[] };
  /** Agentic Babymode mod state (sleepiness/nutrition), or null when the mod is not installed. */
  babymode: BabymodeStatus | null;
  player: {
    username: string | null;
    position: { x: number; y: number; z: number } | null;
    blockPosition: { x: number; y: number; z: number } | null;
    yawDegrees: number | null;
    pitchDegrees: number | null;
    facing: string | null;
    velocity: { x: number; y: number; z: number } | null;
    onGround: boolean | null;
    health: number | null;
    food: number | null;
    foodSaturation: number | null;
    oxygenLevel: number | null;
    experienceLevel: number | null;
    gameMode: string | null;
  };
  world: {
    dimension: string | null;
    minecraftVersion: string | null;
    difficulty: string | null;
    biome: string | null;
    timeOfDay: number | null;
    isDay: boolean | null;
    isRaining: boolean | null;
    isThundering: boolean | null;
  };
  inventory: {
    selectedHotbarSlot: number | null;
    heldItem: { name: string; count: number } | null;
    hotbar: Array<{ slot: number; name: string; count: number } | null>;
    items: Array<{ name: string; count: number }>;
    armor: { head: string | null; torso: string | null; legs: string | null; feet: string | null };
    emptySlots: number | null;
  };
  surroundings: {
    blockAtFeet: string | null;
    blockBelowFeet: string | null;
    blockAtHead: string | null;
    nearbyBlockRadius: number;
    /** Head-ray-visible non-air blocks, independent of current rotation, aggregated by name and nearest distance. */
    nearbyBlocks: Array<{
      name: string;
      count: number;
      nearest: { x: number; y: number; z: number };
      distance: number;
      canHarvestWithHeldItem: boolean | null;
      /** Tools that yield drops, cheapest to obtain first, so the first entry is the one worth crafting. */
      harvestToolOptions: string[];
    }>;
    localAirspace: {
      scanRadius: number;
      clearanceBlocksAboveHead: number;
      horizontalOpenings: Array<{
        direction: string;
        delta: { x: number; z: number };
        openBlocks: number;
        firstBlockedBy: {
          feet: "open" | "solid" | "unloaded";
          head: "open" | "solid" | "unloaded";
        } | null;
      }>;
      navigationSummary: {
        reachableStandableCells: number;
        elevationRange: {
          minimumDelta: number;
          maximumDelta: number;
        };
        highestWaypoint: NavigationWaypoint;
        maxClearanceWaypoint: NavigationWaypoint;
        furthestWaypoint: NavigationWaypoint;
        frontierWaypoints: NavigationWaypoint[];
      };
    };
    /** Entities within 16 blocks, sorted by distance. */
    nearbyEntities: Array<{ id: number; name: string; kind: string; position: { x: number; y: number; z: number }; distance: number }>;
    /** Nearby water/lava the player would hear (danger source + direction). */
    hazards: Array<{ type: "water" | "lava"; direction: string | null; distance: number; nearest: { x: number; y: number; z: number } | null }>;
  };
}

const AIR_BLOCKS = new Set(["air", "cave_air", "void_air"]);
const MAX_NEARBY_BLOCK_KINDS = 48;
const MAX_NEARBY_ENTITIES = 20;
const NEARBY_ENTITY_RADIUS = 16;
/** Hazard scan radius: how far the bot can plausibly hear lava or water. */
const HAZARD_SCAN_RADIUS = 12;
/** Decimals kept for every coordinate, distance, and angle in this snapshot. */
const DECIMALS = 1;
/** Harvest tool materials ordered by survival acquisition cost, cheapest first. */
const HARVEST_TOOL_MATERIALS = ["wooden", "stone", "iron", "golden", "diamond", "netherite"];

interface NavigationWaypoint {
  position: { x: number; y: number; z: number };
  distance: number;
  clearanceBlocksAboveHead: number;
  openHorizontalNeighbors: number;
}

export async function buildLLMState(bot: Bot, options: { nearbyBlockRadius?: number; messages?: MinecraftMessage[] } = {}): Promise<LLMStateSnapshot> {
  const radius = options.nearbyBlockRadius ?? 8;
  const entity = bot.entity;
  const position = entity?.position ?? null;
  const babymode = await fetchBabymodeStatus(bot).catch(() => null);

  return {
    capturedAt: new Date().toISOString(),
    chat: { messages: options.messages ?? [] },
    babymode,
    player: buildPlayer(bot, babymode),
    world: buildWorld(bot),
    inventory: buildInventory(bot),
    surroundings: {
      blockAtFeet: position ? blockNameAt(bot, position.floored()) : null,
      blockBelowFeet: position ? blockNameAt(bot, position.floored().offset(0, -1, 0)) : null,
      blockAtHead: position ? blockNameAt(bot, position.floored().offset(0, 1, 0)) : null,
      nearbyBlockRadius: radius,
      nearbyBlocks: position ? scanNearbyBlocks(bot, position, radius) : [],
      hazards: position ? scanHazards(bot, position) : [],
      localAirspace: position
        ? scanLocalAirspace(bot, position, radius)
        : {
            scanRadius: radius,
            clearanceBlocksAboveHead: 0,
            horizontalOpenings: [],
            navigationSummary: {
              reachableStandableCells: 0,
              elevationRange: {
                minimumDelta: 0,
                maximumDelta: 0
              },
              highestWaypoint: {
                position: { x: 0, y: 0, z: 0 },
                distance: 0,
                clearanceBlocksAboveHead: 0,
                openHorizontalNeighbors: 0
              },
              maxClearanceWaypoint: {
                position: { x: 0, y: 0, z: 0 },
                distance: 0,
                clearanceBlocksAboveHead: 0,
                openHorizontalNeighbors: 0
              },
              furthestWaypoint: {
                position: { x: 0, y: 0, z: 0 },
                distance: 0,
                clearanceBlocksAboveHead: 0,
                openHorizontalNeighbors: 0
              },
              frontierWaypoints: []
            }
          },
      nearbyEntities: position ? scanNearbyEntities(bot, position) : []
    }
  };
}

function scanLocalAirspace(
  bot: Bot,
  center: Vec3,
  radius: number
): LLMStateSnapshot["surroundings"]["localAirspace"] {
  const origin = center.floored();
  const clearanceAt = (position: Vec3): number => {
    let clearance = 0;
    for (let step = 1; step <= radius; step++) {
      const name = blockNameAt(
        bot,
        position.offset(0, step + 1, 0)
      );
      if (name === null || !AIR_BLOCKS.has(name)) {
        break;
      }
      clearance += 1;
    }
    return clearance;
  };
  const clearanceBlocksAboveHead = clearanceAt(origin);

  const occupancy = (
    name: string | null
  ): "open" | "solid" | "unloaded" => (
    name === null
      ? "unloaded"
      : AIR_BLOCKS.has(name)
        ? "open"
        : "solid"
  );
  const isStandable = (position: Vec3): boolean => {
    const feet = blockNameAt(bot, position);
    const head = blockNameAt(bot, position.offset(0, 1, 0));
    const support = blockNameAt(bot, position.offset(0, -1, 0));
    return (
      feet !== null
      && head !== null
      && support !== null
      && AIR_BLOCKS.has(feet)
      && AIR_BLOCKS.has(head)
      && !AIR_BLOCKS.has(support)
    );
  };
  const cardinalDeltas = [
    [0, -1],
    [1, 0],
    [0, 1],
    [-1, 0]
  ] as const;
  const openHorizontalNeighbors = (position: Vec3): number => (
    cardinalDeltas.filter(([dx, dz]) => (
      [1, 0, -1].some((dy) => (
        isStandable(position.offset(dx, dy, dz))
      ))
    )).length
  );
  const waypoint = (position: Vec3): NavigationWaypoint => ({
    position: {
      x: position.x,
      y: position.y,
      z: position.z
    },
    distance: round(center.distanceTo(position), DECIMALS),
    clearanceBlocksAboveHead: clearanceAt(position),
    openHorizontalNeighbors: openHorizontalNeighbors(position)
  });

  const reachable: Vec3[] = [origin];
  const queue: Vec3[] = [origin];
  const visited = new Set([`${origin.x},${origin.y},${origin.z}`]);
  while (queue.length > 0) {
    const current = queue.shift();
    if (current === undefined) break;
    for (const [dx, dz] of cardinalDeltas) {
      for (const dy of [1, 0, -1]) {
        const candidate = current.offset(dx, dy, dz);
        if (
          Math.abs(candidate.x - origin.x) > radius
          || Math.abs(candidate.y - origin.y) > radius
          || Math.abs(candidate.z - origin.z) > radius
        ) {
          continue;
        }
        const key = `${candidate.x},${candidate.y},${candidate.z}`;
        if (visited.has(key) || !isStandable(candidate)) {
          continue;
        }
        visited.add(key);
        reachable.push(candidate);
        queue.push(candidate);
        break;
      }
    }
  }
  const waypoints = reachable.map(waypoint);
  const choose = (
    compare: (left: NavigationWaypoint, right: NavigationWaypoint) => number
  ): NavigationWaypoint => [...waypoints].sort(compare)[0] ?? waypoint(origin);
  const highestWaypoint = choose((left, right) => (
    right.position.y - left.position.y
    || right.clearanceBlocksAboveHead - left.clearanceBlocksAboveHead
    || right.distance - left.distance
  ));
  const maxClearanceWaypoint = choose((left, right) => (
    right.clearanceBlocksAboveHead - left.clearanceBlocksAboveHead
    || right.openHorizontalNeighbors - left.openHorizontalNeighbors
    || right.position.y - left.position.y
    || right.distance - left.distance
  ));
  const furthestWaypoint = choose((left, right) => (
    right.distance - left.distance
    || right.position.y - left.position.y
  ));
  const frontierWaypoints = reachable
    .filter((position) => (
      Math.abs(position.x - origin.x) === radius
      || Math.abs(position.y - origin.y) === radius
      || Math.abs(position.z - origin.z) === radius
    ))
    .map(waypoint)
    .sort((left, right) => (
      right.openHorizontalNeighbors - left.openHorizontalNeighbors
      || right.clearanceBlocksAboveHead - left.clearanceBlocksAboveHead
      || right.position.y - left.position.y
      || right.distance - left.distance
      || left.position.x - right.position.x
      || left.position.z - right.position.z
    ))
    .slice(0, 8);

  const directions = [
    ["north", 0, -1],
    ["north_east", 1, -1],
    ["east", 1, 0],
    ["south_east", 1, 1],
    ["south", 0, 1],
    ["south_west", -1, 1],
    ["west", -1, 0],
    ["north_west", -1, -1]
  ] as const;
  const horizontalOpenings = directions.map(([direction, dx, dz]) => {
    let openBlocks = 0;
    let firstBlockedBy: {
      feet: "open" | "solid" | "unloaded";
      head: "open" | "solid" | "unloaded";
    } | null = null;
    for (let step = 1; step <= radius; step++) {
      const feet = blockNameAt(
        bot,
        origin.offset(dx * step, 0, dz * step)
      );
      const head = blockNameAt(
        bot,
        origin.offset(dx * step, 1, dz * step)
      );
      if (
        feet === null
        || head === null
        || !AIR_BLOCKS.has(feet)
        || !AIR_BLOCKS.has(head)
      ) {
        firstBlockedBy = {
          feet: occupancy(feet),
          head: occupancy(head)
        };
        break;
      }
      openBlocks += 1;
    }
    return {
      direction,
      delta: { x: dx, z: dz },
      openBlocks,
      firstBlockedBy
    };
  });
  return {
    scanRadius: radius,
    clearanceBlocksAboveHead,
    horizontalOpenings,
    navigationSummary: {
      reachableStandableCells: reachable.length,
      elevationRange: {
        minimumDelta: Math.min(
          ...reachable.map((position) => position.y - origin.y)
        ),
        maximumDelta: Math.max(
          ...reachable.map((position) => position.y - origin.y)
        )
      },
      highestWaypoint,
      maxClearanceWaypoint,
      furthestWaypoint,
      frontierWaypoints
    }
  };
}

function buildPlayer(bot: Bot, babymode: BabymodeStatus | null): LLMStateSnapshot["player"] {
  const entity = bot.entity;
  const yawDegrees = typeof entity?.yaw === "number" ? normalizeYaw(entity.yaw * 180 / Math.PI) : null;
  const raw = bot as Bot & { foodSaturation?: number; oxygenLevel?: number; experience?: { level?: number }; game?: { gameMode?: string } };
  // The Babymode mod reports the real air gauge (full = 300). Mineflayer's bot.oxygenLevel is
  // derived from raw entity metadata that goes stale/erratic on dry land (and is distorted by the
  // low-drowning mod), so report the true value: raw air / 15.
  const oxygenLevel =
    babymode?.air != null
      ? Math.round(babymode.air / 15)
      : numberOrNull(raw.oxygenLevel);
  return {
    username: bot.username ?? null,
    position: entity?.position ? roundVec(entity.position, DECIMALS) : null,
    blockPosition: entity?.position ? roundVec(entity.position.floored(), 0) : null,
    yawDegrees,
    pitchDegrees: typeof entity?.pitch === "number" ? round(entity.pitch * 180 / Math.PI, DECIMALS) : null,
    facing: yawDegrees !== null ? compassFacing(yawDegrees) : null,
    velocity: entity?.velocity ? roundVec(entity.velocity, DECIMALS) : null,
    onGround: typeof entity?.onGround === "boolean" ? entity.onGround : null,
    health: numberOrNull(bot.health),
    food: numberOrNull(bot.food),
    foodSaturation: numberOrNull(raw.foodSaturation),
    oxygenLevel,
    experienceLevel: numberOrNull(raw.experience?.level),
    gameMode: typeof raw.game?.gameMode === "string" ? raw.game.gameMode : null
  };
}

function buildWorld(bot: Bot): LLMStateSnapshot["world"] {
  const raw = bot as Bot & {
    game?: { dimension?: string; difficulty?: string };
    time?: { timeOfDay?: number };
    isRaining?: boolean;
    thunderState?: number;
  };
  const timeOfDay = numberOrNull(raw.time?.timeOfDay);
  return {
    dimension: typeof raw.game?.dimension === "string" ? raw.game.dimension : null,
    minecraftVersion: bot.version ?? null,
    difficulty:
      typeof raw.game?.difficulty === "string" ? raw.game.difficulty : null,
    biome: biomeAtPlayer(bot),
    timeOfDay,
    // Minecraft daytime runs 0 (sunrise) to ~12500 (sunset) out of 24000 ticks.
    isDay: timeOfDay !== null ? timeOfDay < 12500 : null,
    isRaining: typeof raw.isRaining === "boolean" ? raw.isRaining : null,
    isThundering: typeof raw.thunderState === "number" ? raw.thunderState > 0 : null
  };
}

function buildInventory(bot: Bot): LLMStateSnapshot["inventory"] {
  const slots = bot.inventory?.slots ?? [];
  const hotbar: Array<{ slot: number; name: string; count: number } | null> = [];
  const aggregated = new Map<string, number>();
  let emptySlots = 0;

  // Player inventory layout: 5-8 armor, 9-35 main, 36-44 hotbar.
  for (let i = 36; i <= 44; i++) {
    const item = slots[i];
    hotbar.push(item && item.name ? { slot: i - 36, name: item.name, count: item.count } : null);
  }
  for (let i = 9; i <= 44; i++) {
    const item = slots[i];
    if (item && item.name) {
      aggregated.set(item.name, (aggregated.get(item.name) ?? 0) + item.count);
    } else {
      emptySlots += 1;
    }
  }

  const armorName = (slot: number): string | null => slots[slot]?.name ?? null;
  const heldItem = bot.heldItem && bot.heldItem.name ? { name: bot.heldItem.name, count: bot.heldItem.count } : null;

  return {
    selectedHotbarSlot: numberOrNull(bot.quickBarSlot),
    heldItem,
    hotbar,
    items: [...aggregated.entries()]
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count),
    armor: { head: armorName(5), torso: armorName(6), legs: armorName(7), feet: armorName(8) },
    emptySlots
  };
}

function scanNearbyBlocks(
  bot: Bot,
  center: Vec3,
  radius: number
): LLMStateSnapshot["surroundings"]["nearbyBlocks"] {
  const origin = center.floored();
  const found = new Map<string, {
    name: string;
    count: number;
    nearest: Vec3;
    distance: number;
    canHarvestWithHeldItem: boolean | null;
    harvestToolOptions: string[];
  }>();

  try {
    for (let dx = -radius; dx <= radius; dx++) {
      for (let dy = -radius; dy <= radius; dy++) {
        for (let dz = -radius; dz <= radius; dz++) {
          const pos = origin.offset(dx, dy, dz);
          const block = bot.blockAt(pos, false);
          if (!block || AIR_BLOCKS.has(block.name) || !isVisibleFromHead(bot, block)) {
            continue;
          }
          const distance = center.distanceTo(pos.offset(0.5, 0.5, 0.5));
          const entry = found.get(block.name);
          if (!entry) {
            const canHarvestWithHeldItem = typeof block.canHarvest === "function"
              ? Boolean(block.canHarvest(bot.heldItem?.type ?? null))
              : null;
            found.set(block.name, {
              name: block.name,
              count: 1,
              nearest: pos,
              distance,
              canHarvestWithHeldItem,
              harvestToolOptions: harvestToolOptions(bot, block)
            });
          } else {
            entry.count += 1;
            if (distance < entry.distance) {
              entry.nearest = pos;
              entry.distance = distance;
            }
          }
        }
      }
    }
  } catch {
    // Unloaded chunks mid-scan: return what was collected so far
  }

  return [...found.values()]
    .sort((a, b) => a.distance - b.distance)
    .slice(0, MAX_NEARBY_BLOCK_KINDS)
    .map((entry) => ({
      name: entry.name,
      count: entry.count,
      nearest: { x: entry.nearest.x, y: entry.nearest.y, z: entry.nearest.z },
      distance: round(entry.distance, DECIMALS),
      canHarvestWithHeldItem: entry.canHarvestWithHeldItem,
      harvestToolOptions: entry.harvestToolOptions
    }));
}

function harvestToolOptions(
  bot: Bot,
  block: unknown
): string[] {
  const harvestTools = (
    block as { harvestTools?: Record<string, boolean> }
  ).harvestTools;
  if (!harvestTools) {
    return [];
  }
  const registry = (
    bot as Bot & {
      registry?: {
        items?: Record<number, { name?: string }>;
      };
    }
  ).registry;
  return Object.entries(harvestTools)
    .filter(([, allowed]) => allowed)
    .map(([itemId]) => registry?.items?.[Number(itemId)]?.name)
    .filter((name): name is string => typeof name === "string")
    .sort((left, right) => (
      harvestToolCost(left) - harvestToolCost(right)
      || left.localeCompare(right)
    ));
}

/** Rank a harvest tool by how expensive its material is to obtain in survival. */
function harvestToolCost(itemName: string): number {
  const material = HARVEST_TOOL_MATERIALS.findIndex(
    (candidate) => itemName.startsWith(`${candidate}_`)
  );
  return material === -1 ? HARVEST_TOOL_MATERIALS.length : material;
}

function scanNearbyEntities(bot: Bot, center: Vec3): LLMStateSnapshot["surroundings"]["nearbyEntities"] {
  const results: LLMStateSnapshot["surroundings"]["nearbyEntities"] = [];
  try {
    for (const entity of Object.values(bot.entities ?? {})) {
      if (!entity || entity === bot.entity || !entity.position) {
        continue;
      }
      const distance = center.distanceTo(entity.position);
      if (distance > NEARBY_ENTITY_RADIUS) {
        continue;
      }
      const raw = entity as typeof entity & { id?: number; name?: string; username?: string; displayName?: string; type?: string };
      if (!Number.isInteger(raw.id)) {
        continue;
      }
      results.push({
        id: raw.id!,
        name: raw.username ?? raw.name ?? raw.displayName ?? "unknown",
        kind: raw.type ?? "unknown",
        position: roundVec(entity.position, DECIMALS),
        distance: round(distance, DECIMALS)
      });
    }
  } catch {
    // Entity map mutation mid-scan: return what was collected so far
  }
  return results.sort((a, b) => a.distance - b.distance).slice(0, MAX_NEARBY_ENTITIES);
}

function biomeAtPlayer(bot: Bot): string | null {
  try {
    const position = bot.entity?.position;
    if (!position) {
      return null;
    }
    const world = bot.world as unknown as { getBiome?: (pos: Vec3) => number };
    const registry = (bot as Bot & { registry?: { biomes?: Record<number, { name?: string }> } }).registry;
    if (typeof world.getBiome !== "function" || !registry?.biomes) {
      return null;
    }
    const biomeId = world.getBiome(position.floored());
    return registry.biomes[biomeId]?.name ?? null;
  } catch {
    return null;
  }
}

function scanHazards(bot: Bot, center: Vec3): LLMStateSnapshot["surroundings"]["hazards"] {
  const closest = new Map<string, { type: "water" | "lava"; nearest: Vec3; distance: number }>();
  const origin = center.floored();
  try {
    for (let dx = -HAZARD_SCAN_RADIUS; dx <= HAZARD_SCAN_RADIUS; dx++) {
      for (let dy = -HAZARD_SCAN_RADIUS; dy <= HAZARD_SCAN_RADIUS; dy++) {
        for (let dz = -HAZARD_SCAN_RADIUS; dz <= HAZARD_SCAN_RADIUS; dz++) {
          const pos = origin.offset(dx, dy, dz);
          if (pos.distanceTo(center) > HAZARD_SCAN_RADIUS) {
            continue;
          }
          const block = blockAtUnloaded(bot, pos);
          if (!block) {
            continue;
          }
          const type = hazardType(block.name);
          if (!type) {
            continue;
          }
          const distance = center.distanceTo(pos.offset(0.5, 0.5, 0.5));
          const entry = closest.get(type);
          if (!entry || distance < entry.distance) {
            closest.set(type, { type, nearest: pos, distance });
          }
        }
      }
    }
  } catch {
    // Unloaded chunks mid-scan: report what was found so far
  }
  return [...closest.values()]
    .sort((a, b) => a.distance - b.distance)
    .map((entry) => ({
      type: entry.type,
      direction: directionTo(center, entry.nearest),
      distance: round(entry.distance, DECIMALS),
      nearest: { x: entry.nearest.x, y: entry.nearest.y, z: entry.nearest.z }
    }));
}

function blockAtUnloaded(bot: Bot, pos: Vec3): { name: string } | null {
  try {
    return bot.blockAt(pos, false);
  } catch {
    return null;
  }
}

function hazardType(name: string): "water" | "lava" | null {
  if (name === "lava" || name === "flowing_lava") {
    return "lava";
  }
  if (name === "water" || name === "flowing_water") {
    return "water";
  }
  return null;
}

function directionTo(from: Vec3, to: Vec3): string | null {
  // Convert a world offset into the same mineflayer yaw frame compassFacing reads.
  const dx = to.x - from.x;
  const dz = to.z - from.z;
  const hypotenuse = Math.hypot(dx, dz);
  if (hypotenuse < 1e-6) {
    return null;
  }
  const yawDegrees = (Math.atan2(-dx, -dz) * 180 / Math.PI + 360) % 360;
  return compassFacing(yawDegrees);
}

function blockNameAt(bot: Bot, pos: Vec3): string | null {
  try {
    return bot.blockAt(pos, false)?.name ?? null;
  } catch {
    return null;
  }
}

function roundVec(vec: { x: number; y: number; z: number }, digits: number): { x: number; y: number; z: number } {
  return { x: round(vec.x, digits), y: round(vec.y, digits), z: round(vec.z, digits) };
}

function round(value: number, digits: number): number {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function normalizeYaw(degrees: number): number {
  // The trailing modulo keeps values that round up to 360.0 at 0.
  return round(((degrees % 360) + 360) % 360, DECIMALS) % 360;
}

function numberOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
