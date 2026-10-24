#!/usr/bin/env python3
"""Capture desktop/mobile screenshots for walkthrough artifacts."""

from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("/opt/cursor/artifacts/screenshots")
BASE = "http://127.0.0.1:8080/testing/jutestromsbygg"
PAGES = [
    ("hem", "/"),
    ("tjanster", "/tjanster/"),
    ("referenser", "/referenser/"),
    ("kontakt", "/kontakt/"),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for slug, path in PAGES:
            for width, label in ((1280, "desktop"), (390, "mobile")):
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.goto(BASE + path, wait_until="networkidle")
                page.screenshot(path=str(OUT / f"jutestromsbygg-{slug}-{label}.png"), full_page=True)
                page.close()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(BASE + "/", wait_until="networkidle")
        page.click("#jb-cms-edit-fab")
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT / "jutestromsbygg-cms-mode-desktop.png"), full_page=True)
        page.close()
        browser.close()
    print("saved to", OUT)


if __name__ == "__main__":
    main()
