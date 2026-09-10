/**
 * One plain-text log at ~/.pm/pm-minecraft/body.log.
 *
 * BODY_LOG_LEVEL picks error, warning, info, or debug. The default is info.
 * Debug adds a fresh full-state snapshot after every action; that scan costs
 * ~125 block lookups per action, so it stays opt-in.
 */

import { appendFileSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const LEVELS: Record<string, number> = { error: 0, warning: 1, info: 2, debug: 3 };

const directory = join(homedir(), ".pm", "pm-minecraft");
const level = process.env.BODY_LOG_LEVEL?.toLowerCase() ?? "info";
if (!(level in LEVELS)) {
  throw new Error(`BODY_LOG_LEVEL must be one of error, warning, info, debug: ${level}`);
}
mkdirSync(directory, { recursive: true });
const filePath = join(directory, "body.log");

export function log(levelName: keyof typeof LEVELS, message: string): void {
  if (LEVELS[levelName] > LEVELS[level]) {
    return;
  }
  const line = `${new Date().toISOString()} ${levelName.toUpperCase()} ${message}`;
  try {
    appendFileSync(filePath, line + "\n");
  } catch {
    // The log file must never break the action it describes.
  }
  if (levelName === "error" || levelName === "warning") {
    console.error(line);
  }
}
