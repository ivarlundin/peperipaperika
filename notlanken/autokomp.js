/**
 * Autokomp engine: generate drums/bass/piano from chord+section timeline + style grids.
 * Pure JS — no audio. Testable without a browser.
 */
import { bassNote, parseChord, voiceChord } from './chord-parser.js';

/** Only kick / snare / hats / cymbals — no toms, percussion toys, etc. */
const DRUM_MIDI = {
  kick: 36,
  snare: 38,
  rim: 38, // rim patterns play as snare
  hat: 42,
  ohat: 46,
  pedal: 42,
  ride: 51,
  bell: 51,
  crash: 49,
};

/** GM drum notes we allow to sound (autokomp + written MIDI). */
export const ALLOWED_DRUM_MIDI = new Set([35, 36, 38, 42, 44, 46, 49, 51, 53]);

const HIT_VEL = { X: 0.72, x: 0.52, o: 0.28 };
/** Mezzoforte scale applied on top of hit velocities */
const MF = 0.62;

/**
 * @typedef {Object} AutokompOpts
 * @property {string} styleId
 * @property {'A'|'B'|'auto'} variant
 * @property {boolean} [humanize]
 * @property {number} [swing]  override 0.5–0.67
 * @property {('drums'|'bass'|'piano')[]} generate
 * @property {'p'|'mf'|'f'} [dynamics]
 * @property {Map<string, object>} styles  id -> style json
 * @property {number} [fromTime]  only emit from this song time (mid-play style swap)
 */

/**
 * @param {object} timeline
 * @param {number[]} timeline.barStarts  seconds
 * @param {{time:number,symbol:string}[]} timeline.chords
 * @param {{time:number,label:string}[]} timeline.sections
 * @param {number} timeline.duration
 * @param {AutokompOpts} opts
 */
export function generate(timeline, opts) {
  const styleId = opts.resolveStyleId
    ? opts.resolveStyleId(opts.styleId)
    : (opts.styleId || 'pop-rock');
  const style = opts.styles.get(styleId) || opts.styles.get('pop-rock');
  if (!style) return [];

  const dynScale = opts.dynamics === 'p' ? 0.75 : opts.dynamics === 'f' ? 1.15 : 1;
  const humanize = opts.humanize !== false;
  const want = new Set(opts.generate || ['drums', 'bass', 'piano']);
  const events = [];

  let prevVoicing = null;
  let prevBass = null;
  let arpIdx = 0;

  const bars = timeline.barStarts;
  let startBi = 0;
  if (opts.fromTime != null && Number.isFinite(opts.fromTime)) {
    startBi = bars.findIndex((t) => t >= opts.fromTime - 0.001);
    if (startBi < 0) return [];
  }
  for (let bi = startBi; bi < bars.length; bi++) {
    const t0 = bars[bi];
    const t1 = bi + 1 < bars.length ? bars[bi + 1] : timeline.duration;
    if (t1 <= t0) continue;

    const section = sectionAt(timeline.sections, t0);
    const variant = resolveVariant(opts.variant, section);
    const grid = style[variant] || style.A || style;
    const steps = style.steps || gridSteps(grid);
    const stepDur = (t1 - t0) / steps;
    const swing = opts.swing ?? style.swing ?? 0.5;

    const chord = parseChord(chordAt(timeline.chords, t0) || 'N.C.');
    const nextChord = parseChord(
      chordAt(timeline.chords, t1) || chordAt(timeline.chords, t0) || 'N.C.',
    );

    const isSectionStart = bi === 0 || sectionChanged(timeline.sections, bars[bi - 1], t0);
    const nextIsSection = bi + 1 < bars.length && sectionChanged(timeline.sections, t0, bars[bi + 1]);
    const isLastBar = bi === bars.length - 1;

    if (want.has('drums')) {
      emitDrums(events, {
        grid, steps, stepDur, t0, swing, humanize, dynScale,
        isSectionStart, nextIsSection, isLastBar, style, bi,
      });
    }
    if (want.has('bass')) {
      prevBass = emitBass(events, {
        grid, steps, stepDur, t0, t1, swing, humanize, dynScale,
        chords: timeline.chords, prevBass,
      });
    }
    if (want.has('piano')) {
      const r = emitPiano(events, {
        grid, steps, stepDur, t0, swing, humanize, dynScale,
        chords: timeline.chords, prevVoicing, arpIdx,
      });
      prevVoicing = r.voicing;
      arpIdx = r.arpIdx;
    }
  }

  events.sort((a, b) => a.time - b.time);
  return events;
}

function gridSteps(grid) {
  for (const k of Object.keys(DRUM_MIDI).concat(['bass', 'piano'])) {
    if (grid[k]) return splitPattern(grid[k]).length;
  }
  return 8;
}

function splitPattern(pat) {
  return String(pat).trim().split(/\s+/);
}

function resolveVariant(pref, sectionLabel) {
  if (pref === 'A' || pref === 'B') return pref;
  const s = String(sectionLabel || '').toLowerCase();
  if (/refr|chorus|brygga|bridge|outro|solo/.test(s)) return 'B';
  return 'A';
}

function sectionAt(sections, t) {
  let label = '';
  for (const s of sections) {
    if (s.time <= t + 0.001) label = s.label;
    else break;
  }
  return label;
}

function chordAt(chords, t) {
  let symbol = '';
  for (const c of chords) {
    if (c.time <= t + 0.001) symbol = c.symbol;
    else break;
  }
  return symbol;
}

function sectionChanged(sections, tA, tB) {
  return sectionAt(sections, tA) !== sectionAt(sections, tB);
}

function stepTime(t0, step, stepDur, swing, steps) {
  // Triplet grids already encode swing — leave them alone.
  if (steps % 3 === 0 || !(swing > 0.5) || step % 2 !== 1) {
    return t0 + step * stepDur;
  }
  const pair = stepDur * 2;
  return t0 + (step - 1) * stepDur + pair * swing;
}

function human(time, vel, on) {
  if (!on) return { time, velocity: vel };
  return {
    time: time + (Math.random() - 0.5) * 0.012,
    velocity: Math.max(0.05, Math.min(1, vel * (0.92 + Math.random() * 0.16))),
  };
}

function emitDrums(events, ctx) {
  const {
    grid, steps, stepDur, t0, swing, humanize, dynScale,
    isSectionStart, nextIsSection, isLastBar, style,
  } = ctx;
  const velMap = style.vel || {};

  if (isSectionStart) {
    const h = human(t0, 0.7 * MF * dynScale, humanize);
    events.push(drumEv(h.time, 49, Math.min(0.15, stepDur * 2), h.velocity));
  }

  for (const [name, midi] of Object.entries(DRUM_MIDI)) {
    const pat = grid[name];
    if (!pat) continue;
    const toks = splitPattern(pat);
    for (let i = 0; i < steps; i++) {
      const tok = toks[i] || '.';
      if (tok === '.') continue;
      const base = (HIT_VEL[tok] ?? 0.5) * MF * dynScale * (velMap[name] ?? 1);
      const h = human(stepTime(t0, i, stepDur, swing, steps), base, humanize);
      events.push(drumEv(h.time, midi, Math.min(stepDur * 0.9, 0.25), h.velocity));
    }
  }

  // fill before next section / end (fill_beats: 0 disables) — snare + kick only
  const fillBeats = style.fill_beats ?? 1;
  if (fillBeats > 0 && (nextIsSection || isLastBar)) {
    const nFill = Math.min(steps, Math.max(2, fillBeats * (style.beat || 2)));
    const start = steps - nFill;
    for (let i = start; i < steps; i++) {
      const h = human(stepTime(t0, i, stepDur, swing, steps), 0.55 * MF * dynScale, humanize);
      events.push(drumEv(h.time, i % 2 === 0 ? 38 : 36, 0.08, h.velocity));
    }
    if (isLastBar) {
      const h = human(t0 + (steps - 1) * stepDur, 0.75 * MF * dynScale, humanize);
      events.push(drumEv(h.time, 49, 0.4, h.velocity));
    }
  }
}

function drumEv(time, midi, duration, velocity) {
  return {
    time, duration, midi, velocity,
    channel: 9, program: 0,
    voice: { kind: 'drums' },
    group: 'drums',
    source: 'auto',
  };
}

function emitBass(events, ctx) {
  const {
    grid, steps, stepDur, t0, t1, swing, humanize, dynScale, chords,
  } = ctx;
  let prevBass = ctx.prevBass;
  const toks = splitPattern(grid.bass || '');
  let lastOn = null;
  for (let i = 0; i < steps; i++) {
    const tok = toks[i] || '.';
    if (tok === '.') {
      lastOn = null;
      continue;
    }
    if (tok === '-') {
      if (lastOn) lastOn.duration += stepDur;
      continue;
    }
    const stepT = stepTime(t0, i, stepDur, swing, steps);
    const chord = parseChord(chordAt(chords, stepT) || 'N.C.');
    if (chord.nc) {
      lastOn = null;
      continue;
    }
    const nextT = i + 1 < steps ? stepTime(t0, i + 1, stepDur, swing, steps) : t1;
    const nextChord = parseChord(chordAt(chords, nextT) || chord.symbol);
    const note = bassNote(chord, nextChord, tok, prevBass);
    if (note == null) continue;
    let n = note;
    while (n < 28) n += 12;
    while (n > 55) n -= 12;
    const h = human(stepT, 0.58 * MF * dynScale, humanize);
    const ev = {
      time: h.time,
      duration: stepDur * 0.95,
      midi: n,
      velocity: h.velocity,
      channel: 1,
      program: 33,
      voice: { kind: 'bass' },
      group: 'bass',
      source: 'auto',
    };
    events.push(ev);
    lastOn = ev;
    prevBass = n;
  }
  return prevBass;
}

function emitPiano(events, ctx) {
  const {
    grid, steps, stepDur, t0, swing, humanize, dynScale, chords,
  } = ctx;
  let prevVoicing = ctx.prevVoicing;
  let arpIdx = ctx.arpIdx;
  const toks = splitPattern(grid.piano || '');
  let held = null;

  for (let i = 0; i < steps; i++) {
    const tok = toks[i] || '.';
    if (tok === '.') {
      held = null;
      continue;
    }
    if (tok === '-') {
      if (held) {
        for (const ev of held) ev.duration += stepDur;
      }
      continue;
    }

    const stepT = stepTime(t0, i, stepDur, swing, steps);
    const chord = parseChord(chordAt(chords, stepT) || 'N.C.');
    if (chord.nc) {
      held = null;
      prevVoicing = null;
      continue;
    }

    const voicing = voiceChord(chord, prevVoicing);
    prevVoicing = voicing;
    if (!voicing.length) continue;

    const accent = tok === 'C';
    const soft = tok === 'c' || tok === 'a';
    const vel = (accent ? 0.55 : 0.38) * MF * dynScale;
    const tHit = stepT;

    if (tok === 'a') {
      const note = voicing[arpIdx % voicing.length];
      arpIdx += 1;
      const h = human(tHit, vel, humanize);
      const ev = pianoEv(h.time, note, stepDur * 1.6, h.velocity);
      events.push(ev);
      held = [ev];
    } else {
      held = [];
      for (const note of voicing) {
        const h = human(tHit, vel * (soft ? 0.9 : 1), humanize);
        const ev = pianoEv(h.time, note, stepDur * 0.95, h.velocity);
        events.push(ev);
        held.push(ev);
      }
    }
  }
  return { voicing: prevVoicing, arpIdx };
}

function pianoEv(time, midi, duration, velocity) {
  return {
    time, duration, midi, velocity,
    channel: 0, program: 4, // electric piano / Rhodes
    voice: { kind: 'piano', sample: 'rhodes' },
    group: 'piano',
    source: 'auto',
  };
}

/**
 * Parse komp: control directives from midi header meta text events.
 * @param {import('@tonejs/midi').Midi} midi
 */
export function parseKompDirectives(midi) {
  const out = { style: null, ending: null, sectionStyles: new Map(), hits: [] };
  const meta = midi.header.meta || [];
  for (const item of meta) {
    if (item.type !== 'text') continue;
    const text = String(item.text || '').trim();
    if (!text.startsWith('komp:')) continue;
    const body = text.slice(5);
    const parts = Object.fromEntries(
      body.split(';').map((p) => {
        const [k, ...rest] = p.split('=');
        return [k.trim(), rest.join('=').trim()];
      }),
    );
    if (parts.stil && !parts.del) out.style = parts.stil;
    if (parts.slut) out.ending = parts.slut;
    if (parts.del) {
      out.sectionStyles.set(parts.del, {
        style: parts.stil,
        dynamics: parts.dyn,
        drumsOff: parts.trummor === 'av',
        fillOff: parts.fill === 'av',
        bassWalk: parts.bas === 'walk',
      });
    }
    if (parts.hit) out.hits.push(parts.hit);
  }
  return out;
}

/**
 * Load all style JSON files from a base URL (browser) or map (tests).
 * @param {string} baseUrl
 */
export async function loadStyles(baseUrl) {
  const catRes = await fetch(new URL('styles/catalog.json', baseUrl));
  const catalog = await catRes.json();
  const map = new Map();
  const ids = [...(catalog.styles || []), ...(catalog.hidden || [])];
  await Promise.all(
    ids.map(async (id) => {
      const r = await fetch(new URL(`styles/${id}.json`, baseUrl));
      if (r.ok) map.set(id, await r.json());
    }),
  );
  return { catalog, styles: map };
}

/** Resolve legacy style ids via catalog.aliases. */
export function resolveStyleId(catalog, id) {
  if (!id) return catalog?.defaultByMeter?.['4/4'] || 'pop-rock';
  const aliases = catalog?.aliases || {};
  return aliases[id] || id;
}

export function defaultStyleForMeter(catalog, numerator, denominator) {
  const key = `${numerator}/${denominator}`;
  return catalog.defaultByMeter?.[key] || 'pop-rock';
}
