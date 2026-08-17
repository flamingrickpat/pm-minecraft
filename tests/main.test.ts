import { describe, expect, it } from "vitest";
import { runMain } from "../src/main.js";
import { createRuntime, type Runtime } from "../src/runtime.js";

describe("runMain", () => {
  it("delegates startup to the shared runtime composition path", async () => {
    const calls: string[] = [];
    const runtime: Runtime = {
      start: async () => {
        calls.push("start");
      },
      stop: async () => {
        calls.push("stop");
      }
    };

    await runMain(() => runtime);

    expect(calls).toEqual(["start"]);
  });

  it("constructs the runtime without opening the web or Minecraft connection", async () => {
    const runtime = createRuntime({
      config: {
        minecraft: { host: "127.0.0.1", port: 1, username: "dry-bot", mineVisibilityIgnoreDistance: 3, walkMaxChunks: 8, walkSearchTimeoutMs: 1000 },
        web: { host: "127.0.0.1", port: 1 },
        viewer: { enabled: false, port: 3001, firstPerson: true, captureWidth: 640, captureHeight: 640, deviceScaleFactor: 2, fovDegrees: 80 },
        command: { timeoutMs: 250, maxFineControlDurationMs: 3000, stateBroadcastIntervalMs: 500 },
        evidence: { directory: "evidence" },
        actionLog: { enabled: false, directory: "logs/actions", nearbyBlockRadius: 8 }
      }
    });

    expect(runtime).toEqual({
      start: expect.any(Function),
      stop: expect.any(Function)
    });
    await runtime.stop();
  });
});
