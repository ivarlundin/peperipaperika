#!/usr/bin/env python3
"""WebKit iPhone: ingress/AEO blocks have no box styling site-wide."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
VIEWPORT = {"width": 390, "height": 844}
BASE = "http://127.0.0.1:8772/testing/halfbandnew2026"

PATHS = (
    "/foretag/",
    "/brollop/",
    "/fest-och-mingel/",
    "/kompband/",
    "/julkonsert/",
    "/kontakt/",
)


def assert_plain_ingress(page, path: str) -> None:
    data = page.evaluate(
        """() => {
          const nodes = Array.from(document.querySelectorAll('.aeo-answer, .alt-service-intro .lead'));
          return nodes.map((el) => {
            const s = getComputedStyle(el);
            return {
              tag: el.tagName,
              cls: el.className,
              paddingTop: s.paddingTop,
              paddingLeft: s.paddingLeft,
              borderLeftWidth: s.borderLeftWidth,
              borderWidth: s.borderTopWidth,
              borderRadius: s.borderTopLeftRadius,
              backgroundColor: s.backgroundColor,
            };
          });
        }"""
    )
    for i, row in enumerate(data):
        label = f"{path} [{i}] {row['cls']}"
        assert row["paddingTop"] == "0px", f"{label} paddingTop {row['paddingTop']}"
        assert row["paddingLeft"] == "0px", f"{label} paddingLeft {row['paddingLeft']}"
        assert row["borderLeftWidth"] == "0px", f"{label} borderLeft {row['borderLeftWidth']}"
        assert row["borderWidth"] == "0px", f"{label} border {row['borderWidth']}"
        assert row["borderRadius"] == "0px", f"{label} radius {row['borderRadius']}"
        bg = row["backgroundColor"]
        assert bg in ("rgba(0, 0, 0, 0)", "transparent"), f"{label} bg {bg}"


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
            browser = p.webkit.launch()
            ctx = browser.new_context(
                viewport=VIEWPORT,
                device_scale_factor=3,
                is_mobile=True,
                has_touch=True,
            )
            page = ctx.new_page()
            for path in PATHS:
                page.goto(f"{BASE}{path}", wait_until="networkidle")
                page.wait_for_timeout(250)
                assert_plain_ingress(page, path)
            ctx.close()
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print("OK: plain ingress (WebKit iPhone)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
