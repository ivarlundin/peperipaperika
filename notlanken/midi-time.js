export function formatClock(seconds) {
  const s = Math.max(0, Math.floor(Number.isFinite(seconds) ? seconds : 0));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${String(r).padStart(2, '0')}`;
}

/**
 * One bar length in seconds at the start of the piece (first tempo + meter).
 * Markers-only files often have midi.duration === -Infinity; bar length is
 * still well-defined from the tempo/time-signature maps.
 * @param {import('@tonejs/midi').Midi} midi
 */
export function estimateBarSeconds(midi) {
  try {
    const bpm = midi.header.tempos?.[0]?.bpm || 120;
    const sig = midi.header.timeSignatures?.[0]?.timeSignature || [4, 4];
    const [num, den] = sig;
    const bar = (60 / bpm) * num * (4 / den);
    return Number.isFinite(bar) && bar > 0 ? bar : 2;
  } catch {
    return 2;
  }
}

/**
 * Transport length for a loaded song.
 *
 * @tonejs/midi sets `duration` to -Infinity (JSON-null) when there are no note
 * events — common for markers-only / autokomp charts. Fall back to the last
 * chord/section marker (+ one bar), last written note, and last tempo time.
 *
 * @param {import('@tonejs/midi').Midi} midi
 * @param {{ writtenEvents?: { time: number }[], chords?: { time: number }[], sections?: { time: number }[] }} [opts]
 */
export function songDurationSeconds(midi, opts = {}) {
  const writtenEvents = opts.writtenEvents || [];
  const chords = opts.chords || [];
  const sections = opts.sections || [];

  const finiteTimes = (...vals) =>
    vals.filter((t) => Number.isFinite(t) && t >= 0);

  const markerEnd = Math.max(
    0,
    ...finiteTimes(
      ...chords.map((c) => c.time),
      ...sections.map((s) => s.time),
    ),
  );

  const lastWritten = writtenEvents.length
    ? writtenEvents[writtenEvents.length - 1].time + 0.5
    : 0;

  const raw = midi?.duration;
  // -Infinity / Infinity / NaN / null / undefined → 0
  const finiteMidi = Number.isFinite(raw) && raw > 0 ? raw : 0;

  let lastTempoTime = 0;
  const tempos = midi?.header?.tempos || [];
  for (const t of tempos) {
    let sec = t.time;
    if (!Number.isFinite(sec) && typeof midi.header.ticksToSeconds === 'function') {
      sec = midi.header.ticksToSeconds(t.ticks);
    }
    if (Number.isFinite(sec)) lastTempoTime = Math.max(lastTempoTime, sec);
  }

  const oneBar = estimateBarSeconds(midi);
  const fromMarkers = markerEnd > 0 ? markerEnd + oneBar : 0;
  const fromTempo = lastTempoTime > 0 ? lastTempoTime + oneBar : 0;

  const dur = Math.max(finiteMidi, lastWritten, fromMarkers, fromTempo);
  return Number.isFinite(dur) ? dur : 0;
}

function timingAt(midi, seconds) {
  const tempos = midi.header.tempos?.length
    ? [...midi.header.tempos].sort((a, b) => a.ticks - b.ticks)
    : [{ ticks: 0, bpm: 120 }];
  const sigs = midi.header.timeSignatures?.length
    ? [...midi.header.timeSignatures].sort((a, b) => a.ticks - b.ticks)
    : [{ ticks: 0, timeSignature: [4, 4] }];

  let bpm = tempos[0].bpm;
  for (const t of tempos) {
    const tSec = typeof midi.ticksToSeconds === 'function'
      ? midi.ticksToSeconds(t.ticks)
      : (t.ticks / midi.header.ppq) * (60 / bpm);
    if (tSec <= seconds) bpm = t.bpm;
  }

  let numerator = 4;
  let denominator = 4;
  for (const s of sigs) {
    const tSec = typeof midi.ticksToSeconds === 'function'
      ? midi.ticksToSeconds(s.ticks)
      : 0;
    if (tSec <= seconds) {
      numerator = s.timeSignature[0];
      denominator = s.timeSignature[1];
    }
  }

  return { bpm, numerator, denominator };
}

/**
 * @param {import('@tonejs/midi').Midi} midi
 * @param {number} seconds
 */
export function secondsToBarBeat(midi, seconds) {
  const s = Math.max(0, seconds);
  const { bpm, numerator, denominator } = timingAt(midi, s);
  const beatDur = 60 / bpm;
  const barDur = beatDur * numerator;
  const bar = Math.floor(s / barDur) + 1;
  const beat = Math.floor((s % barDur) / beatDur) + 1;
  return { bar, beat, numerator, denominator };
}

export function formatBarBeat(midi, seconds) {
  const { bar, beat, numerator, denominator } = secondsToBarBeat(midi, seconds);
  return `takt ${bar} slag ${beat} (${numerator}/${denominator})`;
}

/**
 * @param {import('@tonejs/midi').Midi} midi
 * @param {number} seconds
 * @param {number} deltaBars
 */
export function jumpBars(midi, seconds, deltaBars) {
  const s = Math.max(0, seconds);
  const { bpm, numerator } = timingAt(midi, s);
  const barDur = (60 / bpm) * numerator;
  return Math.max(0, s + deltaBars * barDur);
}

/**
 * Start time (seconds) of every bar up to endSeconds, following the
 * time-signature map.
 * @param {import('@tonejs/midi').Midi} midi
 * @param {number} endSeconds
 */
export function barStarts(midi, endSeconds) {
  const ppq = midi.header.ppq;
  const sigs = midi.header.timeSignatures?.length
    ? [...midi.header.timeSignatures].sort((a, b) => a.ticks - b.ticks)
    : [{ ticks: 0, timeSignature: [4, 4] }];
  const out = [];
  let tick = 0;
  let si = 0;
  for (let guard = 0; guard < 5000; guard++) {
    const sec = midi.header.ticksToSeconds(tick);
    if (sec > endSeconds) break;
    out.push(sec);
    while (si + 1 < sigs.length && sigs[si + 1].ticks <= tick) si++;
    const [num, den] = sigs[si].timeSignature;
    tick += Math.round(ppq * (4 / den)) * num;
  }
  return out;
}
