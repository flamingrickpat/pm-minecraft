import { once } from "node:events";
import { createServer as createNetServer } from "node:net";
import { describe, expect, it } from "vitest";
import { createRuntimeHttpServer } from "../src/server/http.js";

describe("GET /api/observation", () => {
  it("returns the supplied rich observation without reshaping it", async () => {
    const port = await freePort();
    const observation = {
      capturedAt: "2026-07-18T20:00:00.000Z",
      player: { username: "mcp-test", position: { x: 1, y: 64, z: 2 } },
      world: { dimension: "overworld", biome: "plains" },
      inventory: { items: [{ name: "coal", count: 3 }] },
      surroundings: { nearbyBlocks: [], nearbyEntities: [] }
    };
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState(),
      observation: () => observation
    });
    await server.start();
    try {
      const response = await fetch(`http://127.0.0.1:${port}/api/observation`);
      expect(response.status).toBe(200);
      expect(await response.json()).toEqual(observation);
    } finally {
      await server.stop();
    }
  });

  it("reports unavailable instead of returning a partial/default observation", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState(),
      observation: () => null
    });
    await server.start();
    try {
      const response = await fetch(`http://127.0.0.1:${port}/api/observation`);
      expect(response.status).toBe(503);
      expect(await response.json()).toMatchObject({ ok: false, error: "observation_unavailable" });
    } finally {
      await server.stop();
    }
  });
});

function healthInput() {
  return {
    startedAt: new Date("2026-07-18T20:00:00.000Z"),
    config: {
      minecraft: { host: "127.0.0.1", port: 12345, username: "mcp-test", mineVisibilityIgnoreDistance: 3, walkMaxChunks: 8, walkSearchTimeoutMs: 1000 },
      web: { host: "127.0.0.1", port: 3000 },
      viewer: { enabled: true, port: 3007, firstPerson: true, captureWidth: 640, captureHeight: 640, deviceScaleFactor: 2, fovDegrees: 80 },
      command: { timeoutMs: 30000, maxFineControlDurationMs: 3000, stateBroadcastIntervalMs: 500 },
      evidence: { directory: "evidence" },
      actionLog: { enabled: true, directory: "logs/actions", nearbyBlockRadius: 8 }
    },
    bot: { connecting: false, connected: true, spawned: true, username: "mcp-test", lastError: null },
    paper: { reachable: true, checkedAt: "2026-07-18T20:00:00.000Z", error: null },
    viewer: { enabled: true, started: true, port: 3007, url: "http://127.0.0.1:3007", error: null }
  };
}

function disconnectedState() {
  return {
    connected: false,
    username: "mcp-test",
    position: null,
    yaw: null,
    pitch: null,
    yawDegrees: null,
    pitchDegrees: null,
    facing: null,
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
