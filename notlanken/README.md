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

**Tips för arrangörsboten:** lägg ackord/sektioner som MIDI **marker**-events (`Intro`, `Vers`, `Refr`, ackordnamn). De visas på tidslinjen och som “Aktuellt” under uppspelning.

## Ljud

Självhostade samples under `samples/` (piano, bas, trummor, blås + FluidR3-fallback). Se `samples/LICENSES.md` och `scripts/fetch-samples.sh`.

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
