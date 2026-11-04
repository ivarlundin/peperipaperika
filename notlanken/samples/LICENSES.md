# Sample licenses (Notlänken ™)

All files in this folder are redistributable in this public repository. Keep this file when adding samples.

## Piano (`piano/`)

- **Source:** [Salamander Grand Piano](https://archive.org/details/SalamanderGrandPianoV3) via [Tone.js Audio](https://github.com/Tonejs/audio/tree/master/salamander)
- **License:** Creative Commons Attribution 3.0 (CC-BY 3.0)
- **Credit:** M. Nagel / Salamander Grand Piano; hosted mirrors by Tone.js

## Bass, trumpet, trombone, tenor sax, brass section (`bass/`, `trumpet/`, etc.)

- **Source:** [FluidR3 GM](https://github.com/gleitz/midi-js-soundfonts) per-note MP3 exports (sparse zones), converted to mono OGG
- **License:** FluidR3 / Lawrence Berkley National Laboratory soundfont license (free use in software)
- **Credit:** FluidR3 GM; gleitz/midi-js-soundfonts distribution

## Drums (`drums/`)

| File | Source |
|------|--------|
| `36-kick`, `38-snare`, `42-closed-hat`, `45-low-tom`, `47-mid-tom`, `50-high-tom`, `41-floor-tom`, `43-high-floor-tom`, `46-open-hat` | [Tone.js Audio – acoustic-kit](https://github.com/Tonejs/audio/tree/master/drum-samples/acoustic-kit) (cwilso/web-audio-samples lineage) |
| `49-crash`, `51-ride`, `53-ride-bell` | [Salamander Drumkit](https://archive.org/details/SalamanderDrumkit) by Alexander Holm — `OH/crash1_OH_FF_1.wav`, `OH/ride1_OH_FF_1.wav`, `OH/ride1Bell_OH_F_1.wav`, converted to mono OGG |

**Salamander Drumkit license:** CC-BY-SA 3.0 originally; author placed the library in the **public domain** (April 2022). Credit: Alexander Holm / Salamander Drumkit.

Do **not** use FluidR3 `reverse_cymbal` or other GM effect presets for play-along drums — they swell in backwards (GM program 120).

Sample URLs use `?v=` from `sample-asset-version.js` and service worker cache `notlanken-assets-v3` (install precache of all hosted OGG).

Unused tom OGG files in this folder are legacy; autokomp/playback only load the files listed in `DRUM_MAP` in `audio-engine.js`.

## Encoding (light play-along set)

Hosted melodic/drum samples are **mono Opus in OGG** (~56 kbps), trimmed to ~2–3 s with a short release fade. Zone counts are listed in `sample-manifest.js` (piano 8 zones, bass/brass 5, rhodes 6). Re-encode after fetching:

```bash
node notlanken/scripts/reencode-light-samples.mjs
```

Rare GM programs not mapped to a local folder fall back to **piano zones** at lower gain (no multi-megabyte soundfont bundles).

## Regenerating from upstream

```bash
./notlanken/scripts/fetch-samples.sh
```

Requires `curl`, `ffmpeg`. Then run `node scripts/reencode-light-samples.mjs` if needed. Total hosted audio stays near **~1 MB** for the full zone library.


## Rhodes / electric piano (`rhodes/`)

- **Source:** FluidR3 GM `electric_piano_1` per-note MP3 via [gleitz/midi-js-soundfonts](https://github.com/gleitz/midi-js-soundfonts), converted to mono OGG
- **License:** FluidR3 / Lawrence Berkley National Laboratory soundfont license (free use in software)
- **Credit:** FluidR3 GM; used as default piano/keys and autokomp piano sound
