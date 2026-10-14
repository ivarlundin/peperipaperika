# Halv Fjorton (site source)

Edit the site **here** in `peperipaperika`. The public labs preview is the **build output** at `testing/halfbandnew2026/` (do not edit that folder by hand).

## Build

From this directory:

```bash
python3 scripts/build.py \
  --output-dir ../../testing/halfbandnew2026 \
  --subpath /testing/halfbandnew2026
```

## Workflow

1. Change copy in `scripts/build.py`, layout/CSS/JS/images under `assets/`, or `alt/index.html`.
2. Run the build command above.
3. Commit **both** this source tree (`_src/halfbandnew2026/`) and `testing/halfbandnew2026/`.

## Local preview

From the **repo root**:

```bash
python3 -m http.server 8080
```

Open `http://localhost:8080/testing/halfbandnew2026/`.

See `MIGRATION.md` for layout notes. Production DNS and apex hosting are documented separately; this repo only hosts the labs subpath.
