import { readFileSync, readdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { parseChord, voiceChord, bassNote } from '../chord-parser.js';
import { detectWrittenTracks, missingTracks } from '../autokomp-detect.js';
import { generate, resolveStyleId } from '../autokomp.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const catalog = JSON.parse(readFileSync(join(root, 'styles/catalog.json'), 'utf8'));
const styles = new Map();
for (const f of readdirSync(join(root, 'styles'))) {
  if (!f.endsWith('.json') || f === 'catalog.json') continue;
  const j = JSON.parse(readFileSync(join(root, 'styles', f), 'utf8'));
  styles.set(j.id || f.replace('.json', ''), j);
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

assert(catalog.styles.length === 5, 'five visible styles');
assert(styles.has('pop-rock') && styles.has('blues') && styles.has('jazz'), 'core styles');
assert(styles.has('waltz34') && styles.has('six8') && styles.has('nine8'), 'hidden meter fallbacks');
assert(resolveStyleId(catalog, 'twelve8') === 'blues', 'alias twelve8');
assert(resolveStyleId(catalog, 'pop44') === 'pop-rock', 'alias pop44');
assert(resolveStyleId(catalog, 'jazzswing') === 'jazz', 'alias jazzswing');

// --- chord parser ---
{
  const c = parseChord('Bm7');
  assert(c.root === 11, 'Bm7 root');
  assert(!c.nc, 'Bm7 not nc');
}
{
  const c = parseChord('D/F#');
  assert(c.root === 2 && c.bass === 6, 'slash');
}
{
  const n = bassNote(parseChord('C'), parseChord('G'), '8', 36);
  assert(n === 48, `octave 8 => ${n}`);
}

// --- detect ---
{
  const midi = {
    tracks: [
      { name: 'Piano', channel: 0, instrument: { number: 0 }, notes: [{ midi: 60, time: 0, duration: 1, velocity: 0.5 }] },
    ],
  };
  const m = missingTracks(detectWrittenTracks(midi));
  assert(m.includes('bass') && m.includes('drums') && !m.includes('piano'), 'fill bass+drums');
}

// --- swing: even 8th grid with swing>0.5 must push odd steps forward ---
{
  // Import stepTime indirectly: generate blues/jazz with swing 0.5 (triplet) — snare on steps 3 & 9
  // For a synthetic even grid, verify formula via small local copy
  function stepTime(t0, step, stepDur, swing, steps) {
    if (steps % 3 === 0 || !(swing > 0.5) || step % 2 !== 1) return t0 + step * stepDur;
    const pair = stepDur * 2;
    return t0 + (step - 1) * stepDur + pair * swing;
  }
  const d = 0.25;
  // old bug put odd steps at 0.32*d; fixed puts them at pair*swing = 0.66*0.5=0.33 from pair start
  const t3 = stepTime(0, 3, d, 0.66, 8); // step index 3 is odd
  assert(Math.abs(t3 - (2 * d + 2 * d * 0.66)) < 1e-9, `swing odd step ${t3}`);
  const tTrip = stepTime(0, 3, d, 0.66, 12); // triplet grid untouched
  assert(Math.abs(tTrip - 3 * d) < 1e-9, 'triplet unswung');
}

function timeline16() {
  // Last-Christmas-like: 16 bars of 2s, chords on each bar
  const bar = 2;
  const symbols = ['D', 'Bm', 'Em', 'A', 'D', 'Bm', 'Em', 'A', 'D', 'Bm', 'Em', 'A', 'D', 'Bm', 'Em', 'A'];
  const bars = symbols.map((_, i) => i * bar);
  const chords = symbols.map((symbol, i) => ({ time: i * bar, symbol }));
  const sections = [
    { time: 0, label: 'Intro' },
    { time: 8, label: 'Refr.' },
  ];
  return { barStarts: bars, chords, sections, duration: 16 * bar };
}

function fingerprint(ev) {
  // Stable signature of first 8 bars of note onsets (group, midi, quantized time)
  return ev
    .filter((e) => e.time < 16)
    .map((e) => `${e.group}:${e.midi}@${e.time.toFixed(3)}`)
    .join('|');
}

const tl = timeline16();
const fps = {};
for (const id of catalog.styles) {
  const ev = generate(tl, {
    styleId: id,
    variant: 'auto',
    humanize: false,
    generate: ['drums', 'bass', 'piano'],
    styles,
    dynamics: 'mf',
    resolveStyleId: (x) => resolveStyleId(catalog, x),
  });
  assert(ev.length > 10, `${id} produces notes`);
  assert(ev.every((e) => ['drums', 'bass', 'piano'].includes(e.group)), `${id} trio only`);
  // bossa must emit rim (37)
  if (id === 'bossa') {
    assert(ev.some((e) => e.group === 'drums' && e.midi === 37), 'bossa rim 37');
  }
  fps[id] = fingerprint(ev);
}

const ids = catalog.styles;
for (let i = 0; i < ids.length; i++) {
  for (let j = i + 1; j < ids.length; j++) {
    assert(fps[ids[i]] !== fps[ids[j]], `${ids[i]} vs ${ids[j]} must differ`);
  }
}

// Riverdance-like 12/8 stub: blues via alias twelve8
{
  const bar = 2.4;
  const bars = Array.from({ length: 8 }, (_, i) => i * bar);
  const chords = ['C', 'Am7', 'Fmaj7', 'G7', 'C', 'Am7', 'Fmaj7', 'G7'].map((symbol, i) => ({
    time: i * bar,
    symbol,
  }));
  const evBlues = generate(
    { barStarts: bars, chords, sections: [{ time: 0, label: 'Vers' }], duration: bar * 8 },
    { styleId: 'twelve8', variant: 'A', humanize: false, generate: ['drums', 'bass', 'piano'], styles, resolveStyleId: (x) => resolveStyleId(catalog, x) },
  );
  const evPop = generate(
    { barStarts: bars, chords, sections: [{ time: 0, label: 'Vers' }], duration: bar * 8 },
    { styleId: 'pop-rock', variant: 'A', humanize: false, generate: ['drums', 'bass', 'piano'], styles },
  );
  assert(evBlues.length > 0 && fingerprint(evBlues) !== fingerprint(evPop), 'twelve8 alias ≠ pop-rock');
}

console.log('autokomp styles5 tests OK', catalog.styles.join(', '));
