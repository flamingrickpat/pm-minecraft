import { describe, expect, it } from "vitest";
import { serializeHealth } from "../src/server/health.js";
import { serializeState } from "../src/server/state.js";

describe("health and state serializers", () => {
  it("returns health shape with process, config, Mineflayer, Paper, and viewer status", () => {
    expect(
      serializeHealth({
        startedAt: new Date("2026-06-17T19:00:00Z"),
        config: {
          minecraft: { host: "127.0.0.1", port: 25565, username: "bot" },
          web: { host: "127.0.0.1", port: 3000 },
          viewer: { enabled: true, port: 3001, firstPerson: true, captureWidth: 640, captureHeight: 640, deviceScaleFactor: 2, fovDegrees: 80 },
          command: { timeoutMs: 30000, maxFineControlDurationMs: 3000, stateBroadcastIntervalMs: 500 },
          evidence: { directory: "evidence" },
          actionLog: { enabled: false, directory: "logs/actions", nearbyBlockRadius: 8 }
        },
        bot: { connecting: false, connected: true, spawned: true, username: "bot", lastError: null },
        paper: { reachable: true, checkedAt: "2026-06-17T19:00:01.000Z", error: null },
        viewer: { enabled: true, started: true, port: 3001, url: "http://127.0.0.1:3001", error: null }
      })
    ).toMatchObject({
      process: { uptimeMs: expect.any(Number), startedAt: "2026-06-17T19:00:00.000Z" },
      config: { minecraft: { host: "127.0.0.1", port: 25565, username: "bot" } },
      mineflayer: { connected: true, spawned: true },
      paper: { reachable: true },
      viewer: { started: true }
    });
  });

  it("serializes minimal state from live bot fields", () => {
    expect(
      serializeState({
        connected: true,
        username: "bot",
        position: { x: 1, y: 64, z: -2 },
        yaw: 0.25,
        pitch: -0.5,
        yawDegrees: 14.3,
        pitchDegrees: -28.6,
        facing: "north",
        dimension: "overworld",
        health: 20,
        food: 20,
        selectedHotbarSlot: 2,
        heldItem: { slot: 38, name: "oak_log", displayName: "Oak Log", count: 3 },
        inventory: { totalSlots: 46, usedSlots: 1, items: [{ slot: 38, name: "oak_log", displayName: "Oak Log", count: 3 }] },
        crosshairBlock: null
      })
    ).toEqual({
      connected: true,
      username: "bot",
      position: { x: 1, y: 64, z: -2 },
      yaw: 0.25,
      pitch: -0.5,
      yawDegrees: 14.3,
      pitchDegrees: -28.6,
      facing: "north",
      dimension: "overworld",
      health: 20,
      food: 20,
      selectedHotbarSlot: 2,
      heldItem: { slot: 38, name: "oak_log", displayName: "Oak Log", count: 3 },
      inventory: { totalSlots: 46, usedSlots: 1, items: [{ slot: 38, name: "oak_log", displayName: "Oak Log", count: 3 }] },
      crosshairBlock: null,
      currentCommand: null
    });
  });
});
