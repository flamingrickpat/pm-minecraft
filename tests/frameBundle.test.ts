import { mkdtemp, readFile, rm, stat, writeFile } from "node:fs/promises";
import { once } from "node:events";
import { createServer as createNetServer } from "node:net";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { Vec3 } from "vec3";
import { describe, expect, it } from "vitest";
import { createFrameBundleCapture } from "../src/targeting/frameBundle.js";
import { createRuntimeHttpServer } from "../src/server/http.js";

const pngBytes = Buffer.from("89504e470d0a1a0a0000000d49484452", "hex");

describe("GET /api/frame/current", () => {
  it("returns HTTP 503 when frames is undefined", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState()
    } as never);

    await server.start();
    try {
      const response = await fetch(`http://127.0.0.1:${port}/api/frame/current`);
      expect(response.status).toBe(503);
      const body = await response.json();
      expect(body.ok).toBe(false);
      expect(body.error).toBe("frame_capture_unavailable");
    } finally {
      await server.stop();
    }
  });

  it("returns {frameId, pngBase64, metadata} with valid base64 PNG", async () => {
    await withTempDir(async (directory) => {
      const port = await freePort();
      let captureCount = 0;
      const server = createRuntimeHttpServer({
        config: { host: "127.0.0.1", port },
        health: () => healthInput(),
        state: () => disconnectedState(),
        frames: {
          capture: async () => {
            captureCount++;
            const frameId = `frame_test_${captureCount}`;
            const pngPath = join(directory, `${frameId}.png`);
            const metadataPath = join(directory, `${frameId}.json`);
            const metadata = {
              frameId,
              capturedAt: new Date().toISOString(),
              pngPath,
              width: 640,
              height: 360,
              botEyePosition: { x: 10, y: 65.62, z: 10 },
              yaw: 0,
              pitch: 0,
              projection: { fovDegrees: 75 },
              dimension: "minecraft:overworld",
              minecraftVersion: "1.21.11",
              loadedWorld: {
                eyeChunk: { x: 0, z: 0 },
                referenceBlock: { position: { x: 10, y: 65, z: 10 }, name: "stone" }
              }
            };
            await writeFile(pngPath, pngBytes);
            await writeFile(metadataPath, JSON.stringify(metadata));
            return { ok: true, bundle: { frameId, pngPath, metadataPath, metadata } };
          }
        }
      } as never);

      await server.start();
      try {
        const response = await fetch(`http://127.0.0.1:${port}/api/frame/current`);
        expect(response.status).toBe(200);
        const body = await response.json();
        expect(body.ok).toBe(true);
        expect(body.frameId).toBe("frame_test_1");
        expect(typeof body.pngBase64).toBe("string");
        expect(body.pngBase64.length).toBeGreaterThan(0);
        expect(body.metadata).toMatchObject({
          width: 640,
          height: 360,
          dimension: "minecraft:overworld"
        });

        // Verify the base64 decodes to valid PNG bytes
        const decoded = Buffer.from(body.pngBase64, "base64");
        expect(decoded).toEqual(pngBytes);
      } finally {
        await server.stop();
      }
    });
  });

  it("captures a fresh frame on each request (different frameIds)", async () => {
    await withTempDir(async (directory) => {
      const port = await freePort();
      let captureCount = 0;
      const server = createRuntimeHttpServer({
        config: { host: "127.0.0.1", port },
        health: () => healthInput(),
        state: () => disconnectedState(),
        frames: {
          capture: async () => {
            captureCount++;
            const frameId = `frame_fresh_${captureCount}`;
            const pngPath = join(directory, `${frameId}.png`);
            const metadataPath = join(directory, `${frameId}.json`);
            const metadata = {
              frameId,
              capturedAt: new Date().toISOString(),
              pngPath,
              width: 640,
              height: 360,
              botEyePosition: { x: 10, y: 65.62, z: 10 },
              yaw: 0,
              pitch: 0,
              projection: { fovDegrees: 75 },
              dimension: "minecraft:overworld",
              minecraftVersion: "1.21.11",
              loadedWorld: {
                eyeChunk: { x: 0, z: 0 },
                referenceBlock: { position: { x: 10, y: 65, z: 10 }, name: "stone" }
              }
            };
            await writeFile(pngPath, pngBytes);
            await writeFile(metadataPath, JSON.stringify(metadata));
            return { ok: true, bundle: { frameId, pngPath, metadataPath, metadata } };
          }
        }
      } as never);

      await server.start();
      try {
        const resp1 = await fetch(`http://127.0.0.1:${port}/api/frame/current`);
        const body1 = await resp1.json();
        const resp2 = await fetch(`http://127.0.0.1:${port}/api/frame/current`);
        const body2 = await resp2.json();

        expect(body1.frameId).toBe("frame_fresh_1");
        expect(body2.frameId).toBe("frame_fresh_2");
        expect(body1.frameId).not.toBe(body2.frameId);
      } finally {
        await server.stop();
      }
    });
  });

  it("returns 500 when PNG file is missing after capture", async () => {
    await withTempDir(async (directory) => {
      const port = await freePort();
      const server = createRuntimeHttpServer({
        config: { host: "127.0.0.1", port },
        health: () => healthInput(),
        state: () => disconnectedState(),
        frames: {
          capture: async () => {
            // Return a path to a file that does not exist (simulates race/deletion)
            return {
              ok: true,
              bundle: {
                frameId: "frame_missing_png",
                pngPath: join(directory, "nonexistent.png"),
                metadataPath: join(directory, "nonexistent.json"),
                metadata: {
                  frameId: "frame_missing_png",
                  capturedAt: new Date().toISOString(),
                  pngPath: join(directory, "nonexistent.png"),
                  width: 640,
                  height: 360,
                  botEyePosition: { x: 10, y: 65.62, z: 10 },
                  yaw: 0,
                  pitch: 0,
                  projection: { fovDegrees: 75 },
                  dimension: "minecraft:overworld",
                  minecraftVersion: "1.21.11",
                  loadedWorld: {
                    eyeChunk: { x: 0, z: 0 },
                    referenceBlock: { position: { x: 10, y: 65, z: 10 }, name: "stone" }
                  }
                }
              }
            };
          }
        }
      } as never);

      await server.start();
      try {
        const response = await fetch(`http://127.0.0.1:${port}/api/frame/current`);
        expect(response.status).toBe(500);
        const body = await response.json();
        expect(body.ok).toBe(false);
        expect(body.error).toBe("capture_failed");
      } finally {
        await server.stop();
      }
    });
  });

  it("returns 503 when frame capture reports viewer_unavailable", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState(),
      frames: {
        capture: async () => ({
          ok: false,
          reason: "viewer_unavailable",
          message: "Frame capture requires a started viewer."
        })
      }
    } as never);

    await server.start();
    try {
      const response = await fetch(`http://127.0.0.1:${port}/api/frame/current`);
      expect(response.status).toBe(503);
      const body = await response.json();
      expect(body.ok).toBe(false);
      expect(body.error).toBe("viewer_unavailable");
    } finally {
      await server.stop();
    }
  });
});

describe("frame bundle capture", () => {
  it("saves PNG bytes and ray-ready metadata grounded in the loaded world", async () => {
    await withTempDir(async (directory) => {
      const capturedPngBytes = Buffer.concat([pngBytes, Buffer.alloc(12_000)]);
      const quality = qualityEvidence(capturedPngBytes.length);
      const capture = createFrameBundleCapture({
        directory,
        viewer: { started: true, url: "http://127.0.0.1:3001", firstPerson: true, error: null },
        bot: spawnedBot(),
        minecraftVersion: () => "1.21.11",
        capturePng: async () => ({
          png: capturedPngBytes,
          width: 640,
          height: 360,
          projection: { fovDegrees: 75, near: 0.1, far: 1000 },
          quality
        })
      });

      const result = await capture.capture();

      expect(result.ok).toBe(true);
      if (!result.ok) {
        return;
      }
      expect(result.bundle.metadata).toMatchObject({
        width: 640,
        height: 360,
        botEyePosition: { x: 12.25, y: 65.62, z: -7.5 },
        yaw: 1.25,
        pitch: -0.2,
        projection: { fovDegrees: 75, near: 0.1, far: 1000 },
        dimension: "minecraft:overworld",
        minecraftVersion: "1.21.11",
        quality,
        loadedWorld: {
          eyeChunk: { x: 0, z: -1 },
          referenceBlock: { position: { x: 12, y: 65, z: -8 }, name: "air" }
        }
      });
      expect(result.bundle.metadata.frameId).toBe(result.bundle.frameId);
      expect(result.bundle.pngPath.endsWith(`${result.bundle.frameId}.png`)).toBe(true);
      expect(result.bundle.metadataPath.endsWith(`${result.bundle.frameId}.json`)).toBe(true);
      expect(await readFile(result.bundle.pngPath)).toEqual(capturedPngBytes);

      const metadata = JSON.parse(await readFile(result.bundle.metadataPath, "utf8")) as Record<string, unknown>;
      expect(metadata.frameId).toBe(result.bundle.frameId);
      expect(metadata.pngPath).toBe(result.bundle.pngPath);
      expect(metadata.quality).toEqual(quality);
    });
  });

  it("generates unique stable frame ids and filenames for rapid captures", async () => {
    await withTempDir(async (directory) => {
      const capture = createFrameBundleCapture({
        directory,
        viewer: { started: true, url: "http://127.0.0.1:3001", firstPerson: true, error: null },
        bot: spawnedBot(),
        minecraftVersion: () => "1.21.11",
        capturePng: async () => ({ png: pngBytes, width: 320, height: 200, projection: { fovDegrees: 75 }, quality: qualityEvidence(pngBytes.length) })
      });

      const first = await capture.capture();
      const second = await capture.capture();

      expect(first.ok && second.ok).toBe(true);
      if (!first.ok || !second.ok) {
        return;
      }
      expect(first.bundle.frameId).not.toBe(second.bundle.frameId);
      expect(first.bundle.pngPath).not.toBe(second.bundle.pngPath);
      await expect(stat(first.bundle.metadataPath)).resolves.toMatchObject({ size: expect.any(Number) });
      await expect(stat(second.bundle.metadataPath)).resolves.toMatchObject({ size: expect.any(Number) });
    });
  });

  it("reports when the bot has not spawned", async () => {
    await withTempDir(async (directory) => {
      const capture = createFrameBundleCapture({
        directory,
        viewer: { started: true, url: "http://127.0.0.1:3001", firstPerson: true, error: null },
        bot: { status: { spawned: false, connected: true }, bot: spawnedBot().bot },
        minecraftVersion: () => "1.21.11",
        capturePng: async () => ({ png: pngBytes, width: 1, height: 1, projection: {}, quality: qualityEvidence(pngBytes.length) })
      });

      await expect(capture.capture()).resolves.toEqual({
        ok: false,
        reason: "bot_unavailable",
        message: "Frame capture requires a spawned bot."
      });
    });
  });

  it("reports when the viewer capture path is unavailable", async () => {
    await withTempDir(async (directory) => {
      const capture = createFrameBundleCapture({
        directory,
        viewer: { started: false, url: null, firstPerson: true, error: "Cannot find module 'canvas'" },
        bot: spawnedBot(),
        minecraftVersion: () => "1.21.11",
        capturePng: async () => ({ png: pngBytes, width: 1, height: 1, projection: {}, quality: qualityEvidence(pngBytes.length) })
      });

      await expect(capture.capture()).resolves.toEqual({
        ok: false,
        reason: "viewer_unavailable",
        message: "Frame capture requires a started viewer: Cannot find module 'canvas'"
      });
    });
  });

  it("reports when loaded world data is unavailable", async () => {
    await withTempDir(async (directory) => {
      const bot = spawnedBot();
      bot.bot.blockAt = () => null;
      const capture = createFrameBundleCapture({
        directory,
        viewer: { started: true, url: "http://127.0.0.1:3001", firstPerson: true, error: null },
        bot,
        minecraftVersion: () => "1.21.11",
        capturePng: async () => ({ png: pngBytes, width: 1, height: 1, projection: {}, quality: qualityEvidence(pngBytes.length) })
      });

      await expect(capture.capture()).resolves.toEqual({
        ok: false,
        reason: "world_unavailable",
        message: "Frame capture requires loaded world data at the bot eye chunk."
      });
    });
  });

  it("exposes a read-only frame capture endpoint", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState(),
      frames: {
        capture: async () => ({
          ok: true,
          bundle: {
            frameId: "frame_20260618T000000000Z_000001",
            pngPath: "evidence/screenshots/frame_20260618T000000000Z_000001.png",
            metadataPath: "evidence/screenshots/frame_20260618T000000000Z_000001.json",
            metadata: {
              frameId: "frame_20260618T000000000Z_000001",
              capturedAt: "2026-06-18T00:00:00.000Z",
              pngPath: "evidence/screenshots/frame_20260618T000000000Z_000001.png",
              width: 640,
              height: 360,
              botEyePosition: { x: 1, y: 65.62, z: 1 },
              yaw: 0,
              pitch: 0,
              projection: { fovDegrees: 75 },
              dimension: "minecraft:overworld",
              minecraftVersion: "1.21.11",
              loadedWorld: {
                eyeChunk: { x: 0, z: 0 },
                referenceBlock: { position: { x: 1, y: 65, z: 1 }, name: "air" }
              }
            }
          }
        })
      }
    } as never);

    await server.start();
    try {
      const response = await fetch(`http://127.0.0.1:${port}/api/frame/capture`, { method: "POST" });
      expect(response.status).toBe(200);
      expect(await response.json()).toMatchObject({
        ok: true,
        frameId: "frame_20260618T000000000Z_000001",
        pngPath: "evidence/screenshots/frame_20260618T000000000Z_000001.png",
        metadata: { width: 640, height: 360, loadedWorld: { eyeChunk: { x: 0, z: 0 } } }
      });
    } finally {
      await server.stop();
    }
  });
});

function spawnedBot(): any {
  return {
    status: { spawned: true, connected: true },
    bot: {
      version: "1.21.11",
      game: { dimension: "minecraft:overworld" },
      entity: {
        position: new Vec3(12.25, 64, -7.5),
        yaw: 1.25,
        pitch: -0.2,
        eyeHeight: 1.62
      },
      blockAt: () => ({
        name: "air",
        position: new Vec3(12, 65, -8)
      })
    }
  };
}

function healthInput() {
  return {
    startedAt: new Date("2026-06-18T00:00:00Z"),
    config: {
      minecraft: { host: "127.0.0.1", port: 25565, username: "turnbased-bot" },
      web: { host: "127.0.0.1", port: 3000 },
      viewer: { enabled: true, port: 3001, firstPerson: true },
      command: { timeoutMs: 30000, maxFineControlDurationMs: 3000, stateBroadcastIntervalMs: 500 },
      evidence: { directory: "evidence" }
    },
    bot: { connecting: false, connected: true, spawned: true, username: "turnbased-bot", lastError: null },
    paper: { reachable: true, checkedAt: "2026-06-18T00:00:00.000Z", error: null },
    http: { listening: true, host: "127.0.0.1", port: 3000, url: "http://127.0.0.1:3000", error: null },
    webSocket: { enabled: true, path: "/ws", clients: 0, error: null },
    viewer: { enabled: true, started: true, port: 3001, url: "http://127.0.0.1:3001", firstPerson: true, error: null }
  };
}

function disconnectedState() {
  return {
    connected: false,
    username: "turnbased-bot",
    position: null,
    yaw: null,
    pitch: null,
    dimension: null,
    health: null,
    food: null,
    selectedHotbarSlot: null,
    heldItem: null,
    inventory: { totalSlots: 0, usedSlots: 0, items: [] },
    crosshairBlock: null
  };
}

function qualityEvidence(byteSize: number) {
  return {
    usable: true,
    reason: "Frame passes quality gate",
    byteSize,
    backgroundFraction: 0.12,
    darkFraction: 0.03,
    distinctColorCount: 42,
    luminanceRange: 64,
    dominantColorFraction: 0.12,
    minimumByteSize: 10_000,
    maximumBackgroundFraction: 0.95,
    maximumDarkFraction: 0.995,
    minimumDistinctColors: 4,
    minimumLuminanceRange: 18,
    maximumDominantColorFraction: 0.85
  };
}

async function freePort(): Promise<number> {
  const server = createNetServer();
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const address = server.address();
  if (address === null || typeof address === "string") {
    throw new Error("Could not allocate test port.");
  }
  const port = address.port;
  server.close();
  await once(server, "close");
  return port;
}

async function withTempDir(run: (directory: string) => Promise<void>): Promise<void> {
  const directory = await mkdtemp(join(tmpdir(), "frame-bundle-"));
  try {
    await run(directory);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}
