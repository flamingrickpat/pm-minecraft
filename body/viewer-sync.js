// Shared by the live viewer and screenshot capture. The server supplies time;
// this renderer only approximates daylight, weather, and dimension sky colors.
globalThis.mcmcpUpdateEnvironment = (viewer, state) => {
  const time = ((state.timeOfDay % 24000) + 24000) % 24000;
  const daylight = time < 12000 ? 1 : time < 14000 ? (14000 - time) / 2000
    : time < 22000 ? 0 : (time - 22000) / 2000;
  const dimension = state.dimension;
  const sky = dimension.includes('nether') ? [0.18, 0.035, 0.025]
    : dimension.includes('end') ? [0.035, 0.025, 0.055]
    : [0.025 + 0.50 * daylight, 0.035 + 0.70 * daylight, 0.08 + 0.84 * daylight];
  const weather = state.isRaining ? 0.65 : 1;
  viewer.scene.background.setRGB(...sky.map(value => value * weather));
  viewer.ambientLight.intensity = 0.22 + daylight * 0.78 * weather;
  viewer.directionalLight.intensity = daylight * 0.5 * weather;
};
