/**
 * Run one skill in a child process. The parent owns the deadline and PID.
 * Script errors return skill results. Process errors stop the current skill.
 * Shutdown sends EOF, then forces the child to exit after one second.
 */
import { spawn, type ChildProcess } from "node:child_process";
import { createInterface } from "node:readline";
import type { Writable } from "node:stream";
import { fileURLToPath } from "node:url";
import type { SkillOutcome } from "./bot.js";
import { log } from "./log.js";

const EXIT_GRACE_MS = 1000;
type Result = Pick<SkillOutcome, "status" | "reason">;

class SkillRunner {
  pid: number | null = null;
  private child: ChildProcess | null = null;
  private finish: ((result: Result) => void) | null = null;

  constructor() {
    process.once("exit", () => {
      if (this.child !== null) {
        this.child.stdin!.end();
        this.child.kill("SIGKILL");
      }
    });
    for (const signal of ["SIGINT", "SIGTERM"] as const) {
      process.once(signal, async () => {
        await this.close();
        process.exit(signal === "SIGINT" ? 130 : 143);
      });
    }
  }

  stop(): void {
    this.finish?.({ status: "stopped", reason: "The skill was stopped." });
  }

  async close(): Promise<void> {
    if (this.child === null) return;
    const exited = new Promise<void>((resolve) => this.child!.once("close", () => resolve()));
    this.stop();
    await exited;
  }

  async run(source: string, args: unknown, budgetMs: number, api: Record<string, unknown>, cancel: () => void): Promise<SkillOutcome> {
    if (this.child !== null) throw new Error("A skill process is already active.");
    const started = performance.now();
    const child = spawn(process.execPath, [fileURLToPath(new URL("./skill-child.js", import.meta.url))], {
      stdio: ["pipe", "pipe", "pipe", "pipe"], windowsHide: true,
    });
    this.child = child;
    this.pid = child.pid ?? null;
    log("info", `skill process started pid=${this.pid}`);
    const stdout: string[] = [];
    const stderr: string[] = [];
    let heartbeats = 0;
    let result: Result | null = null;
    let killTimer: NodeJS.Timeout | undefined;
    let deadlineTimer: NodeJS.Timeout;
    const lines = createInterface({ input: child.stdout! });

    const outcome = new Promise<SkillOutcome>((resolve) => {
      this.finish = (value) => {
        if (result !== null) return;
        result = value;
        clearTimeout(deadlineTimer);
        child.stdin!.end();
        log("info", `skill EOF sent pid=${this.pid} status=${value.status}`);
        killTimer = setTimeout(() => {
          log("warning", `skill force kill pid=${child.pid}`);
          child.kill("SIGKILL");
        }, EXIT_GRACE_MS);
        if (value.status !== "ok") cancel();
      };
      deadlineTimer = setTimeout(() => this.finish!({
        status: "timeout", reason: "The skill time budget expired.",
      }), budgetMs);
      child.on("error", (error) => this.finish!({ status: "typescript_error", reason: error.message }));
      // A child can exit between a response and its pipe write.
      const pipeError = (error: NodeJS.ErrnoException) => {
        if (error.code !== "EPIPE" && error.code !== "ERR_STREAM_DESTROYED") throw error;
        if (result !== null) return;
        this.finish!({ status: "typescript_error", reason: "The skill pipe closed." });
      };
      child.stdin!.on("error", pipeError);
      (child.stdio[3] as Writable).on("error", pipeError);
      child.stderr!.on("data", (data) => stderr.push(String(data)));
      child.once("close", (code, signal) => {
        clearTimeout(deadlineTimer);
        clearTimeout(killTimer);
        lines.close();
        if (result === null) {
          result = { status: "typescript_error", reason: `The skill process exited: code=${code}, signal=${signal}.` };
          cancel();
        }
        log("info", `skill process exited pid=${child.pid} code=${code} signal=${signal}`);
        this.child = null;
        this.pid = null;
        this.finish = null;
        resolve({ ...result, stdout_tail: tail(stdout), stderr_tail: tail(stderr), heartbeats,
          duration_ms: performance.now() - started });
      });
    });

    lines.on("line", async (line) => {
      const message = JSON.parse(line);
      if (result !== null) return;
      if (message.kind === "log") {
        (message.stream === "stdout" ? stdout : stderr).push(message.text);
      } else if (message.kind === "result") {
        this.finish!(message.result);
      } else if (message.kind === "call") {
        let response;
        try {
          const value = await (api[message.method] as (args: unknown) => unknown)(message.args);
          heartbeats += 1;
          response = { id: message.id, value };
        } catch (error) {
          const value = error as Error;
          response = { id: message.id, error: { name: value.name, message: value.message } };
        }
        if (result !== null) return;
        const pipe = message.sync ? child.stdio[3] as Writable : child.stdin!;
        pipe.write(JSON.stringify(response) + "\n");
      } else {
        throw new Error(`Unknown skill message: ${message.kind}`);
      }
    });
    child.stdin!.write(JSON.stringify({ source, args, methods: Object.keys(api) }) + "\n");
    return outcome;
  }
}

function tail(lines: string[]): string | null {
  return lines.length === 0 ? null : lines.slice(-20).join("\n");
}

export const skillRunner = new SkillRunner();
