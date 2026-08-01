import type { Bot } from "mineflayer";
import type { RuntimeConfig } from "../config.js";

/**
 * Viewer readiness needs the real bot attachment; start prismarine-viewer and expose literal startup status.
 *
 * @remarks
 * archetype: service-provider
 * owns: prismarine-viewer startup attempts and status fields for health reporting.
 * not own: screenshots, frame metadata, targeting, or browser UI controls.
 * fails when: prismarine-viewer throws while binding or attaching to the live Mineflayer bot.
 * domain: WI-01 reports readiness only; later work captures frame bundles through this viewer seam.
 * invariant: a started viewer is attached to the runtime's live bot, never a placeholder.
 */
export interface ViewerRuntime {
  status: ViewerStatus;
  start(bot: Bot): Promise<void>;
}

export interface ViewerStatus {
  enabled: boolean;
  started: boolean;
  port: number;
  url: string | null;
  firstPerson: boolean;
  error: string | null;
}

export function createViewerRuntime(config: RuntimeConfig["viewer"], host: string): ViewerRuntime {
  const status: ViewerStatus = {
    enabled: config.enabled,
    started: false,
    port: config.port,
    url: null,
    firstPerson: config.firstPerson,
    error: null
  };

  return {
    status,
    start: async (bot: Bot) => {
      if (!config.enabled || status.started) {
        return;
      }

      try {
        const { mineflayer: startMineflayerViewer } = await import("prismarine-viewer");
        startMineflayerViewer(bot, {
          port: config.port,
          firstPerson: config.firstPerson,
          viewDistance: config.viewDistance ?? 12
        });
        status.started = true;
        status.url = `http://${host}:${config.port}`;
      } catch (error) {
        status.error = error instanceof Error ? error.message : String(error);
      }
    }
  };
}
