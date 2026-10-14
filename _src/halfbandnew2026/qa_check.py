#!/usr/bin/env python3
"""
Halv Fjorton QA gate — run before every push (see QA.md).

  python3 qa_check.py              # build + local full matrix
  python3 qa_check.py --quick --pages /brollop/ /foretag/  # fast subset (Chromium)
  python3 qa_check.py --live       # after deploy, against labs URL
  python3 qa_check.py --skip-build # local only, existing testing output
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote, urljoin

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

# qa_lib lives under scripts/
_SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(_SRC / "scripts"))
from qa_lib import (  # noqa: E402
    CHECKS_JS,
    FORBIDDEN_PHRASES,
    MOBILE_MENU_MAX_WIDTH,
    SAFE_AREA_INIT,
    WIDTHS,
    find_forbidden_phrases,
    page_fingerprint,
    site_root_paths,
)

REPO_ROOT = _SRC.parents[1]
TESTING_OUT = REPO_ROOT / "testing" / "halfbandnew2026"
SUBPATH = "/testing/halfbandnew2026"
LOCAL_PORT = 8789
LIVE_BASE = "https://labs.ivarlundin.se/testing/halfbandnew2026"
SCREENSHOT_DIR = Path("/opt/cursor/artifacts/qa-screenshots")
QUICK_WIDTHS = (390, 1280)

MENU_TOGGLE = "[data-nav-toggle]"
MENU_CLOSE = "[data-nav-close]"
MENU_MOTION_MS = 400


class QAFail(Exception):
    pass


def normalize_page_paths(raw: list[str], allowed: set[str]) -> list[str]:
    """Map CLI page tokens to canonical site paths (e.g. brollop -> /brollop/)."""
    out: list[str] = []
    for token in raw:
        t = token.strip()
        if not t:
            continue
        if t.startswith("http"):
            raise QAFail(f"invalid --pages entry (use paths like /brollop/): {token}")
        if t.endswith("index.html"):
            t = t[: -len("index.html")]
        if not t.startswith("/"):
            t = "/" + t
        if not t.endswith("/"):
            if "." in t.rsplit("/", 1)[-1]:
                raise QAFail(f"--pages must be site paths, not files: {token}")
            t = t + "/"
        if t not in allowed:
            raise QAFail(f"unknown page {t!r} (not in testing build)")
        if t not in out:
            out.append(t)
    if not out:
        raise QAFail("--pages: no valid paths")
    return out


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
        cwd=str(_SRC),
        check=True,
    )


def http_get(url: str, timeout: float = 30.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "hf-qa-check/1.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def local_html_path(path: str) -> Path:
    if path == "/":
        return TESTING_OUT / "index.html"
    clean = path.strip("/")
    if clean.endswith(".html"):
        return TESTING_OUT / clean
    return TESTING_OUT / clean / "index.html"


def wait_for_live(base: str, paths: list[str], timeout_s: int = 300) -> None:
    local_fps = {}
    for p in paths[:5]:
        local_fps[p] = page_fingerprint(local_html_path(p).read_text(encoding="utf-8"))

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        ok = True
        for p, fp_local in local_fps.items():
            url = urljoin(base.rstrip("/") + "/", p.lstrip("/"))
            if not url.endswith("/") and p != "/":
                url = url.rstrip("/") + "/"
            try:
                live_html = http_get(url + ("?qa=" + str(int(time.time())) if "?" not in url else ""))
            except (urllib.error.URLError, TimeoutError):
                ok = False
                break
            if page_fingerprint(live_html) != fp_local:
                ok = False
                break
        if ok:
            print("QA: live deploy matches local fingerprint (sample pages)")
            return
        time.sleep(12)
    raise QAFail("live deploy did not match local build within timeout")


def set_menu(page, open_menu: bool, width: int) -> None:
    if width > MOBILE_MENU_MAX_WIDTH:
        return
    toggle = page.locator(MENU_TOGGLE)
    if toggle.count() == 0 or not toggle.first.is_visible():
        if open_menu:
            return
    is_open = page.evaluate("() => document.body.classList.contains('nav-open')")
    if open_menu and not is_open:
        if toggle.count() and toggle.first.is_visible():
            toggle.first.click()
            page.wait_for_timeout(MENU_MOTION_MS)
    elif not open_menu and is_open:
        close = page.locator(MENU_CLOSE)
        if close.count():
            close.first.click()
            page.wait_for_timeout(MENU_MOTION_MS + 80)


def run_state_checks(
    page,
    label: str,
    at_top: bool,
    menu_open: bool,
    console_errors: list[str],
    check_urls: bool,
) -> list[str]:
    failures: list[str] = []
    if console_errors:
        failures.extend(f"{label}: console: {e}" for e in console_errors[-3:])
    data = page.evaluate(
        CHECKS_JS,
        {"atTop": at_top, "menuOpen": menu_open},
    )
    for err in data.get("errors") or []:
        failures.append(f"{label}: {err}")

    text = page.evaluate(
        """() => {
          const main = document.querySelector('main');
          return main ? main.innerText : '';
        }"""
    )
    for phrase in find_forbidden_phrases(text):
        failures.append(f"{label}: forbidden-phrase-main '{phrase}'")

    if check_urls:
        urls = page.evaluate(
            """() => {
              const out = [];
              document.querySelectorAll('main img[src]').forEach(img => {
                const s = img.getAttribute('src');
                if (s && !s.startsWith('http')) out.push(s.split('?')[0]);
              });
              document.querySelectorAll('main a[href]').forEach(a => {
                const h = a.getAttribute('href');
                if (h && h.startsWith('/') && !h.startsWith('//')) {
                  const p = h.split('#')[0].split('?')[0];
                  if (p.endsWith('/') || p.endsWith('.html') || p.includes('.')) out.push(p);
                }
              });
              return [...new Set(out)].slice(0, 25);
            }"""
        )
        for rel in urls:
            if not rel:
                continue
            if rel.startswith("http"):
                target = rel
            else:
                target = urljoin(page.url, rel)
            candidates = [target]
            if SUBPATH in target and not target.endswith("/") and "." not in target.rsplit("/", 1)[-1]:
                candidates.append(target.rstrip("/") + "/")
            ok = False
            for cand in candidates:
                try:
                    req = urllib.request.Request(
                        cand, method="HEAD", headers={"Cache-Control": "no-cache"}
                    )
                    with urllib.request.urlopen(req, timeout=12) as resp:
                        if resp.status < 400:
                            ok = True
                            break
                except urllib.error.HTTPError as e:
                    if e.code == 405:
                        try:
                            http_get(cand, timeout=12)
                            ok = True
                            break
                        except urllib.error.HTTPError:
                            pass
                except urllib.error.URLError:
                    pass
            if not ok:
                failures.append(f"{label}: broken-url {rel}")

    return failures


def capture_screenshot(page, path: str, width: int, browser_name: str) -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe = path.strip("/").replace("/", "_") or "home"
    out = SCREENSHOT_DIR / f"{safe}-w{width}-{browser_name}.png"
    page.screenshot(path=str(out), full_page=True)


def run_matrix(
    base_url: str,
    paths: list[str],
    browsers: tuple[str, ...],
    screenshot: bool,
    widths: tuple[int, ...] = WIDTHS,
) -> list[str]:
    failures: list[str] = []
    steps_run: list[str] = []

    with sync_playwright() as p:
        for browser_name in browsers:
            launch = p.chromium.launch() if browser_name == "chromium" else p.webkit.launch()
            browser = launch
            try:
                for width in widths:
                    height = 900 if width >= 768 else 844
                    mobile = width <= MOBILE_MENU_MAX_WIDTH
                    ctx = browser.new_context(
                        viewport={"width": width, "height": height},
                        device_scale_factor=3 if width <= 390 else 1,
                        is_mobile=mobile,
                        has_touch=mobile,
                    )
                    if mobile:
                        ctx.add_init_script(SAFE_AREA_INIT)
                    page = ctx.new_page()
                    console_errors: list[str] = []

                    def on_console(msg):
                        if msg.type == "error":
                            console_errors.append(msg.text[:200])

                    page.on("console", on_console)

                    for path in paths:
                        url = base_url.rstrip("/") + quote(path, safe="/")
                        if not url.endswith("/") and path.endswith("/"):
                            url += "/"
                        cache_bust = f"qa={int(time.time())}"
                        url = url + ("&" if "?" in url else "?") + cache_bust

                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=45000)
                        except PlaywrightError as e:
                            failures.append(f"{browser_name}/{width}/{path}: navigation {e}")
                            continue
                        page.wait_for_timeout(150)

                        states = [
                            ("top-closed", True, False),
                            ("scrolled-closed", False, False),
                        ]
                        has_toggle = (
                            mobile
                            and page.locator(MENU_TOGGLE).count() > 0
                            and page.locator(MENU_TOGGLE).first.is_visible()
                        )
                        if has_toggle:
                            states.extend(
                                [
                                    ("top-open", True, True),
                                    ("scrolled-open", False, True),
                                ]
                            )

                        for state_name, at_top, menu_open in states:
                            if menu_open and not has_toggle:
                                continue
                            label = f"{browser_name}/{width}/{path}/{state_name}"
                            steps_run.append(label)
                            page.evaluate("window.scrollTo(0, 0)")
                            page.wait_for_timeout(60)
                            if not at_top:
                                page.evaluate(
                                    "() => window.scrollTo(0, Math.min(1200, document.body.scrollHeight * 0.35))"
                                )
                                page.wait_for_timeout(80)
                            set_menu(page, menu_open, width)
                            console_errors.clear()
                            failures.extend(
                                run_state_checks(
                                    page,
                                    label,
                                    at_top,
                                    menu_open,
                                    console_errors,
                                    check_urls=(state_name == "top-closed"),
                                )
                            )

                        if screenshot and browser_name == "webkit" and width == 390:
                            page.evaluate("window.scrollTo(0, 0)")
                            set_menu(page, False, width)
                            capture_screenshot(page, path, width, browser_name)

                    ctx.close()
            finally:
                browser.close()

    summary_path = SCREENSHOT_DIR / "qa-steps.json"
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps({"steps": steps_run, "failures": failures}, indent=2), encoding="utf-8")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Halv Fjorton QA (binding — see QA.md)")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Fast mode: Chromium only, widths 390+1280, same state/failure rules (requires --pages)",
    )
    parser.add_argument(
        "--pages",
        nargs="+",
        metavar="PATH",
        help="Site paths to check (e.g. /brollop/ brollop foretag). Required with --quick.",
    )
    parser.add_argument("--live", action="store_true", help="Run against labs after deploy")
    parser.add_argument("--live-base", default=LIVE_BASE)
    parser.add_argument("--wait-deploy", type=int, default=240, help="Seconds to wait for live==local")
    parser.add_argument("--no-screenshots", action="store_true")
    args = parser.parse_args()

    if args.quick and not args.pages:
        parser.error("--quick requires --pages (one or more paths, e.g. /brollop/ /foretag/)")
    if args.pages and not args.quick:
        parser.error("--pages is only valid with --quick")
    if args.quick and args.live:
        parser.error("--quick does not support --live (confirm push landed separately; see QA.md)")

    if not args.skip_build and not args.live:
        print("QA: build + build-time asserts…")
        run_build()

    if not TESTING_OUT.is_dir():
        print("QA: missing testing output", file=sys.stderr)
        return 1

    all_paths = [p for p in site_root_paths(TESTING_OUT) if p not in {"/repertoar/"}]
    allowed = set(all_paths)

    if args.quick:
        paths = normalize_page_paths(args.pages, allowed)
        browsers: tuple[str, ...] = ("chromium",)
        widths = QUICK_WIDTHS
        screenshot = False
        print(
            f"QA (quick): {len(paths)} page(s) × {len(widths)} widths × chromium "
            f"(top/scrolled, menu closed/open on mobile)"
        )
    else:
        paths = all_paths
        browsers = ("chromium", "webkit")
        widths = WIDTHS
        screenshot = not args.no_screenshots
        print(f"QA: {len(paths)} pages × {len(widths)} widths × chromium+webkit")

    if args.live:
        print(f"QA: waiting for live deploy ({args.live_base})…")
        wait_for_live(args.live_base, paths, timeout_s=args.wait_deploy)
        base = args.live_base
        server = None
    else:
        base = f"http://127.0.0.1:{LOCAL_PORT}{SUBPATH}"
        server = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(LOCAL_PORT), "--bind", "127.0.0.1"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.4)

    t0 = time.perf_counter()
    try:
        failures = run_matrix(
            base,
            paths,
            browsers,
            screenshot=screenshot,
            widths=widths,
        )
    finally:
        if server:
            server.terminate()
            server.wait(timeout=5)
    elapsed = time.perf_counter() - t0

    if failures:
        print(f"QA FAILED ({len(failures)} issues)", file=sys.stderr)
        for line in failures[:40]:
            print(f"  - {line}", file=sys.stderr)
        if len(failures) > 40:
            print(f"  … and {len(failures) - 40} more", file=sys.stderr)
        if args.quick:
            print(f"QA: quick run time {elapsed:.1f}s", file=sys.stderr)
        return 1

    phase = "live" if args.live else "local"
    if args.quick:
        print(
            f"OK: qa_check passed (quick, {phase}, {len(paths)} page(s), chromium, "
            f"widths {list(widths)}, {elapsed:.1f}s)"
        )
    else:
        print(f"OK: qa_check passed ({phase}, {len(paths)} pages, chromium+webkit, widths {list(widths)})")
    if screenshot:
        print(f"QA: full-page screenshots in {SCREENSHOT_DIR} (internal review)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except QAFail as e:
        print(f"QA FAILED: {e}", file=sys.stderr)
        sys.exit(1)
