export default async function run(api: SurvivalApi) {
  await api.observe({ includeImage: false });
  return { observed: true };
}
