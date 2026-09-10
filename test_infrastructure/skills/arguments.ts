export default async function run(api: SurvivalApi, arguments_: { steps: number }) {
  for (let index = 0; index < arguments_.steps; index += 1) {
    await api.observe({ includeImage: false });
  }
  return { steps: arguments_.steps };
}
