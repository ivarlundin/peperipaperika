# UX-granskning — Notlänken

Senast uppdaterad: 2025-11-04

## Metod (design-review, humbleteam)

Granskning enligt [humbleteam/design-review](https://github.com/humbleteam/design-review) (MIT): rubric 0–4, max 6 prioriterade fynd med Before/After/Why. Endast **användbarhet, konventioner, tillgänglighet och buggar** — ingen visuell rebrand (ägaren vill behålla early-2000s-skin).

**Underlag:** live https://labs.ivarlundin.se/notlanken/ (desktop + ~390px mobil), kodgenomgång, `npm test`.

## Notlänken spelare — score **3/4**

Strukturen är tydlig (LCD, transport, autokomp, lane, tidslinje). Kvarvarande problem var mest feedback/states och uppspelningsrace; adresserat i PR #51–#53.

### Humbleteam-fynd (status)

| # | Fynd | Status |
|---|------|--------|
| 1 | Transport visar inte tydligt att det spelar | [ok] PR #51 — `aria-pressed`, `is-playing`, LCD `data-state` |
| 2 | Första tonen uteblev vid async soundfonts | [ok] PR #51 + #52 — `prepareInstrumentsForEvents`, load guard |
| 3 | Mixer svår att upptäcka | [ok] PR #51 `title` + PR #53 engångstips (localStorage), `aria-label` |
| 4 | Autokomp-variant A/B oklar | [ok] PR #51 statusrad + PR #53 `aria-label` på chip |
| 5 | Tidslinje utan tangentbord vid fokus | [ok] PR #51 |
| 6 | Aktiv låt syns inte i listan vid tillbaka | [ok] PR #51 + PR #53 `listHighlightFile` i listvy |

---

## Tidigare rundor (första audit, P1–P3)

### P1 — implementerat (PR #49 m.fl.)

| # | Problem | Status |
|---|---------|--------|
| 1 | Sök/filter låtlista | [ok] |
| 2 | Autokomp-etiketter | [ok] |
| 3 | Transport-genvägar hint | [ok] |
| 4 | Lane-skubb hint | [ok] |
| 5 | Titel Notlänken ™ | [ok] |
| 6 | Sektionsrubriker i spelvy | [ok] |
| 7 | Sticky transport mobil | [ok] |
| 8 | Tidslinje `aria-valuenow` / `aria-valuetext` | [ok] |

### P2 — implementerat eller medvetet enkelt

| # | Problem | Status |
|---|---------|--------|
| 9 | Mixer dold | [ok] Tips vid första låtöppning; `title` + `aria-label` (ingen badge — undviker visuellt brus) |
| 10 | Variant A/B | [ok] Statusrad + chip `aria-label` |
| 11 | Anteckningar lätt att missa | [ok] Rubrik + localStorage-hint |
| 12 | Många hastighetsknappar | [ok] Grupper **Långsam / Normal / Snabb**, alla värden kvar |
| 13 | Ackordrad kontext | [ok] `aria-live` på LCD |

### P3 — nice to have

| # | Problem | Status |
|---|---------|--------|
| 14 | ”Spelar nu” i listan | [ok] `aria-current` via hash + senast öppnad låt efter ← Låtar |
| 15 | Dela deep link | [ok] Knapp **Kopiera länk** i spelvy (hash-URL) |
| 16 | Första ljudstart kräver klick | ⏭️ Behålls (browser policy, korrekt) |

### Övrigt (PR #52, parallell agent)

- Persistent sidhuvud `#site-home` / varumärke
- `song-load-guard.js`, avbruten laddning vid låtbyte
- Playwright e2e `tests/e2e/playback.spec.js`

### Medvetet utelämnat

- **Ny visuell identitet** — skin oförändrat enligt ägare
- **Kopiera-länk i listvy** — endast när en låt är öppen (meningsfull URL)
- **Mixer-badge / animation** — skulle bryta mot ”ingen slop-UI”-krav

## Låtlista

Publikt: **Last Christmas (D) v0.3** och **Willo Intro 2026 v1**. Övriga MIDI i `midi/archive/`.

## Verifiering

```bash
cd notlanken && npm test
```

Manuellt: Last Christmas + Willo Intro, mobil ~390px, mellanslag spela/paus, mixer, autokomp på Willo, lane-ackord, tillbaka till listan (markering), kopiera länk.
