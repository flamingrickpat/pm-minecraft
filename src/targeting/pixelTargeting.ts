import { readFile } from "node:fs/promises";
import { join } from "node:path";
import type { Bot } from "mineflayer";
import { iterators } from "prismarine-world";
import { Vec3 } from "vec3";
import type { FrameMetadata } from "./frameBundle.js";
import type { JumpPlaceBlockInput, PlaceBlockInput, Vector3 } from "../commands/types.js";

/**
 * frame pixels need world targets; convert saved frame camera metadata into loaded-world block hits.
 *
 * @remarks
 * archetype: service-provider
 * owns: pixel validation-independent ray math, loaded-world ray traversal, and command target shaping.
 * not own: frame capture, image analysis, physical command execution, or HTTP transport.
 * fails when: a frame id is unknown, the ray reaches unloaded world data, or no block intersects the ray.
 * domain: a selected screenshot pixel becomes a stable Minecraft block target only through the saved camera pose and bot world.
 * invariant: successful target results always come from loaded world data, never from PNG colors or approximate coordinates.
 */
export interface PixelTargeting {
  resolve(input: PixelTargetInput): Promise<PixelTargetResult>;
}

export interface PixelTargetInput {
  frameId: string;
  x: number;
  y: number;
  maxDistance: number;
}

export type PixelTargetResult =
  | PixelTargetHit
  | { ok: false; reason: "frame_not_found" | "world_not_loaded" | "no_block_on_ray"; message: string };

export interface PixelTargetHit {
  ok: true;
  frameId: string;
  pixel: { x: number; y: number };
  block: Vector3;
  blockName: string;
  face: Vector3 | null;
  distance: number | null;
  commandTargets: {
    look: { target: Vector3 };
    mine: { block: Vector3 };
    place: PlaceBlockInput;
    jumpPlace: JumpPlaceBlockInput;
    use: { block: Vector3 };
    inspect: { block: Vector3 };
  };
}

export interface PixelTargetingDependencies {
  getFrame(frameId: string): Promise<FrameMetadata | null>;
  bot: Bot | (() => Bot | null);
}

type WorldBlock = {
  name: string;
  position: Vec3;
  shapes?: Array<[number, number, number, number, number, number]>;
};

type RaycastBlockPosition = { x: number; y: number; z: number; face: number };

type RayWorld = {
  getBlock(position: Vec3): WorldBlock | null;
};

const { RaycastIterator } = iterators;

export function createPixelTargeting(dependencies: PixelTargetingDependencies): PixelTargeting {
  return {
    resolve: async (input) => {
      const frame = await dependencies.getFrame(input.frameId);
      if (!frame) {
        return { ok: false, reason: "frame_not_found", message: "Frame metadata was not found." };
      }
      const bot = currentBot(dependencies.bot);
      if (!bot) {
        return {
          ok: false,
          reason: "world_not_loaded",
          message: "The selected pixel ray reached unloaded world data before hitting a block."
        };
      }

      console.log('[TARGET] frame=' + input.frameId + ' dims=' + frame.width + 'x' + frame.height + ' pixel=(' + input.x + ',' + input.y + ') maxDist=' + input.maxDistance + ' eye=(' + frame.botEyePosition.x + ',' + frame.botEyePosition.y + ',' + frame.botEyePosition.z + ') yaw=' + frame.yaw.toFixed(2) + ' pitch=' + frame.pitch.toFixed(2));
      const ray = pixelToWorldRay(frame, input.x, input.y);
      const hit = raycastLoadedWorld(bot.world as RayWorld, ray.origin, ray.direction, input.maxDistance);
      if (!hit.ok) {
        return hit;
      }

      const block = vector(hit.block.position);
      const face = faceVector(hit.face);
      return {
        ok: true,
        frameId: frame.frameId,
        pixel: { x: input.x, y: input.y },
        block,
        blockName: hit.block.name,
        face,
        distance: hit.distance,
        commandTargets: {
          look: { target: centerOf(block) },
          mine: { block },
          place: { referenceBlock: block, face: face ?? { x: 0, y: 1, z: 0 }, walkIntoRange: true },
          jumpPlace: { referenceBlock: block, face: face ?? { x: 0, y: 1, z: 0 }, walkIntoRange: true },
          use: { block },
          inspect: { block }
        }
      };
    }
  };
}

function currentBot(source: PixelTargetingDependencies["bot"]): Bot | null {
  return typeof source === "function" ? source() : source;
}

export function createFrameMetadataFileStore(directory: string): { getFrame(frameId: string): Promise<FrameMetadata | null> } {
  return {
    getFrame: async (frameId) => {
      if (!/^[A-Za-z0-9_-]+$/.test(frameId)) {
        return null;
      }
      try {
        return JSON.parse(await readFile(join(directory, `${frameId}.json`), "utf8")) as FrameMetadata;
      } catch (error) {
        if (error && typeof error === "object" && "code" in error && (error as { code?: unknown }).code === "ENOENT") {
          return null;
        }
        throw error;
      }
    }
  };
}

export function pixelToNormalizedDeviceCoordinates(x: number, y: number, width: number, height: number): { x: number; y: number } {
  return {
    x: ((x + 0.5) / width) * 2 - 1,
    y: 1 - ((y + 0.5) / height) * 2
  };
}

export function pixelToWorldRay(frame: FrameMetadata, x: number, y: number): { origin: Vec3; direction: Vec3 } {
  const ndc = pixelToNormalizedDeviceCoordinates(x, y, frame.width, frame.height);
  const verticalFov = ((frame.projection.fovDegrees ?? 75) * Math.PI) / 180;
  const halfHeight = Math.tan(verticalFov / 2);
  const halfWidth = halfHeight * (frame.width / frame.height);
  const forward = mineflayerViewDirection(frame.yaw, frame.pitch);
  const right = new Vec3(Math.cos(frame.yaw), 0, -Math.sin(frame.yaw)).normalize();
  const up = right.cross(forward).normalize();
  const direction = forward
    .plus(right.scaled(ndc.x * halfWidth))
    .plus(up.scaled(ndc.y * halfHeight))
    .normalize();

  console.log('[RAY] frame=' + frame.width + 'x' + frame.height + ' pixel=(' + x + ',' + y + ') ndc=(' + ndc.x.toFixed(3) + ',' + ndc.y.toFixed(3) + ') dir=(' + direction.x.toFixed(3) + ',' + direction.y.toFixed(3) + ',' + direction.z.toFixed(3) + ') fov=' + (frame.projection.fovDegrees ?? 75));

  return {
    origin: new Vec3(frame.botEyePosition.x, frame.botEyePosition.y, frame.botEyePosition.z),
    direction
  };
}

function raycastLoadedWorld(
  world: RayWorld,
  origin: Vec3,
  direction: Vec3,
  maxDistance: number
): { ok: true; block: WorldBlock; face: number | null; distance: number | null } | Extract<PixelTargetResult, { ok: false }> {
  const iterator = new RaycastIterator(origin, direction, maxDistance);
  let position: Vec3 | RaycastBlockPosition | null = origin;
  let steps = 0;
  while (position) {
    steps++;
    const block = world.getBlock(new Vec3(position.x, position.y, position.z));
    if (!block) {
      console.log('[RAY] world_not_loaded at step ' + steps + ' pos=(' + position.x + ',' + position.y + ',' + position.z + ')');
      return {
        ok: false,
        reason: "world_not_loaded",
        message: "The selected pixel ray reached unloaded world data before hitting a block."
      };
    }

    const shapes = block.shapes ?? [];
    const intersect = shapes.length > 0 ? iterator.intersect(shapes, block.position) : null;
    if (intersect) {
      console.log('[RAY] hit ' + block.name + ' at step ' + steps + ' dist=' + origin.distanceTo(intersect.pos).toFixed(1));
      return {
        ok: true,
        block,
        face: intersect.face,
        distance: origin.distanceTo(intersect.pos)
      };
    }
    position = iterator.next();
  }

  console.log('[RAY] no_block_on_ray after ' + steps + ' steps (maxDist=' + maxDistance + ')');
  return {
    ok: false,
    reason: "no_block_on_ray",
    message: "No loaded block was hit along the selected pixel ray (traversed " + steps + " blocks)."
  };
}

function mineflayerViewDirection(yaw: number, pitch: number): Vec3 {
  const cosPitch = Math.cos(pitch);
  return new Vec3(-Math.sin(yaw) * cosPitch, Math.sin(pitch), -Math.cos(yaw) * cosPitch);
}

function faceVector(face: number | null): Vector3 | null {
  switch (face) {
    case 0:
      return { x: 0, y: -1, z: 0 };
    case 1:
      return { x: 0, y: 1, z: 0 };
    case 2:
      return { x: 0, y: 0, z: -1 };
    case 3:
      return { x: 0, y: 0, z: 1 };
    case 4:
      return { x: -1, y: 0, z: 0 };
    case 5:
      return { x: 1, y: 0, z: 0 };
    default:
      return null;
  }
}

function vector(value: Vector3): Vector3 {
  return { x: value.x, y: value.y, z: value.z };
}

function centerOf(block: Vector3): Vector3 {
  return { x: block.x + 0.5, y: block.y + 0.5, z: block.z + 0.5 };
}
