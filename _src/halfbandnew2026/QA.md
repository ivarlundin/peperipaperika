# QA – Halv Fjorton (labs build)

Automated checks for the static site built from this directory into `testing/halfbandnew2026/`.

## Run

From `_src/halfbandnew2026/`:

```bash
python3 scripts/qa_check.py
```

Rebuilds the labs output, starts a local static server, and runs WebKit checks. Use `--skip-build` if you already built. Use `--sticky-only` to run only the sticky-header probes.

## What `qa_check.py` enforces

### Sticky header vs. content (top scroll)

At `scrollY ≈ 0`, with the menu closed, **no primary hero content may sit under the fixed header**. Probed elements:

- Service pages (`/brollop/`, `/foretag/`, `/mingel/`): banner **H1** and **Kontakta oss** CTA
- Home: hero **H1** and primary CTA

On iPhone WebKit the run also injects a minimum safe-area inset so regressions like “only the button peeks out under the header” are caught before deploy.

Failure example: `content under sticky header at top: service-h1 top=12px < headerBottom=98px`.

### Bundled verifiers (full run)

| Script | Focus |
|--------|--------|
| `verify_service_hero_webkit.py` | Shared service banner, typewriter H1, layout, ingress |
| `verify_mobile_menu_webkit.py` | Mobile header: no blur at top, mild blur when scrolled, solid open menu |
| `verify_no_horizontal_scroll_webkit.py` | No horizontal overflow |

Other scripts under `scripts/verify_*.py` can be run ad hoc; add them to `qa_check.py` when they should gate every merge.

## Manual spot-check (optional)

- Labs URL: `https://labs.ivarlundin.se/testing/halfbandnew2026/`
- After deploy, hard-refresh or confirm CSS URL updates if cache-busting is enabled.

## Workflow

1. Edit source under `_src/halfbandnew2026/`.
2. `python3 scripts/qa_check.py`
3. Commit source **and** `testing/halfbandnew2026/` when the build output is meant to ship to labs.
