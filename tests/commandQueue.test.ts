import { describe, expect, it, vi } from "vitest";
import { CommandQueue } from "../src/commands/commandQueue.js";

describe("CommandQueue", () => {
  it("runs one physical command through accepted, running, succeeded, and idle", async () => {
    const events: unknown[] = [];
    const cleanup = vi.fn();
    const queue = new CommandQueue({ cleanup, emit: (event) => events.push(event), defaultTimeoutMs: 1000 });

    const accepted = queue.enqueueOrReject({
      name: "fine_control",
      input: { durationMs: 1 },
      run: async ({ log }) => {
        log("moving forward");
        return { ok: true, message: "Done." };
      }
    });

    expect(accepted.accepted).toBe(true);
    if (!accepted.accepted) {
      throw new Error("Expected command to be accepted.");
    }
    expect(queue.currentCommand?.status).toBe("running");

    await expect(accepted.completed).resolves.toMatchObject({ status: "succeeded", ok: true });
    expect(cleanup).toHaveBeenCalledTimes(1);
    expect(queue.currentCommand).toBeNull();
    expect(events).toEqual([
      expect.objectContaining({ type: "command_started", command: "fine_control" }),
      { type: "log", level: "info", message: "moving forward" },
      expect.objectContaining({ type: "command_finished", ok: true }),
      expect.objectContaining({ type: "log", level: "info", message: expect.stringContaining("succeeded") })
    ]);
  });

  it("rejects a second physical command while one is running", async () => {
    let finish!: () => void;
    const queue = new CommandQueue({ cleanup: vi.fn(), emit: vi.fn(), defaultTimeoutMs: 1000 });

    const first = queue.enqueueOrReject({
      name: "fine_control",
      run: async () => {
        await new Promise<void>((resolve) => {
          finish = resolve;
        });
        return { ok: true, message: "Done." };
      }
    });
    expect(first.accepted).toBe(true);

    const second = queue.enqueueOrReject({
      name: "fine_control",
      run: async () => ({ ok: true, message: "Should not run." })
    });

    expect(second).toEqual({
      accepted: false,
      statusCode: 409,
      error: "command_conflict",
      message: "A physical command is already running."
    });

    finish();
    if (first.accepted) {
      await first.completed;
    }
  });

  it("times out visibly, runs cleanup, emits failure, and returns to idle", async () => {
    vi.useFakeTimers();
    try {
      const events: unknown[] = [];
      const cleanup = vi.fn();
      const queue = new CommandQueue({ cleanup, emit: (event) => events.push(event), defaultTimeoutMs: 50 });

      const accepted = queue.enqueueOrReject({
        name: "fine_control",
        run: async ({ signal }) => {
          await new Promise<void>((resolve, reject) => {
            signal.addEventListener("abort", () => reject(signal.reason), { once: true });
          });
          return { ok: true, message: "Should not finish." };
        }
      });

      expect(accepted.accepted).toBe(true);
      if (!accepted.accepted) {
        throw new Error("Expected command to be accepted.");
      }

      await vi.advanceTimersByTimeAsync(50);
      await expect(accepted.completed).resolves.toMatchObject({
        status: "timed_out",
        ok: false,
        reason: "command_timed_out",
        message: "Command timed out."
      });
      expect(cleanup).toHaveBeenCalledTimes(1);
      expect(queue.currentCommand).toBeNull();
      expect(events).toContainEqual(expect.objectContaining({ type: "command_failed", reason: "command_timed_out" }));
    } finally {
      vi.useRealTimers();
    }
  });

  it("returns to idle on timeout even when a command does not observe abort", async () => {
    vi.useFakeTimers();
    try {
      const cleanup = vi.fn();
      const queue = new CommandQueue({ cleanup, emit: vi.fn(), defaultTimeoutMs: 25 });

      const accepted = queue.enqueueOrReject({
        name: "fine_control",
        run: async () => {
          await new Promise(() => undefined);
          return { ok: true, message: "Should not finish." };
        }
      });

      expect(accepted.accepted).toBe(true);
      if (!accepted.accepted) {
        throw new Error("Expected command to be accepted.");
      }

      await vi.advanceTimersByTimeAsync(25);
      await expect(accepted.completed).resolves.toMatchObject({ status: "timed_out", ok: false });
      expect(cleanup).toHaveBeenCalledTimes(1);
      expect(queue.currentCommand).toBeNull();
    } finally {
      vi.useRealTimers();
    }
  });

  it("cancels the running command, clears pathfinder and controls, emits cancelled, and returns to idle", async () => {
    const events: unknown[] = [];
    const cleanup = vi.fn();
    const queue = new CommandQueue({ cleanup, emit: (event) => events.push(event), defaultTimeoutMs: 1000 });

    const accepted = queue.enqueueOrReject({
      name: "fine_control",
      run: async ({ signal }) => {
        await new Promise<void>((resolve, reject) => {
          signal.addEventListener("abort", () => reject(signal.reason), { once: true });
        });
        return { ok: true, message: "Should not finish." };
      }
    });

    expect(accepted.accepted).toBe(true);
    const stop = await queue.cancelCurrent();
    expect(stop).toEqual({ ok: true, message: "Stopped current command." });
    if (!accepted.accepted) {
      throw new Error("Expected command to be accepted.");
    }

    await expect(accepted.completed).resolves.toMatchObject({
      status: "cancelled",
      ok: false,
      reason: "command_cancelled",
      message: "Command cancelled."
    });
    expect(cleanup).toHaveBeenCalledTimes(1);
    expect(queue.currentCommand).toBeNull();
    expect(events).toContainEqual(expect.objectContaining({ type: "command_cancelled", reason: "command_cancelled" }));
  });
});
