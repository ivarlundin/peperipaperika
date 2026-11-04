import assert from 'node:assert/strict';
import { createSongLoadGuard } from '../song-load-guard.js';

const guard = createSongLoadGuard();
const a = guard.bump();
assert.equal(guard.isActive(a), true);
assert.equal(guard.current(), a);

const b = guard.bump();
assert.equal(guard.isActive(a), false);
assert.equal(guard.isActive(b), true);

/** Stale async work must not commit after a newer bump (song switch). */
async function staleFetchCompletesAfterSwitch() {
  const g = createSongLoadGuard();
  const first = g.bump();
  await Promise.resolve();
  const second = g.bump();
  assert.equal(g.isActive(first), false);
  assert.equal(g.isActive(second), true);
}

await staleFetchCompletesAfterSwitch();

console.log('song-load-guard tests OK');
