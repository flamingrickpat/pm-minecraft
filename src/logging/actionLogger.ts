import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import type { CommandHooks, CommandCompletion } from "../commands/commandQueue.js";

/**
 * Agents need verifiable action evidence; persist screenshot + state.json before and after every physical command.
 *
 * @remarks
 * archetype: service-provider
 * owns: per-action log folders (`<dir>/<timestamp>_<action>/`) containing before.png,
 *       before.state.json, after.png, after.state.json, and result.json.
 * not own: state content (llmState), screenshot capture (browserCapture), or command execution.
 * fails when: never fatally — logging errors are reported through the log callback and
 *             must not affect command execution.
 * domain: this evidence lets an agent check whether a command succeeded and how the world changed.
 * invariant: the before snapshot is taken before the command runs; the after snapshot after it settles.
 */
export interface ActionLoggerOptions {
  enabled: boolean;
  directory: string;
  snapshotState: () => unknown | null;
  captureScreenshot: () => Promise<Buffer | null>;
  log?: (level: "info" | "warn", message: string) => void;
}

export interface ActionLogContext {
  directory: string;
  command: string;
  input: unknown;
  startedAt: string;
}

export function createActionLogger(options: ActionLoggerOptions): CommandHooks {
  const emit = options.log ?? (() => undefined);

  const writeSnapshot = async (
    directory: string,
    phase: "before" | "after",
    command: string,
    input: unknown
  ): Promise<void> => {
    const statePath = join(directory, `${phase}.state.json`);
    const state = {
      phase,
      command,
      input,
      capturedAt: new Date().toISOString(),
      state: safeSnapshot(options.snapshotState)
    };
    await writeFile(statePath, JSON.stringify(state, null, 2));

    const png = await options.captureScreenshot().catch(() => null);
    if (png) {
      await writeFile(join(directory, `${phase}.png`), png);
    }
  };

  return {
    beforeCommand: async (command, input) => {
      if (!options.enabled) {
        return null;
      }
      try {
        const startedAt = new Date().toISOString();
        const folderName = `${startedAt.replace(/[:.]/g, "-")}_${sanitizeName(command)}`;
        const directory = join(options.directory, folderName);
        await mkdir(directory, { recursive: true });
        await writeSnapshot(directory, "before", command, input);
        return { directory, command, input, startedAt } satisfies ActionLogContext;
      } catch (error) {
        emit("warn", `Action log (before) failed for ${command}: ${message(error)}`);
        return null;
      }
    },
    afterCommand: async (context, completion: CommandCompletion) => {
      const ctx = context as ActionLogContext | null;
      if (!options.enabled || !ctx) {
        return;
      }
      try {
        await writeSnapshot(ctx.directory, "after", ctx.command, ctx.input);
        const result = {
          command: ctx.command,
          input: ctx.input,
          startedAt: ctx.startedAt,
          finishedAt: new Date().toISOString(),
          status: completion.status,
          ok: completion.ok,
          reason: completion.reason ?? null,
          message: completion.message,
          data: completion.data ?? null,
          durationMs: completion.durationMs
        };
        await writeFile(join(ctx.directory, "result.json"), JSON.stringify(result, null, 2));
        emit("info", `Action logged: ${ctx.directory}`);
      } catch (error) {
        emit("warn", `Action log (after) failed for ${ctx.command}: ${message(error)}`);
      }
    }
  };
}

function safeSnapshot(snapshot: () => unknown | null): unknown {
  try {
    return snapshot();
  } catch (error) {
    return { error: `State snapshot failed: ${message(error)}` };
  }
}

function sanitizeName(name: string): string {
  return name.replace(/[^A-Za-z0-9_-]+/g, "_").slice(0, 48) || "command";
}

function message(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
