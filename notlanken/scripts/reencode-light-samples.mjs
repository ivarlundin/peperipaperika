#!/usr/bin/env node
/**
 * Re-encode self-hosted samples: mono Opus in OGG, trimmed with release fade.
 * Run from notlanken/: node scripts/reencode-light-samples.mjs
 */
import { execFileSync } from 'node:child_process';
import { readdirSync, unlinkSync, existsSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { SAMPLE_MANIFEST, MELODIC_TRIM_SEC, MELODIC_FADE_SEC } from '../sample-manifest.js';

const ROOT = join(import.meta.dirname, '..');
const SAMPLES = join(ROOT, 'samples');

const DRUM_TRIM = {
  '36-kick.ogg': 1.1,
  '38-snare.ogg': 1.4,
  '42-closed-hat.ogg': 0.55,
  '46-open-hat.ogg': 1.6,
  '49-crash.ogg': 2.6,
  '51-ride.ogg': 2.6,
  '53-ride-bell.ogg': 2.2,
  '41-floor-tom.ogg': 1.8,
  '43-high-floor-tom.ogg': 1.8,
  '45-low-tom.ogg': 1.8,
  '47-mid-tom.ogg': 1.8,
  '50-high-tom.ogg': 1.8,
};

function encode(inPath, outPath, trimSec) {
  const fadeStart = Math.max(0.05, trimSec - MELODIC_FADE_SEC);
  const af = `afade=t=out:st=${fadeStart}:d=${MELODIC_FADE_SEC}`;
  execFileSync('ffmpeg', [
    '-y', '-hide_banner', '-loglevel', 'error',
    '-i', inPath,
    '-ac', '1', '-ar', '24000',
    '-t', String(trimSec),
    '-af', af,
    '-c:a', 'libopus', '-b:a', '56k', '-vbr', 'on',
    outPath,
  ], { stdio: 'inherit' });
}

function folderKey(folder) {
  return folder.replace('samples/', '');
}

function pruneFolder(folder, keepNotes) {
  const dir = join(SAMPLES, folderKey(folder));
  if (!existsSync(dir)) return;
  const keep = new Set(keepNotes.map((n) => `${n}.ogg`));
  for (const f of readdirSync(dir)) {
    if (f.endsWith('.ogg') && !keep.has(f)) {
      unlinkSync(join(dir, f));
      console.log('removed', join(dir, f));
    }
  }
}

let total = 0;
for (const [key, notes] of Object.entries(SAMPLE_MANIFEST)) {
  const dir = join(SAMPLES, key);
  if (!existsSync(dir)) continue;
  pruneFolder(`samples/${key}`, notes);
  for (const n of notes) {
    const file = join(dir, `${n}.ogg`);
    if (!existsSync(file)) {
      console.warn('missing (skipped)', file);
      continue;
    }
    const tmp = `${file}.tmp.ogg`;
    encode(file, tmp, MELODIC_TRIM_SEC);
    unlinkSync(file);
    execFileSync('mv', [tmp, file]);
    total += statSync(file).size;
  }
}

const drumDir = join(SAMPLES, 'drums');
if (existsSync(drumDir)) {
  for (const f of readdirSync(drumDir)) {
    if (!f.endsWith('.ogg')) continue;
    const trim = DRUM_TRIM[f] ?? 1.8;
    const file = join(drumDir, f);
    const tmp = `${file}.tmp.ogg`;
    encode(file, tmp, trim);
    unlinkSync(file);
    execFileSync('mv', [tmp, file]);
    total += statSync(file).size;
  }
}

console.log('Re-encoded payload (manifest zones + drums):', Math.round(total / 1024), 'KiB');
