/**
 * Environment strings need typed runtime settings; parse and validate them once at the process boundary.
 *
 * @remarks
 * archetype: interfacer; also: information-holder
 * A side: process environment variables supplied as strings.
 * B side: typed runtime settings for Minecraft, web, viewer, command, and evidence paths.
 * lossy ops: none; all supported settings are copied or defaulted explicitly.
 * fails when: numeric settings are not integers, booleans are not true/false-like values, or required text is blank.
 * invariant: downstream runtime code receives validated values and never reparses environment variables.
 */
export interface RuntimeConfig {
  minecraft: {
    host: string; port: number; username: string; viewDistance?: number;
    /** mine_block skips its head-line-of-sight gate for targets within this many blocks (tunneling). */
    mineVisibilityIgnoreDistance: number;
    /** walk_to rejects targets farther than this many blocks; split long routes into hops. */
    walkToMaxDistance: number;
  };
  web: { host: string; port: number };
  viewer: { enabled: boolean; port: number; firstPerson: boolean; viewDistance?: number; captureWidth: number; captureHeight: number; deviceScaleFactor: number; fovDegrees: number };
  command: { timeoutMs: number; maxFineControlDurationMs: number; stateBroadcastIntervalMs: number };
  evidence: { directory: string };
  actionLog: { enabled: boolean; directory: string; nearbyBlockRadius: number };
}

export function parseRuntimeConfig(env: NodeJS.ProcessEnv): RuntimeConfig {
  return {
    minecraft: {
      host: textValue(env.MINECRAFT_HOST, "127.0.0.1", "MINECRAFT_HOST"),
      port: intValue(env.MINECRAFT_PORT, 55608, "MINECRAFT_PORT"),
      username: textValue(env.MINECRAFT_USERNAME, "turnbased-bot", "MINECRAFT_USERNAME"),
      viewDistance: intValue(env.MINECRAFT_VIEW_DISTANCE, 12, "MINECRAFT_VIEW_DISTANCE"),
      mineVisibilityIgnoreDistance: floatValue(
        env.MINECRAFT_MINE_VISIBILITY_IGNORE_DISTANCE,
        3.0,
        "MINECRAFT_MINE_VISIBILITY_IGNORE_DISTANCE"
      ),
      walkToMaxDistance: floatValue(
        env.MINECRAFT_WALK_TO_MAX_DISTANCE,
        16.0,
        "MINECRAFT_WALK_TO_MAX_DISTANCE"
      )
    },
    web: {
      host: textValue(env.WEB_HOST, "127.0.0.1", "WEB_HOST"),
      port: intValue(env.WEB_PORT, 3000, "WEB_PORT")
    },
    viewer: {
      enabled: boolValue(env.VIEWER_ENABLED, true, "VIEWER_ENABLED"),
      port: intValue(env.VIEWER_PORT, 3001, "VIEWER_PORT"),
      firstPerson: boolValue(env.VIEWER_FIRST_PERSON, true, "VIEWER_FIRST_PERSON"),
      viewDistance: intValue(env.VIEWER_VIEW_DISTANCE, 12, "VIEWER_VIEW_DISTANCE"),
      captureWidth: intValue(env.VIEWER_CAPTURE_WIDTH, 640, "VIEWER_CAPTURE_WIDTH"),
      captureHeight: intValue(env.VIEWER_CAPTURE_HEIGHT, 640, "VIEWER_CAPTURE_HEIGHT"),
      deviceScaleFactor: intValue(env.VIEWER_DEVICE_SCALE_FACTOR, 1, "VIEWER_DEVICE_SCALE_FACTOR"),
      fovDegrees: intValue(env.VIEWER_FOV_DEGREES, 80, "VIEWER_FOV_DEGREES")
    },
    command: {
      timeoutMs: intValue(env.COMMAND_TIMEOUT_MS, 30000, "COMMAND_TIMEOUT_MS"),
      maxFineControlDurationMs: intValue(env.MAX_FINE_CONTROL_DURATION_MS, 3000, "MAX_FINE_CONTROL_DURATION_MS"),
      stateBroadcastIntervalMs: intValue(env.STATE_BROADCAST_INTERVAL_MS, 500, "STATE_BROADCAST_INTERVAL_MS")
    },
    evidence: {
      directory: textValue(env.EVIDENCE_DIR, "evidence", "EVIDENCE_DIR")
    },
    actionLog: {
      enabled: boolValue(env.ACTION_LOG_ENABLED, true, "ACTION_LOG_ENABLED"),
      directory: textValue(env.ACTION_LOG_DIR, "logs/actions", "ACTION_LOG_DIR"),
      nearbyBlockRadius: intValue(env.ACTION_LOG_BLOCK_RADIUS, 8, "ACTION_LOG_BLOCK_RADIUS")
    }
  };
}

function textValue(value: string | undefined, defaultValue: string, name: string): string {
  const parsed = value ?? defaultValue;
  if (parsed.trim().length === 0) {
    throw new Error(`${name} must not be blank`);
  }
  return parsed;
}

function intValue(value: string | undefined, defaultValue: number, name: string): number {
  if (value === undefined) {
    return defaultValue;
  }

  if (!/^-?\d+$/.test(value)) {
    throw new Error(`${name} must be an integer`);
  }

  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed <= 0) {
    throw new Error(`${name} must be a positive safe integer`);
  }
  return parsed;
}

function boolValue(value: string | undefined, defaultValue: boolean, name: string): boolean {
  if (value === undefined) {
    return defaultValue;
  }

  const normalized = value.trim().toLowerCase();
  if (["1", "true", "yes", "on"].includes(normalized)) {
    return true;
  }
  if (["0", "false", "no", "off"].includes(normalized)) {
    return false;
  }
  throw new Error(`${name} must be a boolean`);
}

function floatValue(value: string | undefined, defaultValue: number, name: string): number {
  if (value === undefined) {
    return defaultValue;
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) {
    throw new Error(`${name} must be a non-negative number`);
  }
  return parsed;
}
