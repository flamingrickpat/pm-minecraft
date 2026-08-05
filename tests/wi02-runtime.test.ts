import { createHash } from "node:crypto";
import { createServer as createNetServer, connect } from "node:net";
import { once } from "node:events";
import { describe, expect, it } from "vitest";
import { createRuntimeHttpServer } from "../src/server/http.js";
import { serializeHealth } from "../src/server/health.js";
import { serializeState } from "../src/server/state.js";
import { createBotStateSnapshot } from "../src/state/botState.js";

describe("WI-02 runtime transport", () => {
  it("reports detailed HTTP, WebSocket, bot, Paper, and viewer readiness", () => {
    expect(
      serializeHealth({
        ...healthInput(),
        http: { listening: true, host: "127.0.0.1", port: 3000, url: "http://127.0.0.1:3000", error: null },
        webSocket: { enabled: true, path: "/ws", clients: 2, error: null },
        viewer: {
          enabled: true,
          started: false,
          port: 3001,
          url: null,
          firstPerson: true,
          error: "Cannot find module 'canvas'"
        }
      } as never)
    ).toMatchObject({
      ready: false,
      http: { listening: true, url: "http://127.0.0.1:3000" },
      webSocket: { enabled: true, path: "/ws", clients: 2 },
      viewer: { started: false, firstPerson: true, error: "Cannot find module 'canvas'" }
    });
  });

  it("creates enriched state snapshots from narrow fake bot objects", () => {
    const snapshot = createBotStateSnapshot(
      {
        username: "turnbased-bot",
        entity: { position: { x: 1, y: 65, z: -3 }, yaw: 0.5, pitch: -0.1 },
        game: { dimension: "minecraft:overworld" },
        health: 17,
        food: 16,
        quickBarSlot: 4,
        heldItem: { name: "oak_log", displayName: "Oak Log", count: 5, slot: 40 },
        inventory: {
          slots: [
            null,
            { name: "oak_log", displayName: "Oak Log", count: 5, slot: 10 },
            { name: "stick", displayName: "Stick", count: 2, slot: 11 }
          ]
        }
      },
      { connected: true, username: "turnbased-bot" }
    );

    expect(snapshot).toEqual({
      connected: true,
      username: "turnbased-bot",
      position: { x: 1, y: 65, z: -3 },
      yaw: 0.5,
      pitch: -0.1,
      yawDegrees: 28.6,
      pitchDegrees: -5.7,
      facing: "northwest",
      dimension: "minecraft:overworld",
      health: 17,
      food: 16,
      selectedHotbarSlot: 4,
      heldItem: { name: "oak_log", displayName: "Oak Log", count: 5, slot: 40 },
      inventory: {
        totalSlots: 3,
        usedSlots: 2,
        items: [
          { slot: 10, name: "oak_log", displayName: "Oak Log", count: 5 },
          { slot: 11, name: "stick", displayName: "Stick", count: 2 }
        ]
      },
      crosshairBlock: null
    });
  });

  it("serializes enriched live bot state fields", () => {
    expect(
      serializeState({
        connected: true,
        username: "turnbased-bot",
        position: { x: 12.5, y: 64, z: -8.25 },
        yaw: 1.5,
        pitch: -0.25,
        yawDegrees: 85.9,
        pitchDegrees: -14.3,
        facing: "west",
        dimension: "minecraft:overworld",
        health: 18,
        food: 19,
        selectedHotbarSlot: 3,
        heldItem: { name: "oak_log", displayName: "Oak Log", count: 4, slot: 39 },
        inventory: {
          totalSlots: 46,
          usedSlots: 2,
          items: [
            { slot: 10, name: "oak_log", displayName: "Oak Log", count: 4 },
            { slot: 39, name: "wooden_axe", displayName: "Wooden Axe", count: 1 }
          ]
        },
        crosshairBlock: null
      })
    ).toEqual({
      connected: true,
      username: "turnbased-bot",
      position: { x: 12.5, y: 64, z: -8.25 },
      yaw: 1.5,
      pitch: -0.25,
      yawDegrees: 85.9,
      pitchDegrees: -14.3,
      facing: "west",
      dimension: "minecraft:overworld",
      health: 18,
      food: 19,
      selectedHotbarSlot: 3,
      heldItem: { name: "oak_log", displayName: "Oak Log", count: 4, slot: 39 },
      inventory: {
        totalSlots: 46,
        usedSlots: 2,
        items: [
          { slot: 10, name: "oak_log", displayName: "Oak Log", count: 4 },
          { slot: 39, name: "wooden_axe", displayName: "Wooden Axe", count: 1 }
        ]
      },
      crosshairBlock: null,
      currentCommand: null
    });
  });

  it("rejects malformed chat before reaching Mineflayer", async () => {
    const port = await freePort();
    const chatCalls: string[] = [];
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState(),
      chat: {
        send: async (text: string) => {
          chatCalls.push(text);
        }
      }
    } as never);

    await server.start();
    try {
      const response = await fetch(`http://127.0.0.1:${port}/api/chat/send`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text: "" })
      });

      expect(response.status).toBe(400);
      expect(await response.json()).toEqual({
        ok: false,
        error: "invalid_chat_text",
        message: "Chat text must be a non-empty string."
      });
      expect(chatCalls).toEqual([]);
    } finally {
      await server.stop();
    }
  });

  it("rejects progression-changing console commands before reaching Mineflayer", async () => {
    const port = await freePort();
    const chatCalls: string[] = [];
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState(),
      chat: { send: async (text: string) => { chatCalls.push(text); } }
    } as never);

    await server.start();
    try {
      for (const text of [
        "/give @p iron_pickaxe",
        "/gamemode creative",
        "/tp @p 0 100 0",
        "/execute as @p run give @s iron_ingot",
        "/kill @e"
      ]) {
        const response = await fetch(`http://127.0.0.1:${port}/api/chat/send`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ text })
        });
        expect(response.status).toBe(403);
        expect(await response.json()).toMatchObject({ ok: false, error: "console_command_forbidden" });
      }
      expect(chatCalls).toEqual([]);
    } finally {
      await server.stop();
    }
  });

  it("allows ordinary chat and non-progression commands", async () => {
    const port = await freePort();
    const chatCalls: string[] = [];
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState(),
      chat: { send: async (text: string) => { chatCalls.push(text); } }
    } as never);

    await server.start();
    try {
      for (const text of ["hello", "/say hello", "/list", "/kill"]) {
        const response = await fetch(`http://127.0.0.1:${port}/api/chat/send`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ text })
        });
        expect(response.status).toBe(200);
      }
      expect(chatCalls).toEqual(["hello", "/say hello", "/list", "/kill"]);
    } finally {
      await server.stop();
    }
  });

  it("broadcasts serialized WebSocket state, log, chat, and error events", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState()
    });

    await server.start();
    try {
      const socket = connect(port, "127.0.0.1");
      socket.on("error", () => undefined);
      const messages: string[] = [];
      let buffer = Buffer.alloc(0);
      socket.on("data", (chunk) => {
        buffer = Buffer.concat([buffer, chunk]);
        const headerEnd = buffer.indexOf("\r\n\r\n");
        if (headerEnd >= 0) {
          buffer = buffer.subarray(headerEnd + 4);
        }
        for (;;) {
          const decoded = decodeWebSocketTextFrame(buffer);
          if (!decoded) {
            break;
          }
          messages.push(decoded.text);
          buffer = buffer.subarray(decoded.consumed);
        }
      });

      socket.write(webSocketHandshake(port));
      await waitFor(() => server.status.webSocket.clients === 1);
      (server as { broadcast: (event: unknown) => void }).broadcast({ type: "state", data: { connected: true } });
      (server as { broadcast: (event: unknown) => void }).broadcast({ type: "log", level: "info", message: "ready" });
      (server as { broadcast: (event: unknown) => void }).broadcast({ type: "chat", username: "Steve", message: "hello" });
      (server as { broadcast: (event: unknown) => void }).broadcast({ type: "error", message: "viewer failed" });

      await waitFor(() => messages.length === 4);
      expect(messages.map((message) => JSON.parse(message))).toEqual([
        { type: "state", data: { connected: true } },
        { type: "log", level: "info", message: "ready" },
        { type: "chat", username: "Steve", message: "hello" },
        { type: "error", message: "viewer failed" }
      ]);
      socket.destroy();
    } finally {
      await server.stop();
    }
  });

  it("drops disconnected WebSocket clients without throwing on later broadcasts", async () => {
    const port = await freePort();
    const server = createRuntimeHttpServer({
      config: { host: "127.0.0.1", port },
      health: () => healthInput(),
      state: () => disconnectedState()
    });

    await server.start();
    try {
      const socket = connect(port, "127.0.0.1");
      socket.on("error", () => undefined);
      await new Promise<void>((resolve, reject) => {
        socket.once("connect", resolve);
        socket.once("error", reject);
      });
      socket.write(webSocketHandshake(port));
      await waitFor(() => server.status.webSocket.clients === 1);
      socket.destroy();

      expect(() => server.broadcast({ type: "state", data: disconnectedState() })).not.toThrow();
      await new Promise((resolve) => setTimeout(resolve, 50));
    } finally {
      await server.stop();
    }
  });
});

function healthInput() {
  return {
    startedAt: new Date("2026-06-17T19:00:00Z"),
    config: {
      minecraft: { host: "127.0.0.1", port: 25565, username: "turnbased-bot", mineVisibilityIgnoreDistance: 3, walkToMaxDistance: 16 },
      web: { host: "127.0.0.1", port: 3000 },
      viewer: { enabled: true, port: 3001, firstPerson: true, captureWidth: 640, captureHeight: 640, deviceScaleFactor: 2, fovDegrees: 80 },
      command: { timeoutMs: 30000, maxFineControlDurationMs: 3000, stateBroadcastIntervalMs: 500 },
      evidence: { directory: "evidence" },
      actionLog: { enabled: false, directory: "logs/actions", nearbyBlockRadius: 8 }
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

function decodeWebSocketTextFrame(buffer: Buffer): { text: string; consumed: number } | null {
  if (buffer.length < 2) {
    return null;
  }
  const length = buffer[1] & 0x7f;
  const headerLength = length === 126 ? 4 : length === 127 ? 10 : 2;
  if (length > 125) {
    throw new Error("Test decoder only supports small text frames.");
  }
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
