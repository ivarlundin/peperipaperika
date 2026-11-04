#!/usr/bin/env bash
# Download and compress self-hosted samples for Notlänken ™.
# Licenses: see ../samples/LICENSES.md
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SAMPLES="$ROOT/samples"
mkdir -p "$SAMPLES/piano" "$SAMPLES/bass" "$SAMPLES/trumpet" "$SAMPLES/trombone" "$SAMPLES/tenor_sax" "$SAMPLES/brass_section" "$SAMPLES/drums" "$SAMPLES/rhodes"

TONE="https://tonejs.github.io/audio"
GLEITZ="https://gleitz.github.io/midi-js-soundfonts/FluidR3_GM"

if ! command -v ffmpeg >/dev/null; then
  echo "ffmpeg required for OGG conversion" >&2
  exit 1
fi

to_light_ogg() {
  local in="$1" out="$2" trim="$3"
  local fade_start
  fade_start="$(awk "BEGIN { print ($trim - 0.35) }")"
  ffmpeg -y -hide_banner -loglevel error -i "$in" -ac 1 -ar 24000 -t "$trim" \
    -af "afade=t=out:st=${fade_start}:d=0.35" \
    -c:a libopus -b:a 56k -vbr on "$out"
}

fetch_piano() {
  local notes=(A2 C3 Ds3 Fs3 A3 C4 Ds4 C5)
  for n in "${notes[@]}"; do
    local tmp
    tmp="$(mktemp)"
    curl -fsSL "$TONE/salamander/${n}.ogg" -o "$tmp"
    to_light_ogg "$tmp" "$SAMPLES/piano/${n}.ogg" 2.8
    rm -f "$tmp"
  done
}

fetch_melodic_sparse() {
  local inst="$1" dest="$2"
  local notes=(C3 G3 C4 G4 C5)
  for n in "${notes[@]}"; do
    local tmp
    tmp="$(mktemp)"
    if curl -fsSL "$GLEITZ/${inst}-mp3/${n}.mp3" -o "$tmp"; then
      to_light_ogg "$tmp" "$dest/${n}.ogg" 2.8
    fi
    rm -f "$tmp"
  done
}

fetch_rhodes() {
  local notes=(C3 E3 G3 C4 E4 G4)
  for n in "${notes[@]}"; do
    local tmp
    tmp="$(mktemp)"
    if curl -fsSL "$GLEITZ/electric_piano_1-mp3/${n}.mp3" -o "$tmp"; then
      to_light_ogg "$tmp" "$SAMPLES/rhodes/${n}.ogg" 2.8
    fi
    rm -f "$tmp"
  done
}

fetch_drums() {
  local kit="$TONE/drum-samples/acoustic-kit"
  curl -fsSL "$kit/kick.mp3" -o /tmp/kick.mp3 && to_light_ogg /tmp/kick.mp3 "$SAMPLES/drums/36-kick.ogg" 1.1
  curl -fsSL "$kit/snare.mp3" -o /tmp/snare.mp3 && to_light_ogg /tmp/snare.mp3 "$SAMPLES/drums/38-snare.ogg" 1.4
  curl -fsSL "$kit/hihat.mp3" -o /tmp/chh.mp3 && to_light_ogg /tmp/chh.mp3 "$SAMPLES/drums/42-closed-hat.ogg" 0.55
  curl -fsSL "$TONE/drum-samples/hihat-short.mp3" -o /tmp/ohh.mp3 && to_light_ogg /tmp/ohh.mp3 "$SAMPLES/drums/46-open-hat.ogg" 1.6
  curl -fsSL "$kit/tom1.mp3" -o /tmp/t1.mp3 && to_light_ogg /tmp/t1.mp3 "$SAMPLES/drums/45-low-tom.ogg" 1.8
  curl -fsSL "$kit/tom2.mp3" -o /tmp/t2.mp3 && to_light_ogg /tmp/t2.mp3 "$SAMPLES/drums/47-mid-tom.ogg" 1.8
  curl -fsSL "$kit/tom3.mp3" -o /tmp/t3.mp3 && to_light_ogg /tmp/t3.mp3 "$SAMPLES/drums/50-high-tom.ogg" 1.8
  curl -fsSL "$kit/tom2.mp3" -o /tmp/floor.mp3 && to_light_ogg /tmp/floor.mp3 "$SAMPLES/drums/41-floor-tom.ogg" 1.8
  curl -fsSL "$kit/tom1.mp3" -o /tmp/ht.mp3 && to_light_ogg /tmp/ht.mp3 "$SAMPLES/drums/43-high-floor-tom.ogg" 1.8

  local sal="https://archive.org/download/SalamanderDrumkit"
  curl -fsSL "$sal/OH/ride1_OH_FF_1.wav" -o /tmp/ride.wav && to_light_ogg /tmp/ride.wav "$SAMPLES/drums/51-ride.ogg" 2.6
  curl -fsSL "$sal/OH/ride1Bell_OH_F_1.wav" -o /tmp/bell.wav && to_light_ogg /tmp/bell.wav "$SAMPLES/drums/53-ride-bell.ogg" 2.2
  curl -fsSL "$sal/OH/crash1_OH_FF_1.wav" -o /tmp/crash.wav && to_light_ogg /tmp/crash.wav "$SAMPLES/drums/49-crash.ogg" 2.6
}

echo "Fetching piano…"
fetch_piano
echo "Fetching bass / brass…"
fetch_melodic_sparse electric_bass_finger "$SAMPLES/bass"
fetch_melodic_sparse trumpet "$SAMPLES/trumpet"
fetch_melodic_sparse trombone "$SAMPLES/trombone"
fetch_melodic_sparse tenor_sax "$SAMPLES/tenor_sax"
fetch_melodic_sparse brass_section "$SAMPLES/brass_section"
echo "Fetching rhodes…"
fetch_rhodes
echo "Fetching drums…"
fetch_drums
echo "Done. Total size:"
du -sh "$SAMPLES"
