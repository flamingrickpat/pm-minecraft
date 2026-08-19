import type { Bot } from "mineflayer";

/**
 * The Agentic Babymode mod reports its JSON status in chat when installed; query it once per
 * state collection so agents can see sleepiness/nutrition alongside the normal Minecraft state.
 *
 * @remarks
 * owns: the `/babymode status json` chat round-trip and its JSON parsing.
 * not own: the rest of the LLM state object, file persistence, or mod configuration.
 * fails when: gracefully — when the mod is absent or times out, resolve null and do nothing else.
 */

export interface BabymodeStatus {
  version: string | null;
  sleepiness: number | null;
  fatigue: number | null;
  nutrition: { grain: number; protein: number; produce: number } | null;
  health: number | null;
  maxHealth: number | null;
  hunger: number | null;
  air: number | null;
  effects: Array<{ id: string; amplifier: number; duration: number }> | null;
}

const BABYMODE_COMMAND = "/babymode status json";
/** The mod answers instantly; a short timeout just avoids hanging forever when it is not installed. */
const RESPONSE_TIMEOUT_MS = 1500;

/** Ask the mod for its JSON status. Returns null when the mod is absent or unreachable. */
export function fetchBabymodeStatus(bot: Bot): Promise<BabymodeStatus | null> {
  return new Promise((resolve) => {
    let timer: NodeJS.Timeout | undefined;
    const onMessage = (message: string): void => {
      const parsed = parseBabymodeStatus(message);
      if (parsed) {
        stop();
        resolve(parsed);
      }
    };
    const stop = (): void => {
      if (timer) {
        clearTimeout(timer);
      }
      bot.removeListener("messagestr", onMessage);
    };
    timer = setTimeout(() => {
      stop();
      resolve(null);
    }, RESPONSE_TIMEOUT_MS);
    bot.on("messagestr", onMessage);
    try {
      bot.chat(BABYMODE_COMMAND);
    } catch {
      stop();
      resolve(null);
    }
  });
}

function parseBabymodeStatus(message: string): BabymodeStatus | null {
  const text = message.trim();
  if (!text.startsWith("{")) {
    return null;
  }
  let json: unknown;
  try {
    json = JSON.parse(text);
  } catch {
    return null;
  }
  if (json === null || typeof json !== "object" || Array.isArray(json)) {
    return null;
  }
  const record = json as Record<string, unknown>;
  if (typeof record.version !== "string") {
    return null;
  }
  return {
    version: record.version,
    sleepiness: num(record.sleepiness),
    fatigue: num(record.fatigue),
    nutrition: asNutrition(record.nutrition),
    health: num(record.health),
    maxHealth: num(record.maxHealth),
    hunger: num(record.hunger),
    air: num(record.air),
    effects: asEffects(record.effects)
  };
}

function asNutrition(value: unknown): BabymodeStatus["nutrition"] {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  const record = value as Record<string, unknown>;
  return {
    grain: num(record.grain) ?? 0,
    protein: num(record.protein) ?? 0,
    produce: num(record.produce) ?? 0
  };
}

function asEffects(value: unknown): BabymodeStatus["effects"] {
  if (!Array.isArray(value)) {
    return null;
  }
  return value.map((entry) => {
    const record = (entry ?? {}) as Record<string, unknown>;
    return {
      id: typeof record.id === "string" ? record.id : "unknown",
      amplifier: num(record.amplifier) ?? 0,
      duration: num(record.duration) ?? 0
    };
  });
}

function num(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
