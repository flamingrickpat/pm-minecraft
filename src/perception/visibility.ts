import type { Bot } from "mineflayer";

type MineflayerBlock = Parameters<Bot["canSeeBlock"]>[0];

/**
 * True when an unobstructed block ray can start at the player's head.
 * Mineflayer's canSeeBlock raycast does not depend on the current yaw/pitch.
 */
export function isVisibleFromHead(bot: Bot, block: MineflayerBlock): boolean {
  return bot.canSeeBlock(block);
}
