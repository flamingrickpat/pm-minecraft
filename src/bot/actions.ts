import type { Bot } from "mineflayer";
import pathfinderPackage from "mineflayer-pathfinder";
import { Vec3 } from "vec3";
import type { CommandResult } from "../commands/commandQueue.js";
import type { AttackEntityInput, ChestInput, FindBlockInput, JumpPlaceBlockInput, MineBlockInput, PlaceBlockInput, UseBlockInput, Vector3, WalkToExactInput, WalkToSurfaceInput, WalkToVisibleInput } from "../commands/types.js";
import { describeMatches, globResolve, globSuggest, hasWildcard } from "./nameMatching.js";
import { isVisibleFromHead } from "../perception/visibility.js";

const { goals, Movements, pathfinder } = pathfinderPackage;
type PathfinderGoal = InstanceType<typeof goals.Goal>;
type PathfinderMove = Vector3 & {
  toBreak?: unknown[];
  toPlace?: unknown[];
};
export type PathfinderUpdate = {
  status: string;
  path: PathfinderMove[];
};

export interface NavigationReport {
  pathStatus: string;
  pathNodes: number;
  ascents: number;
  drops: number;
  stalled: boolean;
  diagnosis: string;
  /** Closest standable position the search actually reached (failures only). */
  closestApproach?: Vector3;
  /** 3D distance from closestApproach to the requested target (failures only). */
  remainingDistance?: number;
}

class NavigationFailure extends Error {
  constructor(message: string, readonly report: NavigationReport) {
    super(message);
    this.name = "NavigationFailure";
  }
}

// A path is considered "movement" for the liveness backstop when the bot
// travels at least this far between polls.
const MIN_PROGRESS_DISTANCE = 0.2;
// If the bot made forward progress but then stops moving for this long while
// walking a path, the walk is stuck (path invalidated by gravel/water/etc).
// This is the "should never happen" safety net, not the normal completion path
// (the pathfinder's own goal_reached/noPath events handle that).
const NO_PROGRESS_TIMEOUT_MS = 3_000;
// Number of blocks in one Minecraft chunk.
const CHUNK = 16;

/**
 * Physical commands need real Mineflayer effects; execute explicit user actions at the bot boundary.
 *
 * @remarks
 * archetype: service-provider
 * owns: look, pathfinder walk, dig, place, block activation, entity attack, and block inspection calls against one live bot.
 * not own: HTTP validation, command serialization, item/tool choice, recipe choice, or autonomous recovery.
 * fails when: target chunks are unloaded, pathfinder cannot reach, Mineflayer rejects the action, or targets are out of range.
 * domain: every method performs one user-requested Minecraft action or its bounded internal walk/look sequence.
 * invariant: no method selects tools/items or changes goals beyond the explicit command it is executing.
 */
export interface PhysicalCommandActions {
  lookAt(target: Vector3): Promise<CommandResult>;
  look(input: { yaw: number; pitch: number }): Promise<CommandResult>;
  getOrientation(): { yaw: number; pitch: number };
  syncOrientation(): void;
  walkToVisible(input: WalkToVisibleInput, signal?: AbortSignal): Promise<CommandResult>;
  walkToSurface(input: WalkToSurfaceInput, signal?: AbortSignal): Promise<CommandResult>;
  walkToExact(input: WalkToExactInput, signal?: AbortSignal): Promise<CommandResult>;
  findBlock(input: FindBlockInput): Promise<CommandResult>;
  findInteractables(input: { maxDistance?: number }): Promise<CommandResult>;
  scanHorizon(input: { maxDistance?: number }): Promise<CommandResult>;
  mineBlock(input: MineBlockInput): Promise<CommandResult>;
  placeBlock(input: PlaceBlockInput): Promise<CommandResult>;
  jumpPlaceBlock(input: JumpPlaceBlockInput): Promise<CommandResult>;
  pillarUp(): Promise<CommandResult>;
  useBlock(input: UseBlockInput): Promise<CommandResult>;
  useHeldItem(): Promise<CommandResult>;
  chestDeposit(input: ChestInput): Promise<CommandResult>;
  chestWithdraw(input: ChestInput): Promise<CommandResult>;
  attackEntity(input: AttackEntityInput): Promise<CommandResult>;
  inspectBlock(block: Vector3): Promise<CommandResult>;
  /** Raycast from the player's head along the current look direction and return what is being looked at. */
  raycast(maxDistance?: number): Promise<CommandResult>;
}

type ActionBot = Bot & {
  canDigBlock?(block: BlockLike): boolean;
  dig(block: BlockLike, forceLook?: boolean | "ignore", digFace?: Vec3 | "raycast" | "auto"): Promise<void>;
  placeBlock(referenceBlock: BlockLike, faceVector: Vec3): Promise<void>;
  _placeBlockWithOptions?(
    referenceBlock: BlockLike,
    faceVector: Vec3,
    options: {
      forceLook: "ignore";
      swingArm: "right";
    }
  ): Promise<void>;
  activateBlock(block: BlockLike, direction?: Vec3, cursorPos?: Vec3): Promise<void>;
};

type EntityLike = NonNullable<Bot["entity"]> & {
  id: number;
  name?: string;
  username?: string;
  displayName?: string;
  type?: string;
  health?: number;
};

interface BlockLike {
  name: string;
  type: number;
  position: Vec3;
  diggable?: boolean;
  boundingBox?: string;
  displayName?: string;
  canHarvest?(heldItemType: number | null): boolean;
}

export function createPhysicalCommandActions(
  bot: Bot,
  options: {
    mineVisibilityIgnoreDistance: number;
    /** Absolute cap (in chunks) on walk search regions; a requested chunk_limit above this is rejected. */
    maxChunkLimit: number;
    /** A* compute budget (ms) for walk_to_exact searches — the longest of the three walks. */
    exactSearchBudgetMs?: number;
    /** Perception radius in blocks (render distance x sqrt(2) chunk widths, capped 256). Derived by the body; never a model-facing parameter. */
    viewRadiusBlocks?: number;
    /** Optional structured logger for walk-family commands (gotoNear, hops, stalls, door retries). */
    walkLog?: (message: string) => void;
  } = {
    mineVisibilityIgnoreDistance: 3.0,
    maxChunkLimit: 8
  }
): PhysicalCommandActions {
  const wlog = options.walkLog ?? ((_message: string) => undefined);
  // Track intended yaw/pitch so getOrientation() is not affected by server
  // position corrections that overwrite bot.entity.yaw/pitch.
  //
  // Convention everywhere in this module: DEGREES in mineflayer's frame —
  // yaw normalized to [0, 360) increasing counterclockwise (turning left),
  // pitch positive looking up. bot.entity stores radians in the same frame.
  //
  // Initialized to 0 because bot.entity is undefined at creation time
  // (before the "spawn" event). getOrientation() syncs from bot.entity
  // lazily once the entity is available.
  let _trackedYaw = 0;
  let _trackedPitch = 0;
  let _orientationSynced = false;

  const syncTrackedFromEntity = (): void => {
    if (bot.entity) {
      _trackedYaw = normalizeYawDeg(radToDeg(bot.entity.yaw));
      _trackedPitch = clampPitchDeg(radToDeg(bot.entity.pitch));
      _orientationSynced = true;
    }
  };

  // Same yaw/pitch math as mineflayer's lookAt (eye-relative, yaw = atan2(-dx, -dz)).
  const syncTrackedToTarget = (target: Vec3): void => {
    const eyeHeight = (bot.entity as typeof bot.entity & { eyeHeight?: number }).eyeHeight ?? 1.62;
    const dx = target.x - bot.entity.position.x;
    const dy = target.y - (bot.entity.position.y + eyeHeight);
    const dz = target.z - bot.entity.position.z;
    const horizontal = Math.sqrt(dx * dx + dz * dz);
    _trackedYaw = normalizeYawDeg(radToDeg(Math.atan2(-dx, -dz)));
    _trackedPitch = clampPitchDeg(radToDeg(Math.atan2(dy, horizontal)));
    _orientationSynced = true;
  };

  const syncTrackedOrientationToBlock = (block: BlockLike): void => {
    syncTrackedToTarget(centerOf(block));
  };

  const actions: PhysicalCommandActions = {
    lookAt: async (target) => {
      await bot.lookAt(vec(target), false);
      syncTrackedToTarget(vec(target));
      return { ok: true, message: "Looked at target.", data: { target, yaw: _trackedYaw, pitch: _trackedPitch } };
    },
    look: async ({ yaw, pitch }) => {
      const yawDeg = normalizeYawDeg(yaw);
      const pitchDeg = clampPitchDeg(pitch);
      await bot.look(degToRad(yawDeg), degToRad(pitchDeg), true);
      _trackedYaw = yawDeg;
      _trackedPitch = pitchDeg;
      _orientationSynced = true;
      return { ok: true, message: `Looking yaw=${yawDeg.toFixed(1)} pitch=${pitchDeg.toFixed(1)}.`, data: { yaw: yawDeg, pitch: pitchDeg } };
    },
    getOrientation: () => {
      // Lazily sync from bot.entity if we haven't synced yet and the entity exists
      if (!_orientationSynced) {
        syncTrackedFromEntity();
      }
      return { yaw: _trackedYaw, pitch: _trackedPitch };
    },
    syncOrientation: () => {
      // Re-sync tracked yaw/pitch from bot.entity. Used after spawn/respawn
      // or when the UI needs to re-establish the baseline orientation.
      syncTrackedFromEntity();
    },
    walkToVisible: async ({ target, tolerance = 1.5, chunkLimit }, signal) => {
      const startPosition = bot.entity.position;
      wlog(`walk_to_visible start pos=${fmtVec(startPosition)} target=${fmtVec(target)} tolerance=${tolerance}`);
      // Already there? Return immediately without searching.
      if (distXZ(startPosition, target) <= tolerance) {
        return { ok: true, message: "Already within tolerance of target.", data: { status: "reached", position: vector(startPosition), target } };
      }
      const limit = Math.min(Math.max(1, Math.round(chunkLimit ?? options.maxChunkLimit)), options.maxChunkLimit);
      const region = navigationRegion(bot, limit);
      // Fail instantly if the target is outside the search region.
      if (
        target.x < region.minX || target.x > region.maxX ||
        target.z < region.minZ || target.z > region.maxZ
      ) {
        const clamped = clampToRegionXZ(vec(target), region);
        return {
          ok: false,
          reason: "target_too_far",
          message: `target ${fmtVec(target)} is outside the ${limit}-chunk (${limit * CHUNK + 2}-block radius) walk search region around your position ${fmtVec(startPosition)}. this tool only walks within that region. use walk_to_surface(x, z) for long-range travel: it chains hops automatically and never fails on distance alone. closest coordinate valid for walk_to_visible from here: x: ${Math.round(clamped.x)}, z: ${Math.round(clamped.z)}.`,
          data: { status: "too_far", position: vector(startPosition), target, chunkLimit: limit, clampedTarget: vector(clamped) }
        };
      }
      // Find safe standable cells in a sphere (radius 5) around the target,
      // sorted nearest-first, with headroom and liquid-safety filtering. When
      // the precise target has no reachable floor (grounded imprecision, an
      // air/deep ravine goal, or a target inside a wall), we route to the best
      // reachable nearby cell instead of failing outright.
      const candidates = findStandableCells(bot, target);
      if (candidates.length === 0) {
        const report = checkStandability(bot, vec(target));
        return {
          ok: false,
          reason: "target_not_standable",
          message: `no safe standable cell within 5 blocks of ${fmtVec(target)}: target block ${report.floorBlock}, blocks above: [${report.blocksAbove.join(", ")}] (${describeStandabilityIssues(report.issues)}). pick a nearby coordinate on solid ground, or use walk_to_surface(x, z) which finds the surface for you.`,
          data: { status: "not_standable", position: vector(startPosition), target, standability: report }
        };
      }
      // Try pathfinding to each candidate in proximity order and use the first
      // one that is actually reachable on foot.
      const attempts: Array<{ standable: Vector3; reason: string; message: string; navigation?: NavigationReport }> = [];
      for (const cell of candidates) {
        try {
          wlog(`walk_to_visible attempting standable cell ${fmtVec(cell)} (${candidates.indexOf(cell) + 1}/${candidates.length})`);
          const navigation = await gotoNear(bot, cell, Math.min(tolerance, 1.5), region, signal, undefined, wlog);
          const snapped = Math.floor(cell.x) !== Math.floor(target.x)
            || Math.floor(cell.y) !== Math.floor(target.y)
            || Math.floor(cell.z) !== Math.floor(target.z);
          return {
            ok: true,
            message: snapped
              ? `Reached target via routed standable cell ${fmtVec(cell)} (requested ${fmtVec(target)}).`
              : "Reached target.",
            data: {
              status: "reached",
              position: vector(bot.entity.position),
              target,
              standable: vector(cell),
              rerouted: snapped,
              navigation
            }
          };
        } catch (error) {
          wlog(`walk_to_visible cell ${fmtVec(cell)} failed: ${navigationReason(error)}: ${errorMessage(error).slice(0, 160)}`);
          attempts.push({
            standable: vector(cell),
            reason: navigationReason(error),
            message: errorMessage(error),
            navigation: error instanceof NavigationFailure ? error.report : undefined
          });
        }
      }
      const firstNav = attempts.find((a) => a.navigation)?.navigation;
      const closest = firstNav?.closestApproach;
      return {
        ok: false,
        reason: "no_paths_findable",
        message: `no path found to any of the ${candidates.length} standable cell(s) near ${fmtVec(target)}. ${attempts.slice(0, 3).map((a, i) => `attempt ${i + 1} -> ${fmtVec(a.standable)}: ${a.message}`).join(" ")}${closest ? ` closest reachable standable position overall: ${fmtVec(closest)}, ${round1(firstNav?.remainingDistance ?? 0)} blocks (3D) from the target — a valid walk_to_exact target. ` : " "}${ravineHint(firstNav)}suggestions: approach from a different angle, staircase/pillar over the obstacle, or use walk_to_surface for a different landing spot.`,
        data: {
          status: "failed",
          position: vector(bot.entity.position),
          target,
          candidateCount: candidates.length,
          candidates: attempts.map((a) => a.standable),
          attempts
        }
      };
    },
    walkToSurface: async ({ x, z, tolerance = 1.5 }, signal) => {
      const requested = { x, z };
      const hops: Array<{ from: Vector3; to: Vector3; status: string; pathNodes: number; ascents: number; drops: number }> = [];
      let lastDistance = distXZ(bot.entity.position, requested);
      let noProgressHops = 0;
      let initialDistance = lastDistance;
      while (hops.length < SURFACE_MAX_HOPS) {
        const position = bot.entity.position;
        const distanceToRequested = distXZ(position, requested);
        if (distanceToRequested <= tolerance) {
          return {
            ok: true,
            message: `Reached the surface at ${fmtVec(position)} (${round1(distanceToRequested)} blocks from the requested point).`,
            data: {
              status: "reached",
              position: vector(position),
              requested: { x, z },
              hops: hops.length,
              hopLog: hops,
              traveled: round1(initialDistance > distanceToRequested ? initialDistance - distanceToRequested : 0)
            }
          };
        }
        // Distant targets have unloaded chunks: the sky-scan cannot see the
        // surface there yet. Walk toward an intermediate point well inside the
        // loaded area and loop — the scan repeats once the terrain loads.
        if (scanSurfaceColumn(bot, Math.floor(x), Math.floor(z)).status === "unloaded") {
          const dx = x - position.x;
          const dz = z - position.z;
          const step = Math.min(distanceToRequested, INTERMEDIATE_HOP_BLOCKS);
          const length = Math.hypot(dx, dz) || 1;
          const intermediate = new Vec3(
            position.x + (dx / length) * step,
            position.y,
            position.z + (dz / length) * step
          );
          const region = navigationRegion(bot, options.maxChunkLimit);
          try {
            const navigation = await gotoNear(bot, intermediate, 4, region, signal);
            hops.push({
              from: vector(position),
              to: vector(intermediate),
              status: navigation.pathStatus,
              pathNodes: navigation.pathNodes,
              ascents: navigation.ascents,
              drops: navigation.drops
            });
            const newDistance = distXZ(bot.entity.position, requested);
            if (newDistance >= lastDistance - 0.5) {
              noProgressHops += 1;
              if (noProgressHops >= SURFACE_MAX_NO_PROGRESS_HOPS) {
                return failed("surface_no_progress", `walk_to_surface stopped making progress toward (${x}, ${z}): still ${round1(newDistance)} blocks away after ${hops.length} hop(s) — the target area is not loaded and intermediate hops stopped advancing. walk partway manually (walk_to_surface on a closer point) and retry.`, {
                  status: "no_progress",
                  position: vector(bot.entity.position),
                  requested,
                  hops: hops.length,
                  hopLog: hops
                });
              }
            } else {
              noProgressHops = 0;
            }
            lastDistance = newDistance;
            continue;
          } catch (error) {
            const navigation = error instanceof NavigationFailure ? error.report : undefined;
            const closest = navigation?.closestApproach;
            return failed(navigationReason(error), `no path found while approaching (${x}, ${z}) — its chunks are not loaded yet, so the walk routes over intermediate ground. ${errorMessage(error)}${closest ? ` closest reachable standable position: ${fmtVec(closest)} — a valid walk_to_exact target; from there, retry walk_to_surface(${x}, ${z}).` : ""} ${ravineHint(navigation)}progress: ${hops.length} hop(s) completed.`, {
              status: "failed",
              position: vector(bot.entity.position),
              requested,
              navigation,
              hops: hops.length,
              hopLog: hops
            });
          }
        }
        // Surface-scan the requested column, spiralling outward when it is
        // water/lava/canopy. The scan runs in loaded chunks around the bot.
        const surface = findSurfaceTarget(bot, Math.floor(x), Math.floor(z), SURFACE_SEARCH_RADIUS);
        if (!surface.cell) {
          return failed("no_standable_surface", describeSurfaceFailure(requested, surface.stats), {
            status: "not_standable",
            position: vector(position),
            requested,
            searchedRadius: SURFACE_SEARCH_RADIUS,
            columnStats: surface.stats,
            hops: hops.length,
            hopLog: hops
          });
        }
        // Terminal case: we are already standing as close as the terrain
        // allows (the requested point itself is liquid/canopy).
        if (distXZ(position, surface.cell) <= Math.min(tolerance, 1.5)) {
          return {
            ok: true,
            message: `Reached the closest standable surface to (${x}, ${z}): standing at ${fmtVec(position)}, ${round1(distanceToRequested)} blocks away. the requested point itself is ${surface.surface.name} (${surface.surface.type}) and cannot be stood on.`,
            data: {
              status: "reached_nearest_standable",
              position: vector(position),
              requested,
              standable: vector(surface.cell),
              requestedSurface: surface.surface,
              hops: hops.length,
              hopLog: hops
            }
          };
        }
        // Clamp far goals to the current search region and keep hopping: the
        // region re-centers on the bot after every hop, so distance alone
        // never fails a walk_to_surface.
        const region = navigationRegion(bot, options.maxChunkLimit);
        const outside =
          surface.cell.x < region.minX || surface.cell.x > region.maxX ||
          surface.cell.z < region.minZ || surface.cell.z > region.maxZ;
        const goal = outside ? clampToRegionXZ(surface.cell, region) : surface.cell;
        try {
          const navigation = await gotoNear(
            bot,
            goal,
            outside ? 4 : Math.min(tolerance, 1.5),
            region,
            signal
          );
          hops.push({
            from: vector(position),
            to: vector(goal),
            status: navigation.pathStatus,
            pathNodes: navigation.pathNodes,
            ascents: navigation.ascents,
            drops: navigation.drops
          });
        } catch (error) {
          const navigation = error instanceof NavigationFailure ? error.report : undefined;
          const closest = navigation?.closestApproach;
          return failed(
            navigationReason(error),
            `no path found while walking to the surface near (${x}, ${z})${outside ? " (goal clamped to the edge of the current search region)" : ""}. ${errorMessage(error)}${closest ? ` closest reachable standable position: ${fmtVec(closest)} — a valid walk_to_exact target; from there, retry walk_to_surface(${x}, ${z}).` : ""} ${ravineHint(navigation)}progress: ${hops.length} hop(s) completed, ${round1(initialDistance - distXZ(bot.entity.position, requested))} of ${round1(initialDistance)} blocks covered.`,
            {
              status: "failed",
              position: vector(bot.entity.position),
              requested,
              standable: vector(surface.cell),
              navigation,
              hops: hops.length,
              hopLog: hops
            }
          );
        }
        const newDistance = distXZ(bot.entity.position, requested);
        if (newDistance >= lastDistance - 0.5) {
          noProgressHops += 1;
          if (noProgressHops >= SURFACE_MAX_NO_PROGRESS_HOPS) {
            return failed("surface_no_progress", `walk_to_surface stopped making progress toward (${x}, ${z}): still ${round1(newDistance)} blocks away after ${hops.length} hop(s). the terrain between here and there probably needs digging, bridging, or pillaring (walk_to_visible to a closer point, then reassess). ${ravineHint(summarizeHopLog(hops))}`, {
              status: "no_progress",
              position: vector(bot.entity.position),
              requested,
              hops: hops.length,
              hopLog: hops
            });
          }
        } else {
          noProgressHops = 0;
        }
        lastDistance = newDistance;
      }
      return failed("surface_hop_limit", `walk_to_surface reached its ${SURFACE_MAX_HOPS}-hop limit while traveling to (${x}, ${z}): ${round1(distXZ(bot.entity.position, requested))} blocks remain. call walk_to_surface(${x}, ${z}) again to continue.`, {
        status: "hop_limit",
        position: vector(bot.entity.position),
        requested,
        hops: hops.length,
        hopLog: hops
      });
    },
    walkToExact: async ({ target, tolerance = 1.0 }, signal) => {
      const startPosition = bot.entity.position;
      wlog(`walk_to_exact start pos=${fmtVec(startPosition)} target=${fmtVec(target)} tolerance=${tolerance}`);
      const cell = new Vec3(Math.floor(target.x), Math.floor(target.y), Math.floor(target.z));
      const exact = checkStandability(bot, cell);
      let goal = cell;
      let snapped: Vector3 | null = null;
      if (!exact.standable) {
        // The saved position may be off by a block (mined out, pillared up,
        // flooded): look for a standable cell within 3 blocks of it.
        const alternatives = findStandableCells(bot, vector(cell), 3)
          .slice()
          .sort((a, b) => a.distanceTo(cell) - b.distanceTo(cell));
        if (alternatives.length === 0) {
          return failed("target_not_standable", `target not standable: target block ${exact.floorBlock}, blocks above: [${exact.blocksAbove.join(", ")}] (${describeStandabilityIssues(exact.issues)}). no standable cell within 3 blocks either — the saved position is probably stale (mined out, pillared up, or flooded). re-observe the area, update your notes, and retry with corrected coordinates.`, {
            status: "not_standable",
            position: vector(startPosition),
            target,
            standability: exact,
            searchedRadius: 3
          });
        }
        goal = alternatives[0];
        snapped = vector(goal);
      }
      const region = navigationRegion(bot, options.maxChunkLimit);
      if (
        goal.x < region.minX || goal.x > region.maxX ||
        goal.z < region.minZ || goal.z > region.maxZ
      ) {
        const clamped = clampToRegionXZ(goal, region);
        return failed("outside_pathfinding_range", `target ${fmtVec(goal)} is outside the ${options.maxChunkLimit}-chunk (${options.maxChunkLimit * CHUNK + 2}-block radius) pathfinding region around your position ${fmtVec(startPosition)}. get closer first — walk_to_surface(${Math.round(goal.x)}, ${Math.round(goal.z)}) travels any distance — then retry walk_to_exact. closest coordinate valid for pathfinding from here: x: ${Math.round(clamped.x)}, z: ${Math.round(clamped.z)}.`, {
          status: "too_far",
          position: vector(startPosition),
          target,
          goal: vector(goal),
          clampedTarget: vector(clamped)
        });
      }
      try {
        const navigation = await gotoNear(bot, goal, Math.max(0.25, Math.min(tolerance, 1.0)), region, signal, {
          searchBudgetMs: options.exactSearchBudgetMs,
          goalMode: "3d"
        }, wlog);
        return {
          ok: true,
          message: snapped
            ? `Reached ${fmtVec(goal)} — the nearest standable cell to the requested ${fmtVec(target)} (requested cell: ${exact.floorBlock}, blocks above: [${exact.blocksAbove.join(", ")}]).`
            : `Reached exact target ${fmtVec(goal)}.`,
          data: {
            status: "reached",
            position: vector(bot.entity.position),
            target,
            goal: vector(goal),
            snapped,
            navigation
          }
        };
      } catch (error) {
        wlog(`walk_to_exact failed: ${navigationReason(error)}: ${errorMessage(error).slice(0, 200)}`);
        const navigation = error instanceof NavigationFailure ? error.report : undefined;
        const closest = navigation?.closestApproach;
        return failed(navigationReason(error), `walk_to_exact failed: ${errorMessage(error)}${closest ? ` closest reachable standable position: ${fmtVec(closest)}, ${round1(navigation?.remainingDistance ?? 0)} blocks (3D) from the target. walk there (walk_to_exact on ${fmtVec(closest)}), then re-assess the remaining obstruction. ${ravineHint(navigation)}` : ""}`, {
          status: "failed",
          position: vector(bot.entity.position),
          target,
          goal: vector(goal),
          snapped,
          navigation
        });
      }
    },
    findBlock: async ({ blockName }) => {
      const registry = (bot as Bot & { registry?: { blocksByName?: Record<string, { id: number }> } }).registry;
      const maxDistance = options.viewRadiusBlocks ?? 256;
      const allNames = Object.keys(registry?.blocksByName ?? {});
      const matches = globResolve(blockName, allNames);
      if (matches.length === 0) {
        const suggestions = globSuggest(`*${blockName}*`, allNames, 20);
        return failed("unknown_block", `Unknown block name: ${blockName}.${suggestions.length > 0 ? ` Did you mean: ${suggestions.join(", ")}?` : ""} Patterns with * are allowed, e.g. '*log*' for any wood.`, { blockName, suggestions });
      }
      const ids = matches.map((name) => registry!.blocksByName![name].id);
      const found = bot.findBlock({
        matching: ids,
        maxDistance,
        // Anti-x-ray is hard-locked here (not just at the HTTP/MCP layer): the
        // scan always requires head line-of-sight (360 degrees) or proximity.
        useExtraInfo: (block) => isVisibleOrNear(bot, block as Parameters<Bot["canSeeBlock"]>[0])
      });
      if (!found) {
        const label = hasWildcard(blockName) ? `${blockName} (${matches.join(", ")})` : blockName;
        return failed("block_not_found", `No head-ray-visible ${label} found within ${maxDistance} loaded blocks. If you can see it in a screenshot, raise your viewpoint or walk closer and retry; if it is underground/hidden, it will not be reported until an exposed face is in sight.`, { blockName, matches, maxDistance, requireVisible: true });
      }
      return {
        ok: true,
        message: `Found ${found.name}${found.name !== blockName ? ` (pattern ${blockName})` : ""}.`,
        data: {
          block: vector(found.position),
          blockName: found.name,
          displayName: found.displayName ?? null,
          distance: bot.entity.position.distanceTo(found.position)
        }
      };
    },
    findInteractables: async ({ maxDistance } = {}) => {
      const range = Math.min(Math.max(4, maxDistance ?? options.viewRadiusBlocks ?? 64), 256);
      const finder = bot as Bot & { findBlocks?(options: Record<string, unknown>): Vec3[] };
      const positions = finder.findBlocks?.({
        matching: (block: unknown) => isInteractableName((block as BlockLike)?.name ?? ""),
        point: bot.entity.position,
        maxDistance: range,
        count: 64,
        // Same anti-x-ray rule as find_block: only head-visible blocks, plus a
        // small proximity override for blocks too close/obscured to raycast.
        useExtraInfo: (block: unknown) => isVisibleOrNear(bot, block as Parameters<Bot["canSeeBlock"]>[0])
      }) ?? [];
      const blocks = positions.map((pos) => ({
        name: (bot.blockAt(pos) as BlockLike | null)?.name ?? "unknown",
        x: pos.x,
        y: pos.y,
        z: pos.z,
        distance: Math.round(bot.entity.position.distanceTo(pos) * 10) / 10
      }));
      return {
        ok: true,
        message: `Found ${blocks.length} interactable block(s) within ${range} blocks.`,
        data: { blocks: blocks.sort((a, b) => a.distance - b.distance), count: blocks.length, maxDistance: range }
      };
    },
    mineBlock: async ({ block: target, walkIntoRange }) => {
      const targetBlock = blockAt(bot, target);
      if (!targetBlock || targetBlock.name === "air") {
        return { ok: false, reason: "block_not_found", message: "No block exists at target position.", data: { block: target } };
      }
      const range = await ensureRange(bot, targetBlock, walkIntoRange);
      if (!range.ok) {
        return range;
      }

      try {
        const visibleTarget = blockAt(bot, target);
        if (!visibleTarget || visibleTarget.name === "air") {
          return failed("block_not_found", "Target block no longer exists after walking into range.", { block: target });
        }
        // Head-line-of-sight is normally required for realistic perception, but
        // the exemption must use the same ruler as the reach check (eye to block
        // center, mineflayer's canDigBlock radius): any block within interaction
        // reach is one the body is standing next to and can plainly touch, so
        // canopy leaves, shaft walls, or terrain cannot hide it. The configured
        // tunnel distance stays as a floor covering canDigBlock-false cases
        // (playtest finding 2c: feet-level block in a 1-wide shaft).
        const eyeHeight = (bot.entity as typeof bot.entity & { eyeHeight?: number }).eyeHeight ?? 1.62;
        const eyeDistance = bot.entity.position
          .offset(0, eyeHeight, 0)
          .distanceTo(centerOf(visibleTarget));
        const withinExemptRange =
          eyeDistance <= MINE_REACH_BLOCKS ||
          bot.entity.position.distanceTo(visibleTarget.position) <=
            options.mineVisibilityIgnoreDistance;
        if (
          !isVisibleFromHead(bot, visibleTarget as Parameters<Bot["canSeeBlock"]>[0])
          && !withinExemptRange
        ) {
          return failed("block_not_visible", "Target block is no longer visible from the player's head after walking into range.", {
            block: target,
            blockName: visibleTarget.name
          });
        }
        await bot.lookAt(centerOf(visibleTarget), false);
        syncTrackedOrientationToBlock(visibleTarget);
        const heldItemBefore = heldItemSnapshot(bot.heldItem);
        const canHarvest = typeof visibleTarget.canHarvest === "function"
          ? Boolean(visibleTarget.canHarvest(bot.heldItem?.type ?? null))
          : null;
        if (canHarvest === false) {
          return failed(
            "unharvestable",
            `${heldItemBefore?.name ?? "Empty hand"} cannot harvest drops from ${visibleTarget.name}.`,
            {
              block: target,
              blockName: visibleTarget.name,
              heldItemBefore,
              canHarvest
            }
          );
        }
        let digError: unknown = null;
        // Viewport-independent face: compute the dig face from the player→block
        // offset instead of mineflayer's raycast, which throws "Block not in
        // view" whenever a neighbouring wall blocks the eye ray. Explicit faces
        // also work from any rotation.
        const digFace = digFaceFor(bot, visibleTarget);
        const digPromise = (bot as ActionBot).dig(visibleTarget, true, digFace).then(
          () => undefined,
          (error: unknown) => {
            digError = error;
          }
        );
        await Promise.race([
          digPromise,
          waitForBlockRemoved(bot, vec(target), 25_000)
        ]);
        // Let the world cache settle before reading the result state so a stale
        // block echo cannot report the pre-mine block name (playtest finding 4).
        await new Promise(resolve => setTimeout(resolve, 250));
        const after = blockAt(bot, target);
        const stillSolid = after !== null && after.name !== "air" && after.boundingBox !== "empty";
        if (digError && stillSolid) {
          throw digError;
        }
        if (stillSolid) {
          return failed("dig_unverified", "Mineflayer returned without removing the target block.", {
            block: target,
            blockName: visibleTarget.name,
            resultBlockName: after.name
          });
        }

        // Walk to the drop location to collect the item, but only when the
        // drop is outside the (raised) pickup radius — pathfinder calls are slow.
        const dropPos = centerOf(visibleTarget);
        if (bot.entity.position.distanceTo(dropPos) > 10) {
          try {
            await gotoNear(bot, dropPos, 1.5, defaultNavigationRegion(bot));
          } catch {
            // Pathfinding may fail if terrain is complex; ignore
          }
        }

        // Minecraft block drops are not immediately collectible. Wait past the
        // normal pickup delay so the authoritative after-state does not race a
        // nearby item entity and send an agent into a false retry loop.
        await new Promise(resolve => setTimeout(resolve, 1_000));
        // Re-read the target AFTER the pickup settle: this is the authoritative
        // result block name (air for a cleanly mined block).
        const resultBlock = blockAt(bot, target);
        const resultBlockName = resultBlock !== null && resultBlock.name !== "air" && resultBlock.boundingBox !== "empty"
          ? resultBlock.name
          : "air";
        
        return {
          ok: true,
          message: "Mined block.",
          data: {
            block: target,
            blockName: visibleTarget.name,
            resultBlockName,
            heldItemBefore,
            canHarvest
          }
        };
      } catch (error) {
        return failed("dig_failed", `Mineflayer dig failed: ${errorMessage(error)}`, { block: target, blockName: targetBlock.name });
      }
    },
    placeBlock: async ({ referenceBlock, face, walkIntoRange }) => {
      const block = blockAt(bot, referenceBlock);
      if (!block || block.name === "air") {
        return { ok: false, reason: "block_not_found", message: "No reference block exists at target position.", data: { referenceBlock } };
      }
      const heldBefore = heldItemSnapshot(bot.heldItem);
      if (!heldBefore) {
        return failed("no_held_item", "No held item is available to place.", { referenceBlock, face });
      }
      const placedPosition = block.position.offset(face.x, face.y, face.z);
      const targetBefore = bot.blockAt(placedPosition);
      if (targetBefore && targetBefore.name !== "air" && targetBefore.boundingBox !== "empty") {
        return failed("place_target_occupied", "The requested placement position is already occupied.", {
          referenceBlock,
          face,
          placedBlock: vector(placedPosition),
          placedBlockName: targetBefore.name
        });
      }
      const range = await ensureRange(bot, block, walkIntoRange);
      if (!range.ok) {
        return range;
      }

      try {
        await bot.lookAt(centerOf(block), false);
        syncTrackedOrientationToBlock(block);
        try {
          await (bot as ActionBot).placeBlock(block, vec(face));
        } catch (err) {
          // placeBlock may time out waiting for blockUpdate, but the block
          // might have been placed anyway. Ignore the timeout and verify.
          const msg = err instanceof Error ? err.message : String(err);
          if (!msg.includes("timeout") && !msg.includes("did not fire")) {
            throw err; // Re-throw non-timeout errors
          }
        }
        // Verify the block was placed
        await new Promise(resolve => setTimeout(resolve, 300));
        const verification = verifyPlacedHeldItem(bot, placedPosition, heldBefore);
        if (!verification.verified && !verification.itemConsumed) {
          return failed("place_unverified", "Place command completed without verified block placement or item consumption.", {
            referenceBlock,
            face,
            placedBlock: vector(placedPosition),
            placedBlockName: verification.placedBlockName
          });
        }
        return {
          ok: true,
          message: verification.verified ? "Placed held item." : "Placed held item; item consumption verified while block update was delayed.",
          data: { referenceBlock, face, placedBlock: vector(placedPosition), verified: verification.verified, itemConsumed: verification.itemConsumed }
        };
      } catch (error) {
        return failed("place_failed", `Mineflayer place failed: ${errorMessage(error)}`, { referenceBlock, face });
      }
    },
    jumpPlaceBlock: async ({ referenceBlock, face, walkIntoRange }) => {
      const block = blockAt(bot, referenceBlock);
      if (!block || block.name === "air") {
        return { ok: false, reason: "block_not_found", message: "No reference block exists at target position.", data: { referenceBlock } };
      }
      const heldBefore = heldItemSnapshot(bot.heldItem);
      if (!heldBefore) {
        return failed("no_held_item", "No held item is available to place.", { referenceBlock, face });
      }
      const placedPosition = block.position.offset(face.x, face.y, face.z);
      const targetBefore = bot.blockAt(placedPosition);
      if (targetBefore && targetBefore.name !== "air" && targetBefore.boundingBox !== "empty") {
        return failed("place_target_occupied", "The requested jump-placement position is already occupied.", {
          referenceBlock,
          face,
          placedBlock: vector(placedPosition),
          placedBlockName: targetBefore.name
        });
      }
      const range = await ensureRange(bot, block, walkIntoRange);
      if (!range.ok) {
        return range;
      }

      try {
        await bot.lookAt(centerOf(block), false);
        syncTrackedOrientationToBlock(block);
        const jumpStartY = bot.entity.position.y;
        bot.setControlState("jump", true);
        if (typeof bot.entity.onGround === "boolean") {
          const roseEnough = await waitForHeight(
            bot,
            jumpStartY + 1,
            1_000
          );
          if (!roseEnough) {
            return failed(
              "jump_did_not_rise",
              "Jump placement never reached a height that clears the target block.",
              {
                startY: jumpStartY,
                maximumObservedY: bot.entity.position.y
              }
            );
          }
        } else {
          await new Promise(resolve => setTimeout(resolve, 350));
        }
        try {
          const actionBot = bot as ActionBot;
          if (actionBot._placeBlockWithOptions) {
            await actionBot._placeBlockWithOptions(
              block,
              vec(face),
              {
                forceLook: "ignore",
                swingArm: "right"
              }
            );
          } else {
            await actionBot.placeBlock(block, vec(face));
          }
        } catch (err) {
          const msg = err instanceof Error ? err.message : String(err);
          if (!msg.includes("timeout") && !msg.includes("did not fire")) {
            throw err;
          }
        }
        await new Promise(resolve => setTimeout(resolve, 300));
        const verification = verifyPlacedHeldItem(bot, placedPosition, heldBefore);
        if (!verification.verified && !verification.itemConsumed) {
          return failed("place_unverified", "Jump-place command completed without verified block placement or item consumption.", {
            referenceBlock,
            face,
            placedBlock: vector(placedPosition),
            placedBlockName: verification.placedBlockName
          });
        }
        return {
          ok: true,
          message: verification.verified ? "Jump-placed held item." : "Jump-placed held item; item consumption verified while block update was delayed.",
          data: { referenceBlock, face, placedBlock: vector(placedPosition), verified: verification.verified, itemConsumed: verification.itemConsumed }
        };
      } catch (error) {
        return failed("place_failed", `Mineflayer jump-place failed: ${errorMessage(error)}`, { referenceBlock, face });
      } finally {
        bot.setControlState("jump", false);
      }
    },
    pillarUp: async () => {
      if (!await waitForGround(bot, Number.NEGATIVE_INFINITY, 2_000)) {
        return failed("pillar_not_grounded", "Cannot pillar up because the player did not reach the ground within 2 seconds.", {
          position: vector(bot.entity.position)
        });
      }
      const heldItem = heldItemSnapshot(bot.heldItem);
      if (!heldItem) {
        return failed(
          "pillar_up_needs_placeable_block",
          "pillar_up requires a placeable solid block in hand (e.g. cobblestone or dirt), but your hand is empty. Equip a solid block first.",
          { position: vector(bot.entity.position), heldItem }
        );
      }
      if (!isPlaceableSolidBlock(bot, heldItem.name)) {
        return failed(
          "pillar_up_needs_placeable_block",
          `pillar_up requires a placeable solid block in hand; the held item '${heldItem.name}' is not a placeable block. Equip a solid block like cobblestone or dirt first.`,
          { position: vector(bot.entity.position), heldItem }
        );
      }
      const start = bot.entity.position.clone();
      const placedPosition = start.floored();
      const referenceBlock = placedPosition.offset(0, -1, 0);
      const targetBefore = blockAt(bot, placedPosition);
      if (targetBefore && targetBefore.name !== "air" && targetBefore.boundingBox !== "empty") {
        return failed("pillar_target_occupied", "The block space at the player's feet is already occupied.", {
          placedBlock: vector(placedPosition),
          placedBlockName: targetBefore.name
        });
      }
      const landingHeadPosition = placedPosition.offset(0, 2, 0);
      const landingHeadBlock = blockAt(bot, landingHeadPosition);
      if (
        landingHeadBlock
        && landingHeadBlock.name !== "air"
        && landingHeadBlock.boundingBox !== "empty"
      ) {
        return failed(
          "pillar_headroom_blocked",
          "Cannot pillar because the landing position has no headroom; clear the block(s) above your head before ascending.",
          {
            blockedHeadPosition: vector(landingHeadPosition),
            blockedBy: landingHeadBlock.name,
            needsHeadroomAbove: true
          }
        );
      }
      let lastResult: CommandResult | null = null;

      for (let attempt = 1; attempt <= 3; attempt += 1) {
        if (!await waitForGround(bot, start.y, 1_500)) break;
        lastResult = await actions.jumpPlaceBlock({
          referenceBlock: vector(referenceBlock),
          face: { x: 0, y: 1, z: 0 },
          walkIntoRange: false
        });
        const placed = await waitForSolidBlock(bot, placedPosition, 1_000);
        if (placed) {
          const landed = await waitForGround(bot, placedPosition.y + 1, 2_000);
          return {
            ok: true,
            message: landed ? "Pillared up one block and landed." : "Pillared up one block; landing was not observed before timeout.",
            data: {
              attempts: attempt,
              startPosition: vector(start),
              referenceBlock: vector(referenceBlock),
              placedBlock: vector(placedPosition),
              placedBlockName: placed.name,
              landed,
              position: vector(bot.entity.position)
            }
          };
        }
      }

      return failed("pillar_up_failed", "Could not place the held block beneath the player after 3 natural jump attempts.", {
        attempts: 3,
        startPosition: vector(start),
        referenceBlock: vector(referenceBlock),
        placedBlock: vector(placedPosition),
        lastFailure: lastResult
      });
    },
    useBlock: async ({ block: target, walkIntoRange }) => {
      const block = blockAt(bot, target);
      if (!block || block.name === "air") {
        return { ok: false, reason: "block_not_found", message: "No block exists at target position.", data: { block: target } };
      }
      const range = await ensureRange(bot, block, walkIntoRange);
      if (!range.ok) {
        return range;
      }

      try {
        await bot.lookAt(centerOf(block), false);
        syncTrackedOrientationToBlock(block);
        await (bot as ActionBot).activateBlock(block);
        // Brief pause to allow the server to open a container window
        await new Promise(resolve => setTimeout(resolve, 300));
        const windowType = detectOpenedWindowType(bot);
        return { ok: true, message: "Used block.", data: { block: target, blockName: block.name, windowType } };
      } catch (error) {
        return failed("use_failed", `Mineflayer use failed: ${errorMessage(error)}`, { block: target, blockName: block.name });
      }
    },
    useHeldItem: async () => {
      const held = bot.heldItem as { name?: string; count?: number; displayName?: string; type?: number } | null;
      if (!held?.name) {
        return failed("no_item_held", "Nothing is held; equip an item first (inventory_equip).", {});
      }
      const registry = (bot as unknown as { registry?: { foodsArray?: Array<{ id: number; foodPoints?: number }> } }).registry;
      const isFood = Array.isArray(registry?.foodsArray) && held.type !== undefined
        ? registry.foodsArray.some((f) => f.id === held.type && (f.foodPoints ?? 0) > 0)
        : false;
      try {
        if (isFood) {
          const eater = bot as Bot & { consume?: () => Promise<void> };
          if (typeof eater.consume !== "function") {
            return failed("use_item_unavailable", "Mineflayer eat/consume is not available on this version.", { itemName: held.name });
          }
          await eater.consume();
          return { ok: true, message: `Consumed ${held.name}.`, data: { action: "consume", itemName: held.name, isFood: true } };
        }
        // Generic right-click use: eggs/ender pearls/chorus fruit/buckets/potions, etc.
        const user = bot as Bot & { activateItem?: (offHand?: boolean) => void };
        if (typeof user.activateItem !== "function") {
          return failed("use_item_unavailable", "Mineflayer activateItem is not available on this version.", { itemName: held.name });
        }
        user.activateItem(false);
        // Let the server process the use (throw/drink/activate).
        await new Promise(resolve => setTimeout(resolve, 400));
        return { ok: true, message: `Used ${held.name}.`, data: { action: "use", itemName: held.name, isFood: false } };
      } catch (error) {
        if (errorMessage(error).toLowerCase().includes("food is full")) {
          return failed("food_full", `Can't eat ${held.name}: food is already full.`, { itemName: held.name });
        }
        return failed("use_item_failed", `Failed to use ${held.name}: ${errorMessage(error)}`, { itemName: held.name });
      }
    },
    chestDeposit: async ({ itemName, count }) => {
      const window = openedContainerWindow(bot);
      if (!window) {
        return failed("no_chest_window", "No container (chest/barrel) window is open. Open one first with use_block, then deposit.", { itemName });
      }
      const inventoryItems = windowItemsInRange(window, window.inventoryStart, window.inventoryEnd);
      const matches = globResolve(itemName, inventoryItems.map((entry) => entry.name));
      if (matches.length === 0) {
        return failed("unknown_item", `No inventory item matches: ${itemName}.${suggestFrom(inventoryItems.map((entry) => entry.name), itemName)}`, { itemName, inventory: inventoryItems });
      }
      let remaining = count !== undefined && count > 0 ? count : Number.POSITIVE_INFINITY;
      const moved: Array<{ itemName: string; count: number }> = [];
      for (const name of matches) {
        if (remaining <= 0) break;
        const itemId = registryItemId(bot, name);
        if (typeof itemId !== "number") continue;
        const available = typeof window.countRange === "function"
          ? window.countRange(window.inventoryStart, window.inventoryEnd, itemId, 0)
          : 0;
        const toMove = Math.min(available, remaining);
        if (toMove > 0) {
          await window.deposit!(itemId, 0, toMove);
          moved.push({ itemName: name, count: toMove });
          remaining -= toMove;
        }
      }
      if (moved.length === 0) {
        return failed("item_not_in_inventory", `No ${itemName} in the player inventory to deposit.`, { itemName, matches });
      }
      const total = moved.reduce((sum, entry) => sum + entry.count, 0);
      return {
        ok: true,
        message: `Deposited ${total} item(s) into the container: ${describeMatches(moved.map((m) => ({ name: m.itemName, count: m.count })))}.`,
        data: { pattern: itemName, moved, count: total, windowContents: containerContents(window) }
      };
    },
    chestWithdraw: async ({ itemName, count }) => {
      const window = openedContainerWindow(bot);
      if (!window) {
        return failed("no_chest_window", "No container (chest/barrel) window is open. Open one first with use_block, then withdraw.", { itemName });
      }
      const containerItems = windowItemsInRange(window, 0, window.inventoryStart);
      const matches = globResolve(itemName, containerItems.map((entry) => entry.name));
      if (matches.length === 0) {
        return failed("unknown_item", `No item in the container matches: ${itemName}.${suggestFrom(containerItems.map((entry) => entry.name), itemName)}`, { itemName, container: containerItems });
      }
      let remaining = count !== undefined && count > 0 ? count : Number.POSITIVE_INFINITY;
      const moved: Array<{ itemName: string; count: number }> = [];
      for (const name of matches) {
        if (remaining <= 0) break;
        const itemId = registryItemId(bot, name);
        if (typeof itemId !== "number") continue;
        const available = typeof window.countRange === "function"
          ? window.countRange(0, window.inventoryStart, itemId, 0)
          : 0;
        const toMove = Math.min(available, remaining);
        if (toMove > 0) {
          await window.withdraw!(itemId, 0, toMove);
          moved.push({ itemName: name, count: toMove });
          remaining -= toMove;
        }
      }
      if (moved.length === 0) {
        return failed("item_not_in_container", `No ${itemName} in the container to withdraw.`, { itemName, matches });
      }
      const total = moved.reduce((sum, entry) => sum + entry.count, 0);
      return {
        ok: true,
        message: `Withdrew ${total} item(s) from the container: ${describeMatches(moved.map((m) => ({ name: m.itemName, count: m.count })))}.`,
        data: { pattern: itemName, moved, count: total, windowContents: containerContents(window) }
      };
    },
    attackEntity: async ({ entityId, walkIntoRange = true }) => {
      // Tuning constants live here, not in the model-facing schema: the model
      // cannot calibrate retry counts by vibes.
      const renavigationCount = 3;
      const maxHits = 25;
      const resolveTarget = (): (EntityLike & { id: number }) | null => {
        const entity = bot.entities?.[entityId] as EntityLike | undefined;
        return entity && entity !== bot.entity && entity.position
          ? (entity as EntityLike & { id: number })
          : null;
      };
      const first = resolveTarget();
      if (!first) {
        return failed("entity_not_found", "The observed entity is no longer present.", { entityId, attempt: 0 });
      }
      const label = first.username ?? first.name ?? first.displayName ?? `entity ${entityId}`;
      const kindOf = (t: EntityLike): string => t.type ?? t.kind ?? "unknown";

      // No health tracking: keep swinging until the target is dead/gone.
      let hits = 0;
      let walks = 0;
      for (let attempt = 0; attempt < maxHits; attempt++) {
        const target = resolveTarget();
        if (!target) {
          return { ok: true, message: `${label} is dead or gone after ${hits} hit(s).`, data: { entityId, name: label, kind: kindOf(first), hits, killed: true, walks } };
        }
        const distance = bot.entity.position.distanceTo(target.position);
        if (distance <= ATTACK_RANGE) {
          try {
            const eyeTarget = target.position.offset(0, 0.8, 0);
            await bot.lookAt(eyeTarget, false);
            syncTrackedToTarget(eyeTarget);
            const hit = await strikeAndDetectHit(bot, target);
            if (hit) hits++;
          } catch (error) {
            return failed("attack_failed", `Mineflayer attack failed: ${errorMessage(error)}`, { entityId, name: label, hits, walks });
          }
          continue;
        }
        if (!walkIntoRange) {
          return failed("entity_out_of_range", `${label} is outside attack range.`, { entityId, distance, hits, walks });
        }
        if (walks >= renavigationCount) {
          return failed("entity_out_of_range", `${label} moved out of range after ${walks} walk(s). Give up and reposition.`, { entityId, distance, hits, walks });
        }
        try {
          await gotoNear(bot, vector(target.position), 2.0, defaultNavigationRegion(bot));
          walks++;
        } catch (error) {
          return failed("entity_unreachable", `Could not reach ${label}: ${errorMessage(error)}`, { entityId, hits, walks });
        }
      }
      return failed("attack_timeout", `${label} is still alive after ${maxHits} swings (${hits} connected).`, { entityId, name: label, kind: kindOf(first), hits, kills: 0, walks });
    },
    inspectBlock: async (target) => {
      const block = blockAt(bot, target);
      if (!block) {
        return { ok: false, reason: "block_not_loaded", message: "Target block is not loaded.", data: { block: target } };
      }
      const heldItem = heldItemSnapshot(bot.heldItem);
      const canHarvestWithHeldItem = typeof block.canHarvest === "function"
        ? Boolean(block.canHarvest(bot.heldItem?.type ?? null))
        : null;
      const digTimeMs = block.diggable ? bot.digTime(block as never) : null;
      return {
        ok: true,
        message: "Inspected block.",
        data: {
          block: target,
          blockName: block.name,
          displayName: block.displayName ?? null,
          type: block.type,
          diggable: block.diggable ?? null,
          boundingBox: block.boundingBox ?? null,
          digTimeMs: Number.isFinite(digTimeMs) ? digTimeMs : null,
          heldItem,
          canHarvestWithHeldItem
        }
      };
    },
    scanHorizon: async ({ maxDistance } = {}) => {
      const eyeHeight = (bot.entity as typeof bot.entity & { eyeHeight?: number }).eyeHeight ?? 1.62;
      const start = bot.entity.position.offset(0, eyeHeight, 0);
      const range = Math.min(Math.max(16, maxDistance ?? options.viewRadiusBlocks ?? 256), 256);
      const world = (bot as Bot & { world?: { raycast?(origin: Vec3, dir: Vec3, range: number, matcher?: (b: unknown) => boolean): unknown } }).world;
      if (!world?.raycast) {
        return failed("world_unavailable", "World raycasting is not available.", {});
      }
      // Solids AND liquids: a distant water surface is exactly the signal a
      // horizon scan wants (ocean directions), and lava glow is a landmark.
      const match = (block: unknown): boolean => {
        const b = block as { name?: string; boundingBox?: string } | null;
        if (!b || !b.name) return false;
        if (b.name === "air" || b.name === "cave_air" || b.name === "void_air") return false;
        return b.boundingBox === "block" || isLiquidName(b.name);
      };
      const headings = 24; // every 15 degrees
      const pitches = [15, 0, -15];
      const results: Array<{
        heading: number;
        pitch: number;
        hit: { blockName: string; position: Vector3; distance: number } | null;
      }> = [];
      for (let h = 0; h < headings; h++) {
        const headingDeg = h * 15;
        for (const pitchDeg of pitches) {
          const headingRad = (headingDeg * Math.PI) / 180;
          const pitchRad = (pitchDeg * Math.PI) / 180;
          const dir = new Vec3(
            Math.sin(headingRad) * Math.cos(pitchRad),
            Math.sin(pitchRad),
            -Math.cos(headingRad) * Math.cos(pitchRad)
          ).normalize();
          const hit = world.raycast(start, dir, range, match) as
            | { name?: string; position?: Vec3 }
            | null;
          results.push({
            heading: headingDeg,
            pitch: pitchDeg,
            hit: hit?.position
              ? {
                blockName: hit.name ?? "?",
                position: vector(hit.position),
                distance: round1(start.distanceTo(hit.position))
              }
              : null
          });
        }
      }
      return {
        ok: true,
        message: describeHorizonScan(start, range, results),
        data: {
          eye: vector(start),
          range,
          headings,
          pitches,
          results,
          notable: notableHorizonHits(results)
        }
      };
    },
    raycast: async (maxDistance?: number) => {
      const range = Math.min(Math.max(1, maxDistance ?? options.viewRadiusBlocks ?? 256), 256);
      // Read the current orientation in this module's degree convention. The
      // tracked degrees mirror lookAt/look so this matches where the crosshair
      // actually points.
      syncTrackedFromEntity();
      const yawRad = degToRad(_trackedYaw);
      const pitchRad = degToRad(_trackedPitch);
      const dir = new Vec3(
        -Math.sin(yawRad) * Math.cos(pitchRad),
        Math.sin(pitchRad),
        -Math.cos(yawRad) * Math.cos(pitchRad)
      ).normalize();
      const eyeHeight = (bot.entity as typeof bot.entity & { eyeHeight?: number }).eyeHeight ?? 1.62;
      const start = bot.entity.position.offset(0, eyeHeight, 0);
      const match = (block: unknown): boolean =>
        !!block && (block as { boundingBox?: string }).boundingBox === "block" &&
        (block as { name?: string }).name !== "air" &&
        (block as { name?: string }).name !== "cave_air";
      const world = (bot as Bot & { world?: { raycast?(origin: Vec3, dir: Vec3, range: number, matcher?: (b: unknown) => boolean): unknown } }).world;
      const hit = world?.raycast?.(start, dir, range, match);
      if (!hit) {
        return {
          ok: true,
          message: `Raycast hit nothing solid within ${range} blocks.`,
          data: { hit: null, yaw: _trackedYaw, pitch: _trackedPitch, maxDistance: range }
        };
      }
      const name = (hit as { name?: string }).name ?? "?";
      const pos = (hit as { position?: Vec3 }).position;
      return {
        ok: true,
        message: `Looking at ${name} at ${pos ? `${pos.x},${pos.y},${pos.z}` : "?"}.`,
        data: {
          hit: { blockName: name, position: pos ? { x: pos.x, y: pos.y, z: pos.z } : null, type: (hit as { type?: number }).type ?? null },
          yaw: _trackedYaw,
          pitch: _trackedPitch,
          maxDistance: range
        }
      };
    }
  };
  return actions;
}

async function waitForGround(bot: Bot, minimumY: number, timeoutMs: number): Promise<boolean> {
  if (typeof bot.entity.onGround !== "boolean") return true;
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (bot.entity.onGround && bot.entity.position.y >= minimumY - 0.1) return true;
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  return bot.entity.onGround && bot.entity.position.y >= minimumY - 0.1;
}

async function waitForHeight(
  bot: Bot,
  minimumY: number,
  timeoutMs: number
): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (bot.entity.position.y >= minimumY) return true;
    await new Promise(resolve => setTimeout(resolve, 20));
  }
  return bot.entity.position.y >= minimumY;
}

async function waitForSolidBlock(bot: Bot, position: Vec3, timeoutMs: number): Promise<BlockLike | null> {
  const deadline = Date.now() + timeoutMs;
  do {
    const block = blockAt(bot, position);
    if (block && block.name !== "air" && block.boundingBox !== "empty") return block;
    await new Promise(resolve => setTimeout(resolve, 50));
  } while (Date.now() < deadline);
  return null;
}

async function waitForBlockRemoved(bot: Bot, position: Vec3, timeoutMs: number): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  do {
    const block = blockAt(bot, position);
    if (!block || block.name === "air" || block.boundingBox === "empty") return true;
    await new Promise(resolve => setTimeout(resolve, 50));
  } while (Date.now() < deadline);
  const block = blockAt(bot, position);
  return !block || block.name === "air" || block.boundingBox === "empty";
}

/**
 * Install mineflayer-pathfinder and cap its A* compute budget. We only ever
 * hand it a static, walk-only goal inside a bounded region, so a small budget
 * is enough: reachable goals resolve in milliseconds, unreachable ones fail
 * fast instead of grinding. thinkTimeout is cumulative *compute* time across
 * physics ticks (~40ms of compute per 50ms tick), so the wall-clock cost stays
 * under ~1.25x the budget.
 */
export function installPathfinder(bot: Bot, searchBudgetMs = 1_000): void {
  const current = bot as Bot & { pathfinder?: unknown; loadPlugin(plugin: (bot: Bot) => void): void };
  if (!current.pathfinder) {
    current.loadPlugin(pathfinder);
  }
  const pf = (bot as unknown as { pathfinder?: { thinkTimeout: number; tickTimeout: number } }).pathfinder;
  if (pf) {
    pf.thinkTimeout = Math.max(250, searchBudgetMs);
    pf.tickTimeout = 40;
  }
}

export interface NavigationRegion {
  minX: number;
  maxX: number;
  minZ: number;
  maxZ: number;
}

// Search-region size for internal walks (attack range, drop pickup, walk-into
// mining/placing range). These targets are normally right next to the bot.
const INTERNAL_NAV_CHUNK_LIMIT = 8;
const ATTACK_RANGE = 4;

function navigationRegion(bot: Bot, chunkLimit: number): NavigationRegion {
  const chunkX = Math.floor(bot.entity.position.x / CHUNK);
  const chunkZ = Math.floor(bot.entity.position.z / CHUNK);
  // Chunk-aligned box, plus a small cushion so boundary cells are not pruned
  // by the exclusion filter before the target's chunk is fully searchable.
  const half = chunkLimit * CHUNK + 2;
  return {
    minX: chunkX * CHUNK - half,
    maxX: chunkX * CHUNK + CHUNK - 1 + half,
    minZ: chunkZ * CHUNK - half,
    maxZ: chunkZ * CHUNK + CHUNK - 1 + half
  };
}

function defaultNavigationRegion(bot: Bot): NavigationRegion {
  return navigationRegion(bot, INTERNAL_NAV_CHUNK_LIMIT);
}

function distXZ(a: { x: number; z: number }, b: { x: number; z: number }): number {
  return Math.hypot(a.x - b.x, a.z - b.z);
}

/**
 * Find safe standable cells in a sphere (radius 5) around the target and,
 * for air/high targets, directly beneath it via raytrace-down. Returns cells
 * sorted by distance from the bot's current position (nearest first), each
 * with clear headroom (2 air above feet) and no standing in / under liquids.
 *
 * A sphere (not a circle) is deliberate: over long distances the precise
 * target can be a block inside the ground due to imprecision or a floating
 * coordinate, so we also scan above the target for a valid floor.
 */
function findStandableCells(bot: Bot, target: Vector3, radius = 5): Vec3[] {
  const results: Vec3[] = [];
  const seen = new Set<string>();
  const x0 = Math.floor(target.x);
  const y0 = Math.floor(target.y);
  const z0 = Math.floor(target.z);
  const push = (cell: Vec3): void => {
    const key = `${cell.x},${cell.y},${cell.z}`;
    if (seen.has(key)) return;
    seen.add(key);
    results.push(cell);
  };

  // Sphere scan (inclusive radius, roughly cubic shell for integer cells).
  const r2 = radius * radius;
  for (let dy = -radius; dy <= radius; dy++) {
    for (let dx = -radius; dx <= radius; dx++) {
      for (let dz = -radius; dz <= radius; dz++) {
        if (dx * dx + dy * dy + dz * dz > r2) continue;
        const cell = new Vec3(x0 + dx, y0 + dy, z0 + dz);
        if (isSafeStandable(bot, cell)) push(cell);
      }
    }
  }

  // Raytrace straight down from the target to first solid floor (air/deep
  // overhang targets that the sphere's ±5 radius may not reach, and grounded
  // targets whose precise Y is buried).
  const raytraced = raytraceDownStandable(bot, target);
  if (raytraced) push(raytraced);

  // Nearest-first so the first pathfinding success is also the closest.
  const pos = bot.entity.position;
  results.sort((a, b) => a.distanceTo(pos) - b.distanceTo(pos));
  return results;
}

/** True when a cell is a safe place to stand: floor below, clear headroom
 * (2 air above feet for a 2-tall player), and not standing in or over a
 * liquid (lava/water) that would be unsafe to walk into. */
function isSafeStandable(bot: Bot, cell: Vec3): boolean {
  return checkStandability(bot, cell).standable;
}

export interface StandabilityIssue {
  /** Where the problem is, relative to the candidate feet cell. */
  location: "feet" | "body" | "head" | "floor";
  blockName: string;
  problem: "solid" | "liquid" | "not_solid" | "unloaded";
  y: number;
}

export interface StandabilityReport {
  standable: boolean;
  issues: StandabilityIssue[];
  /** Block at the feet cell. */
  feetBlock: string | null;
  /** Block that would be the floor (one below the feet cell). */
  floorBlock: string | null;
  /** [feet, body, head] block names above the floor. */
  blocksAbove: string[];
}

const LIQUID_NAMES = new Set(["water", "lava", "flowing_water", "flowing_lava"]);

function isLiquidName(name: string | undefined): boolean {
  if (!name) return false;
  if (LIQUID_NAMES.has(name)) return true;
  return name.includes("lava") || name.includes("water");
}

/** Full standability verdict for a feet cell, with per-block diagnostics so
 * failures can name the exact obstruction ("target dirt, blocks above:
 * [air, leaves]") instead of a bare boolean. */
export function checkStandability(bot: Bot, cell: Vec3): StandabilityReport {
  const at = bot.blockAt(cell) as BlockLike | null;
  const below = bot.blockAt(cell.offset(0, -1, 0)) as BlockLike | null;
  const above1 = bot.blockAt(cell.offset(0, 1, 0)) as BlockLike | null;
  const above2 = bot.blockAt(cell.offset(0, 2, 0)) as BlockLike | null;
  const name = (b: BlockLike | null): string => b?.name ?? "?";
  const issues: StandabilityIssue[] = [];
  if (!at || !below || !above1 || !above2) {
    issues.push({ location: "feet", blockName: name(at), problem: "unloaded", y: cell.y });
  } else {
    if (at.boundingBox === "block") {
      issues.push({ location: "feet", blockName: at.name, problem: "solid", y: cell.y });
    } else if (isLiquidName(at.name)) {
      issues.push({ location: "feet", blockName: at.name, problem: "liquid", y: cell.y });
    }
    if (isLiquidName(below.name)) {
      issues.push({ location: "floor", blockName: below.name, problem: "liquid", y: cell.y - 1 });
    } else if (below.boundingBox !== "block") {
      issues.push({ location: "floor", blockName: below.name, problem: "not_solid", y: cell.y - 1 });
    }
    if (above1.boundingBox === "block") {
      issues.push({ location: "body", blockName: above1.name, problem: "solid", y: cell.y + 1 });
    } else if (isLiquidName(above1.name)) {
      issues.push({ location: "body", blockName: above1.name, problem: "liquid", y: cell.y + 1 });
    }
    if (above2.boundingBox === "block") {
      issues.push({ location: "head", blockName: above2.name, problem: "solid", y: cell.y + 2 });
    }
  }
  return {
    standable: issues.length === 0,
    issues,
    feetBlock: name(at),
    floorBlock: name(below),
    blocksAbove: [name(at), name(above1), name(above2)]
  };
}

function describeStandabilityIssues(issues: StandabilityIssue[]): string {
  if (issues.length === 0) return "no issues";
  return issues.map((i) => `${i.location} ${i.problem} (${i.blockName} at y=${i.y})`).join("; ");
}

// Vertical scan window for walk_to_surface: the full overworld build range
// (1.18+). Columns are read top-down; the first solid-or-liquid block defines
// the surface. blockAt() on a loaded chunk is an in-memory lookup, so a full
// column scan is cheap.
const WORLD_TOP_Y = 319;
const WORLD_BOTTOM_Y = -64;
// How far walk_to_surface spirals out from the requested column when the
// requested surface cell itself is not standable (water, lava, canopy).
const SURFACE_SEARCH_RADIUS = 12;
// walk_to_surface loop guards: total hops and consecutive no-progress hops.
const SURFACE_MAX_HOPS = 64;
/** Mineflayer's canDigBlock reach: eye-to-block-center distance in blocks. */
const MINE_REACH_BLOCKS = 5.1;
const SURFACE_MAX_NO_PROGRESS_HOPS = 3;
// When the requested column is in unloaded chunks, advance this many blocks
// per intermediate hop (well inside the loaded area; the scan repeats after
// each hop as new terrain streams in).
const INTERMEDIATE_HOP_BLOCKS = 64;

export interface SurfaceBlockInfo {
  name: string;
  type: number;
  y: number;
}

export interface SurfaceColumnResult {
  status: "standable" | "liquid" | "obstructed" | "no_ground" | "unloaded";
  surface: SurfaceBlockInfo | null;
  /** Feet cell standing on the surface block (status "standable" only). */
  cell: Vec3 | null;
  report: StandabilityReport | null;
}

/** Scan one column from the sky down: the first solid or liquid block is the
 * surface. Liquids are reported as such (not standable); solids get a full
 * standability check of the cell above them. */
function scanSurfaceColumn(bot: Bot, x: number, z: number): SurfaceColumnResult {
  for (let y = WORLD_TOP_Y; y > WORLD_BOTTOM_Y; y--) {
    const block = bot.blockAt(new Vec3(x, y, z)) as BlockLike | null;
    if (!block) {
      // Column not loaded (outside view distance) or outside the world.
      return { status: "unloaded", surface: null, cell: null, report: null };
    }
    const solid = block.boundingBox === "block";
    const liquid = isLiquidName(block.name);
    if (!solid && !liquid) continue; // torches, grass, signs, snow layers...
    const surface: SurfaceBlockInfo = { name: block.name, type: block.type, y };
    if (liquid) {
      return { status: "liquid", surface, cell: null, report: null };
    }
    const cell = new Vec3(x, y + 1, z);
    const report = checkStandability(bot, cell);
    if (report.standable) {
      return { status: "standable", surface, cell, report };
    }
    return { status: "obstructed", surface, cell, report };
  }
  return { status: "no_ground", surface: null, cell: null, report: null };
}

/** Offsets ordered as expanding square rings (Chebyshev radius), each ring
 * sorted by Euclidean distance — a spiral outward from (0, 0). */
function spiralOffsets(maxRadius: number): Array<{ dx: number; dz: number; ring: number }> {
  const offsets: Array<{ dx: number; dz: number; ring: number }> = [];
  for (let ring = 0; ring <= maxRadius; ring++) {
    const ringCells: Array<{ dx: number; dz: number; ring: number }> = [];
    for (let dx = -ring; dx <= ring; dx++) {
      for (let dz = -ring; dz <= ring; dz++) {
        if (Math.max(Math.abs(dx), Math.abs(dz)) !== ring) continue;
        ringCells.push({ dx, dz, ring });
      }
    }
    ringCells.sort((a, b) => (a.dx * a.dx + a.dz * a.dz) - (b.dx * b.dx + b.dz * b.dz));
    offsets.push(...ringCells);
  }
  return offsets;
}

export interface SurfaceSearchStats {
  sampled: number;
  standable: number;
  /** surface-block name -> {count, type} for liquid columns (water/lava). */
  liquids: Record<string, { count: number; type: number }>;
  /** first-obstruction name -> count for obstructed columns. */
  obstructions: Record<string, { count: number; type: number }>;
  unloaded: number;
  noGround: number;
}

export interface SurfaceTargetResult {
  cell: Vec3 | null;
  surface: SurfaceBlockInfo;
  report: StandabilityReport | null;
  /** Chebyshev ring (blocks) at which the standable column was found. */
  ring: number;
  stats: SurfaceSearchStats;
  nearestFailure: SurfaceColumnResult | null;
  nearestFailureRing: number;
}

/** Find the standable surface column nearest to (x, z): the exact column
 * first, then a spiral outward up to maxRadius. Always returns full column
 * statistics for failure reporting. */
function findSurfaceTarget(bot: Bot, x: number, z: number, maxRadius: number): SurfaceTargetResult {
  const stats: SurfaceSearchStats = {
    sampled: 0,
    standable: 0,
    liquids: {},
    obstructions: {},
    unloaded: 0,
    noGround: 0
  };
  let nearestFailure: SurfaceColumnResult | null = null;
  let nearestFailureRing = Number.POSITIVE_INFINITY;
  const bump = (record: Record<string, { count: number; type: number }>, name: string, type: number): void => {
    const entry = record[name] ?? { count: 0, type };
    entry.count += 1;
    record[name] = entry;
  };
  for (const { dx, dz, ring } of spiralOffsets(maxRadius)) {
    const result = scanSurfaceColumn(bot, x + dx, z + dz);
    stats.sampled += 1;
    if (result.status === "standable") {
      stats.standable += 1;
      return {
        cell: result.cell,
        surface: result.surface!,
        report: result.report,
        ring,
        stats,
        nearestFailure,
        nearestFailureRing
      };
    }
    if (result.status === "liquid" && result.surface) {
      bump(stats.liquids, result.surface.name, result.surface.type);
    } else if (result.status === "obstructed") {
      const cause = result.report?.issues[0]?.blockName ?? result.surface?.name ?? "unknown";
      bump(stats.obstructions, cause, result.surface?.type ?? -1);
    } else if (result.status === "unloaded") {
      stats.unloaded += 1;
    } else if (result.status === "no_ground") {
      stats.noGround += 1;
    }
    if (ring < nearestFailureRing) {
      nearestFailure = result;
      nearestFailureRing = ring;
    }
  }
  // No standable column anywhere in the spiral; surface fields describe the
  // requested column itself when it was scannable.
  const requestedColumn = nearestFailureRing === 0 ? nearestFailure : null;
  return {
    cell: null,
    surface: requestedColumn?.surface ?? nearestFailure?.surface ?? { name: "unknown", type: -1, y: 0 },
    report: requestedColumn?.report ?? null,
    ring: -1,
    stats,
    nearestFailure,
    nearestFailureRing
  };
}

/** Render the walk_to_surface "nowhere to stand" failure with everything the
 * scan learned: the most-hit obstruction, per-block counts, and a hint. */
function describeSurfaceFailure(requested: { x: number; z: number }, stats: SurfaceSearchStats): string {
  const liquidEntries = Object.entries(stats.liquids).sort((a, b) => b[1].count - a[1].count);
  const obstructionEntries = Object.entries(stats.obstructions).sort((a, b) => b[1].count - a[1].count);
  const parts: string[] = [];
  if (liquidEntries.length > 0) {
    parts.push(`liquid columns: ${liquidEntries.map(([name, v]) => `${name}(${v.type}) x${v.count}`).join(", ")}`);
  }
  if (obstructionEntries.length > 0) {
    parts.push(`obstructed columns: ${obstructionEntries.map(([name, v]) => `${name}(${v.type}) x${v.count}`).join(", ")}`);
  }
  if (stats.unloaded > 0) {
    parts.push(`unloaded columns: ${stats.unloaded}`);
  }
  if (stats.noGround > 0) {
    parts.push(`empty columns: ${stats.noGround}`);
  }
  const mostHit = liquidEntries[0] ?? obstructionEntries[0];
  let hint = "";
  if (mostHit && (mostHit[0].includes("water") || mostHit[0].includes("lava"))) {
    hint = " the area looks like open liquid — pick a target on land, or approach the shore from another direction.";
  } else if (obstructionEntries.length > 0 && obstructionEntries.some(([name]) => name.includes("leaves") || name.includes("log"))) {
    hint = " dense canopy — walk to the trunk with walk_to_visible and mine/pillar up through the leaves.";
  } else if (stats.unloaded > 0) {
    hint = " some columns are not loaded — walk closer with walk_to_surface toward an intermediate point first.";
  }
  return `no standable block found within ${SURFACE_SEARCH_RADIUS} blocks of (${requested.x}, ${requested.z}). sampled ${stats.sampled} columns: ${parts.join("; ") || "no surface data"}. most hit block: ${mostHit ? `${mostHit[0]}(${mostHit[1].type})` : "unknown"}.${hint}`;
}

/** Ravine/cliff heuristic from a navigation report: many more drops than
 * ascents along the tried route. */
function ravineHint(navigation: NavigationReport | undefined): string {
  if (!navigation || navigation.drops < 6 || navigation.drops <= navigation.ascents * 2) return "";
  return `warning: significant drop between here and the target on tried paths (${navigation.drops} drops vs ${navigation.ascents} ascents) — maybe a ravine or cliff. `;
}

/**
 * Scan the straight line from a failed path's closest approach to the target
 * (2D, at the approach's feet/head level) and name the first solid block in
 * the way — the concrete reason a walk gave up. Door/gate blocks get an
 * actionable "open it" hint.
 */
function blockerHint(bot: Bot, closest: Vec3, target: Vector3): string {
  const dx = target.x - closest.x;
  const dz = target.z - closest.z;
  const length = Math.hypot(dx, dz);
  if (length < 1) return "";
  const steps = Math.max(1, Math.ceil(length * 2)); // sample every half block
  for (let i = 1; i <= steps; i += 1) {
    const t = i / steps;
    const x = Math.floor(closest.x + dx * t);
    const z = Math.floor(closest.z + dz * t);
    if (x === Math.floor(closest.x) && z === Math.floor(closest.z)) continue;
    for (const y of [Math.floor(closest.y), Math.floor(closest.y) + 1]) {
      const block = bot.blockAt(new Vec3(x, y, z));
      if (!block || block.name === "air" || block.boundingBox !== "block") continue;
      const isDoorish = block.name.endsWith("_door") || block.name.endsWith("_gate") || block.name.endsWith("_trapdoor");
      const hint = isDoorish
        ? ` — door/gate in the way; open it manually with use_block on (${x}, ${y}, ${z}) and retry the walk`
        : "";
      return `path blocked by ${block.name} at (${x}, ${y}, ${z})${hint}. `;
    }
  }
  return "";
}

/** Clamp a goal into a navigation region (with a small margin so the
 * pathfinder has room around the clamped point). */
function clampToRegionXZ(p: Vec3, region: NavigationRegion): Vec3 {
  const margin = 4;
  return new Vec3(
    Math.min(Math.max(p.x, region.minX + margin), region.maxX - margin),
    p.y,
    Math.min(Math.max(p.z, region.minZ + margin), region.maxZ - margin)
  );
}

function round1(value: number): number {
  return Math.round(value * 10) / 10;
}

const HORIZON_CARDINALS: Record<number, string> = {
  0: "N", 45: "NE", 90: "E", 135: "SE", 180: "S", 225: "SW", 270: "W", 315: "NW"
};

// Blocks whose surface sightline is worth calling out even when the model
// only skims the table: wood, village tells, ores, farming, and hazards.
const NOTABLE_HORIZON_PATTERNS: RegExp[] = [
  /_log$/,
  /_planks$/,
  /^stripped_/,
  /^cobblestone/,
  /^chest/,
  /_ore$/,
  /^hay_bale$/,
  /^dirt_path$/,
  /^wheat$/,
  /^carrots$/,
  /^potatoes$/,
  /^water/,
  /^lava/,
  /_bed$/,
  /^barrel$/,
  /^composter$/,
  /^crafting_table$/,
  /^furnace$/,
  /^blast_furnace$/,
  /^campfire$/,
  /^bell$/,
  /^lantern$/,
  /^bookshelf$/,
  /^emerald_block$/,
  /^diamond_block$/,
  /^gold_block$/,
  /^iron_block$/,
  /^beacon$/,
  /^obsidian$/,
  /^netherrack$/,
  /^spawner$/,
  /^rail$/,
  /^torch$/,
  /^soul_sand$/,
  /^moss_block$/
];

function isNotableHorizonBlock(name: string): boolean {
  return NOTABLE_HORIZON_PATTERNS.some((pattern) => pattern.test(name));
}

function headingLabel(heading: number): string {
  const cardinal = HORIZON_CARDINALS[heading];
  const degrees = heading.toString().padStart(3, "0");
  return cardinal ? `${degrees} ${cardinal}` : degrees;
}

function describeHorizonScan(
  eye: Vec3,
  range: number,
  results: Array<{ heading: number; pitch: number; hit: { blockName: string; position: Vector3; distance: number } | null }>
): string {
  const byHeading = new Map<number, Array<{ pitch: number; hit: { blockName: string; position: Vector3; distance: number } | null }>>();
  for (const entry of results) {
    const list = byHeading.get(entry.heading) ?? [];
    list.push({ pitch: entry.pitch, hit: entry.hit });
    byHeading.set(entry.heading, list);
  }
  const rows: string[] = [];
  for (const [heading, entries] of [...byHeading.entries()].sort((a, b) => a[0] - b[0])) {
    // Order the row as +15 (sky) / 0 (horizon) / -15 (ground).
    const cells = [...entries]
      .sort((a, b) => b.pitch - a.pitch)
      .map((entry) => (entry.hit ? `${entry.hit.blockName}@${entry.hit.distance}` : "sky"));
    rows.push(`${headingLabel(heading)}: ${cells.join(" | ")}`);
  }
  const notable = notableHorizonHits(results);
  const notableLine = notable.length > 0
    ? ` notable: ${notable.map((n) => `${n.hit.blockName}@${n.hit.distance} at ${headingLabel(n.heading)} (${n.hit.position.x}, ${n.hit.position.y}, ${n.hit.position.z})`).join("; ")}`
    : "";
  return `horizon scan from (${round1(eye.x)}, ${round1(eye.y)}, ${round1(eye.z)}), range ${range} blocks, columns are pitch +15 (sky) | 0 (horizon) | -15 (ground), distances in blocks:\n${rows.join("\n")}.${notableLine} tip: aim with rotate(yaw_degrees=...) then minecraft_raytrace or walk_to_surface(x, z) to travel to anything listed here.`;
}

function notableHorizonHits(
  results: Array<{ heading: number; pitch: number; hit: { blockName: string; position: Vector3; distance: number } | null }>
): Array<{ heading: number; hit: { blockName: string; position: Vector3; distance: number } }> {
  const notable = results
    .filter((entry) => entry.hit && isNotableHorizonBlock(entry.hit.blockName))
    .map((entry) => ({ heading: entry.heading, hit: entry.hit! }))
    .sort((a, b) => a.hit.distance - b.hit.distance);
  // Keep the nearest hit per (blockName, heading) so a forest row does not
  // flood the list — the nearest visible instance is the actionable one.
  const seen = new Set<string>();
  const deduped = [];
  for (const entry of notable) {
    const key = `${entry.hit.blockName}@${Math.round(entry.heading / 15) * 15}`;
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(entry);
  }
  return deduped;
}

/** Fold a hop log into a pseudo navigation report for ravineHint. */
function summarizeHopLog(hops: Array<{ ascents: number; drops: number }> | undefined): NavigationReport | undefined {
  if (!hops || hops.length === 0) return undefined;
  let ascents = 0;
  let drops = 0;
  for (const hop of hops) {
    ascents += hop.ascents;
    drops += hop.drops;
  }
  return { pathStatus: "aggregated", pathNodes: hops.length, ascents, drops, stalled: false, diagnosis: "aggregated hop log" };
}

/** From the target, scan straight down (up to 64 blocks) for the first safe
 * standable cell, the classic "raytrace to ground" for air targets. Returns
 * the first candidate found from the target downward. */
function raytraceDownStandable(bot: Bot, target: Vector3): Vec3 | null {
  const x = Math.floor(target.x);
  const z = Math.floor(target.z);
  for (let y = Math.floor(target.y); y > Math.floor(target.y) - 64; y--) {
    const cell = new Vec3(x, y, z);
    if (isSafeStandable(bot, cell)) return cell;
  }
  return null;
}

function fmtVec(v: Vector3): string {
  return `{x:${Math.round(v.x * 10) / 10},y:${Math.round(v.y * 10) / 10},z:${Math.round(v.z * 10) / 10}}`;
}

/**
 * A Movements instance restricted to plain walking: no digging, placing,
 * parkour, towers, or falls over one block — plus a spatial bound that
 * keeps the search inside the region. Doors are passable: the pathfinder
 * activates them itself (canOpenDoors) and they must be registered as
 * openable (upstream only auto-registers fence gates).
 */
function makeWalkMovements(bot: Bot, region: NavigationRegion): InstanceType<typeof Movements> {
  const movements = new Movements(bot);
  movements.canDig = false;
  movements.allowParkour = false;
  movements.allow1by1towers = false;
  movements.scafoldingBlocks = [];
  movements.canOpenDoors = false; // upstream's useOne door-clicking loops ("Causes issues") — we open doors ourselves in gotoNear
  for (const block of bot.registry.blocksArray) {
    if (block.name.endsWith("_door") && block.name !== "iron_door") {
      movements.openable.add(block.id);
    }
  }
  // Doors must be PASSABLE in the search (upstream's getMoveForward only
  // exempts the door's LOWER half; the upper half sits in the head cell and
  // safeOrBreak would return 100 with canDig=false). Patch safeOrBreak so
  // openable blocks count as safe: the walk layer opens them before passing.
  const originalSafeOrBreak = movements.safeOrBreak.bind(movements) as unknown as
    (block: BlockLike, toBreak: unknown[]) => number;
  (movements as unknown as {
    safeOrBreak: (block: BlockLike, toBreak: unknown[]) => number;
  }).safeOrBreak = (block, toBreak) => {
    if (block && movements.openable.has(block.type)) {
      return originalSafeOrBreak(
        { ...block, safe: true, physical: false, boundingBox: "empty" } as unknown as BlockLike,
        toBreak
      );
    }
    return originalSafeOrBreak(block, toBreak);
  };
  movements.maxDropDown = 1;
  movements.infiniteLiquidDropdownDistance = false;
  movements.allowSprinting = true;
  // Moves that touch a block outside the region cost >= 100 and the pathfinder
  // prunes them, so the search can never leave the box.
  const bound = (block: unknown): number => {
    const pos = (block as { position?: { x: number; z: number } })?.position;
    if (!pos) return 0;
    return pos.x < region.minX || pos.x > region.maxX || pos.z < region.minZ || pos.z > region.maxZ ? 100 : 0;
  };
  movements.exclusionAreasStep.push(bound);
  movements.exclusionAreasBreak.push(bound);
  movements.exclusionAreasPlace.push(bound);
  return movements;
}

interface GotoOptions {
  /** A* compute budget override (ms); defaults to the pathfinder's thinkTimeout. */
  searchBudgetMs?: number;
  /** "xz" (GoalNearXZ, default) or "3d" (GoalNear) for exact 3D targets. */
  goalMode?: "xz" | "3d";
}

/** Blocks whose right-click toggles passage. Iron doors/gates need redstone. */
function isHandOpenableDoor(name: string): boolean {
  if (name === "iron_door" || name === "iron_trapdoor") return false;
  return name.endsWith("_door") || name.endsWith("_gate") || name.endsWith("_trapdoor");
}

function doorIsOpen(bot: Bot, position: Vec3): boolean {
  const block = bot.blockAt(position) as (BlockLike & { _properties?: { open?: boolean } }) | null;
  return block?._properties?.open === true;
}

/** The closed door/gate/trapdoor nearest the bot's feet (search box 5x3x5). */
function findNearbyClosedDoor(bot: Bot): BlockLike | undefined {
  const feet = bot.entity.position.floored();
  let best: { block: BlockLike; dist: number } | undefined;
  for (let dx = -2; dx <= 2; dx += 1) {
    for (let dz = -2; dz <= 2; dz += 1) {
      for (const dy of [0, 1, -1]) {
        const position = new Vec3(feet.x + dx, feet.y + dy, feet.z + dz);
        const block = bot.blockAt(position) as (BlockLike & { _properties?: { open?: boolean } }) | null;
        if (!block || !isHandOpenableDoor(block.name)) continue;
        if (block._properties?.open === true) continue; // already open
        const dist = position.distanceTo(bot.entity.position);
        if (!best || dist < best.dist) best = { block, dist };
      }
    }
  }
  return best?.block;
}

/** Right-click the block and wait until the world reports it open. */
async function openDoorAndWait(bot: Bot, door: BlockLike): Promise<boolean> {
  const activator = (bot as unknown as {
    activateBlock(block: unknown): Promise<void>;
  }).activateBlock;
  if (typeof activator !== "function") return false;
  try {
    await activator(door);
  } catch {
    return false;
  }
  const deadline = Date.now() + 1500;
  while (Date.now() < deadline) {
    if (doorIsOpen(bot, door.position)) return true;
    await new Promise<void>((resolve) => setTimeout(resolve, 100));
  }
  return false;
}

/**
 * Walk near a target, opening doors/gates that stall the way. The underlying
 * walk treats doors as passable (see makeWalkMovements) but cannot open them,
 * so a closed door makes the walk stall within NO_PROGRESS_TIMEOUT_MS; here we
 * detect that, open the culprit, and retry the walk. Each retry makes progress
 * up to the next door, so a hallway of doors costs one retry per door.
 */
async function gotoNear(
  bot: Bot,
  target: Vector3,
  tolerance: number,
  region: NavigationRegion,
  signal?: AbortSignal,
  opts: GotoOptions = {},
  wlog: (message: string) => void = () => undefined
): Promise<NavigationReport> {
  const MAX_DOOR_RETRIES = 8;
  let lastError: unknown;
  for (let attempt = 0; attempt <= MAX_DOOR_RETRIES; attempt += 1) {
    try {
      return await gotoNearOnce(bot, target, tolerance, region, signal, opts, wlog);
    } catch (error) {
      lastError = error;
      const stalled = (error instanceof NavigationFailure && error.report.stalled)
        || (error as { name?: string })?.name === "PathStopped";
      if (!stalled || signal?.aborted) throw error;
      const door = findNearbyClosedDoor(bot);
      wlog(`walk stalled (attempt ${attempt + 1}); nearby closed door: ${door ? `${door.name} at ${fmtVec(door.position)}` : "none"}`);
      if (!door) throw error;
      const opened = await openDoorAndWait(bot, door);
      wlog(`door open attempt on ${door.name} at ${fmtVec(door.position)}: ${opened ? "opened, retrying walk" : "failed"}`);
      if (!opened) throw error;
      // Door opened — retry the walk from the new state.
    }
  }
  throw lastError;
}

async function gotoNearOnce(
  bot: Bot,
  target: Vector3,
  tolerance: number,
  region: NavigationRegion,
  signal?: AbortSignal,
  opts: GotoOptions = {},
  wlog: (message: string) => void = () => undefined
): Promise<NavigationReport> {
  const pathfinderBot = bot as Bot & {
    pathfinder?: {
      setMovements(movements: InstanceType<typeof Movements>): void;
      setGoal(goal: PathfinderGoal | null, dynamic?: boolean): void;
      stop(): void;
      thinkTimeout?: number;
      getPathFromTo(
        movements: InstanceType<typeof Movements>,
        startPos: Vec3,
        goal: PathfinderGoal | null,
        options?: { timeout?: number }
      ): Generator<{ result: { status: string; path: PathfinderMove[]; visitedNodes?: number } }>;
    };
  };
  if (!pathfinderBot.pathfinder) {
    throw new Error("mineflayer-pathfinder is not loaded.");
  }

  const start = vector(bot.entity.position);
  if (distXZ(start, target) <= tolerance) {
    return { pathStatus: "success", pathNodes: 0, ascents: 0, drops: 0, stalled: false, diagnosis: "already within tolerance" };
  }

  let update: PathfinderUpdate = { status: "searching", path: [] };
  let stallReason = "The path was stopped before it could be completed.";

  const bad = (name: string, message: string, report?: NavigationReport): Error => {
    if (report) {
      // NavigationFailure carries the report (closest approach, route stats)
      // while keeping the conventional name so navigationReason() classifies it.
      const failure = new NavigationFailure(message, report);
      (failure as Error & { name: string }).name = name;
      return failure;
    }
    const err = new Error(message);
    (err as Error & { name: string }).name = name;
    return err;
  };

  // Install the restricted movements BEFORE attaching listeners / searching: a
  // leftover stop flag from a previous aborted walk is consumed by the library
  // on setMovements and its path_stop event would otherwise race our handlers.
  const movements = makeWalkMovements(bot, region);
  pathfinderBot.pathfinder.setMovements(movements);

  // GoalNearXZ: aim at the horizontal target and let the pathfinder choose
  // whichever standable Y is reachable (the caller already validated that a
  // standable cell exists nearby). GoalNear (3d) pins the vertical too, for
  // walk_to_exact.
  const goal = opts.goalMode === "3d"
    ? new goals.GoalNear(target.x, target.y, target.z, tolerance)
    : new goals.GoalNearXZ(target.x, target.z, tolerance);

  // Phase 1 — resolve the search to a verdict WITHOUT moving. Mineflayer's
  // incremental pathfinder can start walking partial paths while the search is
  // still running, which used to displace the bot several blocks whenever a
  // search ended in noPath. By settling the search first and only handing the
  // goal to the walker once a path is confirmed, a noPath/timeout verdict now
  // leaves the bot exactly where it started.
  const searchBudget = opts.searchBudgetMs ?? pathfinderBot.pathfinder.thinkTimeout ?? 1000;
  const searchResult = await settleSearch(pathfinderBot, movements, goal, searchBudget, signal);
  wlog(`search verdict=${searchResult.status} nodes=${searchResult.path.length} visited=${searchResult.visitedNodes ?? "?"} budget=${searchBudget}ms`);
  if (searchResult.status === "noPath" || searchResult.status === "timeout") {
    // The A* "bestNode" path is the closest standable position the search
    // actually reached — reconstruct it for the failure report so the caller
    // can suggest a valid walk_to_exact target.
    const closest = searchResult.path.length > 0
      ? vector(searchResult.path[searchResult.path.length - 1])
      : start;
    const remaining = Math.hypot(closest.x - target.x, closest.y - target.y, closest.z - target.z);
    const partial = summarizeNavigation({ status: searchResult.status, path: searchResult.path }, start, target, false);
    const report: NavigationReport = {
      ...partial,
      closestApproach: closest,
      remainingDistance: round1(remaining)
    };
    const ravine = ravineHint(report).trim();
    const blocker = blockerHint(bot, new Vec3(closest.x, closest.y, closest.z), target).trim();
    throw bad(
      searchResult.status === "noPath" ? "NoPath" : "Timeout",
      `${searchResult.status === "noPath" ? "no path found" : "path search timed out"}. closest encountered standable position: (${round1(closest.x)}, ${round1(closest.y)}, ${round1(closest.z)}). distance to target (3d): ${round1(remaining)} blocks — a valid walk_to_exact target. route so far: +${partial.ascents} up / -${partial.drops} down over ${searchResult.path.length} nodes (${partial.pathNodes} visited).${blocker ? " " + blocker : ""}${ravine ? " " + ravine : ""}`,
      report
    );
  }
  update = { status: searchResult.status, path: searchResult.path ?? [] };
  (update as PathfinderUpdate & { visitedNodes?: number }).visitedNodes = searchResult.visitedNodes;

  // Phase 2 — feed the confirmed (reachable) goal to the library walker.
  // Static goals make the pathfinder emit goal_reached when it arrives.
  pathfinderBot.pathfinder.setGoal(goal, false);

  return await new Promise<NavigationReport>((resolve, reject) => {
    let settled = false;
    let stalled = false;
    let lastPosition = bot.entity.position.clone();
    let lastMovedAt = Date.now();
    let backstop: ReturnType<typeof setInterval> | undefined;

    const report = (): NavigationReport => summarizeNavigation(update, start, target, stalled);


    const onReached = (): void => finish(null);
    const onUpdate = (value: PathfinderUpdate): void => {
      update = value;
      wlog(`path_update status=${value.status} nodes=${value.path.length}`);
      if (value.status === "noPath") {
        finish(bad("NoPath", "No walkable path to the target within the search region: the way is blocked or the target is unreachable on foot."));
      } else if (value.status === "timeout") {
        finish(bad("Timeout", "Pathfinding timed out before finding a route; the target may be too complex to reach on foot. Try moving closer."));
      }
    };
    const onChanged = (changed: unknown): void => {
      if (changed !== goal) {
        finish(bad("GoalChanged", "The navigation goal was changed before it could be completed."));
      }
    };
    const onStopped = (): void => finish(bad("PathStopped", stallReason));

    const onAbort = (): void => {
      stalled = true;
      stallReason = "Navigation was stopped: command timeout or cancel fired mid-walk.";
      finish(bad("PathStopped", stallReason));
    };

    const detach = (): void => {
      if (backstop) clearInterval(backstop);
      bot.removeListener("goal_reached", onReached);
      bot.removeListener("path_update", onUpdate);
      bot.removeListener("goal_updated", onChanged);
      bot.removeListener("path_stop", onStopped);
      if (signal) signal.removeEventListener("abort", onAbort);
    };

    function finish(err: Error | null): void {
      if (settled) return;
      settled = true;
      detach();
      // Stop cleanly: clearing the goal resets the path and control states
      // without setting the library's sticky stop flag (pathfinder.stop()
      // would poison the next walk).
      try {
        pathfinderBot.pathfinder?.setGoal(null as unknown as PathfinderGoal);
      } catch {
        // already stopped
      }
      setTimeout(() => (err ? reject(err) : resolve(report())), 0);
    }

    bot.on("goal_reached", onReached);
    bot.on("path_update", onUpdate);
    bot.on("goal_updated", onChanged);
    bot.on("path_stop", onStopped);
    if (signal) {
      if (signal.aborted) onAbort();
      else signal.addEventListener("abort", onAbort, { once: true });
    }

    // Backstop: normal completion is driven by the library's own events above.
    // This only settles the cases where the library went silent: the bot
    // arrived (success) or stopped moving forever (stuck walk).
    backstop = setInterval(() => {
      const position = bot.entity.position;
      if (distXZ(position, target) <= tolerance) {
        wlog(`backstop: within tolerance of ${fmtVec(target)} — success`);
        finish(null);
        return;
      }
      const moved = position.distanceTo(lastPosition);
      if (moved >= MIN_PROGRESS_DISTANCE) {
        lastPosition = position.clone();
        lastMovedAt = Date.now();
      } else if (Date.now() - lastMovedAt >= NO_PROGRESS_TIMEOUT_MS) {
        // Fires whether or not the walk ever moved: a walk that never starts
        // moving (blocked immediately, e.g. by a closed door) must also fail
        // fast instead of hanging until the command timeout.
        stalled = true;
        stallReason = "The bot stopped moving during the walk; the path may have been invalidated (e.g. falling gravel or changed blocks) or blocked (e.g. a closed door). Try again or pick a closer target.";
        const feet = bot.entity.position.floored();
        const front = [new Vec3(1, 0, 0), new Vec3(-1, 0, 0), new Vec3(0, 0, 1), new Vec3(0, 0, -1)]
          .map((dir) => {
            const block = bot.blockAt(feet.offset(dir.x, 1, dir.z));
            const doorish = block && (block.name.endsWith("_door") || block.name.endsWith("_gate") || block.name.endsWith("_trapdoor"));
            return `${dir.x},${dir.z}:${block ? block.name : "?"}${doorish ? "(door)" : ""}`;
          })
          .join(" ");
        const below = bot.blockAt(feet.offset(0, -1, 0));
        wlog(`backstop: stalled at ${fmtVec(bot.entity.position)} with no movement for ${NO_PROGRESS_TIMEOUT_MS}ms; pos=${fmtVec(bot.entity.position)} target=${fmtVec(target)}; blocks around head level: ${front}; block under feet: ${below ? below.name : "?"}`);
        finish(bad("PathStopped", stallReason));
      }
    }, 250);
  });
}

async function settleSearch(
  pathfinderBot: Bot & {
    pathfinder?: {
      getPathFromTo(
        movements: InstanceType<typeof Movements>,
        startPos: Vec3,
        goal: PathfinderGoal | null,
        options?: { timeout?: number }
      ): Generator<{ result: { status: string; path: PathfinderMove[]; visitedNodes?: number } }>;
    };
  },
  movements: InstanceType<typeof Movements>,
  goal: PathfinderGoal,
  budgetMs: number,
  signal?: AbortSignal
): Promise<{ status: string; path: PathfinderMove[]; visitedNodes?: number }> {
  if (!pathfinderBot.pathfinder) {
    throw new Error("mineflayer-pathfinder is not loaded.");
  }
  const startPos = (pathfinderBot as unknown as { entity?: { position: Vec3 } }).entity?.position
    ?? new Vec3(0, 0, 0);
  const generator = pathfinderBot.pathfinder.getPathFromTo(movements, startPos, goal, { timeout: budgetMs });
  let result: { status: string; path: PathfinderMove[]; visitedNodes?: number } = { status: "searching", path: [] };
  for (;;) {
    if (signal?.aborted) {
      const err = new Error("Navigation was stopped: command timeout or cancel fired during pathfinding.");
      (err as Error & { name: string }).name = "PathStopped";
      throw err;
    }
    const step = generator.next();
    result = step.value.result;
    if (result.status !== "partial") break;
    // Let physics ticks / keepalives breathe between compute slices.
    await new Promise<void>((resolve) => setImmediate(resolve));
  }
  return result;
}

export function summarizeNavigation(
  update: PathfinderUpdate,
  start: Vector3,
  target: Vector3,
  stalled: boolean
): NavigationReport {
  let ascents = 0;
  let drops = 0;
  let previous: Vector3 = start;
  for (const move of update.path) {
    if (move.y > previous.y) ascents += 1;
    if (move.y < previous.y) drops += 1;
    previous = move;
  }
  const raw = update as PathfinderUpdate & { visitedNodes?: number };
  let diagnosis = "walk route found";
  if (stalled) {
    diagnosis = "the bot stopped moving during the walk; the path may have been invalidated or the terrain changed";
  } else if (update.status === "noPath") {
    diagnosis = "no walkable route; the target is blocked or unreachable on foot within the search region";
  } else if (update.status === "timeout") {
    diagnosis = "path search exhausted its budget; the target may be unreachable or the terrain too complex on foot";
  } else if (update.status !== "success" && update.status !== "partial") {
    diagnosis = `pathfinder ended with status ${update.status}`;
  }
  return {
    pathStatus: update.status,
    pathNodes: typeof raw.visitedNodes === "number" ? raw.visitedNodes : update.path.length,
    ascents,
    drops,
    stalled,
    diagnosis
  };
}

async function walkToBlockRange(bot: Bot, block: BlockLike): Promise<void> {
  await gotoNear(bot, vector(block.position), 2.0, defaultNavigationRegion(bot));
}

async function ensureRange(bot: Bot, block: BlockLike, walkIntoRange = true): Promise<CommandResult | { ok: true }> {
  if (inReach(bot, block)) {
    return { ok: true };
  }
  if (!walkIntoRange) {
    return {
      ok: false,
      reason: "target_out_of_range",
      message: "Target block is out of range.",
      data: { block: vector(block.position), blockName: block.name }
    };
  }
  try {
    await walkToBlockRange(bot, block);
  } catch (error) {
    return {
      ok: false,
      reason: navigationReason(error),
      message: `Could not walk into range: ${errorMessage(error)}`,
      data: {
        block: vector(block.position),
        blockName: block.name,
        navigation: error instanceof NavigationFailure ? error.report : undefined
      }
    };
  }
  if (!inReach(bot, block)) {
    return {
      ok: false,
      reason: "target_out_of_range",
      message: "Target block is out of range after walking.",
      data: { block: vector(block.position), blockName: block.name }
    };
  }
  return { ok: true };
}

const INTERACTABLE_NAMES = new Set([
  "lever", "chest", "trapped_chest", "ender_chest", "barrel",
  "furnace", "blast_furnace", "smoker", "crafting_table",
  "anvil", "chip_anvil", "damaged_anvil", "dispenser", "dropper", "hopper",
  "beacon", "note_block", "daylight_detector", "grindstone", "stonecutter",
  "cartography_table", "fletching_table", "smithing_table", "loom", "composter",
  "lectern", "brewing_stand", "enchanting_table", "jukebox", "respawn_anchor",
  "repeater", "comparator", "target", "bell"
]);

/** True for right-click/use interactable blocks: doors, gates, buttons, plates, beds, etc. */
function isInteractableName(name: string): boolean {
  if (INTERACTABLE_NAMES.has(name)) return true;
  return (
    /_door$/.test(name) ||
    /_fence_gate$/.test(name) ||
    /_trapdoor$/.test(name) ||
    /_button$/.test(name) ||
    /_pressure_plate$/.test(name) ||
    /_bed$/.test(name) ||
    /shulker_box$/.test(name)
  );
}

// Blocks this close to the player's eye are always reported even when the
// head ray fails (too near, or the view is partly obscured). This prevents
// the scan from repeatedly missing blocks a player would trivially see by
// turning around, while still blocking far-distance "x-ray" scanning.
const PROXIMITY_VISIBLE_BLOCKS = 4;
/**
 * True when a block is visible from the player's head (360 degrees, not
 * dependent on what the bot currently faces) or within PROXIMITY_VISIBLE_BLOCKS.
 */
function isVisibleOrNear(bot: Bot, block: Parameters<Bot["canSeeBlock"]>[0]): boolean {
  const eyeHeight = (bot.entity as typeof bot.entity & { eyeHeight?: number }).eyeHeight ?? 1.62;
  const eye = bot.entity.position.offset(0, eyeHeight, 0);
  if (block.position.distanceTo(eye) <= PROXIMITY_VISIBLE_BLOCKS) return true;
  return isVisibleFromHead(bot, block);
}

/**
 * Strike the target and report whether the server registered damage.
 * The entityHurt mineflayer event is authoritative; entity.health metadata is
 * unreliable on some versions, so it is only a fallback.
 */
async function strikeAndDetectHit(bot: Bot, targetState: EntityLike & { id: number }): Promise<boolean> {
  return await new Promise<boolean>((resolve) => {
    let settled = false;
    let timer: ReturnType<typeof setTimeout>;
    const onHurt = (entity: unknown): void => {
      if ((entity as { id?: number })?.id !== targetState.id) return;
      finish(true);
    };
    const finish = (hit: boolean): void => {
      if (settled) return;
      settled = true;
      bot.removeListener("entityHurt", onHurt);
      clearTimeout(timer);
      resolve(hit);
    };
    bot.on("entityHurt", onHurt);
    // Entity health is not populated in mineflayer on 1.19.4, so the only
    // reliable hit signal is the server's entityHurt event.
    timer = setTimeout(() => finish(false), 800);
    try {
      (bot as Bot & { attack(entity: unknown): void }).attack(targetState as never);
    } catch {
      finish(false);
    }
  });
}

function blockAt(bot: Bot, target: Vector3): BlockLike | null {
  return bot.blockAt(vec(target), false) as BlockLike | null;
}

function inReach(bot: Bot, block: BlockLike): boolean {
  const actionBot = bot as ActionBot;
  if (typeof actionBot.canDigBlock === "function" && actionBot.canDigBlock(block)) {
    return true;
  }
  const eyeHeight = (bot.entity as typeof bot.entity & { eyeHeight?: number }).eyeHeight ?? 1.62;
  const eye = bot.entity.position.offset(0, eyeHeight, 0);
  return eye.distanceTo(centerOf(block)) <= 5.1;
}

function radToDeg(radians: number): number {
  return radians * 180 / Math.PI;
}

function degToRad(degrees: number): number {
  return degrees * Math.PI / 180;
}

function normalizeYawDeg(degrees: number): number {
  return ((degrees % 360) + 360) % 360;
}

function clampPitchDeg(degrees: number): number {
  return Math.max(-89.5, Math.min(89.5, degrees));
}

function vec(value: Vector3): Vec3 {
  return new Vec3(value.x, value.y, value.z);
}

function vector(value: Vector3): Vector3 {
  return { x: value.x, y: value.y, z: value.z };
}

function centerOf(block: BlockLike): Vec3 {
  return block.position.offset(0.5, 0.5, 0.5);
}

function failed(reason: string, message: string, data: unknown): CommandResult {
  return { ok: false, reason, message, data };
}

function heldItemSnapshot(item: { name?: string; count?: number } | null | undefined): { name: string; count: number } | null {
  if (!item?.name || typeof item.count !== "number") {
    return null;
  }
  return { name: item.name, count: item.count };
}

function isPlaceableSolidBlock(bot: Bot, itemName: string): boolean {
  const registry = (bot as Bot & { registry?: { blocksByName?: Record<string, { boundingBox?: string }> } }).registry;
  const blockType = registry?.blocksByName?.[itemName];
  if (!blockType) {
    return false;
  }
  return blockType.boundingBox === "block";
}

function verifyPlacedHeldItem(
  bot: Bot,
  placedPosition: Vec3,
  heldBefore: { name: string; count: number }
): { verified: boolean; itemConsumed: boolean; placedBlockName: string | null } {
  const placedBlock = bot.blockAt(placedPosition);
  const heldAfter = heldItemSnapshot(bot.heldItem);
  return {
    verified: placedBlock?.name === heldBefore.name,
    itemConsumed: !heldAfter || heldAfter.name !== heldBefore.name || heldAfter.count < heldBefore.count,
    placedBlockName: placedBlock?.name ?? null
  };
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function pathfinderReason(error: unknown): string {
  const message = errorMessage(error).toLowerCase();
  if (message.includes("timeout")) {
    return "pathfinder_timed_out";
  }
  return "pathfinder_failed";
}

function navigationReason(error: unknown): string {
  if (error instanceof NavigationFailure && error.report.stalled) {
    return "pathfinder_stalled";
  }
  if (error instanceof NavigationFailure && error.report.pathStatus === "noPath") {
    return "pathfinder_no_path";
  }
  const name = error instanceof Error ? error.name : "";
  if (name === "NoPath") return "pathfinder_no_path";
  if (name === "Timeout") return "pathfinder_timed_out";
  return pathfinderReason(error);
}

/**
 * Detect the type of container window that opened after activating a block.
 * Returns the window type string or null if no window opened.
 *
 * bot.currentWindow.type values (Minecraft 1.21.x):
 *   "minecraft:crafting"  → crafting table (3x3 grid)
 *   "minecraft:furnace"   → furnace (smelting)
 *   "minecraft:inventory" → player inventory (2x2 crafting, rarely opened via activateBlock)
 */
function detectOpenedWindowType(bot: Bot): "crafting_table" | "furnace" | "chest" | null {
  const raw = bot as Bot & { currentWindow?: { type?: string | number } };
  if (!raw.currentWindow) return null;
  const typeStr = typeof raw.currentWindow.type === "string"
    ? raw.currentWindow.type
    : String(raw.currentWindow.type ?? "");
  if (typeStr === "minecraft:crafting") return "crafting_table";
  if (typeStr === "minecraft:furnace") return "furnace";
  // Generic item containers share the same deposit/withdraw machinery.
  if (typeStr.includes("chest") || typeStr.includes("barrel") || typeStr.includes("shulker") || typeStr.includes("hopper") || typeStr.includes("container")) {
    return "chest";
  }
  return null;
}

interface ContainerWindowLike {
  type?: string | number;
  inventoryStart: number;
  inventoryEnd: number;
  countRange?(start: number, end: number, itemType: number, metadata?: number): number;
  containerItems?(): Array<{ name: string; count: number; slot: number }>;
  deposit?(itemType: number, metadata: number, count: number): Promise<void>;
  withdraw?(itemType: number, metadata: number, count: number): Promise<void>;
}

function openedContainerWindow(bot: Bot): ContainerWindowLike | null {
  const window = (bot as Bot & { currentWindow?: ContainerWindowLike }).currentWindow;
  if (!window) return null;
  const typeStr = typeof window.type === "string" ? window.type : String(window.type ?? "");
  const isContainer = typeStr.includes("chest") || typeStr.includes("barrel") || typeStr.includes("shulker") || typeStr.includes("hopper") || typeStr.includes("container");
  return isContainer ? window : null;
}

function containerContents(window: ContainerWindowLike): Array<{ name: string; count: number; slot: number }> {
  if (typeof window.containerItems !== "function") return [];
  return window.containerItems().map((item) => ({ name: item.name, count: item.count, slot: item.slot }));
}

/** Aggregate items within a window slot range (used for glob matching). */
function windowItemsInRange(window: ContainerWindowLike, start: number, end: number): Array<{ name: string; count: number }> {
  const totals = new Map<string, number>();
  if (typeof window.countRange !== "function") return [];
  // Iterate the visible slots to discover which item names are present.
  const slots = (window as unknown as { slots?: Array<{ name?: string; count?: number } | null> }).slots ?? [];
  for (let slot = start; slot < Math.min(end, slots.length); slot++) {
    const item = slots[slot];
    if (item?.name) {
      totals.set(item.name, (totals.get(item.name) ?? 0) + (item.count ?? 1));
    }
  }
  return [...totals.entries()].map(([name, count]) => ({ name, count })).sort((a, b) => a.name.localeCompare(b.name));
}

/** Suggest close names for a failed pattern, e.g. 'logg' -> oak_log, spruce_log. */
function suggestFrom(candidates: string[], pattern: string): string {
  const suggestions = globSuggest(`*${pattern}*`, candidates, 10);
  return suggestions.length > 0 ? ` Did you mean: ${suggestions.join(", ")}? Patterns with * are allowed, e.g. '*log*' for any wood.` : " Patterns with * are allowed, e.g. '*log*' for any wood.";
}

function registryItemId(bot: Bot, itemName: string): number | undefined {
  return (bot as Bot & { registry?: { itemsByName?: Record<string, { id: number }> } }).registry?.itemsByName?.[itemName]?.id;
}

function digFaceFor(bot: Bot, block: BlockLike): Vec3 {
  const eyeHeight = (bot.entity as { eyeHeight?: number }).eyeHeight ?? 1.62;
  const dx = bot.entity.position.x - (block.position.x + 0.5);
  const dy = bot.entity.position.y + eyeHeight - (block.position.y + 0.5);
  const dz = bot.entity.position.z - (block.position.z + 0.5);
  const ax = Math.abs(dx);
  const ay = Math.abs(dy);
  const az = Math.abs(dz);
  if (ay >= ax && ay >= az) return new Vec3(0, dy >= 0 ? 1 : -1, 0);
  if (ax >= az) return new Vec3(dx >= 0 ? 1 : -1, 0, 0);
  return new Vec3(0, 0, dz >= 0 ? 1 : -1);
}
