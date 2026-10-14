#!/usr/bin/env python3
"""WebKit: hidden service pages noindex; nav shows three services only."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
BASE = "http://127.0.0.1:8771/testing/halfbandnew2026"
MOBILE = {"width": 390, "height": 844}
HIDDEN = (
    "/kompband/",
    "/50-arsfest/",
    "/brollopsband-smaland/",
    "/coverband-skane-malmo/",
    "/for-eventbolag/",
)
VISIBLE_SERVICES = ("Bröllop", "Företag", "Fest och mingel")


def assert_home_nav(page) -> None:
    page.goto(f"{BASE}/", wait_until="networkidle")
    page.locator("[data-nav-toggle]").click()
    page.wait_for_timeout(450)
    page.locator("#mobile-nav-tjanster-btn").click()
    page.wait_for_timeout(200)
    labels = page.locator("#mobile-nav-tjanster a[role='menuitem']").all_inner_texts()
    assert labels == list(VISIBLE_SERVICES), f"Tjänster menu labels: {labels}"
    menu_html = page.locator("[data-mobile-menu]").inner_html()
    for hidden in HIDDEN:
        assert hidden not in menu_html, f"hidden link {hidden} in mobile menu"


def assert_hidden_noindex(page, path: str) -> None:
    page.goto(f"{BASE}{path}", wait_until="networkidle")
    robots = page.locator('meta[name="robots"]').get_attribute("content")
    assert robots == "noindex,nofollow", f"{path} robots={robots}"


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
            ctx = browser.new_context(viewport=MOBILE, is_mobile=True, has_touch=True)
            page = ctx.new_page()
            assert_home_nav(page)
            for path in HIDDEN:
                assert_hidden_noindex(page, path)
            sitemap = (ROOT / "testing/halfbandnew2026/sitemap.xml").read_text(encoding="utf-8")
            for path in HIDDEN:
                assert path not in sitemap, f"{path} in sitemap"
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print("OK: hidden services excluded from nav/sitemap; noindex on hidden pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
