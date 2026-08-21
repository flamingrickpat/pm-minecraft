import { type MinecraftContext, type SkillEntrypoint } from "../lib/minecraft";

/**
 * LEGACY / EXAMPLE — DO NOT USE.
 *
 * This skill dug a straight 1-wide vertical shaft straight down, which the
 * pathfinder cannot reliably climb back out of (and risks lava/water/bedrock
 * traps below). It has been retired.
 *
 * INSTEAD use: staircase_down (or dig_staircase) which carves a 2-tall,
 * 1-wide ramp the bot can walk down AND back up.
 */
interface Input {
  targetY?: number;
}

const run: SkillEntrypoint = async (_context: MinecraftContext, _rawInput: unknown) => {
  throw new Error(
    "dig-straight-down: legacy and example code, never dig straight down. " +
    "You won't be able to quickly get back up! Use staircase_down or dig_staircase " +
    "(a 1-wide 2-tall ramp) to descend safely instead, or dig_staircase_up to ascend."
  );
};

export default run;
