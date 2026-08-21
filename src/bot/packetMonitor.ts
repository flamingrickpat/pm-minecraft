import type { Bot } from "mineflayer";
import type { RuntimeEvent } from "../server/http.js";

/**
 * The 2026-08-21 stall (both sides timing out on each other while both
 * processes stayed alive) proved the game socket can go permanently silent
 * with no visible symptom until the keepalive timers kill the connection.
 * This module makes the inbound/outbound packet stream observable: live stats
 * for /api/health, a stall watchdog that warns while it is happening, and a
 * ring-buffer dump on disconnect so the dying moments are on record.
 *
 * @remarks
 * archetype: observability
 * owns: inbound/outbound packet timestamps+counts, the recent-packet ring
 *       buffers, the stall watchdog, and the end-of-connection dump.
 * not own: reconnection policy, keepalive handling, or anything that mutates
 *           the connection — this is strictly read-only observation plus logs.
 * fails when: never fatally — all hooks are wrapped so observation cannot
 *             break the stream it observes.
 * invariant: hooking the monitor must not alter packet handling in any way.
 */

export interface PacketStats {
  connected: boolean;
  lastPacketAt: string | null;
  lastPacketName: string | null;
  packetsReceived: number;
  lastWriteAt: string | null;
  lastWriteName: string | null;
  packetsWritten: number;
  /** Milliseconds since the last inbound packet, or null before the first one. */
  stalledMs: number | null;
}

export interface PacketMonitor {
  stats(): PacketStats;
  /** Human-readable one-liner for logs: where the stream currently stands. */
  describe(): string;
  /** Recent inbound packets, oldest first (at, offsetMs, name, sizeBytes). */
  recentInbound(limit?: number): Array<{ at: string; offsetMs: number; name: string; sizeBytes: number | null }>;
  dispose(): void;
}

export interface PacketMonitorOptions {
  /** Ring buffer size for inbound packet names. */
  inboundRingSize?: number;
  /** Ring buffer size for outbound packet names. */
  outboundRingSize?: number;
  /** Watchdog fires (once per stall) after this many ms without an inbound packet. */
  warnAfterMs?: number;
  /** Watchdog polling interval. */
  watchdogIntervalMs?: number;
}

interface RingEntry {
  at: number;
  name: string;
  sizeBytes: number | null;
}

const DEFAULT_INBOUND_RING = 400;
const DEFAULT_OUTBOUND_RING = 100;
// Vanilla servers send keep-alives every ~15s, so an idle-but-healthy stream
// can legitimately be silent for 15+ seconds. 20s stays above that while
// still warning well before the 30s keepalive timers kill the connection.
const DEFAULT_WARN_AFTER_MS = 20_000;
const DEFAULT_WATCHDOG_INTERVAL_MS = 2_000;

export function installPacketMonitor(
  bot: Bot,
  emit: (event: RuntimeEvent) => void,
  options: PacketMonitorOptions = {}
): PacketMonitor {
  const inboundRingSize = options.inboundRingSize ?? DEFAULT_INBOUND_RING;
  const outboundRingSize = options.outboundRingSize ?? DEFAULT_OUTBOUND_RING;
  const warnAfterMs = options.warnAfterMs ?? DEFAULT_WARN_AFTER_MS;
  const watchdogIntervalMs = options.watchdogIntervalMs ?? DEFAULT_WATCHDOG_INTERVAL_MS;

  let connected = false;
  let lastPacketAt: number | null = null;
  let lastPacketName: string | null = null;
  let packetsReceived = 0;
  let lastWriteAt: number | null = null;
  let lastWriteName: string | null = null;
  let packetsWritten = 0;
  let stallWarned = false;
  let disposed = false;

  const inbound: RingEntry[] = [];
  const outbound: RingEntry[] = [];

  const pushRing = (ring: RingEntry[], entry: RingEntry, limit: number): void => {
    ring.push(entry);
    if (ring.length > limit) {
      ring.splice(0, ring.length - limit);
    }
  };

  const tailInbound = (limit: number): string[] =>
    inbound.slice(-limit).map((entry) => {
      const ago = lastPacketAt ? Math.round(entry.at - lastPacketAt) : 0;
      const size = entry.sizeBytes != null ? ` (${entry.sizeBytes}B)` : "";
      return `    +${ago}ms ${entry.name}${size}`;
    });

  const tailOutbound = (limit: number): string[] =>
    outbound.slice(-limit).map((entry) => {
      const ago = lastWriteAt ? Math.round(entry.at - lastWriteAt) : 0;
      return `    +${ago}ms ${entry.name}`;
    });

  const stats = (): PacketStats => ({
    connected,
    lastPacketAt: lastPacketAt != null ? new Date(lastPacketAt).toISOString() : null,
    lastPacketName,
    packetsReceived,
    lastWriteAt: lastWriteAt != null ? new Date(lastWriteAt).toISOString() : null,
    lastWriteName,
    packetsWritten,
    stalledMs: lastPacketAt != null ? Math.max(0, Date.now() - lastPacketAt) : null
  });

  const describe = (): string => {
    const current = stats();
    const inboundPart = current.lastPacketName
      ? `last inbound ${current.lastPacketName} ${Math.round(current.stalledMs ?? 0)}ms ago`
      : "no inbound packets yet";
    const outboundPart = current.lastWriteName
      ? `last outbound ${current.lastWriteName} ${current.lastWriteAt ? Math.round(Date.now() - new Date(current.lastWriteAt).getTime()) : 0}ms ago`
      : "no outbound packets yet";
    return `packet stream: ${inboundPart} (${current.packetsReceived} received), ${outboundPart} (${current.packetsWritten} written)`;
  };

  // Watchdog: catch a silent stream while the connection is still nominally
  // up, so the stall is visible in body.log BEFORE both keepalive timers fire.
  const watchdog = setInterval((): void => {
    if (disposed || !connected || lastPacketAt == null) {
      return;
    }
    const silentFor = Date.now() - lastPacketAt;
    if (silentFor >= warnAfterMs && !stallWarned) {
      stallWarned = true;
      const message =
        `PACKET STALL: no inbound packet for ${Math.round(silentFor / 1000)}s ` +
        `(last: ${lastPacketName} at ${new Date(lastPacketAt).toISOString()}); ` +
        `outbound still ${lastWriteAt != null ? `alive (${Math.round((Date.now() - lastWriteAt) / 1000)}s since last write)` : "idle"}. ` +
        `If this persists the connection will die by keepalive timeout.\n  recent inbound:\n${tailInbound(25).join("\n")}`;
      console.warn(`[packet-monitor] ${message}`);
      emit({ type: "log", level: "warn", message });
    }
  }, watchdogIntervalMs);
  watchdog.unref?.();

  const hookClient = (client: {
    on(event: string, listener: (...args: unknown[]) => void): unknown;
    write(name: string, params?: unknown): unknown;
  }): void => {
    connected = true;
    client.on("packet", (...args: unknown[]) => {
      const metadata = args[1] as { name?: string } | undefined;
      const buffer = args[2] as { length?: number } | undefined;
      const name = typeof metadata?.name === "string" ? metadata.name : "unknown";
      lastPacketAt = Date.now();
      lastPacketName = name;
      packetsReceived += 1;
      stallWarned = false;
      pushRing(inbound, { at: lastPacketAt, name, sizeBytes: typeof buffer?.length === "number" ? buffer.length : null }, inboundRingSize);
    });

    // Outbound observation: wrap write so a one-way death (still writing,
    // nothing arriving) is visible in the dump.
    const target = client as { write: (name: string, params?: unknown) => unknown };
    const originalWrite = target.write.bind(target);
    target.write = (name: string, params?: unknown): unknown => {
      lastWriteAt = Date.now();
      lastWriteName = name;
      packetsWritten += 1;
      pushRing(outbound, { at: lastWriteAt, name, sizeBytes: null }, outboundRingSize);
      return originalWrite(name, params);
    };
  };

  const onEnd = (reason: unknown): void => {
    if (connected) {
      connected = false;
    }
    const current = stats();
    const silentFor = current.lastPacketAt != null ? Math.round((Date.now() - new Date(current.lastPacketAt).getTime()) / 1000) : -1;
    const dump =
      `CONNECTION ENDED (${String(reason)}): ${current.packetsReceived} packets received, ${current.packetsWritten} written. ` +
      `last inbound ${current.lastPacketName} at ${current.lastPacketAt} (${silentFor}s before end), ` +
      `last outbound ${current.lastWriteName} at ${current.lastWriteAt}.\n` +
      `  last inbound packets (offset from final packet):\n${tailInbound(40).join("\n") || "    (none)"}\n` +
      `  last outbound packets (offset from final write):\n${tailOutbound(20).join("\n") || "    (none)"}`;
    console.error(`[packet-monitor] ${dump}`);
    emit({ type: "log", level: "error", message: dump });
  };

  // _client exists once the protocol layer is set up; inject_allowed is the
  // earliest mineflayer hook where it is safe to attach.
  bot.once("inject_allowed", () => {
    const client = (bot as Bot & { _client?: Parameters<typeof hookClient>[0] })._client;
    if (client) {
      try {
        hookClient(client);
      } catch (error) {
        console.warn(`[packet-monitor] failed to hook client: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
  });
  bot.on("end", onEnd);

  return {
    stats,
    describe,
    recentInbound: (limit = 50) =>
      inbound.slice(-limit).map((entry) => ({
        at: new Date(entry.at).toISOString(),
        offsetMs: lastPacketAt != null ? Math.round(entry.at - lastPacketAt) : 0,
        name: entry.name,
        sizeBytes: entry.sizeBytes
      })),
    dispose: () => {
      disposed = true;
      clearInterval(watchdog);
      bot.removeListener("end", onEnd);
    }
  };
}
