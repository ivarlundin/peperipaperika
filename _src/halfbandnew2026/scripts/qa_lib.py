"""Shared QA helpers for Halv Fjorton (used by qa_check.py)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

WIDTHS = (360, 390, 768, 1280, 1440)
MOBILE_MENU_MAX_WIDTH = 900
DASH_CHARS = ("\u2013", "\u2014")

# Hard-fail subset of skills/svensk-copy/SKILL.md (visible main). Expand as legacy copy is cleaned.
FORBIDDEN_PHRASES: tuple[str, ...] = (
    "boka nu",
    "missa inte",
    "säkra ert datum",
    "magisk stämning",
    "i världsklass",
    "minnen för livet",
    "oförglömlig",
    "unforgettable",
    "seamless",
    "next level",
)

GALLERY_STEM_RE = re.compile(
    r"/assets/img/gallery/(halvfjorton-\d+)-\d+w\.webp",
    re.IGNORECASE,
)

SAFE_AREA_INIT = """
(() => {
  if (document.getElementById('qa-safe-area')) return;
  const style = document.createElement('style');
  style.id = 'qa-safe-area';
  style.textContent = `
    @supports (padding: env(safe-area-inset-top)) {
      .alt-page {
        --alt-header-total: calc(var(--alt-header) + max(env(safe-area-inset-top), 47px));
      }
    }
  `;
  document.documentElement.appendChild(style);
})();
"""


def site_root_paths(site_root: Path) -> list[str]:
    paths = ["/"]
    for html_path in sorted(site_root.rglob("*.html")):
        rel = html_path.relative_to(site_root).as_posix()
        if rel == "index.html":
            continue
        if rel.endswith("/index.html"):
            paths.append("/" + rel[: -len("index.html")])
        elif rel.endswith(".html"):
            paths.append("/" + rel)
    return sorted(set(paths))


def page_fingerprint(html: str) -> str:
    """Stable-ish marker for live vs local comparison."""
    m = re.search(r"<title>([^<]+)</title>", html, re.I)
    title = m.group(1) if m else ""
    m2 = re.search(r'class="alt-service-hero"', html)
    hero = "1" if m2 else "0"
    m3 = re.search(r"<!-- build-css: ([a-f0-9]+) -->", html)
    css = m3.group(1) if m3 else ""
    return f"{title}|{hero}|{css}"


CHECKS_JS = """
(states) => {
  const vw = document.documentElement.clientWidth;
  const header = document.querySelector('.alt-header');
  const headerBottom = header ? header.getBoundingClientRect().bottom : 0;
  const docSW = document.documentElement.scrollWidth;
  const docCW = document.documentElement.clientWidth;
  const errors = [];

  if (docSW > docCW + 1) {
    errors.push(`horizontal-scroll doc ${docSW}>${docCW}`);
  }

  const main = document.querySelector('main');
  if (main) {
    const ms = getComputedStyle(main);
    const mr = main.getBoundingClientRect();
    if (main.scrollWidth > main.clientWidth + 1) {
      errors.push(`horizontal-scroll main ${main.scrollWidth}>${main.clientWidth}`);
    }
  }

  if (states.atTop && !states.menuOpen && header) {
    const probes = [
      '.alt-service-hero h1',
      '.alt-service-hero__actions a',
      '.alt-hero h1',
      '.alt-hero a.alt-btn--primary, .alt-hero .alt-btn--primary',
    ];
    for (const sel of probes) {
      document.querySelectorAll(sel).forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.height < 2) return;
        const st = getComputedStyle(el);
        if (st.visibility === 'hidden' || st.display === 'none') return;
        if (r.top < headerBottom - 1.5) {
          errors.push(`under-header ${sel} top=${r.top.toFixed(1)}`);
        }
      });
    }
  }

  if (states.atTop && !states.menuOpen) {
    const textSel = 'main h1, main h2, main h3, main p, main .lead, main .aeo-answer';
    document.querySelectorAll(textSel).forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.height < 4 || r.width < 4) return;
      const st = getComputedStyle(el);
      if (st.visibility === 'hidden') return;
      if (r.top > window.innerHeight) return;
      if (r.right > vw + 3) {
        errors.push(`text-clipped-right ${el.tagName}`.slice(0, 40));
      }
      if (r.left < -3) {
        errors.push(`text-clipped-left ${el.tagName}`.slice(0, 40));
      }
    });
  }

  document.querySelectorAll('main img').forEach((img) => {
    const r = img.getBoundingClientRect();
    if (r.width < 48 || r.height < 48) return;
    const nw = img.naturalWidth;
    const nh = img.naturalHeight;
    if (!nw || !nh) return;
    const natural = nw / nh;
    const rendered = r.width / r.height;
    const drift = Math.abs(natural - rendered) / natural;
    const fit = getComputedStyle(img).objectFit;
    if (fit === 'cover' || fit === 'contain') return;
    if (drift > 0.28) {
      errors.push(`stretched-img ${img.alt || img.src}`.slice(0, 60));
    }
  });

  if (document.querySelector('.alt-service-hero')) {
    const stems = [];
    document.querySelectorAll('main img[src*="gallery/halvfjorton"]').forEach((img) => {
      const m = (img.getAttribute('src') || '').match(/halvfjorton-\\d+/i);
      if (m) stems.push(m[0].toLowerCase());
    });
    const seen = new Set();
    const dup = new Set();
    stems.forEach((s) => {
      if (seen.has(s)) dup.add(s);
      seen.add(s);
    });
    if (dup.size) {
      errors.push(`duplicate-gallery ${[...dup].join(',')}`);
    }
  }

  const bodyText = document.body.innerText || '';
  if (bodyText.includes('\\u2013') || bodyText.includes('\\u2014') || bodyText.includes('–') || bodyText.includes('—')) {
    errors.push('typographic-dash');
  }
  if (document.querySelector('.eyebrow')) {
    errors.push('eyebrow-kicker');
  }

  document.querySelectorAll('.aeo-answer, .alt-service-intro .lead, .alt-service-hero__dek').forEach((el) => {
    const s = getComputedStyle(el);
    const border = Math.max(
      parseFloat(s.borderLeftWidth) || 0,
      parseFloat(s.borderTopWidth) || 0,
      parseFloat(s.borderWidth) || 0
    );
    const pad = parseFloat(s.paddingTop) || 0;
    const bg = s.backgroundColor;
    const hasBg = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
    if (border > 0) errors.push('ingress-border');
    if (hasBg && pad > 8) errors.push('ingress-box');
  });

  if (document.body.classList.contains('alt-page')) {
    if (!document.querySelector('.alt-header')) errors.push('missing-header');
    if (!document.querySelector('.site-footer')) errors.push('missing-footer');
  }

  return { errors, docSW, docCW, vw };
}
"""


def find_forbidden_phrases(text: str) -> list[str]:
    lower = text.lower()
    return [p for p in FORBIDDEN_PHRASES if p in lower]
