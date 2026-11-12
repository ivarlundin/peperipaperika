# Ivar Lundin — portfolio (dev skeleton)

Hidden static site under **`testing/portfolio/`** on GitHub Pages (`labs.ivarlundin.se`). Not linked from the labs root; every page uses `noindex, nofollow`.

## Pages

| File | Purpose |
|------|---------|
| `index.html` | Home — **name keyboard** headline + intro copy |
| `design.html` | Design work — Fiona-style placeholder list |
| `music.html` | Music — same list pattern, static placeholders |
| `css/styles.css` | Shared monochrome layout (Inter variable) |
| `js/site.js` | Scroll reveals, sticky nav, cursor/scroll → Inter weight on headings |
| `js/home.js` | Playable “IVAR LUNDIN” letters, optional Web Audio |
| `favicon.svg` | Monochrome mark |

Contact is **`mailto:hello@ivarlundin.se`** from the nav (no separate contact page).

All asset paths are **relative** for subpath hosting now and domain-root hosting later.

## Front-page interaction

**Your name is a keyboard** — the large headline **IVAR LUNDIN** is the instrument. Each letter is a button: **hover** (mouse), **tap** (touch), or **focus + Enter/Space** hits a note mapped to an **A major pentatonic** scale (two octaves). Inter **wght** jumps to 900 and eases back to thin (~520ms; shortened when `prefers-reduced-motion`). **Sound off** by default; the small toggle enables triangle-wave Web Audio. Mashing letters plays a riff even without sound.

## Local preview

```bash
cd testing/portfolio
python3 -m http.server 8765
```

Open **http://localhost:8765/** (trailing slash keeps relative URLs correct).

## Visibility

- `noindex, nofollow` on every HTML page
- Not in any sitemap
- Root `robots.txt` unchanged (no `Disallow` line, to avoid advertising the path)

## Move to own repo + domain

1. Copy this folder to a new repo root.
2. Enable GitHub Pages (static, no build).
3. Point DNS to GitHub; set custom domain in repo settings.
4. Remove the labs copy when the new site is live, if desired.

## Labs URL (after merge)

**https://labs.ivarlundin.se/testing/portfolio/**
