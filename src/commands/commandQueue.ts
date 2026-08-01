import type { RuntimeEvent } from "../server/http.js";
import type { CommandRecord } from "../evidence/evidenceStore.js";

export type CommandTerminalStatus = "succeeded" | "failed" | "cancelled" | "timed_out";
export type CommandStatus = "accepted" | "running" | CommandTerminalStatus;

export interface CommandState {
  commandId: string;
  command: string;
  status: CommandStatus;
  input: unknown;
  acceptedAt: string;
  startedAt: string | null;
  finishedAt: string | null;
}

export interface CommandRunContext {
  signal: AbortSignal;
  log(message: string): void;
}

export interface PhysicalCommand {
  name: string;
  input?: unknown;
  timeoutMs?: number;
  run(context: CommandRunContext): Promise<CommandResult>;
}

export interface CommandResult {
  ok: boolean;
  message: string;
  reason?: string;
  data?: unknown;
}

export interface CommandCompletion extends CommandResult {
  commandId: string;
  command: string;
  status: CommandTerminalStatus;
  durationMs: number;
}

export type EnqueueResult =
  | { accepted: true; commandId: string; completed: Promise<CommandCompletion> }
  | { accepted: false; statusCode: 409; error: "command_conflict"; message: string };

export interface CommandQueueOptions {
  defaultTimeoutMs: number;
  cleanup(): void | Promise<void>;
  emit(event: RuntimeEvent): void;
  evidence?: RecordEvidence;
  hooks?: CommandHooks;
}

/**
 * Observation hooks around command execution. beforeCommand runs before the
 * command's timeout window starts; its return value (e.g. a log context) is
 * handed back to afterCommand once the command settles. Hook failures must
 * never affect command execution.
 */
export interface CommandHooks {
  beforeCommand(command: string, input: unknown): Promise<unknown>;
  afterCommand(context: unknown, completion: CommandCompletion): Promise<void>;
}

export interface RecordEvidence {
  recordCommand(cmd: CommandRecord): Promise<void>;
}

class CommandAbort extends Error {
  constructor(readonly kind: "cancelled" | "timed_out") {
    super(kind === "cancelled" ? "Command cancelled." : "Command timed out.");
  }
}

export class CommandQueue {
  #counter = 0;
  #current: CommandState | null = null;
  #controller: AbortController | null = null;
  #cleanupAlreadyRun = false;
  #cleanupPromise: Promise<void> | null = null;

  constructor(private readonly options: CommandQueueOptions) {}

  get currentCommand(): CommandState | null {
    return this.#current ? { ...this.#current } : null;
  }

  enqueueOrReject(command: PhysicalCommand): EnqueueResult {
    if (this.#current) {
      return {
        accepted: false,
        statusCode: 409,
        error: "command_conflict",
        message: "A physical command is already running."
      };
    }

    const commandId = `cmd_${Date.now()}_${++this.#counter}`;
    const controller = new AbortController();
    const now = new Date().toISOString();
    this.#controller = controller;
    this.#cleanupAlreadyRun = false;
    this.#cleanupPromise = null;
    this.#current = {
      commandId,
      command: command.name,
      status: "accepted",
      input: command.input ?? null,
      acceptedAt: now,
      startedAt: null,
      finishedAt: null
    };

    const completed = this.#execute(command, controller);
    return { accepted: true, commandId, completed };
  }

  async cancelCurrent(): Promise<{ ok: boolean; message: string }> {
    if (!this.#current || !this.#controller) {
      await this.#runCleanup();
      return { ok: true, message: "Stopped current command." };
    }

    if (!this.#controller.signal.aborted) {
      this.#controller.abort(new CommandAbort("cancelled"));
    }
    await this.#runCleanup();
    return { ok: true, message: "Stopped current command." };
  }

  async #execute(command: PhysicalCommand, controller: AbortController): Promise<CommandCompletion> {
    const active = this.#current;
    if (!active) {
      throw new Error("Command queue invariant failed: missing active command.");
    }

    // Capture pre-command evidence before the timeout window starts so slow
    // screenshots never eat into the command's own time budget.
    let hookContext: unknown = null;
    if (this.options.hooks) {
      try {
        hookContext = await this.options.hooks.beforeCommand(active.command, active.input);
      } catch {
        // Hooks must never block command execution
      }
    }

    const startedAt = Date.now();
    active.status = "running";
    active.startedAt = new Date(startedAt).toISOString();
    this.options.emit({
      type: "command_started",
      commandId: active.commandId,
      command: active.command,
      data: active.input
    });

    const timeoutMs = command.timeoutMs ?? this.options.defaultTimeoutMs;
    let timeout: NodeJS.Timeout;
    const timeoutPromise = new Promise<never>((_, reject) => {
      timeout = setTimeout(() => {
        const abort = new CommandAbort("timed_out");
        if (!controller.signal.aborted) {
          controller.abort(abort);
        }
        reject(abort);
      }, timeoutMs);
    });

    let completion: CommandCompletion;
    try {
      const commandPromise = command.run({
        signal: controller.signal,
        log: (message) => this.options.emit({ type: "log", level: "info", message })
      });
      commandPromise.catch(() => undefined);
      const result = await Promise.race([commandPromise, timeoutPromise]);
      completion = {
        commandId: active.commandId,
        command: active.command,
        status: result.ok ? "succeeded" : "failed",
        ok: result.ok,
        reason: result.reason,
        message: result.message,
        data: result.data,
        durationMs: Date.now() - startedAt
      };
    } catch (error) {
      completion = this.#completionFromError(active, error, startedAt);
    } finally {
      clearTimeout(timeout!);
    }

    try {
      if (!this.#cleanupAlreadyRun) {
        await this.#runCleanup();
      }
    } catch (error) {
      completion = {
        commandId: active.commandId,
        command: active.command,
        status: "failed",
        ok: false,
        reason: "cleanup_failed",
        message: error instanceof Error ? error.message : String(error),
        durationMs: Date.now() - startedAt
      };
    }

    active.status = completion.status;
    active.finishedAt = new Date().toISOString();
    if (this.options.hooks) {
      try {
        await this.options.hooks.afterCommand(hookContext, completion);
      } catch {
        // Hooks must never block command completion
      }
    }
    await this.#recordEvidence(completion, active);
    this.#emitCompletion(completion);
    this.options.emit({
      type: "log",
      level: completion.ok ? "info" : "error",
      message: `Command ${active.commandId} ${completion.status}: ${completion.message}`
    });
    this.#current = null;
    this.#controller = null;
    this.#cleanupAlreadyRun = false;
    this.#cleanupPromise = null;
    return completion;
  }

  async #recordEvidence(completion: CommandCompletion, active: CommandState): Promise<void> {
    if (!this.options.evidence) {
      return;
    }
    const cmd: CommandRecord = {
      id: null,
      runId: "default",
      evidenceType: "command",
      commandId: completion.commandId,
      command: completion.command,
      status: completion.status,
      input: active.input ?? null,
      acceptedAt: active.acceptedAt,
      startedAt: active.startedAt,
      finishedAt: active.finishedAt,
      durationMs: completion.durationMs,
      ok: completion.ok,
      reason: completion.reason ?? null,
      message: completion.message,
      data: completion.data ?? null,
      recordedAt: new Date().toISOString()
    };
    try {
      await this.options.evidence.recordCommand(cmd);
    } catch {
      // Evidence recording must not block command completion
    }
  }

  #completionFromError(active: CommandState, error: unknown, startedAt: number): CommandCompletion {
    const abort = abortFrom(error);
    if (abort?.kind === "cancelled") {
      return {
        commandId: active.commandId,
        command: active.command,
        status: "cancelled",
        ok: false,
        reason: "command_cancelled",
        message: "Command cancelled.",
        durationMs: Date.now() - startedAt
      };
    }
    if (abort?.kind === "timed_out") {
      return {
        commandId: active.commandId,
        command: active.command,
        status: "timed_out",
        ok: false,
        reason: "command_timed_out",
        message: "Command timed out.",
        durationMs: Date.now() - startedAt
      };
    }

    return {
      commandId: active.commandId,
      command: active.command,
      status: "failed",
      ok: false,
      reason: "command_failed",
      message: error instanceof Error ? error.message : String(error),
      durationMs: Date.now() - startedAt
    };
  }

  #emitCompletion(completion: CommandCompletion): void {
    if (completion.status === "succeeded") {
      this.options.emit({
        type: "command_finished",
        commandId: completion.commandId,
        command: completion.command,
        ok: true,
        data: completion.data ?? null
      });
      return;
    }

    const eventType = completion.status === "cancelled" ? "command_cancelled" : "command_failed";
    this.options.emit({
      type: eventType,
      commandId: completion.commandId,
      command: completion.command,
      ok: false,
      reason: completion.reason ?? "command_failed",
      message: completion.message
    });
  }

  async #runCleanup(): Promise<void> {
    if (!this.#cleanupPromise) {
      this.#cleanupPromise = Promise.resolve()
        .then(() => this.options.cleanup())
        .then(() => {
          this.#cleanupAlreadyRun = true;
        });
    }
    await this.#cleanupPromise;
  }
}

function abortFrom(error: unknown): CommandAbort | null {
  if (error instanceof CommandAbort) {
    return error;
  }
  if (error && typeof error === "object" && "kind" in error && (error as { kind?: unknown }).kind === "cancelled") {
    return new CommandAbort("cancelled");
  }
  if (error && typeof error === "object" && "kind" in error && (error as { kind?: unknown }).kind === "timed_out") {
    return new CommandAbort("timed_out");
  }
  return null;
}
