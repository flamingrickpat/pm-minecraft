/** Check the actual wrong-container failure before the body opens a window. */
import { readFileSync } from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import { storageTargetReason } from '../dist/bot.js';

const captured = JSON.parse(readFileSync(new URL('./fixtures/a13-furnace-storage-target.json', import.meta.url)));
test('the actual furnace is refused; projected nearby storage remains available', () => {
  const inspect = captured.rows.find(row => row.seq === 18 && row.event === 'result');
  const walk = captured.rows.find(row => row.seq === 20 && row.event === 'result');
  const uncertain = captured.rows.find(row => row.event === 'uncertain');
  assert.equal(uncertain.tool, 'minecraft_chest_withdraw');
  assert.equal(storageTargetReason(inspect.result.block_name, walk.result.distance_remaining), 'not_storage_container');
  assert.equal(storageTargetReason('chest', 5), null);
  assert.equal(storageTargetReason('blue_shulker_box', 4), null);
  assert.equal(storageTargetReason('barrel', 5.01), 'out_of_range');
  assert.equal(storageTargetReason(null, 3), 'target_changed');
});
