/** How long (ms) to wait before the next reconnect attempt, given the number
 *  of consecutive failures so far. Delays double per failure (exponential
 *  backoff), starting at `baseMs` and capped at `maxMs`, so a flaky server or
 *  a long outage never hammers the network yet still recovers promptly. */
export function reconnectDelayMs(failedAttempts: number, baseMs = 1000, maxMs = 15_000): number {
  if (baseMs <= 0 || maxMs <= 0 || failedAttempts <= 0) {
    return Math.max(0, Math.min(baseMs, maxMs));
  }
  const shifted = baseMs * 2 ** failedAttempts;
  return Number.isFinite(shifted) ? Math.min(shifted, maxMs) : maxMs;
}
