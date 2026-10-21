/** Detect which of drums/bass/piano already exist as written tracks. */

const PIANO_PROGRAMS = new Set([0, 1, 2, 3, 4, 5, 6, 7]);
const BASS_PROGRAMS = new Set([32, 33, 34, 35, 36, 37, 38, 39]);

/**
 * @param {import('@tonejs/midi').Midi} midi
 * @returns {{ drums: boolean, bass: boolean, piano: boolean }}
 */
export function detectWrittenTracks(midi) {
  const out = { drums: false, bass: false, piano: false };
  for (const track of midi.tracks) {
    if (!track.notes?.length) continue;
    const channel = track.channel ?? 0;
    const program = track.instrument?.number ?? 0;
    const name = String(track.name || '').toLowerCase();

    if (channel === 9 || /trum|drum|perc/.test(name)) {
      out.drums = true;
      continue;
    }
    if (BASS_PROGRAMS.has(program) || /\bbas(s)?\b|bass/.test(name)) {
      out.bass = true;
      continue;
    }
    if (PIANO_PROGRAMS.has(program) || /piano|keys|rhodes|klav/.test(name)) {
      out.piano = true;
    }
  }
  return out;
}

/**
 * @param {{ drums: boolean, bass: boolean, piano: boolean }} written
 * @returns {('drums'|'bass'|'piano')[]}
 */
export function missingTracks(written) {
  /** @type {('drums'|'bass'|'piano')[]} */
  const need = [];
  if (!written.drums) need.push('drums');
  if (!written.bass) need.push('bass');
  if (!written.piano) need.push('piano');
  return need;
}
