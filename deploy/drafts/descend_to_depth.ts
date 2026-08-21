import { type MinecraftContext, type SkillEntrypoint } from "../lib/minecraft";

/**
 * LEGACY / EXAMPLE — DO NOT USE.
 *
 * This skill dug a straight 1-wide shaft straight down to a depth target. A
 * straight shaft cannot be climbed back up, so the bot would strand itself
 * (or fall into an undetectable lava/water/bedrock pocket). Retired.
 *
 * INSTEAD use: staircase_down (a 1-wide 2-tall ramp, walkable both ways) to
 * descend to depth, or dig_staircase for configurable direction/stop rules.
 */
interface Input {
  targetY?: number;
}

const run: SkillEntrypoint = async (_context: MinecraftContext, _rawInput: unknown) => {
  throw new Error(
    "dig-straight-down: legacy and example code, never dig straight down. " +
    "You won't be able to quickly get back up! Use staircase_down / dig_staircase " +
    "to descend to depth via a walkable ramp instead."
  );
};

export default run;
