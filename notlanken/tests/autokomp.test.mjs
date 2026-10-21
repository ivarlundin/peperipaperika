import { readFileSync, readdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { parseChord, voiceChord, bassNote } from '../chord-parser.js';
import { detectWrittenTracks, missingTracks } from '../autokomp-detect.js';
import { generate } from '../autokomp.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const styles = new Map();
for (const f of readdirSync(join(root, 'styles'))) {
  if (!f.endsWith('.json') || f === 'catalog.json') continue;
  const j = JSON.parse(readFileSync(join(root, 'styles', f), 'utf8'));
  styles.set(j.id || f.replace('.json', ''), j);
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

// --- chord parser ---
{
  const c = parseChord('Bm7');
  assert(c.root === 11, 'Bm7 root');
  assert(c.tones.includes(2) || c.tones.includes((11 + 3) % 12), 'Bm7 has minor third');
  assert(!c.nc, 'Bm7 not nc');
}
{
  const c = parseChord('D/F#');
  assert(c.root === 2, 'D root');
  assert(c.bass === 6, 'F# bass');
}
{
  const c = parseChord('Fmaj7');
  assert(c.tones.includes((5 + 11) % 12), 'maj7');
}
{
  const c = parseChord('N.C.');
  assert(c.nc, 'N.C.');
}
{
  const v = voiceChord(parseChord('Cmaj7'), null);
  assert(v.length >= 3, 'voicing notes');
  assert(v.every((n) => n >= 50 && n <= 76), 'voicing in range');
}
{
  const ch = parseChord('C');
  const n = bassNote(ch, parseChord('G'), 'R', null);
  assert(n != null && n % 12 === 0, 'bass root C');
}

// --- detect tracks (mock midi-like) ---
{
  const midi = {
    tracks: [
      { name: 'Piano', channel: 0, instrument: { number: 0 }, notes: [{ midi: 60, time: 0, duration: 1, velocity: 0.5 }] },
    ],
  };
  const w = detectWrittenTracks(midi);
  assert(w.piano && !w.bass && !w.drums, 'piano only');
  const m = missingTracks(w);
  assert(m.includes('bass') && m.includes('drums') && !m.includes('piano'), 'fill bass+drums');
}
{
  const midi = {
    tracks: [
      { name: 'Bas', channel: 1, instrument: { number: 33 }, notes: [{ midi: 40, time: 0, duration: 1, velocity: 0.5 }] },
      { name: 'Trummor', channel: 9, instrument: { number: 0 }, notes: [{ midi: 36, time: 0, duration: 0.1, velocity: 0.5 }] },
      { name: 'Piano', channel: 0, instrument: { number: 0 }, notes: [{ midi: 60, time: 0, duration: 1, velocity: 0.5 }] },
    ],
  };
  assert(missingTracks(detectWrittenTracks(midi)).length === 0, 'full komp nothing missing');
}

// --- generate pop44 ---
{
  const bar = 2; // 120bpm 4/4
  const bars = Array.from({ length: 8 }, (_, i) => i * bar);
  const chords = [
    { time: 0, symbol: 'C' },
    { time: 2, symbol: 'Am7' },
    { time: 4, symbol: 'Fmaj7' },
    { time: 6, symbol: 'G7' },
    { time: 8, symbol: 'C' },
    { time: 10, symbol: 'Am7' },
    { time: 12, symbol: 'Fmaj7' },
    { time: 14, symbol: 'G7' },
  ];
  const sections = [
    { time: 0, label: 'Vers' },
    { time: 8, label: 'Refr.' },
  ];
  const ev = generate(
    { barStarts: bars, chords, sections, duration: 16 },
    { styleId: 'pop44', variant: 'auto', humanize: false, generate: ['drums', 'bass', 'piano'], styles, dynamics: 'mf' },
  );
  assert(ev.length > 20, `pop44 events ${ev.length}`);
  assert(ev.every((e) => ['drums', 'bass', 'piano'].includes(e.group)), 'only trio');
  assert(ev.every((e) => e.source === 'auto'), 'source auto');
  assert(ev.filter((e) => e.group === 'drums').some((e) => e.midi === 36), 'has kick');
  assert(ev.filter((e) => e.group === 'bass').length > 0, 'has bass');
  assert(ev.filter((e) => e.group === 'piano').every((e) => e.velocity < 0.55), 'mf piano not forte');
}

// --- generate twelve8 ---
{
  const bar = 2.4; // rough
  const bars = Array.from({ length: 4 }, (_, i) => i * bar);
  const chords = [
    { time: 0, symbol: 'C' },
    { time: bar, symbol: 'Am7' },
    { time: bar * 2, symbol: 'Fmaj7' },
    { time: bar * 3, symbol: 'G7' },
  ];
  const ev = generate(
    { barStarts: bars, chords, sections: [{ time: 0, label: 'Vers' }], duration: bar * 4 },
    { styleId: 'twelve8', variant: 'A', humanize: false, generate: ['drums', 'bass'], styles, dynamics: 'mf' },
  );
  assert(ev.some((e) => e.group === 'drums'), 'twelve8 drums');
  assert(!ev.some((e) => e.group === 'piano'), 'piano not requested');
}

// --- only missing ---
{
  const bars = [0, 2, 4, 6];
  const chords = bars.map((t) => ({ time: t, symbol: 'C' }));
  const ev = generate(
    { barStarts: bars, chords, sections: [], duration: 8 },
    { styleId: 'pop44', variant: 'A', humanize: false, generate: ['bass', 'drums'], styles },
  );
  assert(!ev.some((e) => e.group === 'piano'), 'no piano when not missing');
}

console.log('autokomp tests OK', styles.size, 'styles loaded');
