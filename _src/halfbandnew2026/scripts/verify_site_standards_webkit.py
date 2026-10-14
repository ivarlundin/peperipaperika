#!/usr/bin/env python3
"""WebKit iPhone + desktop: offert layout, text-wrap, copy rules, nav colors."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
BASE = "http://127.0.0.1:8773/testing/halfbandnew2026"
MOBILE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 900}


def assert_page(page, path: str, desktop: bool) -> None:
    tag = f"{path}{' desktop' if desktop else ' iphone'}"
    page.goto(f"{BASE}{path}", wait_until="networkidle")
    page.wait_for_timeout(300)
    if path == "/":
        page.evaluate("() => document.querySelector('#offert')?.scrollIntoView()")
        page.wait_for_timeout(200)

    data = page.evaluate(
        """() => {
          const offertGrid = document.querySelector('#offert .contact-offert__grid')
            || document.querySelector('.contact-offert__grid');
          const bullets = offertGrid
            ? offertGrid.querySelectorAll('.list-check > li').length
            : 0;
          const heading = document.querySelector('main :is(h1, h2, h3)');
          const p = document.querySelector('#offert p') || document.querySelector('main p');
          const h2Wrap = heading
            ? getComputedStyle(heading).getPropertyValue('text-wrap').trim()
            : 'missing';
          const pWrap = p ? getComputedStyle(p).getPropertyValue('text-wrap').trim() : 'missing';
          const bodyText = document.body.innerText || '';
          const navLink = document.querySelector('.alt-nav__links > li > a')
            || document.querySelector('.mobile-menu__list > li > a');
          const dropLink = document.querySelector('.nav-dropdown__menu a');
          const navColor = navLink ? getComputedStyle(navLink).color : '';
          const dropColor = dropLink ? getComputedStyle(dropLink).color : '';
          const cols = offertGrid ? getComputedStyle(offertGrid).gridTemplateColumns : '';
          return {
            bullets,
            h2Wrap,
            pWrap,
            hasEyebrow: !!document.querySelector('.eyebrow'),
            hasDash: bodyText.includes('–') || bodyText.includes('—'),
            navColor,
            dropColor,
            cols,
          };
        }"""
    )
    assert data["bullets"] <= 3, f"{tag}: offert bullets {data['bullets']}"
    if desktop and path in ("/", "/kontakt/"):
        assert data["cols"].count(" ") >= 1, f"{tag}: offert grid not 2-col ({data['cols']})"
    assert data["h2Wrap"] == "balance", f"{tag}: h2 text-wrap {data['h2Wrap']}"
    assert data["pWrap"] == "pretty", f"{tag}: p text-wrap {data['pWrap']}"
    assert not data["hasEyebrow"], f"{tag}: eyebrow"
    assert not data["hasDash"], f"{tag}: typographic dash"
    assert data["navColor"] == "rgb(255, 255, 255)", f"{tag}: nav color {data['navColor']}"
    if data["dropColor"]:
        assert data["dropColor"] == "rgb(255, 255, 255)", f"{tag}: dropdown {data['dropColor']}"


def run(browser, desktop: bool) -> None:
    ctx = browser.new_context(
        viewport=DESKTOP if desktop else MOBILE,
        device_scale_factor=1 if desktop else 3,
        is_mobile=not desktop,
        has_touch=not desktop,
    )
    page = ctx.new_page()
    for path in ("/", "/kontakt/", "/foretag/"):
        assert_page(page, path, desktop)
    ctx.close()


def main() -> int:
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8773", "--bind", "127.0.0.1"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.35)
    try:
        with sync_playwright() as p:
            browser = p.webkit.launch()
            run(browser, False)
            run(browser, True)
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print("OK: site standards (WebKit iPhone + desktop)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
