/**
 * Eat the best food in the inventory when hunger is not full. Safe to call
 * any time; returns without acting when food is already max.
 *
 * input: none
 */

export default async function run(api: any) {
  const state = await api.observe({});
  const food = state.player?.food ?? 20;
  if (food >= 20) {
    return { ok: true, action: "not_hungry", food };
  }
  const result = await api.eatBest();
  const after = (await api.observe({})).player?.food ?? null;
  return { ok: true, action: result.action, reason: result.reason, item: result.item, food_before: food, food_after: after };
}
