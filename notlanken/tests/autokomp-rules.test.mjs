import { readFileSync, readdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { generate } from '../autokomp.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const catalog = JSON.parse(readFileSync(join(root, 'styles/catalog.json'), 'utf8'));
const styles = new Map();
for (const f of readdirSync(join(root, 'styles'))) {
  if (!f.endsWith('.json') || f === 'catalog.json') continue;
  const j = JSON.parse(readFileSync(join(root, 'styles', f), 'utf8'));
  styles.set(j.id, j);
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

function drumTimeline(styleId, variant = 'A', bars = 2) {
  const bar = 2;
  const barStarts = Array.from({ length: bars }, (_, i) => i * bar);
  return {
    barStarts,
    chords: [{ time: 0, symbol: 'D' }],
    sections: [{ time: 0, label: 'Intro' }],
    duration: bars * bar,
    styleId,
    variant,
  };
}

function drumEvents(styleId, variant) {
  const tl = drumTimeline(styleId, variant);
  return generate(
    tl,
    {
      styleId,
      variant,
      humanize: false,
      generate: ['drums'],
      styles,
      dynamics: 'mf',
      resolveStyleId: (x) => x,
    },
  ).filter((e) => e.group === 'drums');
}

// Rule 1: Jazz + Bossa use GM ride (51) and jazz accents use bell (53)
{
  for (const variant of ['A', 'B']) {
    const jazz = drumEvents('jazz', variant);
    const mids = new Set(jazz.map((e) => e.midi));
    assert(mids.has(51), `jazz ${variant} must include ride (GM 51)`);
    assert(mids.has(53), `jazz ${variant} must include ride bell (GM 53) from ride X accents`);
  }
  for (const variant of ['A', 'B']) {
    const bossa = drumEvents('bossa', variant);
    const mids = new Set(bossa.map((e) => e.midi));
    assert(mids.has(51), `bossa ${variant} must include ride (GM 51)`);
  }
}

// Rule 2: Autokomp never generates brass/horns — only drums, bass, piano
{
  const tl = {
    barStarts: [0, 2, 4, 6],
    chords: [{ time: 0, symbol: 'D' }, { time: 4, symbol: 'A' }],
    sections: [{ time: 0, label: 'Vers' }, { time: 4, label: 'Refr.' }],
    duration: 8,
  };
  for (const id of catalog.styles) {
    const ev = generate(tl, {
      styleId: id,
      variant: 'auto',
      humanize: false,
      generate: ['drums', 'bass', 'piano', 'brass', 'trumpet'],
      styles,
      resolveStyleId: (x) => x,
    });
    assert(ev.every((e) => ['drums', 'bass', 'piano'].includes(e.group)), `${id}: illegal autokomp group`);
    assert(
      ev.every((e) => !['trumpet', 'tenor_sax', 'trombone', 'brass_section', 'gm'].includes(e.voice?.kind)),
      `${id}: autokomp must not emit horn voices`,
    );
  }
}

console.log('autokomp-rules tests OK');
