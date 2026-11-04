import { readFileSync, readdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { spawnSync } from 'node:child_process';
import { generate } from '../autokomp.js';
import { DRUM_MAP } from '../audio-engine.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const catalog = JSON.parse(readFileSync(join(root, 'styles/catalog.json'), 'utf8'));
const styles = new Map();
for (const f of readdirSync(join(root, 'styles'))) {
  if (!f.endsWith('.json') || f === 'catalog.json') continue;
  const j = JSON.parse(readFileSync(join(root, 'styles', f), 'utf8'));
  styles.set(j.id, j);
}

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
  return { peak, earlyRatio: peak > 0 ? earlyPeak / peak : 0 };
}

const drumDir = join(root, 'samples', 'drums');
const bar = 2;
const barStarts = [0, bar, bar * 2, bar * 3];

for (const styleId of catalog.styles) {
  const ev = generate(
    {
      barStarts,
      chords: [{ time: 0, symbol: 'D' }, { time: bar * 2, symbol: 'A' }],
      sections: [{ time: 0, label: 'Test' }],
      duration: bar * 4,
    },
    {
      styleId,
      variant: 'A',
      humanize: false,
      generate: ['drums'],
      dynamics: 'mf',
      styles,
      resolveStyleId: (x) => x,
    },
  ).filter((e) => e.group === 'drums');

  const midis = new Set(ev.map((e) => e.midi));
  for (const midi of midis) {
    const file = DRUM_MAP[midi];
    if (!file) throw new Error(`${styleId}: unmapped drum MIDI ${midi}`);
    if (String(file).includes('steel') || String(file).includes('reverse')) {
      throw new Error(`${styleId}: bad drum file ${file} for MIDI ${midi}`);
    }
  }

  const files = new Set([...midis].map((m) => DRUM_MAP[m]));
  for (const file of files) {
    const path = join(drumDir, file);
    const { earlyRatio } = analyzeOgg(path);
    const isCymbal = file.startsWith('49-') || file.startsWith('51-') || file.startsWith('53-');
    const minRatio = isCymbal ? 0.9 : 0.75;
    if (earlyRatio < minRatio) {
      throw new Error(`${styleId}: ${file} slow attack (${(earlyRatio * 100).toFixed(1)}%)`);
    }
  }
}

console.log('autokomp-style-drums tests OK');
