# Ivar Lundin — portfolio (dev skeleton)

Hidden static playground under **`x/portfolio/`** on the peperipaperika GitHub Pages site (`labs.ivarlundin.se`). Not linked from the root site and marked `noindex, nofollow`.

## Structure

| Path | Purpose |
|------|---------|
| `index.html` | Landing: UX + music sections, placeholder cards |
| `css/styles.css` | Layout, theme, motion (respects `prefers-reduced-motion`) |
| `js/main.js` | Hue playground (arrow keys), light pointer parallax |
| `favicon.svg` | Simple mark, no raster assets |

All asset URLs are **relative** so the folder works at a subpath now and at a domain root later.

## Local preview

From this directory:

```bash
python3 -m http.server 8765
```

Open `http://localhost:8765/` (trailing slash matters for relative paths).

## Visibility / SEO

- Every page uses `<meta name="robots" content="noindex, nofollow">`.
- Not added to any sitemap.
- Root `robots.txt` was **not** updated with a `Disallow` for this path: a Disallow line advertises the URL to anyone who reads `robots.txt`. Meta `noindex` keeps the path out of search indexes without listing it publicly (same choice as avoiding a sitemap entry).

## Move to own repo + custom domain

1. Copy this entire folder to a new repository root (or keep the files at repo root).
2. Enable GitHub Pages on that repo (branch `main`, folder `/` or `/docs` if you prefer).
3. Point DNS (A/CNAME) to GitHub Pages; set the custom domain in repo settings.
4. No build step required. If you later add a bundler, keep deploy output as static HTML/CSS/JS with root-relative or relative paths consistent with hosting.
5. Remove or archive the copy under `peperipaperika/x/portfolio/` once the new site is live, if you no longer need the labs preview.

## Labs URL (after merge)

`https://labs.ivarlundin.se/x/portfolio/`
