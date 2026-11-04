# UX-granskning — Notlänken

Senast uppdaterad: 2025-11-04

## Metod (design-review, humbleteam)

Granskning enligt [humbleteam/design-review](https://github.com/humbleteam/design-review) (MIT): rubric 0–4, max 6 prioriterade fynd med Before/After/Why. Endast **användbarhet, konventioner, tillgänglighet och buggar** — ingen visuell rebrand (ägaren vill behålla early-2000s-skin).

**Underlag:** live https://labs.ivarlundin.se/notlanken/ (desktop + ~390px mobil), kodgenomgång, `npm test`.

## Notlänken spelare — score **3/4**

Strukturen är tydlig (LCD, transport, autokomp, lane, tidslinje). Kvarvarande problem är mest feedback/states och ett uppspelningsrace, inte layout eller varumärke.

### 1. Transport visar inte tydligt att det spelar

- **Before:** Spela- och pausknappar ser likadana ut oavsett om uppspelning pågår; bara paus blir enabled.
- **After:** `aria-pressed` på spela/paus, klass `is-playing` på transport (paus får fokusring, spela dämpas), LCD `data-state` för skärmläsare.
- **Why:** Nielsen heuristic #1 (Visibility of system status) — användaren ska se att ljudmotor och transport är i läget ”spelar”.

### 2. Första tonen uteblev när soundfonts laddades i bakgrunden (Willo m.fl.)

- **Before:** `preparePlayback` markerade klar efter piano/trummor; FluidR3 för trumpet/bas laddades asynkront → första `play` kunde tysta blås/bas.
- **After:** `prepareInstrumentsForEvents(events)` efter autokomp-merge laddar soundfonts/GM som låten faktiskt använder innan modal stängs; samma vid sen `startPlayback` om nödvändigt.
- **Why:** Nielsen heuristic #1 — systemet ska vara redo innan primär åtgärd (Spela) presenteras som klar.

### 3. Mixer svår att upptäcka

- **Before:** Endast textknappen ”Mixer” utan förklaring att volym/reverb finns där.
- **After:** `title="Volym och reverb per spår"` (ingen visuell ändring).
- **Why:** Nielsen heuristic #6 (Recognition rather than recall) — funktion ska framgå utan att användaren minns dokumentation.

### 4. Autokomp-variant A/B oklar

- **Before:** Knapparna Auto/A/B utan kontext när autokomp är aktiv.
- **After:** Statusrad utökas med ”Auto växlar variant A/B efter sektion” när stilmenyn är aktiv.
- **Why:** Nielsen heuristic #10 (Help and documentation) — kort, uppgiftsnära hjälp.

### 5. Tidslinje saknade tangentbordsstöd när fokuserad

- **Before:** `role="slider"` men pilar/Home/End gällde bara globalt, inte när fokus låg på tidslinjen.
- **After:** Pilar, Home och End på `#timeline` när den har fokus (samma hopp som globala genvägar).
- **Why:** WCAG 2.2 SC 2.1.1 (Keyboard) — fokuserbart kontroll ska kunna styras med tangentbord.

### 6. Aktiv låt syns inte i listan vid tillbaka-navigering

- **Before:** Hash-deep link fungerade men listan markerade inte vilken låt som öppnades.
- **After:** `aria-current="true"` på aktiv låtknapp (outline i befintlig accentfärg).
- **Why:** Nielsen heuristic #1 — synlig position i navigering.

**Fix this first:** Soundfont-race (#2) — påverkar tillit och upplevd kvalitet direkt; övriga är polish som minskar friktion.

---

## Tidigare rundor (sammanfattning)

- Titel **Notlänken ™**, sök i låtlista, autokomp-etiketter, sektionsrubriker, sticky transport mobil, lane-bredd/staplade ackord, LCD, early-2000s-skin (oförändrat i denna runda).
- Publikt: **Last Christmas (D) v0.3** och **Willo Intro 2026 v1**; övriga MIDI i `midi/archive/`.

## Verifiering

```bash
cd notlanken && npm test
```

Manuellt: Last Christmas + Willo Intro, mobil ~390px, mellanslag spela/paus, mixer, autokomp på Willo, lane-ackord läsbara.
