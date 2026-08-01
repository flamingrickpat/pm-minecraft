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
 * fails when: runtime startup rejects, usually because an external dependency or HTTP port is unavailable.
 * invariant: this file is the only application start entry.
 */
export async function runMain(runtimeFactory: () => Runtime = createRuntime): Promise<void> {
  const runtime = runtimeFactory();
  process.once("SIGINT", () => {
    void runtime.stop().finally(() => process.exit(0));
  });
  process.once("SIGTERM", () => {
    void runtime.stop().finally(() => process.exit(0));
  });

  await runtime.start();
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  runMain().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
}
