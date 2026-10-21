import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import minecraftData from 'minecraft-data';
import blockFactory from 'prismarine-block';
import pathfinderPackage from 'mineflayer-pathfinder';
import { Vec3 } from 'vec3';
import { survivalMovements } from '../dist/bot.js';

const captured = JSON.parse(readFileSync(new URL('./fixtures/emmy-terrace.json', import.meta.url)));
const registry = minecraftData('1.19.4');
const Block = blockFactory(registry);
const bot = {
  registry, entities: {}, inventory: { items: () => [] }, game: { minY: -64 },
  entity: { position: new Vec3(captured.feet.x, captured.feet.y, captured.feet.z), effects: {} },
  blockAt(position) {
    const cell = position.floored();
    const offset = cell.minus(new Vec3(captured.minimum.x, captured.minimum.y, captured.minimum.z));
    const name = captured.layers[offset.y]?.[offset.z]?.[offset.x];
    if (name === undefined) return null;
    const block = Block.fromStateId(registry.blocksByName[name].defaultState, 0);
    block.position = cell;
    return block;
  },
};

test('captured terrace replaces an upstream diagonal climb with cardinal jumps', () => {
  const node = { x: 15, y: 111, z: -3, remainingBlocks: 0 };
  const upstream = [];
  new pathfinderPackage.Movements(bot).getMoveDiagonal(node, { x: -1, z: 1 }, upstream);
  assert.ok(upstream.some(next => next.y > node.y), 'the original graph permits the captured corner climb');
  const repaired = survivalMovements(bot, null);
  const diagonals = [];
  repaired.getMoveDiagonal(node, { x: -1, z: 1 }, diagonals);
  assert.equal(diagonals.length, 0);
  for (const direction of [{ x: -1, z: 0 }, { x: 0, z: 1 }]) {
    const jumps = [];
    repaired.getMoveJumpUp(node, direction, jumps);
    assert.ok(jumps.some(next => next.y === 112), 'ordinary one-block ascent stays available');
  }
});

test('captured one-block descent remains available to cardinal routes', () => {
  const moves = survivalMovements(bot, null);
  const down = [];
  moves.getMoveDropDown({ x: 15, y: 112, z: -2, remainingBlocks: 0 }, { x: 1, z: 0 }, down);
  assert.ok(down.some(next => next.x === 16 && next.y === 111 && next.z === -2));
});
