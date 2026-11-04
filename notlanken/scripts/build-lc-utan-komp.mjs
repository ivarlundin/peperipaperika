/**
 * Build Last Christmas "utan komp" chart: section + chord markers only (header meta).
 * No note tracks — autokomp fills drums, bass, piano at playback.
 * Source: midi/last-christmas-d-v03.mid (unchanged). Output: new file in midi/.
 */
import { readFileSync, writeFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';
import { parseSongMeta } from '../midi-meta.js';

const require = createRequire(import.meta.url);
const { Midi } = require('@tonejs/midi');

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const srcPath = join(root, 'midi/last-christmas-d-v03.mid');
const outPath = join(root, 'midi/last-christmas-d-v03-utan-komp.mid');

const src = new Midi(readFileSync(srcPath));
const meta = parseSongMeta(src);
if (meta.chords.length < 10) {
  throw new Error(`Expected chord markers in source (${meta.chords.length})`);
}

const out = new Midi();
out.header = JSON.parse(JSON.stringify(src.header));
out.tracks = [];

const noteCount = out.tracks.reduce((n, t) => n + t.notes.length, 0);
if (noteCount !== 0) {
  throw new Error(`Output must have zero notes, got ${noteCount}`);
}

writeFileSync(outPath, Buffer.from(out.toArray()));
console.log(
  'Wrote',
  outPath,
  `markers-only chords=${meta.chords.length} sections=${meta.sections.length} tracks=${out.tracks.length}`,
);
