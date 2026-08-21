import { type MinecraftContext, type SkillEntrypoint } from "../lib/minecraft";

/**
 * LEGACY / EXAMPLE — DO NOT USE.
 *
 * This skill walked a straight compass heading in 30-block hops, checking
 * nearbyBlocks at each stop. It was unreliable (fails when a hop stalls, and
 * a flat-ground walk gives no sight over hills to spot a village). Retired.
 *
 * INSTEAD use the manual high-point strategy: climb / pillar to a high point,
 * scan in a full circle with minecraft_rotate, look at surroundings for village
 * blocks/entities, confirm with minecraft_raytrace, save the position with
 * minecraft_add_waypoint, then minecraft_walk_to it with a settable chunk_limit.
 * (See the find-village skill.)
 */
interface Input {
  heading?: string;
}

const run: SkillEntrypoint = async (_context: MinecraftContext, _rawInput: unknown) => {
  throw new Error(
    "find_village: legacy and example code, this skill does not work. " +
    "Locating a village is too complex for a TS script. Instead climb to a high " +
    "vantage point, scan around with minecraft_rotate + minecraft_observe, confirm " +
    "candidates with minecraft_raytrace, and travel with minecraft_walk_to " +
    "(settable chunk_limit). Save the sighting with minecraft_add_waypoint."
  );
};

export default run;
