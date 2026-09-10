import assert from 'node:assert/strict';
import test from 'node:test';
import minecraftData from 'minecraft-data';
import { Vec3 } from 'vec3';
import { MinecraftBody } from '../dist/bot.js';

// Exercise the real result handling with controlled pathfinder failures and
// post-dig block updates. These tests do not connect to or change a world.
function bodyWithBot() {
  const body = Object.create(MinecraftBody.prototype);
  body.configuration = { walkReachedDistanceBlocks: 3 };
  body.bot = {
    registry: minecraftData('1.20.4'),
    entity: { position: new Vec3(0.5, 61, 0.5), yaw: 0, pitch: 0, height: 1.8 },
    blockAt: () => ({ name: 'water', boundingBox: 'empty' }),
    clearControlStates() {},
    pathfinder: {
      setMovements() {},
      getPathTo: () => ({ status: 'success', path: [] }),
      async goto() {},
    },
  };
  return body;
}

test('arrival within tolerance still exposes two blocks of vertical error and water', async () => {
  const body = bodyWithBot();
  const result = await body.walk('test', { x: 0.5, y: 63, z: 0.5 }, {}, 1000);
  assert.equal(result.ok, true);
  assert.deepEqual(result.target_offset, { x: 0, y: 2, z: 0 });
  assert.equal(result.distance_remaining, 2);
  assert.equal(result.diagnostics.head_block, 'water');
  assert.equal(result.diagnostics.path_status, 'success');
});

for (const [name, reason, cause] of [
  ['GoalChanged', 'movement_error', 'movement_error'],
  ['NoPath', 'no_path', 'movement_no_path'],
  ['Timeout', 'timeout', 'replanning_timeout'],
  ['WalkTimeout', 'timeout', 'movement_timeout'],
]) {
  test(`preserves ${name} instead of hiding its cause`, async () => {
    const body = bodyWithBot();
    body.bot.pathfinder.goto = async () => { throw Object.assign(new Error('original detail'), { name }); };
    const result = await body.walk('test', { x: 4, y: 63, z: 0 }, {}, 1000);
    assert.equal(result.ok, false);
    assert.equal(result.reason, reason);
    assert.equal(result.diagnostics.cause, cause);
    assert.equal(result.diagnostics.error_name, name);
    assert.equal(result.diagnostics.error_message, 'original detail');
    assert.deepEqual(result.target_offset, { x: 3.5, y: 2, z: -0.5 });
  });
}

for (const replacement of ['air', 'cave_air', 'water', 'lava', 'stone', null]) {
  test(`post-dig replacement ${replacement}`, async () => {
    const body = bodyWithBot();
    let dug = false;
    body.bot.blockAt = () => dug
      ? replacement === null ? null : { name: replacement, displayName: replacement, boundingBox: replacement === 'stone' ? 'block' : 'empty' }
      : { name: 'stone', position: new Vec3(1, 61, 0), boundingBox: 'block', drops: [], canHarvest: () => true };
    body.bot.lookAt = async () => {};
    body.bot.dig = async () => { dug = true; };
    const result = await body.mine({ x: 1, y: 61, z: 0 });
    assert.equal(result.ok, replacement !== 'stone' && replacement !== null);
  });
}
