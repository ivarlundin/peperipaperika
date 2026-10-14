#!/usr/bin/env python3
"""Playwright WebKit iPhone: home gallery bento marquee layout and image sharpness."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
VIEWPORT = {"width": 390, "height": 844}
BASE_URL = "http://127.0.0.1:8765/testing/halfbandnew2026/"


def main() -> int:
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.35)

    try:
        with sync_playwright() as p:
            browser = p.webkit.launch()
            page = browser.new_context(
                viewport=VIEWPORT,
                device_scale_factor=3,
                is_mobile=True,
                has_touch=True,
            ).new_page()
            page.goto(BASE_URL, wait_until="networkidle")
            gallery = page.locator(".alt-gallery")
            gallery.scroll_into_view_if_needed()
            page.wait_for_timeout(800)

            col_count = page.locator(".alt-gallery__set").first.locator(
                ".alt-gallery__col"
            ).count()
            assert col_count == 3, f"expected 3 bento columns per set, got {col_count}"

            boxes = page.locator(".alt-gallery__set").first.locator(
                ".alt-gallery__col"
            ).evaluate_all(
                "els => els.map(el => ({ w: el.getBoundingClientRect().width, h: el.getBoundingClientRect().height }))"
            )
            for i, box in enumerate(boxes):
                assert box["w"] >= 88, f"column {i} too narrow: {box['w']}"
                assert box["h"] >= 260, f"column {i} too short for bento stack: {box['h']}"

            cards_per_col = page.locator(".alt-gallery__set").first.locator(
                ".alt-gallery__col"
            ).first.locator(".alt-gallery__card").count()
            assert cards_per_col == 2, "each column should stack two cards"

            sharp = page.evaluate(
                """async () => {
                  const imgs = [...document.querySelectorAll('.alt-gallery__card img')].slice(0, 6);
                  for (const img of imgs) {
                    try { await img.decode(); } catch (e) {}
                  }
                  return imgs.map(img => {
                    const r = img.getBoundingClientRect();
                    const src = img.currentSrc || img.src;
                    const okSrc = /-(480|800|1200|1920)w\\./.test(src);
                    const okWidth = r.width > 0 && r.width <= 130;
                    return { ok: img.complete && okSrc && okWidth, src, w: r.width };
                  });
                }"""
            )
            bad = [s for s in sharp if not s.get("ok")]
            assert not bad, f"gallery images missing or wrong src: {bad}"

            track_width = page.locator(".alt-gallery__track").evaluate(
                "el => el.getBoundingClientRect().width"
            )
            set_width = page.locator(".alt-gallery__set").first.evaluate(
                "el => el.getBoundingClientRect().width"
            )
            assert track_width >= set_width * 1.95, (
                f"track should contain two sets for loop (track={track_width}, set={set_width})"
            )

            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)

    print("OK: WebKit iPhone gallery bento marquee")
    return 0


if __name__ == "__main__":
    sys.exit(main())
