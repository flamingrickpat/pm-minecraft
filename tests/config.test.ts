import { describe, expect, it } from "vitest";
import { parseRuntimeConfig } from "../src/config.js";

describe("parseRuntimeConfig", () => {
  it("uses documented defaults for Minecraft, web, viewer, command, and evidence settings", () => {
    expect(parseRuntimeConfig({})).toEqual({
      minecraft: {
        host: "127.0.0.1",
        port: 55608,
        username: "turnbased-bot",
        viewDistance: 12,
        mineVisibilityIgnoreDistance: 3,
        walkToMaxDistance: 16
      },
      web: {
        host: "127.0.0.1",
        port: 3000
      },
      viewer: {
        enabled: true,
        port: 3001,
        firstPerson: true,
        viewDistance: 12,
        captureWidth: 640,
        captureHeight: 640,
        deviceScaleFactor: 1,
        fovDegrees: 80
      },
      command: {
        timeoutMs: 30000,
        maxFineControlDurationMs: 3000,
        stateBroadcastIntervalMs: 500
      },
      evidence: {
        directory: "evidence"
      },
      actionLog: {
        enabled: true,
        directory: "logs/actions",
        nearbyBlockRadius: 8
      }
    });
  });

  it("rejects invalid numeric environment values instead of silently falling back", () => {
    expect(() => parseRuntimeConfig({ MINECRAFT_PORT: "abc" })).toThrow(
      "MINECRAFT_PORT must be an integer"
    );
  });
});
