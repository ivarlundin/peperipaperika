# Juteström Bygg (site source)

Static MVP for **Juteström Bygg** (Sams byggfirma). Labs preview is the build output at `testing/jutestromsbygg/` (do not edit that folder by hand).

## Build

From this directory:

```bash
python3 scripts/build.py \
  --output-dir ../../testing/jutestromsbygg \
  --subpath /testing/jutestromsbygg
```

## Workflow

1. Change copy in `scripts/build.py`, styles in `assets/css/site.css`, or images under `assets/img/`.
2. Run the build command above.
3. Commit **both** `_src/jutestromsbygg/` and `testing/jutestromsbygg/`.

## Local preview

From the **repo root**:

```bash
python3 -m http.server 8080
```

Open `http://localhost:8080/testing/jutestromsbygg/`.

## QA

```bash
python3 qa_check.py
```

## CMS mode

See `docs/CMS-MODE.md`. Use the discreet **Edit** button (bottom-right) on labs to enable inline editing, export JSON, and apply changes with `scripts/apply_cms_export.py`.

### Image manifest

Gallery and the CMS image picker read `assets/cms/image-manifest.json`, generated on each build from files in `assets/img/`. Add or replace images under `assets/img/` (for example `assets/img/gallery/`), run `build.py`, and commit source plus `testing/` output.

## Live (labs)

https://labs.ivarlundin.se/testing/jutestromsbygg/
