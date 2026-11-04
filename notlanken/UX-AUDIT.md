# UX-granskning — Notlänken

Datum: 2025-11-04 (autonom granskning inför förbättringar utan visuell rebrand).

## Metod

Genomgång av låtlistan, spelaren, autokomp, transport, tidslinjer, mixer, hastighet och anteckningar utifrån flöde, tydlighet, touch/mobil och tillgänglighet. Jämförelse mot typiska behov: snabbt hitta låt, höra arrangemang, styra autokomp, skrubba i tid, lämna feedback till arrangör.

## Sammanfattning

Appen är funktionellt rik men packad vertikalt utan tydliga avsnittsgränser. Flera kraftfulla interaktioner (lane-skubb, översiktstidslinje, mixer) saknar förklaring. Autokomp benämns otydligt som bara ”Komp”. På mobil hamnar transport långt från tummen när man scrollar. Ljudladdning är redan tydlig via modal.

## Prioriterade fynd

### P1 — Måste fixas (implementerat i denna PR)

| # | Problem | Rekommendation | Status |
|---|---------|----------------|--------|
| 1 | Ingen sökning/filter när låtlistan växer | Sökfält ovanför listan, filtrerar titel/filnamn | ✅ |
| 2 | Autokomp oklart (“Komp”) | Rubrik ”Autokomp”, checkbox ”Aktivera autokomp”, befintlig statusrad kvar | ✅ |
| 3 | Transport/genvägar osynliga | Kort hint under transport (mellanslag, pilar) | ✅ |
| 4 | Lane-skubb inte uppenbar | Hint ”Dra vågrätt…” + behållen `aria-label` | ✅ |
| 5 | `<title>` sa ”Notlåda” | ”Notlänken ™” i HTML och dynamisk titel | ✅ |
| 6 | Spelvyn saknar struktur | Små sektionsetiketter (Transport, Nästa takter, Hela låten, Anteckningar…) | ✅ |
| 7 | Mobil: transport försvinner vid scroll | Sticky transport-block överst på smal skärm | ✅ |
| 8 | Tidslinje svår att förstå för skärmläsare | `aria-valuenow` / `aria-valuetext` uppdateras vid position | ✅ |

### P2 — Bör fixas (delvis / nästa steg)

| # | Problem | Rekommendation | Status |
|---|---------|----------------|--------|
| 9 | Mixer dold — användare vet inte att volym finns | Ev. badge eller första-besök-hint; nu oförändrat (låg risk att störa) | ⏳ |
| 10 | Variant A/B utan förklaring | Tooltip eller hjälptext i status (”Auto växlar mönster per sektion”) | ⏳ |
| 11 | Anteckningar längst ner lätt att missa | Sektionsrubrik + hint om localStorage | ✅ rubrik/hint |
| 12 | Hastighetsknappar många | Behåll alla (övningsbehov); ev. gruppera ”Långsam / Normal / Snabb” senare | ⏳ |
| 13 | Ackordrad utan kontext | `aria-live="polite"` när ackord byts | ✅ |

### P3 — Nice to have

| # | Problem | Rekommendation |
|---|---------|----------------|
| 14 | Ingen ”spelar nu”-indikator i listan | Markera aktiv låt via hash |
| 15 | Deep link delas sällan | Hash-URL fungerar redan; ev. kopiera-länk-knapp |
| 16 | Första ljudstart kräver klick (browser policy) | Behåll `ensureContext()` på låtval — korrekt |

## Flödeskartor (förenklad)

**Lista → spel**

1. Välj låt (sök valfritt) → hash → ladda MIDI + samples → spelvy.

**Spel → feedback**

1. Spela/paus → skrubba lane eller hela låten → ev. autokomp-stil → anteckning → kopiera till urklipp.

## Ljud (parallellt spår)

Separat från UX men påverkar upplevd kvalitet: akustiskt piano som standard, bättre sample-interpolation mellan zoner, synkron GM-fallback efter preload, mild lowpass per grupp, förbättrad envelope.

## Visuell rebrand

Genomförd i denna PR: tidig-2000-tals **skinned app**-känsla (WinBoost/avast/Pentaphonic-inspirerad) — borstad metall, grön modulpanel, LCD-display för titel/takt/tid, stora runda transportknappar. **Inte** Windows 95-grått.

## Låtlista

Publikt syns endast **Last Christmas (D) v0.3** och **Willo Intro 2026 v1**. Övriga MIDI-filer ligger kvar i `midi/archive/` (ej raderade).

## Verifiering

- `cd notlanken && npm test`
- Manuell test i webbläsare: flera låtar, alla fem autokomp-stilar (Pop/Rock, Blues, Jazz, Bossa, Funk), mobilbredd (~390px).
