#!/usr/bin/env python3
"""WebKit: shared service hero banner on brollop, foretag, mingel (iPhone + desktop)."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = Path("/opt/cursor/artifacts/screenshots")
BASE = "http://127.0.0.1:8771/testing/halfbandnew2026"
MOBILE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 900}

PAGES = {
    "brollop": {
        "path": "/brollop/",
        "img_stem": "halvfjorton-03",
        "h1": "Bröllopsband med helband, blås och dans",
    },
    "foretag": {
        "path": "/foretag/",
        "img_stem": "halvfjorton-01",
        "h1": "Personalfest, kickoff och jubileum",
    },
    "mingel": {
        "path": "/mingel/",
        "img_stem": "halvfjorton-04",
        "h1": "Mingelmusik som håller tonen låg",
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
            introInHero: hero ? hero.querySelectorAll('.aeo-answer, .lead').length : -1,
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
            introBlock: !!document.querySelector('.alt-service-intro'),
            aeoInIntro: document.querySelector('.alt-service-intro .aeo-answer'),
            expectedStem,
            expectedH1,
          };
        }""",
        [spec["img_stem"], spec["h1"]],
    )
    intro_styles = page.evaluate(
        """() => {
          const el = document.querySelector('.alt-service-intro .aeo-answer')
            || document.querySelector('.alt-service-intro .lead');
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
    assert data["heroH"] >= 170, f"{slug}/{label}: hero too short ({data['heroH']})"
    assert data["seoH1"] == spec["h1"], f"{slug}/{label}: SEO h1 mismatch"
    assert data["hasTypewriterScript"], f"{slug}/{label}: typewriter script missing"
    assert spec["img_stem"] in data["imgSrc"], (
        f"{slug}/{label}: hero image should match offer card stem, got {data['imgSrc']}"
    )
    assert data["objectFit"] == "cover", f"{slug}/{label}: object-fit {data['objectFit']}"
    assert data["docSW"] <= data["docCW"] + 1, (
        f"{slug}/{label}: horizontal overflow {data['docSW']} > {data['docCW']}"
    )
    assert not data["hasEyebrow"], f"{slug}/{label}: eyebrow present"
    assert not data["hasDash"], f"{slug}/{label}: dash in copy"
    assert data["headerCount"] == 1 and data["footerCount"] == 1, (
        f"{slug}/{label}: header/footer count"
    )
    assert data["introInHero"] == 0, f"{slug}/{label}: ingress must not sit in hero"
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
    start_text = page.locator(".alt-service-hero [data-typewriter-text]").inner_text()
    assert len(start_text) == full_len, f"{slug}/{label}: initial typewriter text"
    page.wait_for_timeout(3200)
    mid_text = page.locator(".alt-service-hero [data-typewriter-text]").inner_text()
    assert len(mid_text) < full_len, f"{slug}/{label}: typewriter should delete ({mid_text!r})"


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
        page.goto(f"{BASE}{PAGES[slug]['path']}", wait_until="networkidle")
        page.wait_for_timeout(350)
        page.evaluate(
            """() => {
              document.querySelectorAll('[data-reveal]').forEach((el) => el.classList.add('is-in'));
            }"""
        )
        assert_service_hero(page, slug, tag)
        if mobile and slug == "brollop":
            assert_typewriter_motion(page, slug, tag)
            page.screenshot(
                path=str(OUT / "service-typewriter-brollop-iphone.png"),
                full_page=False,
            )
        page.screenshot(
            path=str(OUT / f"service-hero-{slug}-{tag}.png"),
            full_page=False,
        )
        ctx.close()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
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
