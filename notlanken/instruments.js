import { gmInstrumentName } from './gm-programs.js';

/** @typedef {'piano'|'bass'|'trumpet'|'trombone'|'tenor_sax'|'brass_section'|'drums'|'gm'} InstrumentKind */

const PIANO_PROGRAMS = new Set([0, 1, 2, 3, 4, 5, 6, 7]);
const BASS_PROGRAMS = new Set([32, 33, 34, 35, 36, 37, 38, 39]);
const BRASS_PROGRAMS = new Set([56, 57, 58, 59, 60, 61, 62, 63]);
const REED_PROGRAMS = new Set([64, 65, 66, 67, 68, 69, 70, 71]);

/**
 * @param {number} channel 0–15
 * @param {number} program GM program 0–127
 * @returns {{ kind: InstrumentKind, gmName?: string, brassVoice?: string }}
 */
export function resolveVoice(channel, program) {
  if (channel === 9) return { kind: 'drums' };

  const p = program | 0;
  if (PIANO_PROGRAMS.has(p)) return { kind: 'piano' };

  if (BASS_PROGRAMS.has(p)) return { kind: 'bass' };

  if (p === 56) return { kind: 'trumpet', brassVoice: 'trumpet' };
  if (p === 57) return { kind: 'trombone', brassVoice: 'trombone' };
  if (p === 66) return { kind: 'tenor_sax', brassVoice: 'tenor_sax' };
  if (BRASS_PROGRAMS.has(p) || REED_PROGRAMS.has(p)) {
    return { kind: 'brass_section', brassVoice: 'brass_section' };
  }

  return { kind: 'gm', gmName: gmInstrumentName(p) };
}
