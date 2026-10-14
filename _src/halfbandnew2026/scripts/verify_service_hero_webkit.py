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
            h1: hero ? (hero.querySelector('h1')?.innerText || '') : '',
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
    assert data["h1"] == spec["h1"], f"{slug}/{label}: h1 mismatch"
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
    assert data["typewriterInHero"] == 0, f"{slug}/{label}: no typewriter in service hero"
    assert data["hasScrim"], f"{slug}/{label}: missing home-style scrim"
    assert data["introBlock"], f"{slug}/{label}: missing alt-service-intro"
    if intro_styles:
        assert intro_styles["paddingTop"] == "0px", intro_styles
        assert intro_styles["borderLeftWidth"] == "0px", intro_styles
        assert intro_styles["boxShadow"] == "none", intro_styles
        assert "inter" in intro_styles["fontFamily"].lower(), intro_styles


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
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print("OK: WebKit service hero banners (3 pages, iPhone + desktop)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
