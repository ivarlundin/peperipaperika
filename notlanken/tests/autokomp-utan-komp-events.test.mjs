import { readFileSync, readdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';
import { generate } from '../autokomp.js';
import { parseSongMeta } from '../midi-meta.js';
import { barStarts, songDurationSeconds } from '../midi-time.js';
import { getAudioEngine, DRUM_MAP } from '../audio-engine.js';

const require = createRequire(import.meta.url);
const { Midi } = require('@tonejs/midi');

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const catalog = JSON.parse(readFileSync(join(root, 'styles/catalog.json'), 'utf8'));
const styles = new Map();
for (const f of readdirSync(join(root, 'styles'))) {
  if (!f.endsWith('.json') || f === 'catalog.json') continue;
  const j = JSON.parse(readFileSync(join(root, 'styles', f), 'utf8'));
  styles.set(j.id, j);
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

const midiPath = join(root, 'midi/last-christmas-d-v03-utan-komp.mid');
const midi = new Midi(readFileSync(midiPath));
const noteCount = midi.tracks.reduce((n, t) => n + t.notes.length, 0);
assert(noteCount === 0, `utan-komp must have no MIDI notes (${noteCount})`);

const written = getAudioEngine('https://example.com/notlanken/').buildEvents(midi);
assert(written.length === 0, `written events must be empty (${written.length})`);

const meta = parseSongMeta(midi);
const duration = songDurationSeconds(midi, {
  writtenEvents: [],
  chords: meta.chords,
  sections: meta.sections,
});
const bars = barStarts(midi, duration);

const BRASS_PROGRAMS = new Set([56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71]);

for (const styleId of catalog.styles) {
  const ev = generate(
    { barStarts: bars, chords: meta.chords, sections: meta.sections, duration },
    {
      styleId,
      variant: 'A',
      humanize: false,
      generate: ['drums', 'bass', 'piano'],
      dynamics: 'mf',
      styles,
      resolveStyleId: (x) => x,
    },
  );
  assert(ev.length > 0, `${styleId}: emits events`);
  for (const e of ev) {
    assert(['drums', 'bass', 'piano'].includes(e.group), `${styleId}: bad group ${e.group}`);
    assert(
      !['gm', 'trumpet', 'trombone', 'tenor_sax', 'brass_section'].includes(e.voice?.kind),
      `${styleId}: horn voice ${e.voice?.kind}`,
    );
    if (e.group === 'drums') {
      assert(e.channel === 9, `${styleId}: drums must be channel 10 (9)`);
      assert((e.program ?? 0) === 0, `${styleId}: drums program must be 0`);
    }
    if (e.group === 'bass') {
      assert(e.voice?.kind === 'bass', `${styleId}: bass voice`);
      assert((e.program ?? 0) === 33, `${styleId}: bass program electric finger`);
    }
    if (e.group === 'piano') {
      assert(e.voice?.kind === 'piano', `${styleId}: piano voice`);
      assert(e.voice?.sample === 'acoustic', `${styleId}: piano must use Salamander acoustic`);
      assert((e.program ?? 0) === 0, `${styleId}: piano program acoustic grand`);
    }
    if (BRASS_PROGRAMS.has(e.program ?? -1) && e.group !== 'drums') {
      throw new Error(`${styleId}: brass program ${e.program} on ${e.group}`);
    }
  }
}

console.log('autokomp-utan-komp-events tests OK');
