export function formatClock(seconds) {
  const s = Math.max(0, Math.floor(seconds));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${String(r).padStart(2, '0')}`;
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
