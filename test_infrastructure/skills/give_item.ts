export default async function run(api: SurvivalApi) {
  return await (api as any).giveItem("diamond", 64);
}
