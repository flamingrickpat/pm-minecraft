import { once } from "node:events";
import { createServer as createNetServer } from "node:net";
import { describe, expect, it, vi } from "vitest";
import { Vec3 } from "vec3";
import { CommandQueue } from "../src/commands/commandQueue.js";
import { createRuntimeHttpServer } from "../src/server/http.js";
import {
  createPixelTargeting,
  pixelToNormalizedDeviceCoordinates,
  pixelToWorldRay,
  type PixelTargeting
} from "../src/targeting/pixelTargeting.js";
import type { FrameMetadata } from "../src/targeting/frameBundle.js";

describe("pixel targeting", () => {
  it("converts frame pixels to normalized device coordinates at center and boundaries", () => {
    expect(pixelToNormalizedDeviceCoordinates(319.5, 179.5, 640, 360)).toEqual({ x: 0, y: 0 });
    const topLeft = pixelToNormalizedDeviceCoordinates(0, 0, 640, 360);
    expect(topLeft.x).toBeCloseTo(-0.9984375, 10);
    expect(topLeft.y).toBeCloseTo(0.9972222222222222, 10);
    const bottomRight = pixelToNormalizedDeviceCoordinates(639, 359, 640, 360);
    expect(bottomRight.x).toBeCloseTo(0.9984375, 10);
    expect(bottomRight.y).toBeCloseTo(-0.9972222222222222, 10);
  });

  it("converts a center pixel to the saved camera direction", () => {
    const ray = pixelToWorldRay(frame({ yaw: 0, pitch: 0 }), 319.5, 179.5);

    expect(ray.origin).toEqual(new Vec3(10.5, 65.62, -4.25));
    expect(ray.direction.x).toBeCloseTo(0, 10);
    expect(ray.direction.y).toBeCloseTo(0, 10);
    expect(ray.direction.z).toBeCloseTo(-1, 10);
  });

  it("uses frame FOV and aspect so corner rays differ from center rays", () => {
    const ray = pixelToWorldRay(frame({ yaw: 0, pitch: 0 }), 0, 0);

    expect(ray.direction.x).toBeLessThan(0);
    expect(ray.direction.y).toBeGreaterThan(0);
    expect(ray.direction.z).toBeLessThan(0);
    expect(ray.direction.norm()).toBeCloseTo(1, 10);
  });

  it("raycasts loaded world data and returns command payloads", async () => {
    const targeter = createPixelTargeting({
      getFrame: async () => frame({ yaw: 0, pitch: 0 }),
      bot: loadedBot({
        "10,65,-5": air(new Vec3(10, 65, -5)),
        "10,65,-6": solid("oak_log", new Vec3(10, 65, -6))
      })
    });

    const result = await targeter.resolve({ frameId: "frame_test", x: 319.5, y: 179.5, maxDistance: 8 });

    expect(result).toMatchObject({
      ok: true,
      block: { x: 10, y: 65, z: -6 },
      blockName: "oak_log",
      face: { x: 0, y: 0, z: 1 },
      commandTargets: {
        look: { target: { x: 10.5, y: 65.5, z: -5.5 } },
        mine: { block: { x: 10, y: 65, z: -6 } },
        place: { referenceBlock: { x: 10, y: 65, z: -6 }, face: { x: 0, y: 0, z: 1 } },
        jumpPlace: { referenceBlock: { x: 10, y: 65, z: -6 }, face: { x: 0, y: 0, z: 1 } },
        use: { block: { x: 10, y: 65, z: -6 } },
        inspect: { block: { x: 10, y: 65, z: -6 } }
      }
    });
    if (result.ok) {
      expect(result.distance).toBeGreaterThan(0);
    }
  });

  it("reports unloaded world before pretending the ray missed", async () => {
    const targeter = createPixelTargeting({
      getFrame: async () => frame({ yaw: 0, pitch: 0 }),
      bot: loadedBot({
        "10,65,-5": air(new Vec3(10, 65, -5))
      })
    });

    await expect(targeter.resolve({ frameId: "frame_test", x: 319.5, y: 179.5, maxDistance: 8 })).resolves.toEqual({
      ok: false,
      reason: "world_not_loaded",
      message: "The selected pixel ray reached unloaded world data before hitting a block."
    });
  });

  it("reports no block when loaded air occupies the whole ray", async () => {
    const blocks: Record<string, BlockLike> = {};
    for (let z = -5; z >= -13; z -= 1) {
      blocks[`10,65,${z}`] = air(new Vec3(10, 65, z));
    }
    const targeter = createPixelTargeting({
      getFrame: async () => frame({ yaw: 0, pitch: 0 }),
      bot: loadedBot(blocks)
    });

    await expect(targeter.resolve({ frameId: "frame_test", x: 319.5, y: 179.5, maxDistance: 8 })).resolves.toEqual({
      ok: false,
      reason: "no_block_on_ray",
      message: "No loaded block was hit along the selected pixel ray (traversed 9 blocks)."
    });
  });

  it("validates the target API before calling the resolver", async () => {
    await withTargetServer(async ({ port, targeting }) => {
      const badFrame = await post(port, "/api/targeting/resolve-pixel", { frameId: "", x: 1, y: 1, maxDistance: 8 });
      expect(badFrame.status).toBe(400);
      expect(await badFrame.json()).toMatchObject({ ok: false, error: "invalid_frame_id" });

      const badPixel = await post(port, "/api/targeting/resolve-pixel", { frameId: "frame_test", x: -1, y: 1, maxDistance: 8 });
      expect(badPixel.status).toBe(400);
      expect(await badPixel.json()).toMatchObject({ ok: false, error: "invalid_pixel" });

      const badRange = await post(port, "/api/targeting/resolve-pixel", { frameId: "frame_test", x: 1, y: 1, maxDistance: 0 });
      expect(badRange.status).toBe(400);
      expect(await badRange.json()).toMatchObject({ ok: false, error: "invalid_max_distance" });

      expect(targeting.resolve).not.toHaveBeenCalled();
    });
  });

  it("exposes pixel targets through a read-only API route", async () => {
    await withTargetServer(async ({ port, targeting }) => {
      targeting.resolve.mockResolvedValueOnce({
        ok: true,
        frameId: "frame_test",
        pixel: { x: 10, y: 20 },
        block: { x: 1, y: 2, z: 3 },
        blockName: "stone",
        face: { x: 0, y: 1, z: 0 },
        distance: 4,
        commandTargets: {
          look: { target: { x: 1.5, y: 2.5, z: 3.5 } },
          mine: { block: { x: 1, y: 2, z: 3 } },
          place: { referenceBlock: { x: 1, y: 2, z: 3 }, face: { x: 0, y: 1, z: 0 }, walkIntoRange: true },
          jumpPlace: { referenceBlock: { x: 1, y: 2, z: 3 }, face: { x: 0, y: 1, z: 0 }, walkIntoRange: true },
          use: { block: { x: 1, y: 2, z: 3 } },
          inspect: { block: { x: 1, y: 2, z: 3 } }
        }
      });

      const response = await post(port, "/api/targeting/resolve-pixel", { frameId: "frame_test", x: 10, y: 20, maxDistance: 8 });

      expect(response.status).toBe(200);
      expect(await response.json()).toMatchObject({
        ok: true,
        block: { x: 1, y: 2, z: 3 },
        blockName: "stone",
        commandTargets: {
          jumpPlace: { referenceBlock: { x: 1, y: 2, z: 3 } },
          mine: { block: { x: 1, y: 2, z: 3 } },
          inspect: { block: { x: 1, y: 2, z: 3 } }
        }
      });
      expect(targeting.resolve).toHaveBeenCalledWith({ frameId: "frame_test", x: 10, y: 20, maxDistance: 8 });
    });
  });
});

function frame(overrides: Partial<Pick<FrameMetadata, "yaw" | "pitch">>): FrameMetadata {
  return {
    frameId: "frame_test",
    capturedAt: "2026-06-18T00:00:00.000Z",
    pngPath: "evidence/screenshots/frame_test.png",
    width: 640,
    height: 360,
    botEyePosition: { x: 10.5, y: 65.62, z: -4.25 },
    yaw: overrides.yaw ?? 0,
    pitch: overrides.pitch ?? 0,
    projection: { fovDegrees: 75 },
    quality: {
      usable: true,
      reason: "Frame passes quality gate",
      byteSize: 12000,
      backgroundFraction: 0.12,
      darkFraction: 0.03,
      distinctColorCount: 42,
      luminanceRange: 64,
      dominantColorFraction: 0.12,
      minimumByteSize: 10000,
      maximumBackgroundFraction: 0.95,
      maximumDarkFraction: 0.995,
      minimumDistinctColors: 4,
      minimumLuminanceRange: 18,
      maximumDominantColorFraction: 0.85
    },
    dimension: "minecraft:overworld",
    minecraftVersion: "1.21.11",
    loadedWorld: {
      eyeChunk: { x: 0, z: -1 },
      referenceBlock: { position: { x: 10, y: 65, z: -4 }, name: "air" }
    }
  };
}

interface BlockLike {
  name: string;
  position: Vec3;
  shapes: Array<[number, number, number, number, number, number]>;
}

function solid(name: string, position: Vec3): BlockLike {
  return { name, position, shapes: [[0, 0, 0, 1, 1, 1]] };
}

function air(position: Vec3): BlockLike {
  return { name: "air", position, shapes: [] };
}

function loadedBot(blocks: Record<string, BlockLike>) {
  return {
    world: {
      getBlock: (position: Vec3) => blocks[`${Math.floor(position.x)},${Math.floor(position.y)},${Math.floor(position.z)}`] ?? null
    }
  } as never;
}

type TargetingMock = { resolve: ReturnType<typeof vi.fn<PixelTargeting["resolve"]>> };

async function withTargetServer(run: (context: {
  port: number;
  targeting: TargetingMock;
}) => Promise<void>): Promise<void> {
  const port = await freePort();
  const targeting = { resolve: vi.fn<PixelTargeting["resolve"]>() };
  let server!: ReturnType<typeof createRuntimeHttpServer>;
  const queue = new CommandQueue({ cleanup: async () => undefined, emit: (event) => server.broadcast(event), defaultTimeoutMs: 1000 });
  server = createRuntimeHttpServer({
    config: { host: "127.0.0.1", port },
    health: () => healthInput(),
    state: () => disconnectedState(),
    commands: {
      queue,
      applyControlStates: async () => undefined,
      actions: createActions()
    },
    targeting
  } as never);

  await server.start();
  try {
    await run({ port, targeting });
  } finally {
    await server.stop();
  }
}

function createActions() {
  return {
    lookAt: vi.fn(),
    walkTo: vi.fn(),
    mineBlock: vi.fn(),
    placeBlock: vi.fn(),
    jumpPlaceBlock: vi.fn(),
    pillarUp: vi.fn(),
    useBlock: vi.fn(),
    inspectBlock: vi.fn()
  };
}

function post(port: number, path: string, body: unknown): Promise<Response> {
  return fetch(`http://127.0.0.1:${port}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body)
  });
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
