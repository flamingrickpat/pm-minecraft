import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import type { Bot } from "mineflayer";
import { Vec3 } from "vec3";
import type { ViewerStatus } from "../viewer/viewer.js";

/**
 * viewer frames need targeting context; save PNG bytes beside bot pose and loaded-world metadata.
 *
 * @remarks
 * archetype: service-provider
 * owns: frame id generation, dependency checks, PNG/metadata persistence, capture-quality evidence, and v1 world grounding.
 * not own: screenshot quality calculation, pixel-to-block ray resolution, SQLite blob storage, or physical command execution.
 * fails when: the viewer capture path, spawned bot, or loaded world data is unavailable.
 * domain: a frame bundle is the durable source for later target requests; a PNG without metadata is invalid.
 * invariant: successful captures always write both PNG bytes and JSON metadata for the same frame id.
 */
export interface FrameBundleCapture {
  capture(): Promise<FrameCaptureResult>;
}

export interface FrameCaptureDependencies {
  directory: string;
  viewer: Pick<ViewerStatus, "started" | "url" | "firstPerson" | "error">;
  bot: FrameBotSource | (() => FrameBotSource | null);
  minecraftVersion: () => string | null;
  capturePng: (input: { url: string; hud?: string[] }) => Promise<CapturedPng>;
}

export interface FrameBotSource {
  status: { spawned: boolean; connected: boolean };
  bot: Bot;
}

export interface CapturedPng {
  png: Buffer;
  width: number;
  height: number;
  projection: ProjectionMetadata;
  quality: FrameQualityAssessment;
}

export interface ProjectionMetadata {
  fovDegrees?: number;
  near?: number;
  far?: number;
  source?: string;
}

export interface FrameQualityAssessment {
  usable: boolean;
  reason: string;
  byteSize: number;
  backgroundFraction: number;
  darkFraction: number;
  distinctColorCount: number;
  luminanceRange: number;
  dominantColorFraction: number;
  minimumByteSize: number;
  maximumBackgroundFraction: number;
  maximumDarkFraction: number;
  minimumDistinctColors: number;
  minimumLuminanceRange: number;
  maximumDominantColorFraction: number;
}

export type FrameCaptureResult =
  | { ok: true; bundle: FrameBundle }
  | { ok: false; reason: "viewer_unavailable" | "bot_unavailable" | "world_unavailable" | "capture_failed"; message: string };

export interface FrameBundle {
  frameId: string;
  pngPath: string;
  metadataPath: string;
  metadata: FrameMetadata;
}

export interface FrameMetadata {
  frameId: string;
  capturedAt: string;
  pngPath: string;
  width: number;
  height: number;
  botEyePosition: { x: number; y: number; z: number };
  yaw: number;
  pitch: number;
  projection: ProjectionMetadata;
  quality: FrameQualityAssessment;
  dimension: string;
  minecraftVersion: string;
  loadedWorld: {
    eyeChunk: { x: number; z: number };
    referenceBlock: { position: { x: number; y: number; z: number }; name: string };
  };
}

let nextFrameSequence = 0;

export function createFrameBundleCapture(dependencies: FrameCaptureDependencies): FrameBundleCapture {
  return {
    capture: async () => {
      if (!dependencies.viewer.started || !dependencies.viewer.url) {
        const detail = dependencies.viewer.error ? `: ${dependencies.viewer.error}` : ".";
        return { ok: false, reason: "viewer_unavailable", message: `Frame capture requires a started viewer${detail}` };
      }

      const source = currentBot(dependencies.bot);
      if (!source || !source.status.spawned || !source.status.connected) {
        return { ok: false, reason: "bot_unavailable", message: "Frame capture requires a spawned bot." };
      }

      const world = loadedWorldReference(source.bot);
      if (!world) {
        return {
          ok: false,
          reason: "world_unavailable",
          message: "Frame capture requires loaded world data at the bot eye chunk."
        };
      }

      let captured: CapturedPng;
      try {
        captured = await dependencies.capturePng({ url: dependencies.viewer.url, hud: botHudLines(source.bot) });
      } catch (error) {
        return {
          ok: false,
          reason: "capture_failed",
          message: `Viewer PNG capture failed: ${errorMessage(error)}`
        };
      }

      const capturedAt = new Date().toISOString();
      const frameId = frameIdFor(capturedAt);
      const pngPath = join(dependencies.directory, `${frameId}.png`);
      const metadataPath = join(dependencies.directory, `${frameId}.json`);
      const metadata: FrameMetadata = {
        frameId,
        capturedAt,
        pngPath,
        width: captured.width,
        height: captured.height,
        botEyePosition: world.eye,
        yaw: source.bot.entity.yaw,
        pitch: source.bot.entity.pitch,
        projection: captured.projection,
        quality: captured.quality,
        dimension: dimensionOf(source.bot),
        minecraftVersion: dependencies.minecraftVersion() ?? source.bot.version,
        loadedWorld: {
          eyeChunk: world.eyeChunk,
          referenceBlock: world.referenceBlock
        }
      };

      await mkdir(dependencies.directory, { recursive: true });
      await writeFile(pngPath, captured.png);
      await writeFile(metadataPath, JSON.stringify(metadata, null, 2));

      return { ok: true, bundle: { frameId, pngPath, metadataPath, metadata } };
    }
  };
}

function currentBot(source: FrameCaptureDependencies["bot"]): FrameBotSource | null {
  return typeof source === "function" ? source() : source;
}

const COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"] as const;

/**
 * Build the HUD lines rendered into every captured frame so the image alone
 * answers "where am I, which way am I looking, am I about to die":
 *   pos (70.5, 64.0, -215.3) | heading 143° SE | yaw 217.3° pitch -12.5°
 *   biome savanna | day | hp 16.0/16 | food 18/20
 * Yaw/pitch follow the same degree convention as the rotate tool (yaw [0,360)
 * counterclockwise, pitch positive up); heading is the compass bearing.
 */
export function botHudLines(bot: Bot): string[] {
  const entity = bot.entity;
  if (!entity) return [];
  const pos = entity.position;
  const yawDeg = ((entity.yaw * 180 / Math.PI) % 360 + 360) % 360;
  const pitchDeg = Math.max(-90, Math.min(90, entity.pitch * 180 / Math.PI));
  // Compass bearing: mineflayer yaw 0 faces north (-Z), increasing
  // counterclockwise, so the bearing is the negated yaw.
  const headingDeg = Math.round((360 - yawDeg) % 360);
  const cardinal = COMPASS[Math.round(headingDeg / 45) % 8];
  const health = typeof bot.health === "number" ? bot.health : null;
  const food = typeof bot.food === "number" ? bot.food : null;
  const timeOfDay = (bot.time as { timeOfDay?: number } | undefined)?.timeOfDay;
  const day = typeof timeOfDay === "number" ? (timeOfDay < 12542 || timeOfDay > 23459) : null;
  const round = (v: number): number => Math.round(v * 10) / 10;
  const line1 =
    `pos (${round(pos.x)}, ${round(pos.y)}, ${round(pos.z)}) | ` +
    `heading ${headingDeg}\u00b0 ${cardinal} | ` +
    `yaw ${round(yawDeg)}\u00b0 pitch ${round(pitchDeg)}\u00b0`;
  const parts = [`biome ${biomeAt(bot) ?? "?"}`];
  if (day !== null) parts.push(day ? "day" : "night");
  if (health !== null) parts.push(`hp ${round(health)}`);
  if (food !== null) parts.push(`food ${food}`);
  return [line1, parts.join(" | ")];
}

function biomeAt(bot: Bot): string | null {
  try {
    const world = (bot as Bot & { world?: { getBiome?: (p: Vec3) => number } }).world;
    const registry = (bot as Bot & { registry?: { biomes?: Record<number, { name?: string }> } }).registry;
    if (!world || typeof world.getBiome !== "function" || !registry?.biomes || !bot.entity) {
      return null;
    }
    const biomeId = world.getBiome(bot.entity.position.floored());
    return registry.biomes[biomeId]?.name ?? null;
  } catch {
    return null;
  }
}

function loadedWorldReference(bot: Bot): FrameMetadata["loadedWorld"] & { eye: FrameMetadata["botEyePosition"] } | null {
  const eye = eyePosition(bot);
  const referencePosition = new Vec3(Math.floor(eye.x), Math.floor(eye.y), Math.floor(eye.z));
  const block = bot.blockAt(referencePosition, false);
  if (!block) {
    return null;
  }

  return {
    eye,
    eyeChunk: { x: Math.floor(eye.x / 16), z: Math.floor(eye.z / 16) },
    referenceBlock: {
      position: { x: block.position.x, y: block.position.y, z: block.position.z },
      name: block.name
    }
  };
}

function eyePosition(bot: Bot): FrameMetadata["botEyePosition"] {
  const eyeHeight = (bot.entity as typeof bot.entity & { eyeHeight?: number }).eyeHeight ?? 1.62;
  return {
    x: bot.entity.position.x,
    y: bot.entity.position.y + eyeHeight,
    z: bot.entity.position.z
  };
}

function dimensionOf(bot: Bot): string {
  const game = bot.game as typeof bot.game & { dimension?: string };
  return game.dimension ?? "unknown";
}

function frameIdFor(capturedAt: string): string {
  nextFrameSequence += 1;
  return `frame_${capturedAt.replace(/\D/g, "")}_${nextFrameSequence.toString().padStart(6, "0")}`;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
