/**
 * Regression: markers-only Last Christmas must get a real transport length and
 * autokomp notes. Root cause of the silent/instant-stop bug was:
 *   @tonejs/midi → duration = -Infinity (no note events)
 *   Math.max(-Infinity, 0) → 0
 *   barStarts(midi, 0) → [0] only
 *   generate → 0 events (t1 <= t0)
 */
import { readFileSync, readdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';
import { parseSongMeta } from '../midi-meta.js';
import { barStarts, songDurationSeconds, estimateBarSeconds } from '../midi-time.js';
import { detectWrittenTracks, missingTracks } from '../autokomp-detect.js';
import { generate, resolveStyleId, defaultStyleForMeter } from '../autokomp.js';

const require = createRequire(import.meta.url);
const { Midi } = require('@tonejs/midi');

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

function loadMidi(file) {
  const buf = readFileSync(join(root, 'midi', file));
  return new Midi(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
}

function oldBuggyDuration(midi, writtenEvents) {
  // Pre-fix: Math.max(-Infinity, 0) === 0
  return Math.max(
    midi.duration,
    writtenEvents.length ? writtenEvents[writtenEvents.length - 1].time + 0.5 : 0,
  );
}

function generateFor(midi, duration) {
  const meta = parseSongMeta(midi);
  const written = detectWrittenTracks(midi);
  const need = missingTracks(written);
  const bars = barStarts(midi, duration);
  const sig = midi.header.timeSignatures?.[0]?.timeSignature || [4, 4];
  const styleId = defaultStyleForMeter(catalog, sig[0], sig[1]);
  const ev = need.length && meta.chords.length
    ? generate(
      { barStarts: bars, chords: meta.chords, sections: meta.sections, duration },
      {
        styleId,
        variant: 'auto',
        humanize: false,
        generate: need,
        dynamics: 'mf',
        styles,
        resolveStyleId: (id) => resolveStyleId(catalog, id),
      },
    )
    : [];
  return { meta, written, need, bars, styleId, ev };
}

// --- exact file: last-christmas-d-v03-markers.mid ---
{
  const file = 'last-christmas-d-v03-markers.mid';
  const midi = loadMidi(file);

  assert(midi.tracks.length === 0, `${file}: no note tracks`);
  assert(
    !Number.isFinite(midi.duration) || midi.duration <= 0,
    `${file}: @tonejs/midi duration is non-finite (got ${midi.duration})`,
  );
  assert(midi.header.meta?.length > 50, `${file}: meta present on header`);
  assert(midi.header.tempos?.length >= 2, `${file}: multi-tempo map (rit.)`);

  const meta = parseSongMeta(midi);
  // Both marker styles: [Intro] + section:Intro, chord marker + lyric + chord:
  assert(meta.sections.length >= 10, `${file}: sections parsed (${meta.sections.length})`);
  assert(meta.chords.length >= 50, `${file}: chords parsed (${meta.chords.length})`);
  assert(meta.sections.some((s) => /intro/i.test(s.label)), `${file}: [Intro]/section:Intro`);
  assert(meta.chords[0].symbol === 'D', `${file}: first chord D`);

  const writtenEvents = [];
  const buggy = oldBuggyDuration(midi, writtenEvents);
  assert(buggy === 0 || !Number.isFinite(buggy), `old formula collapses (got ${buggy})`);

  const duration = songDurationSeconds(midi, {
    writtenEvents,
    chords: meta.chords,
    sections: meta.sections,
  });
  assert(duration > 240 && duration < 320, `${file}: duration ~4:30 (got ${duration})`);
  assert(estimateBarSeconds(midi) > 1.5 && estimateBarSeconds(midi) < 3, 'bar ~2.22s at ♩=108');

  const { need, bars, styleId, ev } = generateFor(midi, duration);
  assert(need.join(',') === 'drums,bass,piano', `${file}: fill all three (${need})`);
  assert(bars.length >= 120 && bars.length <= 130, `${file}: ~121 bars (got ${bars.length})`);
  assert(styleId === 'pop-rock', `${file}: 4/4 default pop-rock (got ${styleId})`);
  assert(ev.length > 1000, `${file}: autokomp emits notes (got ${ev.length})`);
  assert(ev.some((e) => e.group === 'drums'), `${file}: drums`);
  assert(ev.some((e) => e.group === 'bass'), `${file}: bass`);
  assert(ev.some((e) => e.group === 'piano'), `${file}: piano`);
  assert(ev[0].time < 0.05, `${file}: starts at t≈0`);
  assert(ev[ev.length - 1].time > 200, `${file}: last event near end`);

  // Old path must produce nothing (the live bug)
  const oldBars = barStarts(midi, buggy || 0);
  const oldEv = generate(
    {
      barStarts: oldBars,
      chords: meta.chords,
      sections: meta.sections,
      duration: buggy || 0,
    },
    {
      styleId: 'pop-rock',
      variant: 'auto',
      humanize: false,
      generate: need,
      dynamics: 'mf',
      styles,
    },
  );
  assert(oldEv.length === 0, 'pre-fix path generates zero notes');
}

// --- Riverdance stub: written brass + markers, 12/8 → blues ---
{
  const file = 'riverdance-12-8-stub.mid';
  const midi = loadMidi(file);
  const meta = parseSongMeta(midi);
  assert(meta.chords.length >= 8, `${file}: chords`);
  assert(meta.sections.length >= 1, `${file}: sections`);

  const writtenEvents = [];
  for (const t of midi.tracks) {
    for (const n of t.notes) writtenEvents.push({ time: n.time });
  }
  writtenEvents.sort((a, b) => a.time - b.time);

  const duration = songDurationSeconds(midi, {
    writtenEvents,
    chords: meta.chords,
    sections: meta.sections,
  });
  assert(duration > 30, `${file}: duration ${duration}`);

  const { need, styleId, ev, written } = generateFor(midi, duration);
  assert(written.drums === false && written.bass === false && written.piano === false,
    `${file}: only brass written`);
  assert(need.includes('drums') && need.includes('bass') && need.includes('piano'),
    `${file}: autokomp fills rhythm section`);
  assert(styleId === 'blues', `${file}: 12/8 → blues (got ${styleId})`);
  assert(ev.length > 50, `${file}: autokomp notes (${ev.length})`);
  assert(Number.isFinite(midi.duration) && midi.duration > 0,
    `${file}: has written notes so finite midi.duration`);
}

// --- Sanity: full Last Christmas has written trio → generate nothing ---
{
  const file = 'last-christmas-d-v03.mid';
  const midi = loadMidi(file);
  const meta = parseSongMeta(midi);
  const duration = songDurationSeconds(midi, {
    writtenEvents: [{ time: midi.duration }],
    chords: meta.chords,
    sections: meta.sections,
  });
  const { need, ev, written } = generateFor(midi, duration);
  assert(written.drums && written.bass && written.piano, `${file}: all written`);
  assert(need.length === 0 && ev.length === 0, `${file}: no autokomp`);
}

console.log('markers-only playback regression OK');
