import { once } from "node:events";
import { createServer as createNetServer } from "node:net";
import { describe, expect, it, vi } from "vitest";
import { CommandQueue } from "../src/commands/commandQueue.js";
import type { CommandResult } from "../src/commands/commandQueue.js";
import { createRuntimeHttpServer } from "../src/server/http.js";

describe("physical command HTTP routes", () => {
  it("validates target vectors and face vectors before enqueueing actions", async () => {
    await withCommandServer(async ({ port, actions }) => {
      const badTarget = await post(port, "/api/command/look-at", { target: { x: 1, y: "64", z: 3 } });
      expect(badTarget.status).toBe(400);
      expect(await badTarget.json()).toMatchObject({ ok: false, error: "invalid_target" });

      const badFace = await post(port, "/api/command/place-block", {
        referenceBlock: { x: 1, y: 64, z: 3 },
        face: { x: 1, y: 1, z: 0 }
      });
      expect(badFace.status).toBe(400);
      expect(await badFace.json()).toMatchObject({ ok: false, error: "invalid_face" });

      expect(actions.lookAt).not.toHaveBeenCalled();
      expect(actions.placeBlock).not.toHaveBeenCalled();
    });
  });

  it("bounds fine-control duration before applying controls", async () => {
    await withCommandServer(async ({ port, applyControlStates }) => {
      const response = await post(port, "/api/command/fine-control", {
        controls: { forward: true },
        durationMs: 3001
      });

      expect(response.status).toBe(400);
      expect(await response.json()).toMatchObject({
        ok: false,
        error: "invalid_duration",
        message: "durationMs must be between 1 and 3000."
      });
      expect(applyControlStates).not.toHaveBeenCalled();
    });
  });

  it("routes physical handlers through the queue and rejects overlap", async () => {
    await withCommandServer(async ({ port, actions }) => {
      let finishWalk!: () => void;
      actions.walkTo.mockImplementation(async () => {
        await new Promise<void>((resolve) => {
          finishWalk = resolve;
        });
        return { ok: true, message: "Reached target.", data: { status: "reached" } };
      });

      const walk = post(port, "/api/command/walk-to", { target: { x: 2, y: 64, z: 2 }, tolerance: 1.5, timeoutMs: 1000 });
      await waitFor(() => actions.walkTo.mock.calls.length === 1);

      const look = await post(port, "/api/command/look-at", { target: { x: 3, y: 64, z: 3 } });
      expect(look.status).toBe(409);
      expect(await look.json()).toMatchObject({ ok: false, error: "command_conflict" });
      expect(actions.lookAt).not.toHaveBeenCalled();

      finishWalk();
      const walkResponse = await walk;
      expect(walkResponse.status).toBe(200);
      expect(await walkResponse.json()).toMatchObject({ ok: true, status: "succeeded" });
    });
  });

  it("routes jump-place-block through the physical command queue", async () => {
    await withCommandServer(async ({ port, actions }) => {
      actions.jumpPlaceBlock.mockResolvedValueOnce({
        ok: true,
        message: "Jump-placed held item.",
        data: { verified: true }
      });

      const response = await post(port, "/api/command/jump-place-block", {
        referenceBlock: { x: -1, y: 94, z: -3 },
        face: { x: 0, y: 1, z: 0 },
        walkIntoRange: true
      });

      expect(response.status).toBe(200);
      expect(await response.json()).toMatchObject({
        ok: true,
        status: "succeeded",
        message: "Jump-placed held item."
      });
      expect(actions.jumpPlaceBlock).toHaveBeenCalledWith({
        referenceBlock: { x: -1, y: 94, z: -3 },
        face: { x: 0, y: 1, z: 0 },
        walkIntoRange: true
      });
    });
  });

  it("routes pillar-up without coordinates", async () => {
    await withCommandServer(async ({ port, actions }) => {
      actions.pillarUp.mockResolvedValueOnce({ ok: true, message: "Pillared up one block and landed." });

      const response = await post(port, "/api/command/pillar-up", {});

      expect(response.status).toBe(200);
      expect(await response.json()).toMatchObject({ ok: true, status: "succeeded", message: "Pillared up one block and landed." });
      expect(actions.pillarUp).toHaveBeenCalledOnce();
    });
  });

  it("reports missing and out-of-range block failures without pretending success", async () => {
    await withCommandServer(async ({ port, actions }) => {
      actions.mineBlock.mockResolvedValueOnce({
        ok: false,
        reason: "block_not_found",
        message: "No block exists at target position."
      });
      const missing = await post(port, "/api/command/mine-block", { block: { x: 1, y: 64, z: 1 }, walkIntoRange: true });
      expect(missing.status).toBe(200);
      expect(await missing.json()).toMatchObject({
        ok: false,
        status: "failed",
        reason: "block_not_found"
      });

      actions.mineBlock.mockResolvedValueOnce({
        ok: false,
        reason: "target_out_of_range",
        message: "Target block is out of range."
      });
      const far = await post(port, "/api/command/mine-block", { block: { x: 50, y: 64, z: 50 }, walkIntoRange: false });
      expect(far.status).toBe(200);
      expect(await far.json()).toMatchObject({
        ok: false,
        status: "failed",
        reason: "target_out_of_range"
      });
    });
  });

  it("reports pathfinder failure from walk-to as a failed command result", async () => {
    await withCommandServer(async ({ port, actions }) => {
      actions.walkTo.mockResolvedValueOnce({
        ok: false,
        reason: "pathfinder_failed",
        message: "No path to target.",
        data: { status: "failed" }
      });

      const response = await post(port, "/api/command/walk-to", { target: { x: 999, y: 64, z: 999 }, timeoutMs: 1000 });
      expect(response.status).toBe(200);
      expect(await response.json()).toMatchObject({
        ok: false,
        status: "failed",
        reason: "pathfinder_failed",
        message: "No path to target."
      });
    });
  });

  it("routes the chunk-limited walk with its default tolerance", async () => {
    await withCommandServer(async ({ port, actions }) => {
      const response = await post(port, "/api/command/walk-to", {
        target: { x: 2, y: 64, z: 2 },
        chunkLimit: 3
      });

      expect(response.status).toBe(200);
      expect(actions.walkTo).toHaveBeenCalledWith({
        target: { x: 2, y: 64, z: 2 },
        tolerance: 1.5,
        chunkLimit: 3
      }, expect.any(AbortSignal));
    });
  });

  it("rejects a chunk limit above the server maximum before queueing an action", async () => {
    await withCommandServer(async ({ port, actions }) => {
      const response = await post(port, "/api/command/walk-to", {
        target: { x: 2, y: 64, z: 2 },
        chunkLimit: 12
      });

      expect(response.status).toBe(400);
      expect(await response.json()).toMatchObject({ error: "chunk_limit_exceeded" });
      expect(actions.walkTo).not.toHaveBeenCalled();
    });
  });

  it("exposes read-only inspect without acquiring the physical command slot", async () => {
    await withCommandServer(async ({ port, actions }) => {
      let finishWalk!: () => void;
      actions.walkTo.mockImplementation(async () => {
        await new Promise<void>((resolve) => {
          finishWalk = resolve;
        });
        return { ok: true, message: "Reached target." };
      });
      actions.inspectBlock.mockResolvedValue({
        ok: true,
        message: "Inspected block.",
        data: { block: { x: 2, y: 63, z: 2 }, blockName: "grass_block" }
      });

      const walk = post(port, "/api/command/walk-to", { target: { x: 2, y: 64, z: 2 }, timeoutMs: 1000 });
      await waitFor(() => actions.walkTo.mock.calls.length === 1);

      const inspect = await post(port, "/api/command/inspect", { block: { x: 2, y: 63, z: 2 } });
      expect(inspect.status).toBe(200);
      expect(await inspect.json()).toMatchObject({
        ok: true,
        message: "Inspected block.",
        data: { blockName: "grass_block" }
      });

      finishWalk();
      await walk;
    });
  });
});

function createActions() {
  return {
    lookAt: vi.fn(async (): Promise<CommandResult> => ({ ok: true, message: "Looked at target." })),
    walkTo: vi.fn(async (): Promise<CommandResult> => ({ ok: true, message: "Reached target." })),
    mineBlock: vi.fn(async (): Promise<CommandResult> => ({ ok: true, message: "Mined block." })),
    placeBlock: vi.fn(async (): Promise<CommandResult> => ({ ok: true, message: "Placed held item." })),
    jumpPlaceBlock: vi.fn(async (): Promise<CommandResult> => ({ ok: true, message: "Jump-placed held item." })),
    pillarUp: vi.fn(async (): Promise<CommandResult> => ({ ok: true, message: "Pillared up one block and landed." })),
    useBlock: vi.fn(async (): Promise<CommandResult> => ({ ok: true, message: "Used block." })),
    inspectBlock: vi.fn(async (): Promise<CommandResult> => ({ ok: true, message: "Inspected block." }))
  };
}

async function withCommandServer(run: (context: {
  port: number;
  actions: ReturnType<typeof createActions>;
  applyControlStates: ReturnType<typeof vi.fn>;
}) => Promise<void>): Promise<void> {
  const port = await freePort();
  const actions = createActions();
  const applyControlStates = vi.fn(async () => undefined);
  let server!: ReturnType<typeof createRuntimeHttpServer>;
  const queue = new CommandQueue({ cleanup: async () => undefined, emit: (event) => server.broadcast(event), defaultTimeoutMs: 1000 });
  server = createRuntimeHttpServer({
    config: { host: "127.0.0.1", port },
    health: () => healthInput(),
    state: () => disconnectedState(),
    commands: {
      queue,
      applyControlStates,
      actions
    }
  } as never);

  await server.start();
  try {
    await run({ port, actions, applyControlStates });
  } finally {
    await server.stop();
  }
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

async function waitFor(predicate: () => boolean): Promise<void> {
  const deadline = Date.now() + 1000;
  while (Date.now() < deadline) {
    if (predicate()) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
  throw new Error("Timed out waiting for test condition.");
}
