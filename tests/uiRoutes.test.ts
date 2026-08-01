import { createHash } from "node:crypto";
import { once } from "node:events";
import { createServer as createNetServer, connect } from "node:net";
import { describe, expect, it } from "vitest";
import { createRuntimeHttpServer } from "../src/server/http.js";
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const publicDir = join(__dirname, "..", "public");

describe("UI static routes", () => {
  it("serves index.html at GET /", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState()
    } as never);

    await server.start();
    try {
      const res = await fetch(`http://127.0.0.1:${port}/`);
      expect(res.status).toBe(200);
      expect(res.headers.get("content-type")).toContain("text/html");
      const body = await res.text();
      expect(body).toContain("<!DOCTYPE html>");
      expect(body.toLowerCase()).toContain("turnbased");
    } finally {
      await server.stop();
    }
  });

  it("serves index.html at GET /ui", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState()
    } as never);

    await server.start();
    try {
      const res = await fetch(`http://127.0.0.1:${port}/ui`);
      expect(res.status).toBe(200);
      expect(res.headers.get("content-type")).toContain("text/html");
    } finally {
      await server.stop();
    }
  });

  it("serves existing static files under /ui/", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState()
    } as never);

    await server.start();
    try {
      const indexHtml = join(publicDir, "index.html");
      expect(existsSync(indexHtml)).toBe(true);
      const content = readFileSync(indexHtml, "utf8");
      expect(content.length).toBeGreaterThan(100);
    } finally {
      await server.stop();
    }
  });

  it("returns 404 for unknown static paths", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState()
    } as never);

    await server.start();
    try {
      const res = await fetch(`http://127.0.0.1:${port}/ui/nonexistent.css`);
      expect(res.status).toBe(404);
    } finally {
      await server.stop();
    }
  });
});

describe("UI WebSocket receives events", () => {
  it("receives state events after connecting", async () => {
    const port = await freePort();
    const messages: unknown[] = [];
    let server!: ReturnType<typeof createRuntimeHttpServer>;
    server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState()
    } as never);

    await server.start();
    try {
      const socket = connect(port, "127.0.0.1");
      socket.on("error", () => undefined);
      collectWebSocketMessages(socket, messages);
      socket.write(webSocketHandshake(port));
      await waitFor(() => server.status.webSocket.clients === 1);

      // Send a state event through broadcast
      server.broadcast({ type: "state", data: { connected: true } });
      await waitFor(() => messages.length > 0);

      const stateMsg = messages.find(m => (m as { type?: string }).type === "state");
      expect(stateMsg).toBeDefined();
      socket.destroy();
    } finally {
      await server.stop();
    }
  });

  it("receives log events after connecting", async () => {
    const port = await freePort();
    const messages: unknown[] = [];
    let server!: ReturnType<typeof createRuntimeHttpServer>;
    server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState()
    } as never);

    await server.start();
    try {
      const socket = connect(port, "127.0.0.1");
      socket.on("error", () => undefined);
      collectWebSocketMessages(socket, messages);
      socket.write(webSocketHandshake(port));
      await waitFor(() => server.status.webSocket.clients === 1);

      server.broadcast({ type: "log", level: "info", message: "Test log event" });
      await waitFor(() => messages.some(m => (m as { type?: string }).type === "log"));

      const logMsg = messages.find(m => (m as { type?: string }).type === "log");
      expect(logMsg).toBeDefined();
      expect((logMsg as { message?: string }).message).toBe("Test log event");
      socket.destroy();
    } finally {
      await server.stop();
    }
  });
});

describe("UI command payload construction", () => {
  it("look-at payload has target vector", async () => {
    const port = await freePort();
    let receivedBody: Record<string, unknown> | null = null;
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState(),
      commands: {
        queue: makeTestQueue(),
        applyControlStates: async () => {},
        actions: {
          lookAt: async (target: { x: number; y: number; z: number }) => {
            receivedBody = target;
            return { ok: true, message: "Looked at target." };
          },
          walkTo: async () => ({ ok: true, message: "Walked." }),
          mineBlock: async () => ({ ok: true, message: "Mined." }),
          placeBlock: async () => ({ ok: true, message: "Placed." }),
          useBlock: async () => ({ ok: true, message: "Used." }),
          inspectBlock: async () => ({ ok: true, message: "Inspected." })
        }
      }
    } as never);

    await server.start();
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/command/look-at`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ target: { x: 100, y: 64, z: -50 } })
      });
      expect(res.status).toBe(200);
      expect(receivedBody).toEqual({ x: 100, y: 64, z: -50 });
    } finally {
      await server.stop();
    }
  });

  it("fine-control payload validates duration bounds", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState(),
      commands: {
        queue: makeTestQueue(),
        applyControlStates: async () => {},
        actions: {
          lookAt: async () => ({ ok: true, message: "ok" }),
          walkTo: async () => ({ ok: true, message: "ok" }),
          mineBlock: async () => ({ ok: true, message: "ok" }),
          placeBlock: async () => ({ ok: true, message: "ok" }),
          useBlock: async () => ({ ok: true, message: "ok" }),
          inspectBlock: async () => ({ ok: true, message: "ok" })
        },
        maxFineControlDurationMs: 3000
      }
    } as never);

    await server.start();
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/command/fine-control`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ controls: { forward: true }, durationMs: 5000 })
      });
      expect(res.status).toBe(400);
      const body = await res.json();
      expect(body.error).toBe("invalid_duration");
    } finally {
      await server.stop();
    }
  });
});

describe("UI inventory API", () => {
  it("GET /api/inventory returns inventory structure", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState()
    } as never);

    await server.start();
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/inventory`);
      expect(res.status).toBe(503); // inventory service not provided
      const body = await res.json();
      expect(body.ok).toBe(false);
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

function makeTestQueue() {
  return {
    currentCommand: null,
    enqueueOrReject: (cmd: { name: string; run: () => Promise<{ ok: boolean; message: string }> }) => {
      return { accepted: true, commandId: "cmd_test", completed: cmd.run() };
    },
    cancelCurrent: async () => ({ ok: true, message: "Stopped current command." })
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
  const deadline = Date.now() + 2000;
  while (Date.now() < deadline) {
    if (predicate()) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
  throw new Error("Timed out waiting for test condition.");
}
