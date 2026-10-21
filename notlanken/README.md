# Notlåda

Privat MIDI-spelare för GitHub Pages (`/notlanken/`). Sidan indexeras inte (meta `noindex` + `robots.txt`).

**URL efter publicering:** `https://labs.ivarlundin.se/notlanken/`

## Lägga till en låt

1. Lägg filen i `notlanken/midi/`, t.ex. `min-lat.mid`
2. Lägg till en rad i `notlanken/midi/songs.json`:

```json
{
  "file": "min-lat.mid",
  "title": "Min låt (C) v0.1"
}
```

3. Committa båda filerna. Ingen build-steg krävs.

**Tips för arrangörsboten:** lägg ackord/sektioner som MIDI **marker**-events (`Intro`, `Vers`, `Refr`, ackordnamn). De visas på tidslinjen och som “Aktuellt” under uppspelning. Autokomp läser **bara** dessa markörer — den räknar aldrig ut ackord själv.

## Autokomp

Spelaren kan generera **trummor, bas och piano** från ackord- och delmarkörer.

- Genererar **bara saknade** spår (kanal 10 = trummor, GM 32–39 = bas, GM 0–7 = piano; spårnamn som fallback).
- Skrivna stämmor (blås, melodi, …) spelas oförändrade. Inga andra instrument genereras.
- Genererade kanaler märks **(auto)** i mixern, med stor MUTE-knapp.
- **Komp**-reglaget, stilmeny och variant Auto A/B / A / B sitter ovanför transporten. Stilbyte under uppspelning regenererar från nästa takt utan hängande noter.
- Standardpiano = **Rhodes** (`samples/rhodes/`). Stilar ligger i `styles/*.json` (portade från Nesticos `grooves.yaml`).
- Valfri styrinfo: textevent `komp:stil=twelve8` m.m. (se planen).
- Enhetstest (utan ljud): `node notlanken/tests/autokomp.test.mjs`

## Ljud

Självhostade samples under `samples/` (Rhodes, akustiskt piano, bas, trummor, blås + FluidR3-fallback). Se `samples/LICENSES.md` och `scripts/fetch-samples.sh`.

## Tangenter (desktop)

| Tangent | Funktion |
|---------|----------|
| `Mellanslag` | Spela / paus |
| `←` / `→` | Hoppa en takt bakåt / framåt |
| `B` | Ny anteckning typ **BUG/FEL** |
| `Ö` eller `W` | Ny anteckning typ **ÖNSKEMÅL** (svenskt/US-tangentbord) |
| `N` | Ny **anteckning** |

Medan anteckningsrutan är öppen är andra tangenter avstängda så du kan skriva fritt. Uppspelning fortsätter.

Anteckningar skapas på ett ställe: knapparna **+ Fel**, **+ Önskemål** och **+ Anteckning** i anteckningspanelen (samma som tangenterna, och det enda sättet på mobil). Positionen sätts när du trycker och uppspelningen fortsätter.

## Anteckningar

- Sparas i `localStorage` per MIDI-fil
- **Kopiera till urklipp** — text för arrangörsboten
- **Rensa** — tar bort alla anteckningar för aktuell låt (med bekräftelse)

## Mixer & reverb

Öppna **Mixer** för master, global **reverb** (våt nivå), volym per grupp (piano, bas, trummor, blås, övrigt), mute/solo och reverb-send per kanal.

## Lokal test

```bash
cd notlanken
python3 -m http.server 8765
```

Öppna `http://localhost:8765/`
