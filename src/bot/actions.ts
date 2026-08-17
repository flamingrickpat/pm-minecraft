import type { Bot } from "mineflayer";
import pathfinderPackage from "mineflayer-pathfinder";
import { Vec3 } from "vec3";
import type { CommandResult } from "../commands/commandQueue.js";
import type { AttackEntityInput, FindBlockInput, JumpPlaceBlockInput, MineBlockInput, PlaceBlockInput, UseBlockInput, Vector3, WalkToInput } from "../commands/types.js";
import { isVisibleFromHead } from "../perception/visibility.js";

const { goals, Movements, pathfinder } = pathfinderPackage;
type PathfinderGoal = InstanceType<typeof goals.GoalNear>;
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
  walkTo(input: WalkToInput, signal?: AbortSignal): Promise<CommandResult>;
  findBlock(input: FindBlockInput): Promise<CommandResult>;
  findInteractables(input: { maxDistance: number }): Promise<CommandResult>;
  mineBlock(input: MineBlockInput): Promise<CommandResult>;
  placeBlock(input: PlaceBlockInput): Promise<CommandResult>;
  jumpPlaceBlock(input: JumpPlaceBlockInput): Promise<CommandResult>;
  pillarUp(): Promise<CommandResult>;
  useBlock(input: UseBlockInput): Promise<CommandResult>;
  attackEntity(input: AttackEntityInput): Promise<CommandResult>;
  inspectBlock(block: Vector3): Promise<CommandResult>;
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
    /** Absolute cap (in chunks) on walk_to's reach; a requested chunk_limit above this is rejected. */
    maxChunkLimit: number;
  } = {
    mineVisibilityIgnoreDistance: 3.0,
    maxChunkLimit: 8
  }
): PhysicalCommandActions {
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
    walkTo: async ({ target, tolerance, chunkLimit }, signal) => {
      const startPosition = bot.entity.position;
      // Already there? Return immediately without searching.
      if (distXZ(startPosition, target) <= tolerance) {
        return { ok: true, message: "Already within tolerance of target.", data: { status: "reached", position: vector(startPosition), target } };
      }
      const limit = Math.min(Math.max(1, Math.round(chunkLimit ?? DEFAULT_CHUNK_LIMIT)), options.maxChunkLimit);
      const region = navigationRegion(bot, limit);
      // Fail instantly if the target is outside the search region.
      if (
        target.x < region.minX || target.x > region.maxX ||
        target.z < region.minZ || target.z > region.maxZ
      ) {
        return {
          ok: false,
          reason: "target_too_far",
          message: `Target is outside the ${limit}-chunk walk search region (limit: ${limit} chunk(s)). Move closer or raise chunk_limit.`,
          data: { status: "too_far", position: vector(startPosition), target, chunkLimit: limit }
        };
      }
      // Fail instantly if there is no place to stand near the target.
      const standable = findStandableCell(bot, target);
      if (!standable) {
        return {
          ok: false,
          reason: "target_not_standable",
          message: "The target has no standable block nearby to walk to.",
          data: { status: "not_standable", position: vector(startPosition), target }
        };
      }
      try {
        const navigation = await gotoNear(bot, target, tolerance, region, signal);
        return { ok: true, message: "Reached target.", data: { status: "reached", position: vector(bot.entity.position), target, navigation } };
      } catch (error) {
        return {
          ok: false,
          reason: navigationReason(error),
          message: error instanceof Error ? error.message : String(error),
          data: {
            status: "failed",
            position: vector(bot.entity.position),
            target,
            navigation: error instanceof NavigationFailure ? error.report : undefined
          }
        };
      }
    },
    findBlock: async ({ blockName, maxDistance, requireVisible = true }) => {
      const registry = (bot as Bot & { registry?: { blocksByName?: Record<string, { id: number }> } }).registry;
      const blockId = registry?.blocksByName?.[blockName]?.id;
      if (typeof blockId !== "number") {
        return failed("unknown_block", `Unknown block name: ${blockName}`, { blockName });
      }
      const found = bot.findBlock({
        matching: blockId,
        maxDistance,
        useExtraInfo: requireVisible ? (block) => isVisibleFromHead(bot, block) : undefined
      });
      if (!found) {
        const visibility = requireVisible ? "head-ray-visible " : "";
        return failed("block_not_found", `No ${visibility}${blockName} found within ${maxDistance} loaded blocks.`, { blockName, maxDistance, requireVisible });
      }
      return {
        ok: true,
        message: `Found ${found.name}.`,
        data: {
          block: vector(found.position),
          blockName: found.name,
          displayName: found.displayName ?? null,
          distance: bot.entity.position.distanceTo(found.position)
        }
      };
    },
    findInteractables: async ({ maxDistance }) => {
      const range = Math.min(Math.max(4, maxDistance), 64);
      const finder = bot as Bot & { findBlocks?(options: Record<string, unknown>): Vec3[] };
      const positions = finder.findBlocks?.({
        matching: (block: unknown) => isInteractableName((block as BlockLike)?.name ?? ""),
        point: bot.entity.position,
        maxDistance: range,
        count: 64
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
        // in a 1-wide shaft the feet-level block directly ahead is not visible
        // from the head. Within the configured tunnel distance we skip the gate
        // so the bot can mine straight ahead (playtest finding 2c).
        const withinTunnelRange =
          bot.entity.position.distanceTo(visibleTarget.position) <=
          options.mineVisibilityIgnoreDistance;
        if (
          !isVisibleFromHead(bot, visibleTarget as Parameters<Bot["canSeeBlock"]>[0])
          && !withinTunnelRange
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
        const digPromise = (bot as ActionBot).dig(visibleTarget, true, "raycast").then(
          () => undefined,
          (error: unknown) => {
            digError = error;
          }
        );
        await Promise.race([
          digPromise,
          waitForBlockRemoved(bot, vec(target), 25_000)
        ]);
        const after = blockAt(bot, target);
        if (digError && after && after.name !== "air" && after.boundingBox !== "empty") {
          throw digError;
        }
        if (after && after.name !== "air" && after.boundingBox !== "empty") {
          return failed("dig_unverified", "Mineflayer returned without removing the target block.", {
            block: target,
            blockName: visibleTarget.name,
            resultBlockName: after.name
          });
        }

        // Walk to the drop location to collect the item, but only when the
        // drop is out of pickup range already — pathfinder calls are slow.
        const dropPos = centerOf(visibleTarget);
        if (bot.entity.position.distanceTo(dropPos) > 2.0) {
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
        
        return {
          ok: true,
          message: "Mined block.",
          data: {
            block: target,
            blockName: visibleTarget.name,
            resultBlockName: after?.name ?? null,
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
    attackEntity: async ({ entityId, walkIntoRange, renavigationCount = 3 }) => {
      const resolveTarget = (): EntityLike | null => {
        const entity = bot.entities?.[entityId] as EntityLike | undefined;
        return entity && entity !== bot.entity && entity.position ? entity : null;
      };

      for (let attempt = 0; ; attempt++) {
        const target = resolveTarget();
        if (!target) {
          return failed("entity_not_found", "The observed entity is no longer present.", { entityId, attempt });
        }
        const label = target.username ?? target.name ?? target.displayName ?? `entity ${entityId}`;
        const distance = bot.entity.position.distanceTo(target.position);
        if (distance <= ATTACK_RANGE) {
          const healthBefore = typeof target.health === "number" ? target.health : null;
          try {
            const eyeTarget = target.position.offset(0, 0.8, 0);
            await bot.lookAt(eyeTarget, false);
            syncTrackedToTarget(eyeTarget);
            await bot.attack(target);
            await new Promise(resolve => setTimeout(resolve, 400));
            const healthAfter = typeof target.health === "number" ? target.health : null;
            const hit = healthBefore !== null && healthAfter !== null && healthAfter < healthBefore;
            return {
              ok: true,
              message: hit ? `Hit ${label}.` : `Attacked ${label}.`,
              data: {
                entityId,
                name: label,
                kind: target.type ?? "unknown",
                hit,
                healthBefore,
                healthAfter: healthAfter ?? null,
                targetStillPresent: resolveTarget() !== null
              }
            };
          } catch (error) {
            return failed("attack_failed", `Mineflayer attack failed: ${errorMessage(error)}`, { entityId, name: label });
          }
        }
        // Out of range: walk to the entity's current position, then re-check.
        if (!walkIntoRange) {
          return failed("entity_out_of_range", `${label} is outside attack range.`, { entityId, distance, attempts: attempt });
        }
        if (attempt >= renavigationCount) {
          return failed("entity_out_of_range", `${label} moved or is out of range after ${attempt} walk(s). Give up and reposition.`, { entityId, distance, attempts: attempt });
        }
        try {
          await gotoNear(bot, vector(target.position), 2.0, defaultNavigationRegion(bot));
        } catch (error) {
          return failed("entity_unreachable", `Could not reach ${label}: ${errorMessage(error)}`, { entityId });
        }
      }
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

const DEFAULT_CHUNK_LIMIT = 3;
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
 * Find a cell the bot could stand in near the target, or null.
 * Walk_to refuses targets with no standable floor at all.
 */
function findStandableCell(bot: Bot, target: Vector3): Vec3 | null {
  const x0 = Math.floor(target.x);
  const z0 = Math.floor(target.z);
  const baseY = Math.floor(target.y);
  for (const y of [baseY, baseY + 1, baseY - 1]) {
    for (let dx = -2; dx <= 2; dx++) {
      for (let dz = -2; dz <= 2; dz++) {
        const cell = new Vec3(x0 + dx, y, z0 + dz);
        if (isStandable(bot, cell)) return cell;
      }
    }
  }
  return null;
}

function isStandable(bot: Bot, cell: Vec3): boolean {
  const at = bot.blockAt(cell);
  const below = bot.blockAt(cell.offset(0, -1, 0));
  if (!at || !below) return false;
  // Feet space must not be fully solid, and something solid must be under it.
  return at.boundingBox !== "block" && below.boundingBox === "block";
}

/**
 * A Movements instance restricted to plain walking: no digging, placing,
 * parkour, towers, doors, or falls over one block — plus a spatial bound that
 * keeps the search inside the region.
 */
function makeWalkMovements(bot: Bot, region: NavigationRegion): InstanceType<typeof Movements> {
  const movements = new Movements(bot);
  movements.canDig = false;
  movements.allowParkour = false;
  movements.allow1by1towers = false;
  movements.scafoldingBlocks = [];
  movements.canOpenDoors = false;
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

async function gotoNear(
  bot: Bot,
  target: Vector3,
  tolerance: number,
  region: NavigationRegion,
  signal?: AbortSignal
): Promise<NavigationReport> {
  const pathfinderBot = bot as Bot & {
    pathfinder?: {
      setMovements(movements: InstanceType<typeof Movements>): void;
      setGoal(goal: PathfinderGoal | null, dynamic?: boolean): void;
      stop(): void;
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

  // Install the restricted movements and a STATIC goal BEFORE attaching
  // listeners: a leftover stop flag from a previous aborted walk is consumed
  // by the library on setMovements/setGoal and its path_stop event would
  // otherwise race our handlers. Static goals make the library emit
  // goal_reached when the bot arrives (dynamic goals do not — that was the
  // original 30s hang).
  pathfinderBot.pathfinder.setMovements(makeWalkMovements(bot, region));
  // GoalNearXZ: aim at the horizontal target and let the pathfinder choose
  // whichever standable Y is reachable (the caller already validated that a
  // standable cell exists nearby).
  const goal = new goals.GoalNearXZ(target.x, target.z, tolerance);
  pathfinderBot.pathfinder.setGoal(goal, false);

  return await new Promise<NavigationReport>((resolve, reject) => {
    let settled = false;
    let stalled = false;
    let sawMovement = false;
    let lastPosition = bot.entity.position.clone();
    let lastMovedAt = Date.now();
    let backstop: ReturnType<typeof setInterval> | undefined;

    const bad = (name: string, message: string): Error => {
      const err = new Error(message);
      (err as Error & { name: string }).name = name;
      return err;
    };
    const report = (): NavigationReport => summarizeNavigation(update, start, target, stalled);

    const onReached = (): void => finish(null);
    const onUpdate = (value: PathfinderUpdate): void => {
      update = value;
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
        finish(null);
        return;
      }
      const moved = position.distanceTo(lastPosition);
      if (moved >= MIN_PROGRESS_DISTANCE) {
        lastPosition = position.clone();
        lastMovedAt = Date.now();
        sawMovement = true;
      } else if (sawMovement && Date.now() - lastMovedAt >= NO_PROGRESS_TIMEOUT_MS) {
        stalled = true;
        stallReason = "The bot stopped moving during the walk; the path may have been invalidated (e.g. falling gravel or changed blocks). Try again or pick a closer target.";
        finish(bad("PathStopped", stallReason));
      }
    }, 250);
  });
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

async function ensureRange(bot: Bot, block: BlockLike, walkIntoRange: boolean): Promise<CommandResult | { ok: true }> {
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
function detectOpenedWindowType(bot: Bot): "crafting_table" | "furnace" | null {
  const raw = bot as Bot & { currentWindow?: { type?: string | number } };
  if (!raw.currentWindow) return null;
  const typeStr = typeof raw.currentWindow.type === "string"
    ? raw.currentWindow.type
    : String(raw.currentWindow.type ?? "");
  if (typeStr === "minecraft:crafting") return "crafting_table";
  if (typeStr === "minecraft:furnace") return "furnace";
  return null;
}
