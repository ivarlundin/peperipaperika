#!/usr/bin/env python3
"""WebKit: bröllop editorial layout, no overflow, screenshots mobile + desktop."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = Path("/opt/cursor/artifacts/screenshots")
URL = "http://127.0.0.1:8770/testing/halfbandnew2026/brollop/"
MOBILE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 900}


def assert_layout(page, label: str) -> None:
    data = page.evaluate(
        """() => {
          const main = document.querySelector('main#innehall');
          const hero = document.querySelector('.alt-wedding-hero');
          const venues = document.querySelector('.alt-wedding-venues__list');
          const text = main ? main.innerText : '';
          return {
            bodyClass: document.body.className,
            hasHero: !!hero,
            heroH: hero ? hero.getBoundingClientRect().height : 0,
            venueCount: venues ? venues.querySelectorAll('li').length : 0,
            docSW: document.documentElement.scrollWidth,
            docCW: document.documentElement.clientWidth,
            hasEyebrow: !!document.querySelector('.eyebrow'),
            hasDash: text.includes('–') || text.includes('—'),
            headerCount: document.querySelectorAll('.alt-header').length,
            footerCount: document.querySelectorAll('.site-footer').length,
          };
        }"""
    )
    assert "alt-page--wedding" in data["bodyClass"], f"{label}: wedding body class"
    assert data["hasHero"], f"{label}: missing wedding hero"
    assert data["heroH"] >= 280, f"{label}: hero too short ({data['heroH']})"
    assert data["venueCount"] == 4, f"{label}: venue list count"
    assert data["docSW"] <= data["docCW"] + 1, (
        f"{label}: horizontal overflow {data['docSW']} > {data['docCW']}"
    )
    assert not data["hasEyebrow"], f"{label}: eyebrow present"
    assert not data["hasDash"], f"{label}: dash in copy"
    assert data["headerCount"] == 1 and data["footerCount"] == 1, (
        f"{label}: header/footer count"
    )

    img = page.locator(".alt-wedding-figure img").first
    fit = img.evaluate("el => getComputedStyle(el).objectFit")
    assert fit == "cover", f"{label}: images must use cover, got {fit}"


def run_viewport(browser, viewport: dict, mobile: bool, tag: str) -> None:
    ctx = browser.new_context(
        viewport=viewport,
        device_scale_factor=3 if mobile else 1,
        is_mobile=mobile,
        has_touch=mobile,
    )
    page = ctx.new_page()
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    page.evaluate(
        """() => {
          document.querySelectorAll('[data-reveal]').forEach((el) => el.classList.add('is-in'));
        }"""
    )
    assert_layout(page, tag)
    page.screenshot(path=str(OUT / f"brollop-{tag}.png"), full_page=True)
    ctx.close()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8770", "--bind", "127.0.0.1"],
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
    print("OK: WebKit bröllop design (iPhone + desktop)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
