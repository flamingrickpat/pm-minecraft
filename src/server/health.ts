import type { RuntimeConfig } from "../config.js";

/**
 * Runtime health needs stable API JSON; serialize process, config, bot, Paper, and viewer readiness without inventing state.
 *
 * @remarks
 * archetype: service-provider
 * owns: the public `/api/health` response shape for the live tracer bullet.
 * not own: probing Paper, connecting Mineflayer, or starting prismarine-viewer.
 * fails when: callers omit required status objects.
 * domain: health is diagnostic evidence and must show failed external dependencies instead of reporting fake readiness.
 * invariant: readiness fields reflect real attempted runtime components.
 */
export interface HealthInput {
  startedAt: Date;
  config: RuntimeConfig;
  bot: {
    connecting: boolean;
    connected: boolean;
    spawned: boolean;
    username: string;
    version?: string | null;
    deathCount?: number;
    spawnCount?: number;
    lastDeathAt?: string | null;
    lastSpawnAt?: string | null;
    lastError: string | null;
  };
  /** Live packet-stream diagnostics from the packet monitor. */
  network?: {
    connected: boolean;
    lastPacketAt: string | null;
    lastPacketName: string | null;
    packetsReceived: number;
    lastWriteAt: string | null;
    lastWriteName: string | null;
    packetsWritten: number;
    stalledMs: number | null;
  };
  paper: { reachable: boolean; checkedAt: string | null; error: string | null };
  http?: { listening: boolean; host: string; port: number; url: string | null; error: string | null };
  webSocket?: { enabled: boolean; path: string; clients: number; error: string | null };
  viewer: { enabled: boolean; started: boolean; port: number; url: string | null; firstPerson?: boolean; error: string | null };
}

export interface HealthResponse {
  ready: boolean;
  process: { uptimeMs: number; startedAt: string };
  config: {
    minecraft: { host: string; port: number; username: string };
    web: { host: string; port: number };
    viewer: { enabled: boolean; port: number; firstPerson: boolean };
    command: { timeoutMs: number; maxFineControlDurationMs: number; stateBroadcastIntervalMs: number };
    evidence: { directory: string };
  };
  mineflayer: {
    connecting: boolean;
    connected: boolean;
    spawned: boolean;
    username: string;
    version: string | null;
    deathCount: number;
    spawnCount: number;
    lastDeathAt: string | null;
    lastSpawnAt: string | null;
    lastError: string | null;
  };
  network?: HealthInput["network"];
  paper: { reachable: boolean; checkedAt: string | null; error: string | null };
  http: { listening: boolean; host: string; port: number; url: string | null; error: string | null };
  webSocket: { enabled: boolean; path: string; clients: number; error: string | null };
  viewer: { enabled: boolean; started: boolean; port: number; url: string | null; firstPerson?: boolean; error: string | null };
}

export function serializeHealth(input: HealthInput): HealthResponse {
  const http = input.http ?? {
    listening: false,
    host: input.config.web.host,
    port: input.config.web.port,
    url: null,
    error: "HTTP server status has not been supplied yet"
  };
  const webSocket = input.webSocket ?? { enabled: true, path: "/ws", clients: 0, error: null };

  return {
    ready: input.paper.reachable && input.bot.connected && input.bot.spawned && http.listening && (!input.viewer.enabled || input.viewer.started),
    process: {
      uptimeMs: Math.max(0, Date.now() - input.startedAt.getTime()),
      startedAt: input.startedAt.toISOString()
    },
    config: input.config,
    mineflayer: {
      ...input.bot,
      version: input.bot.version ?? null,
      deathCount: input.bot.deathCount ?? 0,
      spawnCount: input.bot.spawnCount ?? 0,
      lastDeathAt: input.bot.lastDeathAt ?? null,
      lastSpawnAt: input.bot.lastSpawnAt ?? null
    },
    network: input.network ?? undefined,
    paper: input.paper,
    http,
    webSocket,
    viewer: input.viewer
  };
}
