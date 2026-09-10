export default async function run(api: SurvivalApi) {
  while (true) {
    await api.fineControl({ forward: true });
  }
}
