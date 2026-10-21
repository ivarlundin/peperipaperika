/** Chord symbol parser for autokomp (plank2midi-compatible subset). */

const NOTE_TO_PC = {
  C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11,
};

/**
 * @typedef {Object} ParsedChord
 * @property {string} symbol
 * @property {number|null} root  pitch class 0–11, or null for N.C.
 * @property {number|null} bass  slash bass pitch class
 * @property {number[]} tones   chord tones as pitch classes relative to C=0 absolute
 * @property {boolean} nc
 */

/**
 * @param {string} symbol
 * @returns {ParsedChord}
 */
export function parseChord(symbol) {
  const raw = String(symbol || '').trim();
  if (!raw || /^n\.?c\.?$/i.test(raw) || raw === '%' || raw === '-') {
    return { symbol: raw || 'N.C.', root: null, bass: null, tones: [], nc: true };
  }

  let s = raw;
  let bass = null;
  const slash = s.match(/^(.*)\/([A-Ga-g][#b♯♭]?)$/);
  if (slash) {
    s = slash[1].trim();
    bass = noteToPc(slash[2]);
  }

  const m = s.match(/^([A-Ga-g])([#b♯♭]?)(.*)$/);
  if (!m) {
    return { symbol: raw, root: null, bass: null, tones: [], nc: true };
  }
  const root = (NOTE_TO_PC[m[1].toUpperCase()] + accidental(m[2])) % 12;
  const quality = m[3].replace(/\s+/g, '');
  const intervals = qualityToIntervals(quality);
  const tones = intervals.map((i) => (root + i) % 12);
  return {
    symbol: raw,
    root,
    bass: bass == null ? root : bass,
    tones,
    nc: false,
  };
}

function accidental(a) {
  if (!a) return 0;
  if (a === '#' || a === '♯') return 1;
  if (a === 'b' || a === '♭') return 11;
  return 0;
}

function noteToPc(name) {
  const m = name.match(/^([A-Ga-g])([#b♯♭]?)$/);
  if (!m) return 0;
  return (NOTE_TO_PC[m[1].toUpperCase()] + accidental(m[2])) % 12;
}

function qualityToIntervals(q) {
  let s = q;
  // defaults: major triad
  let third = 4;
  let fifth = 7;
  let seventh = null;
  const extras = new Set();

  if (/^(maj|ma|Δ|M)7/.test(s) || s.startsWith('maj7') || s === 'M7' || s === 'Δ7') {
    third = 4; fifth = 7; seventh = 11;
    s = s.replace(/^(maj|ma|Δ|M)7/, '');
  } else if (/^m\(maj7\)|^mMaj7|^min\(maj7\)/i.test(s)) {
    third = 3; fifth = 7; seventh = 11;
    s = s.replace(/^m\(maj7\)|^mMaj7|^min\(maj7\)/i, '');
  } else if (/^(m7b5|m7\(b5\)|ø|ø7|min7b5)/i.test(s)) {
    third = 3; fifth = 6; seventh = 10;
    s = s.replace(/^(m7b5|m7\(b5\)|ø7|ø|min7b5)/i, '');
  } else if (/^(dim7|o7)/i.test(s)) {
    third = 3; fifth = 6; seventh = 9;
    s = s.replace(/^(dim7|o7)/i, '');
  } else if (/^(dim|o)(?!7)/i.test(s)) {
    third = 3; fifth = 6;
    s = s.replace(/^(dim|o)/i, '');
  } else if (/^(aug|\+)/i.test(s)) {
    third = 4; fifth = 8;
    s = s.replace(/^(aug|\+)/i, '');
  } else if (/^(m7|min7|-7)/i.test(s)) {
    third = 3; fifth = 7; seventh = 10;
    s = s.replace(/^(m7|min7|-7)/i, '');
  } else if (/^(m|min|-)(?![aA])/.test(s)) {
    third = 3; fifth = 7;
    s = s.replace(/^(min|m|-)/, '');
  } else if (/^7sus4?/i.test(s)) {
    third = 5; fifth = 7; seventh = 10;
    s = s.replace(/^7sus4?/i, '');
  } else if (/^sus2/i.test(s)) {
    third = 2; fifth = 7;
    s = s.replace(/^sus2/i, '');
  } else if (/^sus4?|^sus/i.test(s)) {
    third = 5; fifth = 7;
    s = s.replace(/^sus4?|^sus/i, '');
  } else if (/^69/.test(s)) {
    third = 4; fifth = 7; seventh = 9;
    extras.add(2);
    s = s.replace(/^69/, '');
  } else if (/^6/.test(s)) {
    third = 4; fifth = 7; seventh = 9;
    s = s.replace(/^6/, '');
  } else if (/^7/.test(s)) {
    third = 4; fifth = 7; seventh = 10;
    s = s.replace(/^7/, '');
  } else if (/^9/.test(s)) {
    third = 4; fifth = 7; seventh = 10;
    extras.add(2);
    s = s.replace(/^9/, '');
  } else if (/^11/.test(s)) {
    third = 4; fifth = 7; seventh = 10;
    extras.add(2); extras.add(5);
    s = s.replace(/^11/, '');
  } else if (/^13/.test(s)) {
    third = 4; fifth = 7; seventh = 10;
    extras.add(2); extras.add(9);
    s = s.replace(/^13/, '');
  } else if (/^add9/i.test(s)) {
    third = 4; fifth = 7;
    extras.add(2);
    s = s.replace(/^add9/i, '');
  } else if (/^alt/i.test(s)) {
    third = 4; fifth = 8; seventh = 10;
    extras.add(1); extras.add(3);
    s = s.replace(/^alt/i, '');
  } else if (s.startsWith('maj') || s.startsWith('ma') || s === 'M') {
    third = 4; fifth = 7;
    s = s.replace(/^(maj|ma|M)/, '');
  }

  // leftover tension tokens
  if (/b9|#9|♯9|♭9/.test(s)) {
    if (/#9|♯9/.test(s)) extras.add(3);
    if (/b9|♭9/.test(s)) extras.add(1);
  }
  if (/#11|♯11/.test(s)) extras.add(6);
  if (/b13|♭13/.test(s)) extras.add(8);
  if (/\b9\b|^9|[^0-9]9/.test(` ${s}`) && !extras.has(2)) extras.add(2);
  if (/11/.test(s)) extras.add(5);
  if (/13/.test(s)) extras.add(9);

  const out = [0, third, fifth];
  if (seventh != null) out.push(seventh);
  for (const e of extras) out.push(e);
  return [...new Set(out)].sort((a, b) => a - b);
}

/**
 * Pick a MIDI note for a pitch class near a preferred octave.
 * @param {number} pc
 * @param {number} preferMidi
 */
export function pcToMidiNear(pc, preferMidi) {
  let best = pc;
  let bestDiff = Infinity;
  for (let oct = 0; oct <= 8; oct++) {
    const n = pc + oct * 12;
    const d = Math.abs(n - preferMidi);
    if (d < bestDiff) {
      bestDiff = d;
      best = n;
    }
  }
  return best;
}

/**
 * Build a drop-2 voicing in D3–E5 (midi 50–76).
 * @param {ParsedChord} chord
 * @param {number[]|null} prevVoicing
 */
export function voiceChord(chord, prevVoicing = null) {
  if (chord.nc || chord.root == null) return [];
  const pcs = chord.tones.length ? chord.tones : [chord.root, (chord.root + 4) % 12, (chord.root + 7) % 12];
  // start from close voicing around C4
  let notes = pcs.map((pc) => pcToMidiNear(pc, 60)).sort((a, b) => a - b);
  // drop-2 for 4+ notes: second from top down an octave
  if (notes.length >= 4) {
    const top2 = notes[notes.length - 2];
    notes[notes.length - 2] = top2 - 12;
    notes.sort((a, b) => a - b);
  }
  // shift into range 50–76
  while (notes[0] < 50) notes = notes.map((n) => n + 12);
  while (notes[notes.length - 1] > 76) notes = notes.map((n) => n - 12);
  // voice-lead toward previous
  if (prevVoicing?.length) {
    const prevAvg = prevVoicing.reduce((a, b) => a + b, 0) / prevVoicing.length;
    const curAvg = notes.reduce((a, b) => a + b, 0) / notes.length;
    if (curAvg - prevAvg > 6) notes = notes.map((n) => n - 12);
    if (prevAvg - curAvg > 6) notes = notes.map((n) => n + 12);
    while (notes[0] < 50) notes = notes.map((n) => n + 12);
    while (notes[notes.length - 1] > 76) notes = notes.map((n) => n - 12);
  }
  return [...new Set(notes)].sort((a, b) => a - b);
}

/**
 * Bass MIDI from chord degree token.
 * @param {ParsedChord} chord
 * @param {ParsedChord|null} nextChord
 * @param {string} token
 * @param {number|null} prevBass
 */
export function bassNote(chord, nextChord, token, prevBass = null) {
  if (token === '.' || chord.nc) return null;
  if (token === '-') return prevBass;
  const root = chord.bass ?? chord.root;
  if (root == null) return null;
  const prefer = prevBass ?? 40; // E2-ish
  if (token === 'R') return pcToMidiNear(root, prefer);
  if (token === '5') return pcToMidiNear((root + 7) % 12, prefer);
  if (token === '8') {
    const rootMidi = pcToMidiNear(root, prefer);
    // Always the bar's root an octave up from the low root placement.
    const low = pcToMidiNear(root, 36);
    return low + 12;
  }
  if (token === '3') {
    const third = chord.tones.find((t) => ((t - (chord.root ?? root) + 12) % 12) === 3 || ((t - (chord.root ?? root) + 12) % 12) === 4);
    return pcToMidiNear(third ?? (root + 4) % 12, prefer);
  }
  if (token === '7') {
    const sev = chord.tones.find((t) => {
      const d = (t - (chord.root ?? root) + 12) % 12;
      return d === 10 || d === 11 || d === 9;
    });
    return pcToMidiNear(sev ?? (root + 10) % 12, prefer);
  }
  if (token === 'A') {
    const nextRoot = nextChord && !nextChord.nc ? (nextChord.bass ?? nextChord.root) : root;
    if (nextRoot == null) return pcToMidiNear(root, prefer);
    return pcToMidiNear((nextRoot + 11) % 12, prefer);
  }
  if (token === 'W') {
    // walking: prefer chord tone near previous, else approach
    if (prevBass != null) {
      const candidates = (chord.tones.length ? chord.tones : [root]).map((pc) => pcToMidiNear(pc, prevBass));
      candidates.sort((a, b) => Math.abs(a - prevBass) - Math.abs(b - prevBass));
      if (candidates[0] !== prevBass) return candidates[0];
      return bassNote(chord, nextChord, 'A', prevBass);
    }
    return pcToMidiNear(root, prefer);
  }
  return pcToMidiNear(root, prefer);
}
