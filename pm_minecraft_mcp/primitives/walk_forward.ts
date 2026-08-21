import { type MinecraftContext, type SkillEntrypoint } from "../sdk/minecraft.js";

/**
 * Walk straight forward for a fixed duration using fine_control (raw control
 * states, no pathfinding). Useful to pass through openings the pathfinder
 * refuses (doors, narrow gaps).
 *
 * input:
 *   durationMs: how long to hold forward (default 1500)
 *   controls:   extra control states (e.g. { jump: true })
 */
interface Input {
  durationMs?: number;
  controls?: Record<string, boolean>;
}

const run: SkillEntrypoint = async (context: MinecraftContext, rawInput: unknown) => {
  const input = (rawInput ?? {}) as Input;
  const durationMs = Math.min(Math.max(Math.floor(input.durationMs ?? 1500), 100), 3000);

  // fine_control requires a fresh visual check frame.
  const frame = await context.call("capture_frame", {}, 30);
  const body = (frame.data ?? frame) as Record<string, unknown>;
  const frameId = body.frameId ?? (body.data as Record<string, unknown> | undefined)?.frameId;
  if (typeof frameId !== "string") {
    throw new Error(`capture_frame returned no frameId: ${JSON.stringify(body).slice(0, 200)}`);
  }

  const controls = { forward: true, ...(input.controls ?? {}) };
  const res = await context.call(
    "fine_control",
    { controls, durationMs, visualCheckFrameId: frameId },
    30
  );
  const after = await context.observe();
  const pos = after.player.position;
  return {
    ok: res.ok,
    fineControl: res.ok === true,
    position: { x: Math.round(pos.x * 10) / 10, y: pos.y, z: Math.round(pos.z * 10) / 10 }
  };
};

export default run;
