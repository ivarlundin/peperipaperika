/**
 * Parse deduplicated section + chord timeline from @tonejs/midi header meta.
 * @param {import('@tonejs/midi').Midi} midi
 */
export function parseSongMeta(midi) {
  /** @type {Map<number, { time: number, section?: string, chord?: string }>} */
  const buckets = new Map();
  const meta = midi.header.meta || [];
  const toSeconds = (ticks) => {
    if (typeof midi.header.ticksToSeconds === 'function') {
      return midi.header.ticksToSeconds(ticks);
    }
    const bpm = midi.header.tempos?.[0]?.bpm ?? 120;
    return (ticks / midi.header.ppq) * (60 / bpm);
  };

  const key = (time) => Math.round(time * 1000);

  for (const item of meta) {
    const time = toSeconds(item.ticks);
    const k = key(time);
    if (!buckets.has(k)) buckets.set(k, { time });
    const b = buckets.get(k);
    const text = String(item.text || '').trim();
    if (!text) continue;

    if (item.type === 'text') {
      if (text.startsWith('section:')) {
        b.section = formatSectionLabel(text.slice(8));
      } else if (text.startsWith('chord:')) {
        b.chord = text.slice(6);
      }
      continue;
    }

    if (item.type === 'marker') {
      const section = parseBracketSection(text);
      if (section) {
        if (!b.section) b.section = section;
      } else if (looksLikeChord(text)) {
        if (!b.chord) b.chord = text;
      }
      continue;
    }

    if (item.type === 'lyrics' && looksLikeChord(text)) {
      if (!b.chord) b.chord = text;
    }
  }

  const sections = [];
  const chords = [];
  for (const b of [...buckets.values()].sort((a, c) => a.time - c.time)) {
    if (b.section) sections.push({ time: b.time, label: b.section });
    if (b.chord) chords.push({ time: b.time, symbol: b.chord });
  }
  return { sections, chords };
}

function formatSectionLabel(raw) {
  const t = raw.trim();
  if (!t) return t;
  return t.charAt(0).toUpperCase() + t.slice(1);
}

function parseBracketSection(text) {
  const m = text.match(/^\[(.+)\]$/);
  return m ? formatSectionLabel(m[1]) : null;
}

function looksLikeChord(text) {
  if (!text || text.length > 12) return false;
  if (text.startsWith('section:') || text.startsWith('chord:')) return false;
  return /^[A-Ga-g][#b]?/.test(text);
}

/**
 * @param {{ time: number, symbol: string }[]} chords
 * @param {number} t
 */
export function chordAtTime(chords, t) {
  let symbol = '';
  for (const c of chords) {
    if (c.time <= t + 0.02) symbol = c.symbol;
    else break;
  }
  return symbol;
}
