#!/usr/bin/env python3
"""Playwright WebKit iPhone: mobile menu full viewport at scroll 0 and 1500px."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = Path("/opt/cursor/artifacts/screenshots")
SCROLL_Y = 1500
VIEWPORT = {"width": 390, "height": 844}
BASE_URL = "http://127.0.0.1:8765/testing/halfbandnew2026/"


def assert_menu_fullscreen(page, label: str) -> None:
    menu = page.locator("[data-mobile-menu]")
    assert not menu.evaluate("el => el.hidden"), f"{label}: menu should be visible"
    box = menu.bounding_box()
    assert box, f"{label}: menu has no bounding box"
    vp = page.viewport_size
    assert vp, f"{label}: no viewport"
    assert abs(box["height"] - vp["height"]) < 8, (
        f"{label}: menu height {box['height']} != viewport {vp['height']}"
    )
    assert box["y"] < 5, f"{label}: menu y={box['y']} not at top"
    # Last nav link visible (not clipped to header strip)
    kontakt = page.locator(".mobile-menu__list a", has_text="Kontakt")
    assert kontakt.is_visible(), f"{label}: Kontakt link not visible"
    cta = page.locator(".mobile-menu__cta")
    assert cta.is_visible(), f"{label}: CTA not visible"
    # CTA should be in mobile menu foot, not header bar
    in_menu = cta.evaluate(
        "el => !!el.closest('[data-mobile-menu]')"
    )
    assert in_menu, f"{label}: CTA not inside mobile menu"
    header_cta = page.locator(".alt-header .alt-nav__cta-desktop")
    assert not header_cta.is_visible(), f"{label}: desktop CTA visible in header"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.35)
    url = BASE_URL

    try:
        with sync_playwright() as p:
            browser = p.webkit.launch()
            context = browser.new_context(
                viewport=VIEWPORT,
                device_scale_factor=3,
                is_mobile=True,
                has_touch=True,
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle")

            page.locator("[data-nav-toggle]").click()
            assert_menu_fullscreen(page, "scrollY=0")
            page.screenshot(path=str(OUT / "mobile-menu-webkit-top.png"), full_page=False)

            page.locator("[data-nav-close]").click()
            page.evaluate(f"window.scrollTo(0, {SCROLL_Y})")
            page.wait_for_timeout(200)
            assert page.evaluate("window.scrollY") >= SCROLL_Y - 20

            page.locator("[data-nav-toggle]").click()
            assert_menu_fullscreen(page, f"scrollY={SCROLL_Y}")
            page.screenshot(
                path=str(OUT / "mobile-menu-webkit-scrolled.png"), full_page=False
            )

            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)

    print("OK: WebKit iPhone mobile menu at top and scrolled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
