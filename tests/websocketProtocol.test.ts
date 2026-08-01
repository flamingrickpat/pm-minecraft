import { createHash } from "node:crypto";
import { once } from "node:events";
import { createServer as createNetServer, connect, type Socket } from "node:net";
import { describe, expect, it } from "vitest";
import { createRuntimeHttpServer } from "../src/server/http.js";

describe("WebSocket ping/pong protocol", () => {
  it("responds to a ping frame with a pong frame", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState()
    } as never);

    await server.start();
    try {
      const socket = connect(port, "127.0.0.1");
      socket.on("error", () => undefined);

      // Set up a frame collector that strips the HTTP handshake and collects WS frames
      const frames: Buffer[] = [];
      let frameBuffer = Buffer.alloc(0);
      socket.on("data", (chunk: Buffer) => {
        frameBuffer = Buffer.concat([frameBuffer, Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)]);
        const headerEnd = frameBuffer.indexOf("\r\n\r\n");
        if (headerEnd >= 0) {
          frameBuffer = frameBuffer.subarray(headerEnd + 4);
        }
        // Extract complete text frames
        for (;;) {
          const decoded = decodeWebSocketTextFrame(frameBuffer);
          if (!decoded) break;
          frames.push(frameBuffer.subarray(frameBuffer.length - decoded.consumed));
          frameBuffer = Buffer.alloc(0);
        }
      });

      socket.write(webSocketHandshake(port));
      await waitFor(() => server.status.webSocket.clients === 1);

      // Wait for any broadcast frames to arrive
      await new Promise((r) => setTimeout(r, 150));
      frames.length = 0; // Clear broadcast frames

      // Send a WebSocket ping frame (opcode 0x9) with a small payload
      const pingPayload = Buffer.from("keepalive", "utf8");
      const pingFrame = buildClientWebSocketFrame(0x9, pingPayload);
      socket.write(pingFrame);

      // Wait for the pong response
      await waitFor(() => frames.length > 0);
      const pongFrame = frames[frames.length - 1];
      if (pongFrame.length < 2) {
        throw new Error("Expected pong frame but got insufficient data");
      }
      const opcode = pongFrame[0] & 0x0f;
      expect(opcode).toBe(0x0a); // pong opcode
    } finally {
      await server.stop();
    }
  });

  it("echoes the ping payload in the pong frame", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState()
    } as never);

    await server.start();
    try {
      const socket = connect(port, "127.0.0.1");
      socket.on("error", () => undefined);
      socket.write(webSocketHandshake(port));
      await waitFor(() => server.status.webSocket.clients === 1);

      // Wait for broadcast to complete, then drain any residual data
      await new Promise((r) => setTimeout(r, 200));
      socket.removeAllListeners("data");

      // Collect all incoming data for a short window to drain broadcasts
      await new Promise<void>((resolve) => {
        const timer = setTimeout(resolve, 100);
        socket.on("data", () => {
          clearTimeout(timer);
          setTimeout(resolve, 10);
        });
      });
      socket.removeAllListeners("data");

      // Send ping with known payload (masked per RFC 6455)
      const pingPayload = Buffer.from("echo-test-payload-123", "utf8");
      const pingFrame = buildClientWebSocketFrame(0x9, pingPayload);
      socket.write(pingFrame);

      // Read the pong and verify payload matches
      const data = await readRaw(socket, 2000);
      if (data.length < 2) {
        throw new Error("Expected pong frame header but got insufficient data");
      }
      const opcode = data[0] & 0x0f;
      expect(opcode).toBe(0x0a); // pong opcode
      const length = data[1] & 0x7f;
      const pongPayload = data.subarray(2, 2 + length);
      expect(pongPayload.toString("utf8")).toBe("echo-test-payload-123");
    } finally {
      await server.stop();
    }
  });

  it("removes client on socket close", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState()
    } as never);

    await server.start();
    try {
      const socket = connect(port, "127.0.0.1");
      socket.on("error", () => undefined);
      socket.write(webSocketHandshake(port));
      await waitFor(() => server.status.webSocket.clients === 1);
      expect(server.status.webSocket.clients).toBe(1);

      // Wait for broadcast to complete, then send a proper WebSocket close frame
      await new Promise((r) => setTimeout(r, 150));
      // Send WebSocket close frame (opcode 0x8, masked, empty payload)
      const closeFrame = buildClientWebSocketFrame(0x8, Buffer.alloc(0));
      socket.write(closeFrame);

      // Wait for the server to process the close and destroy the socket
      await waitFor(() => server.status.webSocket.clients === 0);
      expect(server.status.webSocket.clients).toBe(0);
    } finally {
      await server.stop();
    }
  });
});

describe("Hotbar select route", () => {
  it("POST /api/hotbar/select accepts hotbarIndex parameter", async () => {
    const port = await freePort();
    const mockInventory = {
      getInventory: () => ({
        selectedHotbarSlot: 0,
        heldItem: null,
        hotbar: [],
        main: [],
        totalSlots: 46,
        usedSlots: 0
      }),
      selectHotbar: async (slot: number) => ({
        ok: true,
        slot,
        message: `Selected hotbar slot ${slot}.`
      }),
      equipItem: async () => ({
        ok: false,
        error: "item_not_found",
        message: "Not found"
      })
    };

    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState(),
      inventory: mockInventory as never
    } as never);

    await server.start();
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/hotbar/select`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ hotbarIndex: 3 })
      });
      expect(res.status).toBe(200);
      const body = await res.json();
      expect(body.ok).toBe(true);
      expect(body.slot).toBe(3);
    } finally {
      await server.stop();
    }
  });

  it("POST /api/hotbar/select rejects out-of-range hotbarIndex", async () => {
    const port = await freePort();
    const mockInventory = {
      getInventory: () => ({}),
      selectHotbar: async () => ({ ok: true, slot: 0, message: "ok" }),
      equipItem: async () => ({})
    };

    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState(),
      inventory: mockInventory as never
    } as never);

    await server.start();
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/hotbar/select`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ hotbarIndex: 10 })
      });
      expect(res.status).toBe(400);
      const body = await res.json();
      expect(body.ok).toBe(false);
    } finally {
      await server.stop();
    }
  });

  it("POST /api/hotbar/select returns 503 when inventory service is missing", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState()
    } as never);

    await server.start();
    try {
      const res = await fetch(`http://127.0.0.1:${port}/api/hotbar/select`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ hotbarIndex: 0 })
      });
      expect(res.status).toBe(503);
    } finally {
      await server.stop();
    }
  });
});

// ── Helpers ──

/**
 * Build a client-side WebSocket frame (masked per RFC 6455 §5.1).
 * Client-to-server frames MUST be masked.
 */
function buildClientWebSocketFrame(opcode: number, payload: Buffer): Buffer {
  const len = payload.length;
  const maskKey = Buffer.from([0x12, 0x34, 0x56, 0x78]);

  // Mask the payload
  const maskedPayload = Buffer.alloc(len);
  for (let i = 0; i < len; i++) {
    maskedPayload[i] = payload[i] ^ maskKey[i % 4];
  }

  if (len <= 125) {
    const frame = Buffer.alloc(6 + len); // 2 header + 4 mask + payload
    frame[0] = 0x80 | opcode;
    frame[1] = 0x80 | len; // mask bit set
    maskKey.copy(frame, 2);
    maskedPayload.copy(frame, 6);
    return frame;
  }
  // Extended length (126)
  const frame = Buffer.alloc(8 + len); // 4 header + 4 mask + payload
  frame[0] = 0x80 | opcode;
  frame[1] = 0x80 | 126;
  frame.writeUInt16BE(len, 2);
  maskKey.copy(frame, 4);
  maskedPayload.copy(frame, 8);
  return frame;
}

function decodeWebSocketTextFrame(buffer: Buffer): { text: string; consumed: number } | null {
  if (buffer.length < 2) return null;
  const lengthByte = buffer[1] & 0x7f;
  const headerLength = lengthByte === 126 ? 4 : lengthByte === 127 ? 10 : 2;
  if (buffer.length < headerLength) return null;
  const length = lengthByte === 126
    ? buffer.readUInt16BE(2)
    : lengthByte === 127
      ? Number(buffer.readBigUInt64BE(2))
      : lengthByte;
  if (buffer.length < headerLength + length) return null;
  return {
    text: buffer.subarray(headerLength, headerLength + length).toString("utf8"),
    consumed: headerLength + length
  };
}

function readRaw(socket: Socket, timeoutMs: number): Promise<Buffer> {
  return new Promise<Buffer>((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("read timeout")), timeoutMs);
    socket.once("data", (chunk: Buffer) => {
      clearTimeout(timer);
      resolve(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
    });
  });
}

async function freePort(): Promise<number> {
  const srv = createNetServer();
  srv.listen(0, "127.0.0.1");
  await once(srv, "listening");
  const addr = srv.address();
  if (addr === null || typeof addr === "string") throw new Error("Could not allocate test port.");
  const port = addr.port;
  srv.close();
  await once(srv, "close");
  return port;
}

function webSocketHandshake(port: number): string {
  const key = createHash("sha1").update(`test-${port}-${Date.now()}`).digest("base64").slice(0, 24);
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

async function waitFor(predicate: () => boolean): Promise<void> {
  const deadline = Date.now() + 2000;
  while (Date.now() < deadline) {
    if (predicate()) return;
    await new Promise((r) => setTimeout(r, 10));
  }
  throw new Error("Timed out waiting for test condition.");
}
