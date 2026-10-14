#!/usr/bin/env python3
"""Chromium: bröllop layout smoke at key widths (top + scrolled, menu closed)."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
URL = "http://127.0.0.1:8772/testing/halfbandnew2026/brollop/"
WIDTHS = (360, 390, 768, 1280, 1440)


def check(page, label: str, at_top: bool) -> None:
    data = page.evaluate(
        """() => {
          const stems = [...document.querySelectorAll('img[src*="/gallery/halvfjorton-"]')]
            .map((img) => (img.getAttribute('src') || '').match(/halvfjorton-\\d+/)?.[0])
            .filter(Boolean);
          const dup = stems.find((s, i) => stems.indexOf(s) !== i);
          const main = document.querySelector('main#innehall');
          const h1 = document.querySelector('.alt-service-hero h1');
          const header = document.querySelector('.alt-header');
          const hr = header ? header.getBoundingClientRect() : { bottom: 0 };
          const h1r = h1 ? h1.getBoundingClientRect() : { top: 0 };
          const bleedImg = document.querySelector('.alt-svc-bleed img');
          const bleedFit = bleedImg ? getComputedStyle(bleedImg).objectFit : '';
          const introFs = (() => {
            const el = document.querySelector('.alt-service-intro .aeo-answer');
            return el ? parseFloat(getComputedStyle(el).fontSize) : 0;
          })();
          return {
            dup,
            overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
            underHeader: h1r.top < hr.bottom - 1,
            bleedFit,
            introFs,
            bleed: document.querySelectorAll('.alt-svc-bleed').length,
          };
        }"""
    )
    assert not data["overflow"], f"{label}: horizontal scroll"
    if at_top:
        assert not data["underHeader"], f"{label}: h1 under header"
    assert not data["dup"], f"{label}: duplicate image {data['dup']}"
    assert data["bleedFit"] == "cover", f"{label}: bleed must use cover ({data['bleedFit']})"
    assert data["bleed"] >= 2, f"{label}: bleed images"
    if page.viewport_size and page.viewport_size["width"] <= 480 and at_top:
        assert data["introFs"] <= 24, f"{label}: ingress too large on mobile ({data['introFs']}px)"


def main() -> int:
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8772", "--bind", "127.0.0.1"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.35)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for w in WIDTHS:
                ctx = browser.new_context(viewport={"width": w, "height": 900})
                page = ctx.new_page()
                page.goto(URL, wait_until="networkidle")
                check(page, f"{w}px-top", True)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.45)")
                page.wait_for_timeout(200)
                check(page, f"{w}px-scroll", False)
                ctx.close()
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print("OK: Chromium bröllop QA widths", WIDTHS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
