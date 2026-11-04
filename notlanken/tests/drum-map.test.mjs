import { readFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { DRUM_MAP } from '../audio-engine.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');

/** GM percussion notes we must resolve for autokomp + written kits. */
const REQUIRED_NOTES = [35, 36, 37, 38, 39, 40, 42, 44, 46, 49, 51, 53, 57];

const ALLOWED_FILES = new Set([
  '36-kick.ogg',
  '38-snare.ogg',
  '42-closed-hat.ogg',
  '46-open-hat.ogg',
  '49-crash.ogg',
  '51-ride.ogg',
  '53-ride-bell.ogg',
]);

for (const midi of REQUIRED_NOTES) {
  const file = DRUM_MAP[midi];
  if (!file) throw new Error(`DRUM_MAP missing GM note ${midi}`);
  if (!ALLOWED_FILES.has(file)) {
    throw new Error(`GM ${midi} maps to unexpected file ${file}`);
  }
}

for (const [midi, file] of Object.entries(DRUM_MAP)) {
  const s = String(file);
  if (s.includes('steel') || s.includes('reverse') || s.includes('melodic_tom')) {
    throw new Error(`GM ${midi} must not use effect sample ${file}`);
  }
}

const fetchSh = readFileSync(join(root, 'scripts/fetch-samples.sh'), 'utf8');
for (const bad of ['steel_drums', 'reverse_cymbal', 'melodic_tom', 'synth_drum']) {
  if (fetchSh.includes(`GLEITZ/${bad}`) || fetchSh.includes(`"${bad}-mp3`)) {
    throw new Error(`fetch-samples.sh downloads GM effect ${bad}`);
  }
}

console.log('drum-map tests OK');
