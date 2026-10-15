# Handoff: Halv Fjorton (`halfbandnew2026`)

## Repo layout

| Path | Role |
|------|------|
| `_src/halfbandnew2026/` | **Källa** (HTML-bygge, CSS, JS, bilder, skills) |
| `testing/halfbandnew2026/` | **Labs-bygge** (GitHub Pages under `labs.ivarlundin.se`) |
| `scripts/build.py` | Genererar sidor, sitemap, llms.txt; kopierar `home/index.html` |

**Bygg labs:**

```bash
cd _src/halfbandnew2026
python3 scripts/build.py --output-dir ../../testing/halfbandnew2026 --subpath /testing/halfbandnew2026
```

**Commit:** alltid källändringar **och** `testing/halfbandnew2026/` i samma push till `main`.

**Rör inte:** repots root (`CNAME`, annat), `ns-midihelper/`.

## Designregler (bindande)

- **Outfit** rubriker, **Inter** (lätt vikt) brödtext.
- Ingress = vanlig text (ingen bakgrund, border, vänsterkant).
- Samma vänster/högerkant som menyn (`--alt-pad-left/right`).
- **Rubrik → ingress → knapp:** använd alltid `--alt-title-desc-gap` (mindre) och `--alt-desc-cta-gap` (tydligt större) i `alt.css`. Gäller tjänste-hero, inner `page-hero`, kontakt/offert, kapitel med `.actions`, startsidans hero, m.m.
- **Rubrik → innehåll** (listor, rutnät, kortblock, FAQ): minst `--alt-heading-content-gap` i `alt.css`. Gäller t.ex. «Vanliga frågor» före accordion, tjänstekapitel före grid, inner `h2` före `.media-grid`, samt FAQ-sida efter `page-hero` (`section` med `.alt-faq`). Inget får vara tightare än tokenen; rubrik → brödtext/ingress använder fortfarande `--alt-title-desc-gap`.
- **Tjänstesidor** (Bröllop, Företag, Fest och mingel): desktop-H1 via `--alt-svc-hero-h1-size` (något mindre än `--alt-hero-h1-size`); beskrivning (`alt-service-hero__dek`) max 50 % bredd på desktop, `text-wrap: balance`.
- **En gallery-bild per sida** (`halvfjorton-*`), inte i hero + body.
- Bilder: `object-fit: cover` med genomtänkt `object-position`, fasta höjder på fullbreddsband; ingen horisontell scroll.
- Inga tankstreck (–/—), kickers, priser, telefon i copy.
- Copy: `skills/svensk-copy/SKILL.md` (ändra inte Ivar-godkänd bröllopstext utan ok).

## QA (obligatoriskt)

Se **`QA.md`**. Kör före varje push:

```bash
python3 qa_check.py
```

Efter deploy:

```bash
python3 qa_check.py --live --skip-build
```

## Bröllop

- Hero: endast `service_hero_banner()` (samma som Företag/Mingel). Ingen egen hero-markup.
- Innehåll: `alt-svc-chapter`-sektioner (wireframe: Festspelning, Tilläggstjänster, FAQ, Kontakt).

## Service-sidor (Bröllop, Företag, Mingel)

- Klass `alt-page--service-banner`, gemensam `alt-service-hero` i `build.py`.
- Hero: `padding-top: var(--alt-header-total)` (= header + safe-area), mobil `min-height: max(min(70svh, 560px), header + innehåll)`.
- Header: `alt-nav.js` sätter `is-solid` vid scroll; mobil utan blur/bakgrund i toppläge, vid scroll `blur(16px) saturate(140%)` via `::before`.

## Öppna / kända

- Framtida funktioner och designreferenser: **[FUTURE_STEPS.md](FUTURE_STEPS.md)** (internt, ingår inte i labs-bygget).
- Dolda SEO-sidor (`/kompband/`, `/brollopsband-smaland/`, …) får inte länkas från synliga sidor (build assert).
- `home/index.html` patchas efter bygge (`patch_home_page`).
- Skills: `.cursor/skills/` (design), `skills/svensk-copy/`.

## Live

https://labs.ivarlundin.se/testing/halfbandnew2026/
