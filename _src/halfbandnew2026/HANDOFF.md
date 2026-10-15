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
- **Inget utanför grid-containern.** «Full bredd» = hela innehållscontainern (samma kanter som H1 och huvudmeny), aldrig viewport (`100vw`, negativa marginaler eller breakout) om det inte uttryckligen står i uppgiften.
- **Rubrik → ingress → knapp (global regel):** avståndet mellan beskrivning och CTA ska **alltid** vara tydligt större än mellan rubrik och beskrivning. Tokens i `.alt-page` i `alt.css`:
  - `--alt-title-desc-gap` — rubrik → ingress/brödtext (tight).
  - `--alt-desc-cta-gap` — ingress/sista brödtext → `.actions` / primär knapp (luftigare; minst ~3× title-gap i praktiken).
  - Sätt gap via `margin-bottom` på rubrik/`.lead`/`.alt-service-hero__dek`/`.alt-hero__lead` och `margin-top` på `.actions` (eller `margin-bottom` på copy före CTA). **Inga** lösa `1rem`/`1.25rem` här. Gäller heroes, tjänstekapitel, inner `page-hero`, kontakt/offert, landningssidor med `.actions`, m.m.
  - `--alt-heading-content-gap` är **inte** samma regel: använd den bara rubrik → FAQ/listor/rutnät (se nedan).
- **Rubrik → innehåll** (listor, rutnät, kortblock, FAQ): minst `--alt-heading-content-gap` i `alt.css`. Gäller t.ex. «Vanliga frågor» före accordion, tjänstekapitel före grid, inner `h2` före `.media-grid`, samt FAQ-sida efter `page-hero` (`section` med `.alt-faq`). Inget får vara tightare än tokenen; rubrik → brödtext/ingress använder fortfarande `--alt-title-desc-gap`.
- **Tjänstesidor** (Bröllop, Företag, Fest och mingel): desktop-H1 via `--alt-svc-hero-h1-size` (något mindre än `--alt-hero-h1-size`); beskrivning (`alt-service-hero__dek`) max 50 % bredd på desktop, `text-wrap: balance`.
- **Fluid rubriker (`clamp`):** delade tokens i `alt.css` — `--alt-hero-h1-size` (start), `--alt-svc-hero-h1-size` (tjänste-hero desktop), `--alt-page-h1-size` (inner `page-hero` / integritet), `--alt-h2-size` (sektioner + `alt-svc-chapter__title`), `--alt-h3-size`. Minskalinjer är satta så långa ord (t.ex. Integritetspolicy, Tilläggstjänster) inte overflow:ar vid 320px; `text-wrap: balance` site-wide på rubriker.
- **FAQ två kolumner:** `row-gap: 0` på `.alt-faq__list--cols` (endast `column-gap` på desktop). Dela inte FAQ med addon-grid-regler som sätter `gap` på båda axlar. Ihopfällt: dolda svar får inte öka radhöjd (`display: none` + `overflow: hidden` på stängda `details`).
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
- Header: `alt-nav.js` sätter `is-solid` vid scroll. Ihopfälld/solid: `--alt-header-solid-bg` (`rgba(10, 10, 11, 0.6)`) + blur (`--alt-header-solid-blur` desktop, `--alt-header-solid-blur-mobile` på mobil via `::before`, ingen saturate). Innehåll i solid header vertikalt centrerat i `--alt-header`. Öppen mobilmeny: helt solid `var(--alt-bg)`, ingen blur.

## Öppna / kända

- Framtida funktioner och designreferenser: **[FUTURE_STEPS.md](FUTURE_STEPS.md)** (internt, ingår inte i labs-bygget). Nästa större repertoar-idé: sökbar låtlista med genre-chips och tvåkolumnslista — se [Downbeat The A-List](https://downbeat.agency/thealist/) och skärmdumpen `docs/future/repertoire-songlist-reference.png` (byggs inte än).
- Dolda SEO-sidor (`/kompband/`, `/brollopsband-smaland/`, …) får inte länkas från synliga sidor (build assert).
- `home/index.html` patchas efter bygge (`patch_home_page`).
- Skills: `.cursor/skills/` (design), `skills/svensk-copy/`.

## Lyssna (videor)

- Rutnät: `.lyssna-video-tile` (YouTube `maxresdefault`, `hqdefault` via `error`/`naturalWidth`), ingen iframe förrän klick.
- Modal: `lyssna-video-modal.js` (autoplay embed, Esc/backdrop/stäng, fokus, scroll-lås). Desktop spelare ~80vh höjd; mobil nästan full höjd.

## Live

https://labs.ivarlundin.se/testing/halfbandnew2026/
