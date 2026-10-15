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
            if not url.endswith("/") and p != "/" and not p.endswith(".html"):
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
) -> tuple[list[str], dict]:
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

    return failures, data


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
    inner_h1_gaps: dict[str, float] = {}
    service_h1_gaps: dict[str, float] = {}

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
                            state_failures, check_data = run_state_checks(
                                page,
                                label,
                                at_top,
                                menu_open,
                                console_errors,
                                check_urls=(state_name == "top-closed"),
                            )
                            failures.extend(state_failures)
                            if (
                                browser_name == "chromium"
                                and width >= 901
                                and at_top
                                and not menu_open
                                and state_name == "top-closed"
                            ):
                                inner_gap = check_data.get("innerH1Gap")
                                if inner_gap is not None:
                                    inner_h1_gaps[path] = float(inner_gap)
                                svc_gap = check_data.get("serviceH1Gap")
                                if svc_gap is not None:
                                    service_h1_gaps[path] = float(svc_gap)

                        if screenshot and browser_name == "webkit" and width == 390:
                            page.evaluate("window.scrollTo(0, 0)")
                            set_menu(page, False, width)
                            capture_screenshot(page, path, width, browser_name)

                    ctx.close()
            finally:
                browser.close()

    if len(inner_h1_gaps) > 1:
        spread = max(inner_h1_gaps.values()) - min(inner_h1_gaps.values())
        if spread > 5:
            failures.append(
                f"h1-inner-offset-mismatch spread={spread:.1f}px samples={inner_h1_gaps}"
            )
    if len(service_h1_gaps) > 1:
        spread = max(service_h1_gaps.values()) - min(service_h1_gaps.values())
        if spread > 6:
            failures.append(
                f"h1-service-hero-inset-mismatch spread={spread:.1f}px samples={service_h1_gaps}"
            )

    summary_path = SCREENSHOT_DIR / "qa-steps.json"
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(
            {
                "steps": steps_run,
                "failures": failures,
                "innerH1Gaps": inner_h1_gaps,
                "serviceH1Gaps": service_h1_gaps,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return failures


DESKTOP_NAV_SERVICE_LINKS = (
    ("/brollop/", "Bröllop"),
    ("/foretag/", "Företag"),
    ("/mingel/", "Fest och mingel"),
)


def run_desktop_tjanster_dropdown_qa(base_url: str) -> list[str]:
    """Desktop Chromium: hover Tjänster → each service link → click navigates."""
    failures: list[str] = []
    home = base_url.rstrip("/") + "/"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            ctx = browser.new_context(
                viewport={"width": 1280, "height": 900},
                device_scale_factor=1,
            )
            page = ctx.new_page()
            for index, (path_suffix, label) in enumerate(DESKTOP_NAV_SERVICE_LINKS):
                page.goto(
                    home + f"?qa=nav-dd-{index}",
                    wait_until="domcontentloaded",
                    timeout=45000,
                )
                page.wait_for_timeout(120)
                dd = page.locator(".alt-header .nav-item--dropdown").first
                trigger = dd.locator("[data-nav-dropdown-trigger]")
                link = dd.locator('a[role="menuitem"]').nth(index)
                if trigger.count() == 0 or dd.locator('a[role="menuitem"]').count() < len(DESKTOP_NAV_SERVICE_LINKS):
                    failures.append(f"desktop-nav-dropdown: missing trigger or menu links (index {index})")
                    continue
                link_text = link.evaluate("el => (el.textContent || '').trim()")
                if link_text != label:
                    failures.append(
                        f"desktop-nav-dropdown: expected link '{label}' at index {index}, got '{link_text}'"
                    )
                    continue
                trigger.hover()
                page.wait_for_timeout(100)
                link.hover()
                page.wait_for_timeout(150)
                is_open = dd.evaluate("el => el.classList.contains('is-open')")
                menu_box = page.locator(".alt-header #nav-tjanster").bounding_box()
                if not is_open and not menu_box:
                    failures.append(
                        f"desktop-nav-dropdown: menu closed while moving pointer to '{label}'"
                    )
                    continue
                try:
                    with page.expect_navigation(wait_until="domcontentloaded", timeout=20000):
                        link.click()
                except PlaywrightError as e:
                    failures.append(f"desktop-nav-dropdown: click '{label}' failed: {e}")
                    continue
                if path_suffix.rstrip("/") not in page.url:
                    failures.append(
                        f"desktop-nav-dropdown: after '{label}' expected path {path_suffix} in {page.url}"
                    )
            ctx.close()
        finally:
            browser.close()
    return failures


FAQ_COLUMN_STABILITY_PATHS = ("/faq/", "/brollop/")


def run_faq_column_stability_qa(base_url: str) -> list[str]:
    """Desktop: opening one FAQ item must not shift siblings horizontally."""
    failures: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            ctx = browser.new_context(
                viewport={"width": 1280, "height": 900},
                device_scale_factor=1,
            )
            page = ctx.new_page()
            for path in FAQ_COLUMN_STABILITY_PATHS:
                url = base_url.rstrip("/") + path + "?qa=faq-cols"
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(200)
                if path == "/faq/":
                    primary_cta = page.locator(
                        ".page-hero__actions a.alt-btn--primary[href*='kontakt']"
                    )
                    if primary_cta.count() == 0:
                        failures.append(
                            "faq-page-cta: 'Frågor? Kontakta oss' must use alt-btn--primary"
                        )
                list_root = page.locator("[data-faq].alt-faq__list--cols")
                if list_root.count() == 0:
                    failures.append(f"faq-column-stability: missing two-column list on {path}")
                    continue
                col_count = page.evaluate(
                    """() => {
                      const list = document.querySelector('[data-faq].alt-faq__list--cols');
                      if (!list) return 0;
                      return getComputedStyle(list).gridTemplateColumns.split(' ').filter(Boolean).length;
                    }"""
                )
                if col_count < 2:
                    failures.append(
                        f"faq-column-stability: expected 2 grid columns on {path}, got {col_count}"
                    )
                    continue
                items = page.locator("[data-faq] .alt-faq__item")
                count = items.count()
                if count == 0:
                    failures.append(f"faq-column-stability: no FAQ items on {path}")
                    continue

                def snapshot_lefts() -> list[dict]:
                    return page.evaluate(
                        """() => {
                          const nodes = document.querySelectorAll('[data-faq] .alt-faq__item');
                          return Array.from(nodes).map((el) => ({
                            left: Math.round(el.getBoundingClientRect().left),
                          }));
                        }"""
                    )

                for index in range(count):
                    before = snapshot_lefts()
                    summary = items.nth(index).locator("summary")
                    summary.click()
                    page.wait_for_timeout(400)
                    after = snapshot_lefts()
                    if len(before) != len(after):
                        failures.append(
                            f"faq-column-stability: item count changed on {path} at index {index}"
                        )
                        break
                    for other in range(count):
                        if other == index:
                            continue
                        delta = abs(before[other]["left"] - after[other]["left"])
                        if delta > 2:
                            failures.append(
                                f"faq-column-stability: {path} item {other} x-shift "
                                f"{before[other]['left']}→{after[other]['left']}px "
                                f"when opening item {index}"
                            )
                    if items.nth(index).evaluate("el => el.open"):
                        summary.click()
                        page.wait_for_timeout(350)
            ctx.close()
        finally:
            browser.close()
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
        if not args.quick:
            failures.extend(run_desktop_tjanster_dropdown_qa(base))
            failures.extend(run_faq_column_stability_qa(base))
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
