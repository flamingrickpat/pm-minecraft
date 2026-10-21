import assert from 'node:assert/strict';
import test from 'node:test';
import minecraftData from 'minecraft-data';
import { Vec3 } from 'vec3';
import { EventEmitter } from 'node:events';
import { MinecraftBody } from '../dist/bot.js';

// Exercise the real result handling with controlled pathfinder failures and
// post-dig block updates. These tests do not connect to or change a world.
function bodyWithBot() {
  const body = Object.create(MinecraftBody.prototype);
  body.configuration = { walkReachedDistanceBlocks: 3 };
  body.bot = Object.assign(new EventEmitter(), {
    registry: minecraftData('1.20.4'),
    entity: { position: new Vec3(0.5, 61, 0.5), yaw: 0, pitch: 0, height: 1.8 },
    blockAt: () => ({ name: 'water', boundingBox: 'empty' }),
    clearControlStates() {},
    pathfinder: {
      setMovements() {},
      getPathTo: () => ({ status: 'success', path: [] }),
      *getPathFromTo() { yield { result: this.getPathTo() }; },
      setGoal() {},
      async goto() {},
    },
  });
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

test('a failed walk retains movement and hop evidence', async () => {
  const body = bodyWithBot();
  body.bot.pathfinder.goto = async () => {
    body.bot.entity.position.x += 2;
    throw Object.assign(new Error('no route after movement'), { name: 'NoPath' });
  };
  const result = await body.walk('test', { x: 10, y: 61, z: 0 }, {}, 1000);
  assert.equal(result.status, 'partial');
  assert.equal(result.hops, 1);
});

test('planning consumes partial slices and stops at a terminal result', async () => {
  const body = bodyWithBot();
  let slices = 0;
  body.bot.pathfinder.getPathFromTo = function* () {
    for (const status of ['partial', 'partial', 'success']) {
      slices += 1;
      yield { result: { status, path: [{ x: 1, y: 61, z: 0 }, { x: 2, y: 61, z: 0 }] } };
    }
  };
  const result = await body.findPath({ x: 2, y: 61, z: 0 }, 32, 1000);
  assert.equal(result.state, 'reachable');
  assert.equal(slices, 3);
});

test('unsupported terrain does not report air as an obstacle', async () => {
  const body = bodyWithBot();
  body.bot.blockAt = () => ({ name: 'air', boundingBox: 'empty' });
  body.bot.pathfinder.getPathTo = () => ({ status: 'noPath', path: [] });
  const result = await body.findPath({ x: 2, y: 64, z: 0 }, 32, 1000);
  assert.equal(result.state, 'blocked');
  assert.equal(result.blocker, null);
});

test('a stalled walker stops promptly with a specific cause', async () => {
  const body = bodyWithBot();
  body.bot.pathfinder.goto = () => new Promise(() => {});
  const started = performance.now();
  const result = await body.walk('test', { x: 10, y: 61, z: 0 }, {}, 120000);
  assert.equal(result.reason, 'no_path');
  assert.equal(result.diagnostics.cause, 'movement_stalled');
  assert.equal(result.hops, 0);
  assert.ok(performance.now() - started < 8000);
});

test('omitted angles preserve pose and reported vectors match Mineflayer', async () => {
  const body = bodyWithBot();
  body.bot.entity.yaw = Math.PI / 2; // west
  body.bot.entity.pitch = 0.3;
  body.bot.look = async (yaw, pitch) => { Object.assign(body.bot.entity, { yaw, pitch }); };
  let camera = await body.rotate(null, 90, true);
  assert.equal(camera.yaw, 90);
  assert.equal(camera.pitch, 90);
  camera = await body.rotate(0, 0, true);
  assert.equal(camera.cardinal, 'south');
  assert.ok(camera.look_vector.z > 0.99);
  camera = await body.rotate(null, null, true);
  assert.equal(camera.yaw, 0);
  camera = await body.rotate(-90, null, false);
  assert.equal(camera.yaw, 270);
  assert.ok(camera.look_vector.x > 0.99);
});

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
