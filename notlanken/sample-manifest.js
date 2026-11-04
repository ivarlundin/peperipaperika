/** Zone note names (without .ogg) per sample folder — pitch-shift between zones. */
export const SAMPLE_MANIFEST = {
  piano: ['A2', 'C3', 'Ds3', 'Fs3', 'A3', 'C4', 'Ds4', 'C5'],
  rhodes: ['C3', 'E3', 'G3', 'C4', 'E4', 'G4'],
  bass: ['C2', 'G2', 'C3', 'G3', 'C4'],
  trumpet: ['C3', 'G3', 'C4', 'G4', 'C5'],
  trombone: ['C3', 'G3', 'C4', 'G4', 'C5'],
  tenor_sax: ['C3', 'G3', 'C4', 'G4', 'C5'],
  brass_section: ['C3', 'G3', 'C4', 'G4', 'C5'],
};

export const DRUM_SAMPLE_FILES = [
  '36-kick.ogg',
  '38-snare.ogg',
  '41-floor-tom.ogg',
  '42-closed-hat.ogg',
  '43-high-floor-tom.ogg',
  '45-low-tom.ogg',
  '46-open-hat.ogg',
  '47-mid-tom.ogg',
  '49-crash.ogg',
  '50-high-tom.ogg',
  '51-ride.ogg',
  '53-ride-bell.ogg',
];

/** @returns {string[]} paths relative to app root (no leading slash) */
export function allSampleRelPaths() {
  const paths = DRUM_SAMPLE_FILES.map((f) => `samples/drums/${f}`);
  for (const [key, notes] of Object.entries(SAMPLE_MANIFEST)) {
    for (const n of notes) paths.push(`samples/${key}/${n}.ogg`);
  }
  return paths;
}

/** Paths required for these playback events (drums + piano core + song folders). */
export function samplePathsForEvents(events, drumMapValues) {
  const paths = new Set();
  for (const f of new Set(drumMapValues)) {
    paths.add(`samples/drums/${f}`);
  }
  const folders = new Set(['samples/piano']);
  for (const ev of events) {
    const { voice } = ev;
    if (!voice) continue;
    if (voice.kind === 'piano') {
      folders.add(voice.sample === 'rhodes' ? 'samples/rhodes' : 'samples/piano');
    } else if (voice.kind === 'bass') {
      folders.add('samples/bass');
    } else if (
      voice.kind === 'trumpet'
      || voice.kind === 'trombone'
      || voice.kind === 'tenor_sax'
      || voice.kind === 'brass_section'
    ) {
      folders.add(`samples/${voice.kind}`);
    }
  }
  for (const folder of folders) {
    const key = folder.replace('samples/', '');
    const notes = SAMPLE_MANIFEST[key] || [];
    for (const n of notes) paths.add(`${folder}/${n}.ogg`);
  }
  return [...paths];
}

/** Max duration (seconds) when re-encoding; drums use per-file overrides in script. */
export const MELODIC_TRIM_SEC = 2.8;
export const MELODIC_FADE_SEC = 0.35;
