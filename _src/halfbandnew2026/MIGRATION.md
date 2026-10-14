# Halv Fjorton → peperipaperika (labs)

The Halv Fjorton static site is developed **in this repository**. Source lives under `_src/halfbandnew2026/` (leading underscore so Jekyll/GitHub Pages does not publish it as a site root). Built HTML is published at **`/testing/halfbandnew2026/`**.

## Layout in `peperipaperika`

```text
peperipaperika/
├── CNAME                    # unchanged (production / other sites)
├── index.html               # unchanged (repo root site)
├── ns-midihelper/           # unchanged
├── _src/
│   └── halfbandnew2026/     # ← edit here (this tree)
│       ├── scripts/build.py
│       ├── assets/
│       ├── alt/
│       └── …
└── testing/
    └── halfbandnew2026/     # ← build output only (do not edit by hand)
```

There is **no** repo-root `.nojekyll` in `peperipaperika` today; `_src/` is excluded from Jekyll by the underscore prefix. The build writes `.nojekyll` into `testing/halfbandnew2026/` when needed.

## Build into the labs subpath

From `_src/halfbandnew2026/`:

```bash
python3 scripts/build.py \
  --output-dir ../../testing/halfbandnew2026 \
  --subpath /testing/halfbandnew2026
```

This refreshes `testing/halfbandnew2026/` and rewrites root-relative URLs (`/assets/…`, `/kontakt/`, etc.) to `/testing/halfbandnew2026/…`.

## Edit workflow

1. Change copy or structure in **`scripts/build.py`** (most pages) and/or **`alt/index.html`** (alternative homepage).
2. Edit **`assets/`** (CSS, JS, images, fonts, `assets/schema/organization.json`).
3. Run the build command above.
4. Commit source under `_src/halfbandnew2026/` and output under `testing/halfbandnew2026/`.

Do not commit secrets or `.env` files.

## Archives (historical)

| Archive | Purpose |
| --- | --- |
| `halfbandnew2026-source.zip` | One-time source migration payload. |
| `halfbandnew2026.zip` | Pre-built `testing/halfbandnew2026/` for one-shot deploys (no longer the normal workflow). |
