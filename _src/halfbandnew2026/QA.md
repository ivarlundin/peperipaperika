# QA (bindande för alla agenter)

Alla ändringar i `_src/halfbandnew2026/` som ska pushas till `main` **måste** passera `qa_check.py` lokalt **före push**. Vid **milestones** eller när Ivar ber om stor granskning: full matris + live efter deploy. Vid **små, fokuserade** ändringar: snabb läge + bekräfta att pushen landade (ingen full live-matris).

## Kommandon

Från `_src/halfbandnew2026/`:

```bash
# Milestone / stor review (bygger testing/halfbandnew2026/)
python3 qa_check.py

# Små ändringar — endast ändrade sidor, mål <30 s
python3 qa_check.py --quick --pages /brollop/ /foretag/
python3 qa_check.py --quick --skip-build --pages brollop mingel

# Efter push (milestones): när GitHub Pages har deployat labs
python3 qa_check.py --live --skip-build
```

`--skip-build` på live-körningen använder redan byggd `testing/` som referens för fingerprint.

### Snabb vs full

| Situation | Före push | Efter push |
|-----------|-----------|------------|
| Små ändringar (t.ex. en tjänstesida, CSS, copy) | `--quick --pages …` | Bekräfta att `main` på origin har din commit (t.ex. `git fetch origin main && git rev-parse HEAD origin/main`). **Kör inte** `--live` om Ivar inte bad om stor review. |
| Milestone / Ivar ber om full QA | `python3 qa_check.py` (ev. `--no-screenshots` lokalt) | `python3 qa_check.py --live --skip-build` |

## Vad som körs

### 1. Snabb läge (`--quick --pages`)

- Endast angivna sidor (`/brollop/`, `foretag`, …).
- **Chromium**, bredder **390** och **1280**.
- Samma tillstånd och **samma fail-regler** som full matris:
  - top / scrollad (~35 %), meny stängd;
  - på mobil (390): top / scrollad, meny öppen (om hamburger finns).
- Bygger `testing/` som vanligt om inte `--skip-build`.
- Inga fullpage-screenshots (snabbare).
- Rapportera **uppmätt körtid** i slutraden.

### 2. Matris (alla sidor)

Varje **byggd HTML-sida** (inkl. redirects och inner pages), i **Chromium och WebKit**, bredder **360, 390, 768, 1280, 1440**, tillstånd:

| Scroll | Meny |
|--------|------|
| Toppläge | Stängd |
| Scrollad (~35 % av sidan) | Stängd |
| Toppläge | Öppen (≤900 px bredd) |
| Scrollad | Öppen (≤900 px bredd) |

På mobilbredder injiceras minsta safe-area för sticky-header-regressioner.

### 2. Automatiska stop-regler

Körningen **failar** vid:

- Horisontell scroll (document/main)
- **H1 / primär CTA under sticky header** i toppläge, meny stängd
- Text som klipps utanför viewport (höger/vänster)
- **Sträckta bilder** (naturligt aspect vs renderat; strängare om inte `object-fit: cover`)
- **Samma gallery-bild två gånger** på en sida (`halvfjorton-*` i `main`)
- Tankstreck (– / —) eller **kickers** (`.eyebrow`)
- **Ingress-rutor** (bakgrund + padding/border på `.aeo-answer` / intro `.lead`)
- Trasiga interna länkar/bilder (HEAD/GET ≥400 mot labs-sökväg)
- **Konsolfel** (`console.error`)
- **Förbjudna fraser** från `skills/svensk-copy/SKILL.md` (lista i `scripts/qa_lib.py`)
- Saknad **header** eller **footer** på sidan

Bygget kör dessutom asserts i `scripts/build.py` (dash, eyebrows, offert bullets, dubblett-bilder på service-sidor, m.m.).

### 3. Efter push (live)

**Milestones / full review:**

1. Pusha **små, fokuserade** commits (endast uppgiften).
2. Kör `python3 qa_check.py --live --skip-build` (väntar upp till ~4 min på att live HTML matchar lokal fingerprint på stickprov).
3. Använd cache-bust (`?qa=…`) på varje sidladdning i QA.

**Små ändringar:** steg 2 utelämnas. Bekräfta bara att pushen landade på `origin/main`.

Labs: `https://labs.ivarlundin.se/testing/halfbandnew2026/`

### 4. Skärmdumpar (internt)

Fullpage-screenshots (WebKit 390 px, alla sidor) sparas under `/opt/cursor/artifacts/qa-screenshots/`. **Granska dem visuellt** (premium? trasigt? stämmer med uppgiften?). **Skicka inte** till Ivar.

Steg-logg: `qa-screenshots/qa-steps.json`.

### 5. Regression

Vid **quick**: regression på **ändrade sidor** (meny/banner/footer på just dessa URL:er). Vid **full matris**: alla sidor. Ändra aldrig mer än uppgiften kräver.

### 6. Rapport till Ivar

Alltid ange:

- **Commit-hash**
- Vilka QA-steg som kördes (**local** / **live**)
- **Kända brister** ärligt om något medvetet lämnats

## Filer

| Fil | Roll |
|-----|------|
| `qa_check.py` | Huvudskript (kör detta) |
| `scripts/qa_lib.py` | Delade regler och JS-prober |
| `scripts/qa_check.py` | Shim → `../qa_check.py` |
| `scripts/verify_*.py` | Äldre fokuserade tester (valfritt; matrisen i `qa_check.py` är normen) |
| `HANDOFF.md` | Struktur, byggflöde, designregler, öppna punkter |

## Workflow

1. Ändra källa under `_src/halfbandnew2026/`.
2. QA före push: `--quick --pages …` (små ändringar) **eller** full `python3 qa_check.py` (milestone).
3. Committa `_src/` + `testing/halfbandnew2026/` om labs ska uppdateras.
4. Push `main`.
5. Efter push: full `python3 qa_check.py --live --skip-build` **eller** (små ändringar) verifiera remote-hash.
6. Rapportera hash + QA-steg (inkl. quick-körtid om relevant).
