export default async function run(api: SurvivalApi) {
  return await (api as any).teleport(1000, 200, 1000);
}
