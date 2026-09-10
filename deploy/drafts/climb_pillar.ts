/**
 * Climb straight up by pillaring: jump and place the held solid block beneath,
 * repeated. Checks health and airspace before each climb.
 *
 * input:
 *   times : how many blocks to climb (default 3, max 16)
 *   block : the solid block to place (default: keep whatever solid block is held)
 */

interface Input {
  times?: number;
  block?: string;
}

const PLACEABLE = new Set([
  "cobblestone", "stone", "dirt", "netherrack", "sandstone", "deepslate",
  "cobbled_deepslate", "oak_planks", "spruce_planks", "birch_planks",
]);

export default async function run(api: any, rawInput: unknown) {
  const input = (rawInput ?? {}) as Input;
  const times = Math.min(16, Math.max(1, Math.floor(input.times ?? 3)));

  const state = await api.observe({});
  if (input.block) {
    await api.equip({ item: input.block });
  } else if (!state.held_item || !PLACEABLE.has(state.held_item.name)) {
    const found = state.inventory.find((item: { name: string }) => PLACEABLE.has(item.name));
    if (!found) {
      return { ok: false, reason: "no_placeable_block", inventory: state.inventory.map((i: any) => i.name) };
    }
    await api.equip({ item: found.name });
  }

  const startY = (await api.observe({})).camera.block_position.y;
  let climbed = 0;
  for (let i = 0; i < times; i++) {
    const before = await api.observe({});
    const health = before.player?.health ?? 0;
    if (health < 10) {
      return { ok: false, reason: "low_health", climbed, startY, health };
    }
    const result = await api.pillarUp();
    if (!result.ok) {
      return { ok: false, reason: result.reason ?? "pillar_failed", climbed, startY };
    }
    climbed = result.climbed;
  }

  const endY = (await api.observe({})).camera.block_position.y;
  return { ok: true, startY, endY, climbed };
}
