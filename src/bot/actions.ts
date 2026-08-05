import type { Bot } from "mineflayer";
import pathfinderPackage from "mineflayer-pathfinder";
import { Vec3 } from "vec3";
import type { CommandResult } from "../commands/commandQueue.js";
import type { FindBlockInput, JumpPlaceBlockInput, MineBlockInput, NavigationProfile, PlaceBlockInput, UseBlockInput, Vector3, WalkToInput } from "../commands/types.js";
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
  profile: NavigationProfile;
  pathStatus: string;
  pathNodes: number;
  ascents: number;
  drops: number;
  blocksToBreak: number;
  blocksToPlace: number;
  stalled: boolean;
  diagnosis: string;
}

class NavigationFailure extends Error {
  constructor(message: string, readonly report: NavigationReport) {
    super(message);
    this.name = "NavigationFailure";
  }
}

/**
 * Physical commands need real Mineflayer effects; execute explicit user actions at the bot boundary.
 *
 * @remarks
 * archetype: service-provider
 * owns: look, pathfinder walk, dig, place, block activation, and block inspection calls against one live bot.
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
  walkTo(input: WalkToInput): Promise<CommandResult>;
  findBlock(input: FindBlockInput): Promise<CommandResult>;
  mineBlock(input: MineBlockInput): Promise<CommandResult>;
  placeBlock(input: PlaceBlockInput): Promise<CommandResult>;
  jumpPlaceBlock(input: JumpPlaceBlockInput): Promise<CommandResult>;
  pillarUp(): Promise<CommandResult>;
  useBlock(input: UseBlockInput): Promise<CommandResult>;
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
    walkToMaxDistance: number;
  } = {
    mineVisibilityIgnoreDistance: 3.0,
    walkToMaxDistance: 512.0
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
    walkTo: async ({ target, tolerance, profile = "adaptive" }) => {
      // Cap a single route to one chunk so a failed call is cheap to
      // diagnose and long journeys are split into explicit hops.
      const startPosition = bot.entity.position;
      const horizontalDistance = Math.hypot(
        target.x - startPosition.x,
        target.z - startPosition.z
      );
      if (horizontalDistance > options.walkToMaxDistance) {
        return {
          ok: false,
          reason: "target_too_far",
          message: (
            `walk_to target is ${horizontalDistance.toFixed(1)} blocks away horizontally, ` +
            `exceeding the ${options.walkToMaxDistance}-block limit. Split the route into shorter hops ` +
            `(alignment is one chunk long).`
          ),
          data: {
            status: "too_far",
            position: vector(startPosition),
            target,
            horizontalDistance: Math.round(horizontalDistance * 10) / 10,
            maxDistance: options.walkToMaxDistance
          }
        };
      }
      try {
        const navigation = await gotoNear(bot, target, tolerance, profile);
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
        await (bot as ActionBot).dig(visibleTarget, true, "raycast");
        const after = blockAt(bot, target);

        // Walk to the drop location to collect the item, but only when the
        // drop is out of pickup range already — pathfinder calls are slow.
        const dropPos = centerOf(visibleTarget);
        if (bot.entity.position.distanceTo(dropPos) > 2.0) {
          try {
            await gotoNear(bot, dropPos, 1.5);
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
    inspectBlock: async (target) => {
      const block = blockAt(bot, target);
      if (!block) {
        return { ok: false, reason: "block_not_loaded", message: "Target block is not loaded.", data: { block: target } };
      }
      const heldItem = heldItemSnapshot(bot.heldItem);
      const canHarvestWithHeldItem = typeof block.canHarvest === "function"
        ? Boolean(block.canHarvest(bot.heldItem?.type ?? null))
        : null;
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

export function installPathfinder(bot: Bot): void {
  const current = bot as Bot & { pathfinder?: unknown; loadPlugin(plugin: (bot: Bot) => void): void };
  if (!current.pathfinder) {
    current.loadPlugin(pathfinder);
  }
  // Give the A* search a much larger total compute budget. The library default
  // (5000ms) is too small for complex mountain terrain and far goals, which is
  // what produced the "path search exhausted its computation budget" failures.
  const pf = (bot as unknown as { pathfinder?: { thinkTimeout: number; tickTimeout: number } }).pathfinder;
  if (pf) {
    pf.thinkTimeout = 40000;
    pf.tickTimeout = 40;
  }
}

async function gotoNear(
  bot: Bot,
  target: Vector3,
  tolerance: number,
  profile: NavigationProfile = "adaptive"
): Promise<NavigationReport> {
  const pathfinderBot = bot as Bot & {
    pathfinder?: {
      goto(goal: PathfinderGoal): Promise<void>;
      setMovements(movements: InstanceType<typeof Movements>): void;
      stop(): void;
      isMoving(): boolean;
    };
  };
  if (!pathfinderBot.pathfinder) {
    throw new Error("mineflayer-pathfinder is not loaded.");
  }

  const start = vector(bot.entity.position);
  let update: PathfinderUpdate = { status: "searching", path: [] };
  let lastPosition = bot.entity.position.clone();
  let lastProgressAt = Date.now();
  let stalled = false;
  const onPathUpdate = (value: PathfinderUpdate): void => {
    update = value;
  };
  bot.on("path_update", onPathUpdate);
  const progressTimer = setInterval(() => {
    const position = bot.entity.position;
    if (position.distanceTo(lastPosition) >= 0.2) {
      lastPosition = position.clone();
      lastProgressAt = Date.now();
    } else if (pathfinderBot.pathfinder?.isMoving() && Date.now() - lastProgressAt >= 40_000) {
      stalled = true;
      pathfinderBot.pathfinder.stop();
    }
  }, 500);

  pathfinderBot.pathfinder.setMovements(configureNavigationMovements(new Movements(bot), profile));
  // Use a GoalXZ so terrain height is auto-chosen: overworld travel should aim
  // at a horizontal position and let the pathfinder pick whichever standable Y
  // is reachable, instead of failing because the exact target Y doesn't match.
  const goal = new goals.GoalNearXZ(target.x, target.z, tolerance);
  // Dynamic goal (dynamic=true): the pathfinder re-paths and requests chunks as
  // it travels, so a goal far beyond the initially-loaded area is reachable in
  // one long walk instead of many hard one-chunk hops. This is what makes
  // long-distance overland travel (e.g. village hunting) work.
  pathfinderBot.pathfinder.setGoal(goal, true);
  try {
    await new Promise<void>((resolve, reject) => {
      let settled = false;
      const fail = (name: string, message: string): Error => {
        const err = new Error(message);
        (err as Error & { name: string }).name = name;
        return err;
      };
      const finish = (err?: Error): void => {
        if (settled) return;
        settled = true;
        bot.removeListener("goal_reached", onReached);
        bot.removeListener("path_update", onUpdate);
        bot.removeListener("goal_updated", onChanged);
        bot.removeListener("path_stop", onStopped);
        setTimeout(() => (err ? reject(err) : resolve()), 0);
      };
      const onReached = (): void => finish();
      const onUpdate = (value: PathfinderUpdate): void => {
        update = value;
        if (value.status === "noPath") {
          finish(fail("NoPath", "No path to the goal!"));
        } else if (value.status === "timeout") {
          finish(fail("Timeout", "Took too long to decide path to goal!"));
        }
      };
      const onChanged = (changed: unknown): void => {
        if (changed !== goal) {
          finish(fail("GoalChanged", "The goal was changed before it could be completed!"));
        }
      };
      const onStopped = (): void => {
        finish(fail("PathStopped", "Path was stopped before it could be completed!"));
      };
      bot.on("goal_reached", onReached);
      bot.on("path_update", onUpdate);
      bot.on("goal_updated", onChanged);
      bot.on("path_stop", onStopped);
    });
    const position = bot.entity.position;
    const dx = target.x - position.x;
    const dz = target.z - position.z;
    const report = summarizeNavigation(update, start, target, stalled, profile);
    if (dx * dx + dz * dz > tolerance * tolerance) {
      throw new NavigationFailure(
        `Pathfinder stopped without reaching goal: position ${JSON.stringify(vector(position))}, ` +
        `target ${JSON.stringify(target)}, tolerance ${tolerance}. ${report.diagnosis}`,
        report
      );
    }
    return report;
  } catch (error) {
    if (error instanceof NavigationFailure) {
      throw error;
    }
    const report = summarizeNavigation(update, start, target, stalled, profile);
    throw new NavigationFailure(`${errorMessage(error)} ${report.diagnosis}`, report);
  } finally {
    clearInterval(progressTimer);
    bot.removeListener("path_update", onPathUpdate);
  }
}

export function configureNavigationMovements(
  movements: InstanceType<typeof Movements>,
  profile: NavigationProfile
): InstanceType<typeof Movements> {
  if (profile === "walk_only") {
    movements.canDig = false;
    movements.allow1by1towers = false;
    movements.allowParkour = false;
    movements.scafoldingBlocks = [];
    movements.maxDropDown = 1;
    movements.infiniteLiquidDropdownDistance = false;
  }
  return movements;
}

export function summarizeNavigation(
  update: PathfinderUpdate,
  start: Vector3,
  target: Vector3,
  stalled: boolean,
  profile: NavigationProfile = "adaptive"
): NavigationReport {
  let ascents = 0;
  let drops = 0;
  let blocksToBreak = 0;
  let blocksToPlace = 0;
  let previous: Vector3 = start;
  for (const move of update.path) {
    if (move.y > previous.y) ascents += 1;
    if (move.y < previous.y) drops += 1;
    blocksToBreak += move.toBreak?.length ?? 0;
    blocksToPlace += move.toPlace?.length ?? 0;
    previous = move;
  }
  const verticalDelta = target.y - start.y;
  let diagnosis = `${profile} route completed`;
  if (stalled) {
    diagnosis = "route found, but the character made no physical progress for 6 seconds";
  } else if (update.status === "noPath" && verticalDelta > 1) {
    diagnosis = profile === "walk_only"
      ? "walk-only pathfinding found no existing ascent within the movement limits"
      : "adaptive pathfinding found no ascent; a deliberate staircase or tunnel may be required";
  } else if (update.status === "noPath" && verticalDelta < (profile === "walk_only" ? -1 : -4)) {
    diagnosis = `${profile} pathfinding found no descent; the required drop exceeds the profile limit`;
  } else if (update.status === "noPath") {
    diagnosis = profile === "walk_only"
      ? "no route exists through loaded walkable terrain without digging, placing, parkour, or a drop over one block"
      : "no route exists through the currently loaded terrain, even with digging and block placement enabled";
  } else if (update.status === "timeout") {
    diagnosis = "path search exhausted its computation budget";
  } else if (update.status !== "success") {
    diagnosis = `pathfinder ended with status ${update.status}`;
  }
  return {
    profile,
    pathStatus: update.status,
    pathNodes: update.path.length,
    ascents,
    drops,
    blocksToBreak,
    blocksToPlace,
    stalled,
    diagnosis
  };
}

async function walkToBlockRange(bot: Bot, block: BlockLike): Promise<void> {
  await gotoNear(bot, vector(block.position), 2.0);
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
