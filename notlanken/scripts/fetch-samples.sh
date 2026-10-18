#!/usr/bin/env bash
# Download and compress self-hosted samples for Notlåda.
# Licenses: see ../samples/LICENSES.md
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SAMPLES="$ROOT/samples"
mkdir -p "$SAMPLES/piano" "$SAMPLES/bass" "$SAMPLES/trumpet" "$SAMPLES/trombone" "$SAMPLES/tenor_sax" "$SAMPLES/brass_section" "$SAMPLES/drums" "$SAMPLES/gm-fallback"

TONE="https://tonejs.github.io/audio"
GLEITZ="https://gleitz.github.io/midi-js-soundfonts/FluidR3_GM"

if ! command -v ffmpeg >/dev/null; then
  echo "ffmpeg required for OGG conversion" >&2
  exit 1
fi

to_ogg() {
  local in="$1" out="$2"
  ffmpeg -y -hide_banner -loglevel error -i "$in" -ac 1 -ar 22050 -c:a libvorbis -q:a 4 "$out"
}

fetch_piano() {
  # Salamander (CC-BY) — minor-third zones
  local notes=(A1 C2 Ds2 Fs2 A2 C3 Ds3 Fs3 A3 C4 Ds4 Fs4 A4 C5 Ds5 Fs5 A5 C6)
  for n in "${notes[@]}"; do
    local tmp
    tmp="$(mktemp)"
    curl -fsSL "$TONE/salamander/${n}.ogg" -o "$tmp"
    cp "$tmp" "$SAMPLES/piano/${n}.ogg"
    rm -f "$tmp"
  done
}

fetch_melodic_sparse() {
  local inst="$1" dest="$2"
  local notes=(C2 E2 G2 C3 E3 G3 C4 E4 G4 C5)
  for n in "${notes[@]}"; do
    local tmp
    tmp="$(mktemp)"
    if curl -fsSL "$GLEITZ/${inst}-mp3/${n}.mp3" -o "$tmp"; then
      to_ogg "$tmp" "$dest/${n}.ogg"
    fi
    rm -f "$tmp"
  done
}

fetch_drums() {
  # Acoustic kit (see LICENSES.md) + short hat; cymbals from Kenney CC0 impacts
  local kit="$TONE/drum-samples/acoustic-kit"
  curl -fsSL "$kit/kick.mp3" -o /tmp/kick.mp3 && to_ogg /tmp/kick.mp3 "$SAMPLES/drums/36-kick.ogg"
  curl -fsSL "$kit/snare.mp3" -o /tmp/snare.mp3 && to_ogg /tmp/snare.mp3 "$SAMPLES/drums/38-snare.ogg"
  curl -fsSL "$kit/hihat.mp3" -o /tmp/chh.mp3 && to_ogg /tmp/chh.mp3 "$SAMPLES/drums/42-closed-hat.ogg"
  curl -fsSL "$TONE/drum-samples/hihat-short.mp3" -o /tmp/ohh.mp3 && to_ogg /tmp/ohh.mp3 "$SAMPLES/drums/46-open-hat.ogg"
  curl -fsSL "$kit/tom1.mp3" -o /tmp/t1.mp3 && to_ogg /tmp/t1.mp3 "$SAMPLES/drums/45-low-tom.ogg"
  curl -fsSL "$kit/tom2.mp3" -o /tmp/t2.mp3 && to_ogg /tmp/t2.mp3 "$SAMPLES/drums/47-mid-tom.ogg"
  curl -fsSL "$kit/tom3.mp3" -o /tmp/t3.mp3 && to_ogg /tmp/t3.mp3 "$SAMPLES/drums/50-high-tom.ogg"
  curl -fsSL "$GLEITZ/reverse_cymbal-mp3/C5.mp3" -o /tmp/crash.mp3 && to_ogg /tmp/crash.mp3 "$SAMPLES/drums/49-crash.ogg"
  curl -fsSL "$GLEITZ/steel_drums-mp3/C5.mp3" -o /tmp/ride.mp3 && to_ogg /tmp/ride.mp3 "$SAMPLES/drums/51-ride.ogg"
  curl -fsSL "$kit/tom2.mp3" -o /tmp/floor.mp3 && to_ogg /tmp/floor.mp3 "$SAMPLES/drums/41-floor-tom.ogg"
  curl -fsSL "$kit/tom1.mp3" -o /tmp/ht.mp3 && to_ogg /tmp/ht.mp3 "$SAMPLES/drums/43-high-floor-tom.ogg"
}

fetch_gm_js() {
  # Self-hosted gleitz FluidR3 .js bundles for GM fallback (lazy-loaded by player)
  local names=(violin flute clarinet acoustic_guitar_nylon string_ensemble_1 choir_aahs synth_strings_1)
  mkdir -p "$SAMPLES/gm-fallback"
  for n in "${names[@]}"; do
    curl -fsSL "$GLEITZ/${n}-mp3.js" -o "$SAMPLES/gm-fallback/${n}-mp3.js"
  done
}

echo "Fetching piano…"
fetch_piano
echo "Fetching bass / brass…"
fetch_melodic_sparse electric_bass_finger "$SAMPLES/bass"
fetch_melodic_sparse trumpet "$SAMPLES/trumpet"
fetch_melodic_sparse trombone "$SAMPLES/trombone"
fetch_melodic_sparse tenor_sax "$SAMPLES/tenor_sax"
fetch_melodic_sparse brass_section "$SAMPLES/brass_section"
echo "Fetching drums…"
fetch_drums
echo "Fetching GM fallback bundles…"
fetch_gm_js
echo "Done. Total size:"
du -sh "$SAMPLES"
