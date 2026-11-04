import { readdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { spawnSync } from 'node:child_process';

/** Files referenced by DRUM_MAP in audio-engine.js (unique). */
const DRUM_FILES = new Set([
  '36-kick.ogg',
  '38-snare.ogg',
  '42-closed-hat.ogg',
  '46-open-hat.ogg',
  '49-crash.ogg',
  '51-ride.ogg',
  '53-ride-bell.ogg',
]);

const root = join(dirname(fileURLToPath(import.meta.url)), '..', 'samples', 'drums');

function analyzeOgg(path) {
  const proc = spawnSync(
    'ffmpeg',
    ['-hide_banner', '-loglevel', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', '44100', '-'],
    { encoding: 'buffer', maxBuffer: 64 * 1024 * 1024 },
  );
  if (proc.status !== 0) throw new Error(`ffmpeg failed for ${path}`);
  const buf = proc.stdout;
  const n = Math.floor(buf.length / 4);
  let peak = 0;
  const win = Math.min(n, Math.floor(0.02 * 44100));
  let earlyPeak = 0;
  for (let i = 0; i < n; i += 1) {
    const s = Math.abs(buf.readFloatLE(i * 4));
    if (s > peak) peak = s;
    if (i < win && s > earlyPeak) earlyPeak = s;
  }
  let t90 = null;
  const thresh = 0.9 * peak;
  for (let i = 0; i < n; i += 1) {
    if (Math.abs(buf.readFloatLE(i * 4)) >= thresh) {
      t90 = (i / 44100) * 1000;
      break;
    }
  }
  return { peak, earlyPeak, t90Ms: t90 };
}

for (const file of DRUM_FILES) {
  const path = join(root, file);
  const { peak, earlyPeak, t90Ms } = analyzeOgg(path);
  if (peak <= 0) throw new Error(`${file}: silent sample`);
  const earlyRatio = earlyPeak / peak;
  const isCymbal = file.startsWith('49-') || file.startsWith('51-') || file.startsWith('53-');
  if (earlyRatio < (isCymbal ? 0.9 : 0.75)) {
    throw new Error(
      `${file}: attack too slow (peak in first 20ms is ${(earlyRatio * 100).toFixed(1)}% of max — reverse-swell?)`,
    );
  }
  if (isCymbal && (t90Ms == null || t90Ms > 20)) {
    throw new Error(`${file}: 90% of peak not reached within 20ms (t90=${t90Ms})`);
  }
}

// No extra FluidR3 cymbal files left in drum kit folder
for (const name of readdirSync(root)) {
  if (!name.endsWith('.ogg')) continue;
  if (!DRUM_FILES.has(name) && name.match(/^(49|51|53)-/)) {
    throw new Error(`unexpected cymbal ogg in drums/: ${name}`);
  }
}

console.log('drum-sample-attack tests OK');
