import assert from 'node:assert/strict';
import test from 'node:test';
import * as THREE from 'three';
import '../viewer-sync.js';

test('server time and rain change the actual viewer sky and lights', () => {
  const viewer = {
    scene: new THREE.Scene(),
    ambientLight: new THREE.AmbientLight(0xcccccc),
    directionalLight: new THREE.DirectionalLight(0xffffff, 0.5),
  };
  viewer.scene.background = new THREE.Color('lightblue');
  const state = { timeOfDay: 6000, dimension: 'overworld', isRaining: false };
  globalThis.mcmcpUpdateEnvironment(viewer, state);
  const day = viewer.scene.background.clone();
  const dayAmbient = viewer.ambientLight.intensity;
  globalThis.mcmcpUpdateEnvironment(viewer, { ...state, timeOfDay: 14756 });
  assert.ok(viewer.scene.background.b < day.b / 4);
  assert.ok(viewer.ambientLight.intensity < dayAmbient / 2);
  assert.equal(viewer.directionalLight.intensity, 0);
  globalThis.mcmcpUpdateEnvironment(viewer, { ...state, isRaining: true });
  assert.ok(viewer.scene.background.b < day.b);
  assert.ok(viewer.directionalLight.intensity < 0.5);
});
