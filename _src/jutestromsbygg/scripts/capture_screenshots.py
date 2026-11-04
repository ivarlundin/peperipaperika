#!/usr/bin/env python3
"""Capture desktop screenshots for walkthrough artifacts."""

from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("/opt/cursor/artifacts/screenshots")
BASE = "http://127.0.0.1:8080/testing/jutestromsbygg"
SHOTS = [
    ("hem", "/", True),
    ("tjanster", "/tjanster/", False),
    ("referenser", "/referenser/", False),
    ("kontakt", "/kontakt/", False),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for slug, path, full_page in SHOTS:
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(BASE + path, wait_until="networkidle")
            page.wait_for_timeout(300)
            page.screenshot(
                path=str(OUT / f"jutestromsbygg-{slug}-desktop.png"),
                full_page=full_page,
            )
            page.close()
        browser.close()
    print("saved to", OUT)


if __name__ == "__main__":
    main()
