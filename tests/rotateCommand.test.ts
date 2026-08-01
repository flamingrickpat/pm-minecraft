import { createServer as createNetServer } from "node:net";
import { describe, expect, it } from "vitest";
import { CommandQueue } from "../src/commands/commandQueue.js";
import { createRuntimeHttpServer } from "../src/server/http.js";
import { createPhysicalCommandActions } from "../src/bot/actions.js";
import type { Bot } from "mineflayer";

describe("rotate command", () => {
  it("rotates by yaw delta relative to current orientation (positive yaw turns right)", async () => {
    const port = await freePort();
    let server!: ReturnType<typeof createRuntimeHttpServer>;
    const queue = new CommandQueue({
      cleanup: async () => undefined,
      emit: (event) => server.broadcast(event),
      defaultTimeoutMs: 3000
    });

    let capturedLook: { yaw: number; pitch: number } | null = null;
    const actions = fakeActions(() => ({ yaw: 90, pitch: 0 }), (input) => {
      capturedLook = input;
    });

    server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState({ x: 0, y: 64, z: 0 }),
      commands: {
        queue,
        applyControlStates: async () => undefined,
        actions
      }
    } as never);

    await server.start();
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/command/rotate`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ yaw: -30, pitch: 0 })
      });
      const body = await res.json();
      expect(res.status).toBe(200);
      expect(body.ok).toBe(true);

      // Request yaw -30 = turn left 30°. Mineflayer yaw increases counterclockwise,
      // so the handler asks look() for 90 - (-30) = 120°.
      expect(capturedLook).not.toBeNull();
      expect(capturedLook!.yaw).toBeCloseTo(120, 5);
      expect(capturedLook!.pitch).toBeCloseTo(0, 5);
    } finally {
      await server.stop();
    }
  });

  it("applies pitch delta relative to current orientation (positive pitch looks up)", async () => {
    const port = await freePort();
    let server!: ReturnType<typeof createRuntimeHttpServer>;
    const queue = new CommandQueue({
      cleanup: async () => undefined,
      emit: (event) => server.broadcast(event),
      defaultTimeoutMs: 3000
    });

    let capturedLook: { yaw: number; pitch: number } | null = null;
    const actions = fakeActions(() => ({ yaw: 0, pitch: -10 }), (input) => {
      capturedLook = input;
    });

    server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState({ x: 0, y: 64, z: 0 }),
      commands: {
        queue,
        applyControlStates: async () => undefined,
        actions
      }
    } as never);

    await server.start();
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/command/rotate`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ yaw: 0, pitch: 25 })
      });
      expect(res.status).toBe(200);
      expect(capturedLook).not.toBeNull();
      expect(capturedLook!.pitch).toBeCloseTo(15, 5);
    } finally {
      await server.stop();
    }
  });

  it("wraps yaw at 360 degrees inside the look action", async () => {
    const captured: Array<{ yaw: number; pitch: number }> = [];
    const actions = createPhysicalCommandActions(fakeBot(captured));

    const result = await actions.look({ yaw: -20, pitch: 0 });
    expect(result.ok).toBe(true);
    expect(captured).toHaveLength(1);
    // -20° wraps to 340°; bot.look receives radians.
    expect(captured[0].yaw).toBeCloseTo((340 * Math.PI) / 180, 5);
    expect(actions.getOrientation().yaw).toBeCloseTo(340, 5);
  });

  it("clamps pitch at vertical limits inside the look action", async () => {
    const captured: Array<{ yaw: number; pitch: number }> = [];
    const actions = createPhysicalCommandActions(fakeBot(captured));

    const result = await actions.look({ yaw: 0, pitch: 100 });
    expect(result.ok).toBe(true);
    expect(captured).toHaveLength(1);
    expect(captured[0].pitch).toBeCloseTo((89.5 * Math.PI) / 180, 5);
    expect(actions.getOrientation().pitch).toBeCloseTo(89.5, 5);
  });

  it("rejects yaw delta exceeding 180 degrees", async () => {
    const port = await freePort();
    let server!: ReturnType<typeof createRuntimeHttpServer>;
    const queue = new CommandQueue({
      cleanup: async () => undefined,
      emit: (event) => server.broadcast(event),
      defaultTimeoutMs: 3000
    });

    server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState({ x: 0, y: 64, z: 0 }),
      commands: {
        queue,
        applyControlStates: async () => undefined,
        actions: fakeActions(() => ({ yaw: 0, pitch: 0 }), () => undefined)
      }
    } as never);

    await server.start();
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/command/rotate`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ yaw: 200, pitch: 0 })
      });
      expect(res.status).toBe(400);
      const body = await res.json();
      expect(body.ok).toBe(false);
      expect(body.error).toBe("invalid_angles");
    } finally {
      await server.stop();
    }
  });

  it("rejects pitch delta exceeding 90 degrees", async () => {
    const port = await freePort();
    let server!: ReturnType<typeof createRuntimeHttpServer>;
    const queue = new CommandQueue({
      cleanup: async () => undefined,
      emit: (event) => server.broadcast(event),
      defaultTimeoutMs: 3000
    });

    server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState({ x: 0, y: 64, z: 0 }),
      commands: {
        queue,
        applyControlStates: async () => undefined,
        actions: fakeActions(() => ({ yaw: 0, pitch: 0 }), () => undefined)
      }
    } as never);

    await server.start();
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/command/rotate`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ yaw: 0, pitch: 100 })
      });
      expect(res.status).toBe(400);
      const body = await res.json();
      expect(body.ok).toBe(false);
      expect(body.error).toBe("invalid_angles");
    } finally {
      await server.stop();
    }
  });

  it("reads orientation at execution time, not request time", async () => {
    const port = await freePort();
    let server!: ReturnType<typeof createRuntimeHttpServer>;
    const queue = new CommandQueue({
      cleanup: async () => undefined,
      emit: (event) => server.broadcast(event),
      defaultTimeoutMs: 3000
    });

    let currentYaw = 45;
    let capturedLook: { yaw: number; pitch: number } | null = null;
    const actions = fakeActions(() => ({ yaw: currentYaw, pitch: 0 }), (input) => {
      capturedLook = input;
    });

    server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState({ x: 0, y: 64, z: 0 }),
      commands: {
        queue,
        applyControlStates: async () => undefined,
        actions
      }
    } as never);

    await server.start();
    try {
      currentYaw = 45;
      const res = await fetch(`http://127.0.0.1:${port}/api/command/rotate`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ yaw: 30, pitch: 0 })
      });
      expect(res.status).toBe(200);

      // Executed against the orientation supplier's value at run time: 45 - 30 = 15.
      expect(capturedLook).not.toBeNull();
      expect(capturedLook!.yaw).toBeCloseTo(15, 5);
    } finally {
      await server.stop();
    }
  });
});

function fakeActions(
  getOrientation: () => { yaw: number; pitch: number },
  onLook: (input: { yaw: number; pitch: number }) => void
) {
  return {
    getOrientation,
    look: async (input: { yaw: number; pitch: number }) => {
      onLook(input);
      return { ok: true, message: "Looking.", data: input };
    },
    lookAt: async () => ({ ok: true, message: "ok" }),
    walkTo: async () => ({ ok: true, message: "ok" }),
    mineBlock: async () => ({ ok: true, message: "ok" }),
    placeBlock: async () => ({ ok: true, message: "ok" }),
    useBlock: async () => ({ ok: true, message: "ok" }),
    inspectBlock: async () => ({ ok: true, message: "ok" })
  };
}

function fakeBot(captured: Array<{ yaw: number; pitch: number }>): Bot {
  return {
    look: async (yaw: number, pitch: number) => {
      captured.push({ yaw, pitch });
    },
    entity: undefined
  } as unknown as Bot;
}

function healthInput() {
  return {
    startedAt: new Date("2026-06-17T19:00:00Z"),
    config: {
      minecraft: { host: "127.0.0.1", port: 25565, username: "turnbased-bot" },
      web: { host: "127.0.0.1", port: 3000 },
      viewer: { enabled: true, port: 3001, firstPerson: true },
      command: { timeoutMs: 30000, maxFineControlDurationMs: 3000, stateBroadcastIntervalMs: 500 },
      evidence: { directory: "evidence" }
    },
    bot: { connecting: false, connected: false, spawned: false, username: "turnbased-bot", lastError: null },
    paper: { reachable: true, checkedAt: "2026-06-17T19:00:01.000Z", error: null },
    viewer: { enabled: true, started: false, port: 3001, url: null, error: null }
  };
}

function disconnectedState(position: { x: number; y: number; z: number }) {
  return {
    connected: false,
    username: "turnbased-bot",
    position,
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
  return new Promise<number>((resolve, reject) => {
    const server = createNetServer();
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      if (address === null || typeof address === "string") {
        reject(new Error("Could not allocate test port."));
        return;
      }
      const port = address.port;
      server.close(() => {
        // Brief pause to let the OS release the socket
        setTimeout(() => resolve(port), 50);
      });
    });
  });
}
