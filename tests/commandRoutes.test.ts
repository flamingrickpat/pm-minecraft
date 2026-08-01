import { createHash } from "node:crypto";
import { once } from "node:events";
import { createServer as createNetServer, connect } from "node:net";
import { describe, expect, it } from "vitest";
import { CommandQueue } from "../src/commands/commandQueue.js";
import { createRuntimeHttpServer } from "../src/server/http.js";

describe("command HTTP routes", () => {
  it("returns HTTP 409 when a physical command is already running", async () => {
    const port = await freePort();
    let server!: ReturnType<typeof createRuntimeHttpServer>;
    const queue = new CommandQueue({ cleanup: async () => undefined, emit: (event) => server.broadcast(event), defaultTimeoutMs: 1000 });
    server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState(),
      commands: {
        queue,
        applyControlStates: async () => undefined
      }
    } as never);

    await server.start();
    try {
      const first = fetch(`http://127.0.0.1:${port}/api/command/fine-control`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ controls: { forward: true }, durationMs: 1000 })
      });
      await waitFor(() => queue.currentCommand?.status === "running");

      const conflict = await fetch(`http://127.0.0.1:${port}/api/command/fine-control`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ controls: { jump: true }, durationMs: 1 })
      });
      expect(conflict.status).toBe(409);
      expect(await conflict.json()).toMatchObject({
        ok: false,
        error: "command_conflict",
        message: "A physical command is already running."
      });

      await fetch(`http://127.0.0.1:${port}/api/command/stop`, { method: "POST" });
      await first;
    } finally {
      await server.stop();
    }
  });

  it("accepts stop during a running command and broadcasts command events", async () => {
    const port = await freePort();
    const messages: unknown[] = [];
    let server!: ReturnType<typeof createRuntimeHttpServer>;
    const queue = new CommandQueue({ cleanup: async () => undefined, emit: (event) => server.broadcast(event), defaultTimeoutMs: 1000 });
    server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState(),
      commands: {
        queue,
        applyControlStates: async () => undefined
      }
    } as never);

    await server.start();
    try {
      const socket = connect(port, "127.0.0.1");
      socket.on("error", () => undefined);
      collectWebSocketMessages(socket, messages);
      socket.write(webSocketHandshake(port));
      await waitFor(() => server.status.webSocket.clients === 1);

      const first = fetch(`http://127.0.0.1:${port}/api/command/fine-control`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ controls: { forward: true }, durationMs: 1000 })
      });
      await waitFor(() => queue.currentCommand?.status === "running");

      const stop = await fetch(`http://127.0.0.1:${port}/api/command/stop`, { method: "POST" });
      expect(stop.status).toBe(200);
      expect(await stop.json()).toEqual({ ok: true, message: "Stopped current command." });
      await first;

      await waitFor(() => messages.some((message) => (message as { type?: string }).type === "command_cancelled"));
      expect(messages).toEqual(expect.arrayContaining([
        expect.objectContaining({ type: "command_started", command: "fine_control" }),
        expect.objectContaining({ type: "command_cancelled", reason: "command_cancelled" }),
        expect.objectContaining({ type: "log", message: expect.stringContaining("cancelled") })
      ]));
      socket.destroy();
    } finally {
      await server.stop();
    }
  });
});

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

function webSocketHandshake(port: number): string {
  const key = createHash("sha1").update(`test-${port}`).digest("base64").slice(0, 16);
  return [
    "GET /ws HTTP/1.1",
    `Host: 127.0.0.1:${port}`,
    "Upgrade: websocket",
    "Connection: Upgrade",
    `Sec-WebSocket-Key: ${key}`,
    "Sec-WebSocket-Version: 13",
    "",
    ""
  ].join("\r\n");
}

function collectWebSocketMessages(socket: NodeJS.ReadWriteStream, messages: unknown[]): void {
  let buffer = Buffer.alloc(0);
  socket.on("data", (chunk) => {
    buffer = Buffer.concat([buffer, Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)]);
    const headerEnd = buffer.indexOf("\r\n\r\n");
    if (headerEnd >= 0) {
      buffer = buffer.subarray(headerEnd + 4);
    }
    for (;;) {
      const decoded = decodeWebSocketTextFrame(buffer);
      if (!decoded) {
        break;
      }
      messages.push(JSON.parse(decoded.text));
      buffer = buffer.subarray(decoded.consumed);
    }
  });
}

function decodeWebSocketTextFrame(buffer: Buffer): { text: string; consumed: number } | null {
  if (buffer.length < 2) {
    return null;
  }
  const lengthByte = buffer[1] & 0x7f;
  const headerLength = lengthByte === 126 ? 4 : lengthByte === 127 ? 10 : 2;
  if (buffer.length < headerLength) {
    return null;
  }
  const length = lengthByte === 126
    ? buffer.readUInt16BE(2)
    : lengthByte === 127
      ? Number(buffer.readBigUInt64BE(2))
      : lengthByte;
  if (buffer.length < headerLength + length) {
    return null;
  }
  return {
    text: buffer.subarray(headerLength, headerLength + length).toString("utf8"),
    consumed: headerLength + length
  };
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
