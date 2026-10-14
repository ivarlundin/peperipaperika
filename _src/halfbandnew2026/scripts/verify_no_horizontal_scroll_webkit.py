#!/usr/bin/env python3
"""WebKit iPhone: no horizontal overflow on all built pages."""
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
SITE_ROOT = ROOT / "testing" / "halfbandnew2026"
BASE = "http://127.0.0.1:8777/testing/halfbandnew2026"
VIEWPORT = {"width": 390, "height": 844}


def page_paths() -> list[str]:
    paths = ["/"]
    for html_path in sorted(SITE_ROOT.rglob("*.html")):
        rel = html_path.relative_to(SITE_ROOT).as_posix()
        if rel == "index.html":
            continue
        if rel.endswith("/index.html"):
            paths.append("/" + rel[: -len("index.html")])
        elif rel.endswith(".html"):
            paths.append("/" + rel)
    return sorted(set(paths))


def assert_no_horizontal_overflow(page, path: str) -> None:
    data = page.evaluate(
        """() => ({
          doc: {
            sw: document.documentElement.scrollWidth,
            cw: document.documentElement.clientWidth,
          },
          body: {
            sw: document.body.scrollWidth,
            cw: document.body.clientWidth,
          },
        })"""
    )
    doc = data["doc"]
    if doc["sw"] != doc["cw"]:
        raise AssertionError(
            f"{path}: document scrollWidth {doc['sw']} != clientWidth {doc['cw']}"
        )
    body = data["body"]
    if body["sw"] > body["cw"] + 1:
        raise AssertionError(
            f"{path}: body scrollWidth {body['sw']} > clientWidth {body['cw']}"
        )


def main() -> int:
    paths = page_paths()
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8777", "--bind", "127.0.0.1"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.35)
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
            for path in paths:
                url = BASE + quote(path, safe="/")
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(120)
                assert_no_horizontal_overflow(page, path)
                if path == "/":
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                    page.wait_for_timeout(120)
                    assert_no_horizontal_overflow(page, path + " (mid-scroll)")
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(120)
                    assert_no_horizontal_overflow(page, path + " (bottom)")
            context.close()
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print(f"OK: no horizontal overflow on {len(paths)} pages (WebKit iPhone)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
