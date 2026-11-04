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

Unused tom OGG files in this folder are legacy; autokomp/playback only load the files listed in `DRUM_MAP` in `audio-engine.js`.

## GM fallback (`gm-fallback/*.js`)

- **Source:** gleitz/midi-js-soundfonts `FluidR3_GM` instrument bundles (violin, flute, clarinet, acoustic_guitar_nylon, string_ensemble_1, choir_aahs, synth_strings_1)
- **License:** Same as FluidR3 GM above

## Regenerating

```bash
./notlanken/scripts/fetch-samples.sh
```

Requires `curl`, `ffmpeg`. Total size should stay well under ~50 MB for GitHub Pages.


## Rhodes / electric piano (`rhodes/`)

- **Source:** FluidR3 GM `electric_piano_1` per-note MP3 via [gleitz/midi-js-soundfonts](https://github.com/gleitz/midi-js-soundfonts), converted to mono OGG
- **License:** FluidR3 / Lawrence Berkley National Laboratory soundfont license (free use in software)
- **Credit:** FluidR3 GM; used as default piano/keys and autokomp piano sound
