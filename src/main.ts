import { createRuntime, type Runtime } from "./runtime.js";
import { pathToFileURL } from "node:url";

/**
 * Process startup needs one product entry; delegate to the shared runtime composition path and report fatal startup errors.
 *
 * @remarks
 * archetype: controller
 * trigger: Node executes `src/main.ts` through the package `dev` script.
 * owns: top-level runtime start, signal handling, and process-level fatal error reporting.
 * coordinates: `src/runtime.ts` creates and owns the live runtime components.
 * fails when: runtime startup rejects, usually because an external dependency or an HTTP port is unavailable.
 * invariant: this file is the only application start entry.
 */

/** True when the embedding Python supervisor attached this process through a stdin lifecycle pipe. */
function stdinLifecycleEnabled(): boolean {
  return process.env.MINECRAFT_STDIN_LIFECYCLE === "1";
}

export async function runMain(runtimeFactory: () => Runtime = createRuntime): Promise<void> {
  const runtime = runtimeFactory();
  let stopping = false;
  const shutdown = () => {
    if (stopping) {
      return;
    }
    stopping = true;
    void runtime.stop().finally(() => process.exit(0));
  };
  process.once("SIGINT", shutdown);
  process.once("SIGTERM", shutdown);
  // Embedded mode: the Python supervisor owns the write end of our stdin
  // pipe. When the supervisor (or its whole process) dies, the OS closes
  // the pipe, stdin ends, and this body shuts down cleanly. No detached
  // processes, no taskkill, same semantics on Windows and Linux.
  if (stdinLifecycleEnabled()) {
    process.stdin.on("end", shutdown);
    process.stdin.on("error", () => undefined);
    process.stdin.resume();
  }

  await runtime.start();
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  runMain().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
}
