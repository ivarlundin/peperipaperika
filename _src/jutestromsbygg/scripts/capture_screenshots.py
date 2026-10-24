#!/usr/bin/env python3
"""Capture desktop/mobile screenshots for walkthrough artifacts."""

from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("/opt/cursor/artifacts/screenshots")
BASE = "http://127.0.0.1:8080/testing/jutestromsbygg"
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for width, label in ((1280, "desktop"), (390, "mobile")):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(BASE + "/", wait_until="networkidle")
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT / f"jutestromsbygg-hem-{label}.png"), full_page=True)
            page.close()
        browser.close()
    print("saved to", OUT)


if __name__ == "__main__":
    main()
