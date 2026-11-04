/**
 * Build Last Christmas "utan komp" chart: chord markers + Blås melody only.
 * Source: midi/last-christmas-d-v03.mid (unchanged). Output: new file in midi/.
 */
import { readFileSync, writeFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const { Midi } = require('@tonejs/midi');

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const srcPath = join(root, 'midi/last-christmas-d-v03.mid');
const outPath = join(root, 'midi/last-christmas-d-v03-utan-komp.mid');

const src = new Midi(readFileSync(srcPath));
const melody = src.tracks.filter((t) => /blås|blas|melodi|lead/i.test(String(t.name || '')));
if (!melody.length) {
  throw new Error('Expected Blås/melody track in source MIDI');
}

const out = new Midi();
out.header = JSON.parse(JSON.stringify(src.header));
out.tracks = melody.map((t) => t);

writeFileSync(outPath, Buffer.from(out.toArray()));
console.log('Wrote', outPath, 'tracks:', out.tracks.map((t) => `${t.name}(${t.notes.length})`).join(', '));
