/** Check live player slots after the actual M3-41 furnace recovery. */
import { readFileSync } from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import { windowInventoryCount } from '../dist/bot.js';

const captured = JSON.parse(readFileSync(new URL('./fixtures/a13-window-inventory.json', import.meta.url)));
test('recovered input belongs to player slots while furnace slots stay excluded', () => {
  const smelt = captured.rows.find(row => row.seq === 23);
  assert.equal(smelt.result.reason, 'missing');
  const raw = smelt.result.inventory_delta.changes.find(row => row.item === 'raw_iron');
  assert.equal(raw.before, 0);
  assert.equal(raw.after, 2);
  const observed = captured.rows.find(row => row.tool === 'minecraft_observe');
  const logs = observed.result.inventory.find(row => row.name === 'birch_log');
  assert.equal(logs.count, 14);
  // Project the successful transfers into the live furnace's player slots.
  const slots = Array(39).fill(null);
  slots[3] = {name: 'raw_iron', count: raw.after};
  slots[4] = {name: 'birch_log', count: logs.count};
  assert.equal(windowInventoryCount(slots, 3, 39, 'raw_iron'), 2);
  assert.equal(windowInventoryCount(slots, 3, 39, 'birch_log'), 14);
  slots[0] = {name: 'raw_iron', count: 3};
  assert.equal(windowInventoryCount(slots, 3, 39, 'raw_iron'), 2);
});
