import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { installPacketMonitor } from "../packetMonitor.js";
import type { Bot } from "mineflayer";
import type { RuntimeEvent } from "../../server/http.js";

interface FakeClient {
  listeners: Map<string, Array<(...args: unknown[]) => void>>;
  on(event: string, listener: (...args: unknown[]) => void): FakeClient;
  emit(event: string, ...args: unknown[]): void;
  write(name: string, params?: unknown): unknown;
  writeLog: Array<{ name: string; params?: unknown }>;
}

function createFakeClient(): FakeClient {
  const listeners = new Map<string, Array<(...args: unknown[]) => void>>();
  const client: FakeClient = {
    listeners,
    on(event, listener) {
      const list = listeners.get(event) ?? [];
      list.push(listener);
      listeners.set(event, list);
      return client;
    },
    emit(event, ...args) {
      for (const listener of listeners.get(event) ?? []) {
        listener(...args);
      }
    },
    write(name, params) {
      client.emit("write", name, params);
      client.writeLog.push({ name, params });
      return undefined;
    },
    writeLog: []
  };
  return client;
}

function createFakeBot(): Bot & { _client?: unknown; _emit(name: string, ...args: unknown[]): void } {
  const handlers = new Map<string, Array<(...args: unknown[]) => void>>();
  const bot = {
    once(event: string, listener: (...args: unknown[]) => void) {
      const list = handlers.get(event) ?? [];
      list.push((...args: unknown[]) => {
        handlers.delete(event);
        listener(...args);
      });
      handlers.set(event, list);
    },
    on(event: string, listener: (...args: unknown[]) => void) {
      const list = handlers.get(event) ?? [];
      list.push(listener);
      handlers.set(event, list);
    },
    removeListener(event: string, listener: (...args: unknown[]) => void) {
      const list = handlers.get(event) ?? [];
      const index = list.indexOf(listener);
      if (index >= 0) list.splice(index, 1);
    },
    _emit(name: string, ...args: unknown[]) {
      for (const listener of handlers.get(name) ?? []) {
        listener(...args);
      }
    }
  } as unknown as Bot & { _client?: FakeClient; _emit(name: string, ...args: unknown[]): void };
  return bot;
}

function createMonitor(bot: ReturnType<typeof createFakeBot>, events: RuntimeEvent[], options?: Parameters<typeof installPacketMonitor>[2]) {
  return installPacketMonitor(bot, (event) => events.push(event), {
    warnAfterMs: 10_000,
    watchdogIntervalMs: 100,
    ...options
  });
}

function receive(client: FakeClient, name: string, sizeBytes = 20): void {
  client.emit("packet", { some: "data" }, { name }, { length: sizeBytes });
}

describe("installPacketMonitor", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("tracks inbound packets with names, counts, and timestamps", () => {
    const bot = createFakeBot();
    const client = createFakeClient();
    (bot as { _client: unknown })._client = client;
    const events: RuntimeEvent[] = [];
    const monitor = createMonitor(bot, events);

    bot._emit("inject_allowed");
    receive(client, "position");
    receive(client, "map_chunk");

    const stats = monitor.stats();
    expect(stats.packetsReceived).toBe(2);
    expect(stats.lastPacketName).toBe("map_chunk");
    expect(stats.lastPacketAt).not.toBeNull();
    expect(stats.stalledMs).toBe(0);
    expect(monitor.recentInbound()).toHaveLength(2);
    monitor.dispose();
  });

  it("tracks outbound writes without changing write behavior", () => {
    const bot = createFakeBot();
    const client = createFakeClient();
    (bot as { _client: unknown })._client = client;
    const events: RuntimeEvent[] = [];
    const monitor = createMonitor(bot, events);

    bot._emit("inject_allowed");
    client.write("keep_alive", { keepAliveId: 7n });
    client.write("position_look", {});

    expect(client.writeLog).toEqual([
      { name: "keep_alive", params: { keepAliveId: 7n } },
      { name: "position_look", params: {} }
    ]);
    const stats = monitor.stats();
    expect(stats.packetsWritten).toBe(2);
    expect(stats.lastWriteName).toBe("position_look");
    monitor.dispose();
  });

  it("warns once when the inbound stream stalls and re-arms after recovery", () => {
    const bot = createFakeBot();
    const client = createFakeClient();
    (bot as { _client: unknown })._client = client;
    const events: RuntimeEvent[] = [];
    const monitor = createMonitor(bot, events);

    bot._emit("inject_allowed");
    receive(client, "position");

    vi.advanceTimersByTime(10_500);
    const warnings = events.filter((event) => event.type === "log" && event.level === "warn");
    expect(warnings).toHaveLength(1);
    expect((warnings[0] as { message: string }).message).toContain("PACKET STALL");

    // Still stalled: no second warning
    vi.advanceTimersByTime(5_000);
    expect(events.filter((event) => event.type === "log" && event.level === "warn")).toHaveLength(1);

    // Recovery re-arms the warning
    receive(client, "keep_alive");
    vi.advanceTimersByTime(11_000);
    expect(events.filter((event) => event.type === "log" && event.level === "warn")).toHaveLength(2);
    monitor.dispose();
  });

  it("dumps the final packet trail on end", () => {
    const bot = createFakeBot();
    const client = createFakeClient();
    (bot as { _client: unknown })._client = client;
    const events: RuntimeEvent[] = [];
    const monitor = createMonitor(bot, events);

    bot._emit("inject_allowed");
    receive(client, "position");
    receive(client, "map_chunk");
    client.write("keep_alive", {});

    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    bot._emit("end", "keepAliveError");
    errorSpy.mockRestore();

    const errors = events.filter((event) => event.type === "log" && event.level === "error");
    expect(errors).toHaveLength(1);
    const dump = (errors[0] as { message: string }).message;
    expect(dump).toContain("CONNECTION ENDED (keepAliveError)");
    expect(dump).toContain("map_chunk");
    expect(dump).toContain("keep_alive");
    monitor.dispose();
  });

  it("does not warn before the client is hooked", () => {
    const bot = createFakeBot();
    const events: RuntimeEvent[] = [];
    const monitor = createMonitor(bot, events);

    vi.advanceTimersByTime(30_000);
    expect(events).toHaveLength(0);
    monitor.dispose();
  });
});
