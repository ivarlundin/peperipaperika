import assert from 'node:assert/strict';
import {
  foldersNeededForEvents,
  getAudioEngine,
} from '../audio-engine.js';

assert.equal(getAudioEngine('https://example.com/a/'), getAudioEngine('https://example.com/b/'));

const events = [
  { voice: { kind: 'piano', sample: 'acoustic' } },
  { voice: { kind: 'trumpet' } },
];
const extra = foldersNeededForEvents(events);
assert.ok(extra.includes('samples/trumpet'));
assert.ok(!extra.includes('samples/piano'));

const engine = getAudioEngine('https://example.com/notlanken/');
engine._coreReady = true;
engine.prepared = true;
engine.beginSongPrepare(99);
assert.equal(engine.prepared, true, 'prepared stays true when core is hot');
assert.equal(engine.isCoreReady(), true);

console.log('prepare-cache tests OK');
