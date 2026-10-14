#!/usr/bin/env python3
"""Automated QA for Halv Fjorton (WebKit). Fails if sticky header covers page content at top."""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SRC = Path(__file__).resolve().parents[1]
REPO_ROOT = SRC.parents[1]
TESTING_OUT = REPO_ROOT / "testing" / "halfbandnew2026"
SUBPATH = "/testing/halfbandnew2026"
PORT = 8788
BASE = f"http://127.0.0.1:{PORT}{SUBPATH}"

MOBILE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 900}

# iPhone safe-area regression: hero padding must account for notch when env() is active.
SAFE_AREA_INIT = """
(() => {
  const style = document.createElement('style');
  style.id = 'qa-safe-area';
  style.textContent = `
    @supports (padding: env(safe-area-inset-top)) {
      .alt-page {
        --alt-header-total: calc(var(--alt-header) + max(env(safe-area-inset-top), 47px));
      }
    }
  `;
  document.documentElement.appendChild(style);
})();
"""

STICKY_PROBE_JS = """() => {
  const header = document.querySelector('.alt-header');
  if (!header) return { ok: false, reason: 'missing .alt-header' };
  const headerBottom = header.getBoundingClientRect().bottom;
  const selectors = [
    ['service-h1', '.alt-service-hero h1'],
    ['service-cta', '.alt-service-hero__actions a'],
    ['home-h1', '.alt-hero h1'],
    ['home-cta', '.alt-hero .alt-btn--primary, .alt-hero a.alt-btn'],
  ];
  const hits = [];
  for (const [kind, sel] of selectors) {
    document.querySelectorAll(sel).forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.width < 1 && r.height < 1) return;
      const style = getComputedStyle(el);
      if (style.visibility === 'hidden' || style.display === 'none') return;
      const obscured = r.top < headerBottom - 1.5;
      hits.push({
        kind,
        top: r.top,
        bottom: r.bottom,
        headerBottom,
        obscured,
        label: (el.innerText || el.textContent || '').trim().slice(0, 48),
      });
    });
  }
  const blocked = hits.filter((h) => h.obscured);
  return {
    ok: blocked.length === 0,
    scrollY: window.scrollY,
    headerBottom,
    blocked,
    hits,
  };
}"""


def run_build() -> None:
    subprocess.run(
        [
            sys.executable,
            "scripts/build.py",
            "--output-dir",
            str(TESTING_OUT),
            "--subpath",
            SUBPATH,
        ],
        cwd=str(SRC),
        check=True,
    )


def run_script(name: str) -> None:
    path = SRC / "scripts" / name
    if not path.is_file():
        raise FileNotFoundError(path)
    subprocess.run([sys.executable, str(path)], cwd=str(SRC), check=True)


def assert_sticky_clearance(page, path: str, label: str) -> None:
    url = f"{BASE}{path}"
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(200)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(80)
    scroll_y = page.evaluate("() => window.scrollY")
    assert scroll_y < 8, f"{label}: expected top scroll, got {scroll_y}"
    data = page.evaluate(STICKY_PROBE_JS)
    if data.get("reason"):
        raise AssertionError(f"{label}: {data['reason']}")
    blocked = data.get("blocked") or []
    if blocked or not data.get("ok"):
        detail = ", ".join(
            f"{b['kind']} top={b['top']:.1f}px < headerBottom={b['headerBottom']:.1f}px ({b['label']!r})"
            for b in blocked
        )
        raise AssertionError(f"{label}: content under sticky header at top: {detail}")


def run_sticky_checks(browser) -> None:
    pages = [
        ("/", "home-iphone"),
        ("/brollop/", "brollop-iphone"),
        ("/foretag/", "foretag-iphone"),
        ("/mingel/", "mingel-iphone"),
    ]
    ctx = browser.new_context(
        viewport=MOBILE,
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True,
    )
    page = ctx.new_page()
    page.add_init_script(SAFE_AREA_INIT)
    for path, label in pages:
        assert_sticky_clearance(page, path, label)
    ctx.close()

    ctx = browser.new_context(viewport=DESKTOP)
    page = ctx.new_page()
    for path, label in [(p, l.replace("iphone", "desktop")) for p, l in pages]:
        assert_sticky_clearance(page, path, label)
    ctx.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Halv Fjorton QA checks (WebKit).")
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Use existing testing/halfbandnew2026 output without rebuilding.",
    )
    parser.add_argument(
        "--sticky-only",
        action="store_true",
        help="Only run sticky-header clearance probes.",
    )
    args = parser.parse_args()

    if not args.skip_build:
        print("QA: building testing output…")
        run_build()

    if not TESTING_OUT.is_dir():
        print(f"QA: missing output dir {TESTING_OUT}", file=sys.stderr)
        return 1

    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.35)
    try:
        with sync_playwright() as p:
            browser = p.webkit.launch()
            print("QA: sticky header clearance (top scroll, iPhone + desktop)…")
            run_sticky_checks(browser)
            browser.close()

        if not args.sticky_only:
            print("QA: verify_service_hero_webkit…")
            run_script("verify_service_hero_webkit.py")
            print("QA: verify_mobile_menu_webkit…")
            run_script("verify_mobile_menu_webkit.py")
            print("QA: verify_no_horizontal_scroll_webkit…")
            run_script("verify_no_horizontal_scroll_webkit.py")
    finally:
        server.terminate()
        server.wait(timeout=5)

    print("OK: qa_check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
