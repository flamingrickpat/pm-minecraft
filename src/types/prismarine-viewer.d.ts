/**
 * prismarine-viewer lacks local TypeScript declarations; describe the Mineflayer entry this runtime calls.
 *
 * @remarks
 * archetype: interfacer
 * A side: the CommonJS prismarine-viewer package export.
 * B side: the narrow TypeScript call signature used by `src/viewer/viewer.ts`.
 * lossy ops: unsupported viewer APIs are intentionally not declared.
 * fails when: the package changes the Mineflayer viewer export shape.
 * invariant: this declaration does not define a fake viewer implementation.
 */
declare module "prismarine-viewer" {
  import type { Bot } from "mineflayer";

  export function mineflayer(bot: Bot, options: { port: number; firstPerson?: boolean; viewDistance?: number }): void;
}
