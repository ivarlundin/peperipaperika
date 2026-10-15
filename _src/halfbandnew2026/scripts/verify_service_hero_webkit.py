#!/usr/bin/env python3
"""WebKit: shared service hero banner on brollop, foretag, mingel (iPhone + desktop)."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
BASE = "http://127.0.0.1:8771/testing/halfbandnew2026"
MOBILE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 900}
DESKTOP_1024 = {"width": 1024, "height": 900}
MOBILE_MIN_HERO = min(844 * 0.7, 560) - 8
SAFE_AREA_INIT = """
(() => {
  const style = document.createElement('style');
  style.id = 'verify-safe-area';
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

PAGES = {
    "brollop": {
        "path": "/brollop/",
        "img_stem": "halvfjorton-03",
        "h1": "Bröllop",
    },
    "foretag": {
        "path": "/foretag/",
        "img_stem": "halvfjorton-01",
        "h1": "Liveband till företagsfest",
    },
    "mingel": {
        "path": "/fest-och-mingel/",
        "img_stem": "halvfjorton-04",
        "h1": "Liveband till fest och mingel",
    },
}


def assert_service_hero(page, slug: str, label: str) -> None:
    spec = PAGES[slug]
    data = page.evaluate(
        """([expectedStem, expectedH1]) => {
          const hero = document.querySelector('.alt-service-hero');
          const img = document.querySelector('.alt-service-hero__img');
          const oldHero = document.querySelector('.page-hero, .alt-wedding-hero');
          const text = document.body.innerText || '';
          return {
            bodyClass: document.body.className,
            heroCount: document.querySelectorAll('.alt-service-hero').length,
            hasOldHero: !!oldHero,
            heroH: hero ? hero.getBoundingClientRect().height : 0,
            seoH1: document.querySelector('.alt-service-hero h1 .visually-hidden')?.innerText || '',
            liveH1: document.querySelector('.alt-service-hero [data-typewriter-text]')?.innerText || '',
            hasTypewriterScript: !!Array.from(document.scripts).some((s) => (s.src || '').includes('alt-hero-typewriter.js')),
            imgSrc: img ? img.getAttribute('src') || '' : '',
            objectFit: img ? getComputedStyle(img).objectFit : '',
            docSW: document.documentElement.scrollWidth,
            docCW: document.documentElement.clientWidth,
            hasEyebrow: !!document.querySelector('.eyebrow'),
            hasDash: text.includes('–') || text.includes('—'),
            headerCount: document.querySelectorAll('.alt-header').length,
            footerCount: document.querySelectorAll('.site-footer').length,
            introInHero: hero ? hero.querySelectorAll('.alt-service-hero__dek').length : -1,
            typewriterInHero: hero ? hero.querySelectorAll('[data-alt-typewriter], .alt-hero__typewriter').length : -1,
            hasScrim: !!document.querySelector('.alt-service-hero__scrim'),
            factsCount: document.querySelectorAll('.alt-facts').length,
            ctaText: (() => {
              const el = document.querySelector('.alt-service-hero__actions a.alt-btn--primary');
              return el ? el.innerText : '';
            })(),
            ctaHref: (() => {
              const el = document.querySelector('.alt-service-hero__actions a.alt-btn--primary');
              return el ? (el.getAttribute('href') || '') : '';
            })(),
            introBlock: !!document.querySelector('.alt-service-hero__dek'),
            aeoInIntro: document.querySelector('.alt-service-hero__dek'),
            expectedStem,
            expectedH1,
          };
        }""",
        [spec["img_stem"], spec["h1"]],
    )
    intro_styles = page.evaluate(
        """() => {
          const el = document.querySelector('.alt-service-hero__dek');
          if (!el) return null;
          const s = getComputedStyle(el);
          return {
            paddingTop: s.paddingTop,
            borderLeftWidth: s.borderLeftWidth,
            backgroundColor: s.backgroundColor,
            boxShadow: s.boxShadow,
            fontFamily: s.fontFamily,
          };
        }"""
    )
    assert "alt-page--service-banner" in data["bodyClass"], f"{slug}/{label}: service-banner class"
    assert data["heroCount"] == 1, f"{slug}/{label}: expected one service hero"
    assert not data["hasOldHero"], f"{slug}/{label}: legacy page hero still present"
    min_h = MOBILE_MIN_HERO if label == "iphone" else 240
    assert data["heroH"] >= min_h, f"{slug}/{label}: hero too short ({data['heroH']} < {min_h})"
    assert data["seoH1"] == spec["h1"], f"{slug}/{label}: SEO h1 mismatch"
    assert data["hasTypewriterScript"], f"{slug}/{label}: typewriter script missing"
    assert spec["img_stem"] in data["imgSrc"], (
        f"{slug}/{label}: hero image should match offer card stem, got {data['imgSrc']}"
    )
    assert data["objectFit"] == "cover", f"{slug}/{label}: object-fit {data['objectFit']}"
    assert data["docSW"] <= data["docCW"] + 1, (
        f"{slug}/{label}: horizontal overflow {data['docSW']} > {data['docCW']}"
    )
    h1_fit = page.evaluate(
        """() => {
          const h1 = document.querySelector('.alt-service-hero h1');
          if (!h1) return null;
          const r = h1.getBoundingClientRect();
          const pad = parseFloat(getComputedStyle(document.documentElement).paddingLeft || 0);
          const cw = document.documentElement.clientWidth;
          return {
            h1Right: r.right,
            clientWidth: cw,
            typewriterNowrap: getComputedStyle(
              document.querySelector('.alt-service-hero h1 .alt-hero__typewriter-text') || h1
            ).whiteSpace,
          };
        }"""
    )
    if h1_fit:
        assert h1_fit["h1Right"] <= h1_fit["clientWidth"] + 1, (
            f"{slug}/{label}: h1 clips past viewport (right={h1_fit['h1Right']}, cw={h1_fit['clientWidth']})"
        )
        assert h1_fit["typewriterNowrap"] in ("normal", "pre-wrap"), (
            f"{slug}/{label}: typewriter text must wrap (white-space={h1_fit['typewriterNowrap']})"
        )
    assert not data["hasEyebrow"], f"{slug}/{label}: eyebrow present"
    assert not data["hasDash"], f"{slug}/{label}: dash in copy"
    assert data["headerCount"] == 1 and data["footerCount"] == 1, (
        f"{slug}/{label}: header/footer count"
    )
    assert data["introInHero"] == 1, f"{slug}/{label}: hero description line missing"
    assert data["typewriterInHero"] == 1, f"{slug}/{label}: service hero typewriter missing"
    assert data["hasScrim"], f"{slug}/{label}: missing home-style scrim"
    assert data["factsCount"] == 0, f"{slug}/{label}: facts strip must not appear"
    assert data["ctaText"].strip() == "Kontakta oss", (
        f"{slug}/{label}: CTA text {data['ctaText']!r}"
    )
    assert data["ctaHref"].endswith("/kontakt/#offert"), data["ctaHref"]
    assert data["introBlock"], f"{slug}/{label}: missing alt-service-intro"
    if intro_styles:
        assert intro_styles["paddingTop"] == "0px", intro_styles
        assert intro_styles["borderLeftWidth"] == "0px", intro_styles
        assert intro_styles["boxShadow"] == "none", intro_styles
        assert "inter" in intro_styles["fontFamily"].lower(), intro_styles


def assert_service_hero_layout_top(page, slug: str, label: str) -> None:
    assert page.evaluate("window.scrollY") < 5, f"{slug}/{label}: expected top scroll"
    data = page.evaluate(
        """() => {
          const header = document.querySelector('.alt-header');
          const hero = document.querySelector('.alt-service-hero');
          const h1 = document.querySelector('.alt-service-hero h1');
          const cta = document.querySelector('.alt-service-hero__actions a.alt-btn--primary');
          const img = document.querySelector('.alt-service-hero__img');
          if (!header || !hero || !h1 || !cta) return null;
          const hr = header.getBoundingClientRect();
          const heroR = hero.getBoundingClientRect();
          const h1R = h1.getBoundingClientRect();
          const ctaR = cta.getBoundingClientRect();
          const heroStyle = getComputedStyle(hero);
          const before = getComputedStyle(header, '::before');
          const backdrop = before.backdropFilter || before.webkitBackdropFilter || '';
          return {
            heroPadTop: parseFloat(heroStyle.paddingTop) || 0,
            heroH: heroR.height,
            headerBottom: hr.bottom,
            h1Top: h1R.top,
            h1Bottom: h1R.bottom,
            ctaTop: ctaR.top,
            ctaBottom: ctaR.bottom,
            heroBottom: heroR.bottom,
            imgH: img ? img.getBoundingClientRect().height : 0,
            solid: header.classList.contains('is-solid'),
            backdrop,
          };
        }"""
    )
    assert data, f"{slug}/{label}: layout probe failed"
    assert data["heroPadTop"] >= 84, (
        f"{slug}/{label}: hero padding-top {data['heroPadTop']}"
    )
    assert data["h1Top"] >= data["headerBottom"] - 2, (
        f"{slug}/{label}: h1 under header (h1Top={data['h1Top']}, headerBottom={data['headerBottom']})"
    )
    assert data["ctaBottom"] <= data["heroBottom"] + 2, (
        f"{slug}/{label}: CTA outside hero"
    )
    assert data["imgH"] >= data["heroH"] * 0.85, (
        f"{slug}/{label}: hero image strip (imgH={data['imgH']}, heroH={data['heroH']})"
    )
    if label == "iphone":
        assert not data["solid"], f"{slug}/{label}: header should not be solid at top"
        assert data["backdrop"] in ("none", ""), (
            f"{slug}/{label}: blur at top ({data['backdrop']})"
        )


def assert_typewriter_motion(page, slug: str, label: str) -> None:
    spec = PAGES[slug]
    layout = page.evaluate(
        """() => {
          const h1 = document.querySelector('.alt-service-hero h1');
          return h1 ? h1.getBoundingClientRect().height : 0;
        }"""
    )
    page.wait_for_timeout(120)
    layout_after = page.evaluate(
        """() => {
          const h1 = document.querySelector('.alt-service-hero h1');
          return h1 ? h1.getBoundingClientRect().height : 0;
        }"""
    )
    assert abs(layout - layout_after) <= 2, (
        f"{slug}/{label}: h1 layout shift {layout} -> {layout_after}"
    )
    full_len = len(spec["h1"])
    page.wait_for_timeout(max(120, full_len * 90 + 400))
    done_text = page.locator(".alt-service-hero [data-typewriter-text]").inner_text()
    assert len(done_text) == full_len, f"{slug}/{label}: typewriter should finish ({done_text!r})"
    page.wait_for_timeout(3200)
    later_text = page.locator(".alt-service-hero [data-typewriter-text]").inner_text()
    assert later_text == done_text, f"{slug}/{label}: typewriter should not delete ({later_text!r})"


def assert_reduced_motion_h1(browser, slug: str = "brollop") -> None:
    ctx = browser.new_context(
        viewport=MOBILE,
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True,
        reduced_motion="reduce",
    )
    page = ctx.new_page()
    page.goto(f"{BASE}{PAGES[slug]['path']}", wait_until="networkidle")
    page.wait_for_timeout(400)
    data = page.evaluate(
        """([expectedH1]) => ({
          seoH1: document.querySelector('.alt-service-hero h1 .visually-hidden')?.innerText || '',
          live: document.querySelector('.alt-service-hero [data-typewriter-text]')?.innerText || '',
          caretHidden: document.querySelector('.alt-service-hero .alt-hero__caret')?.hidden,
        })""",
        [PAGES[slug]["h1"]],
    )
    assert data["seoH1"] == PAGES[slug]["h1"]
    assert data["live"] == PAGES[slug]["h1"]
    assert data["caretHidden"] is True
    ctx.close()


def run_viewport(browser, viewport: dict, mobile: bool, tag: str) -> None:
    for slug in PAGES:
        ctx = browser.new_context(
            viewport=viewport,
            device_scale_factor=3 if mobile else 1,
            is_mobile=mobile,
            has_touch=mobile,
        )
        page = ctx.new_page()
        if mobile:
            page.add_init_script(SAFE_AREA_INIT)
        page.goto(f"{BASE}{PAGES[slug]['path']}", wait_until="networkidle")
        page.wait_for_timeout(350)
        page.evaluate(
            """() => {
              document.querySelectorAll('[data-reveal]').forEach((el) => el.classList.add('is-in'));
            }"""
        )
        assert_service_hero(page, slug, tag)
        assert_service_hero_layout_top(page, slug, tag)
        if mobile and slug == "brollop":
            assert_typewriter_motion(page, slug, tag)
        ctx.close()


def main() -> int:
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8771", "--bind", "127.0.0.1"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.35)
    try:
        with sync_playwright() as p:
            browser = p.webkit.launch()
            run_viewport(browser, MOBILE, True, "iphone")
            run_viewport(browser, DESKTOP_1024, False, "desktop-1024")
            run_viewport(browser, DESKTOP, False, "desktop")
            assert_reduced_motion_h1(browser)
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print("OK: WebKit service hero banners (3 pages, iPhone + desktop)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
