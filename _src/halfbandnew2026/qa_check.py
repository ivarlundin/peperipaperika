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

BUTTON_HOVER_CONTRAST_PAGES = (
    "/",
    "/konserter/",
    "/kontakt/",
    "/faq/",
    "/brollop/",
    "/foretag/",
    "/mingel/",
    "/lyssna/",
    "/om-oss/",
)

_CONTRAST_RATIO_JS = """
(el) => {
  function parseRgb(color) {
    const m = color.match(/rgba?\\(\\s*([\\d.]+)\\s*,\\s*([\\d.]+)\\s*,\\s*([\\d.]+)/);
    if (!m) return null;
    return [+m[1], +m[2], +m[3]];
  }
  function lum([r, g, b]) {
    const a = [r, g, b].map((v) => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2];
  }
  function contrast(fg, bg) {
    const l1 = lum(fg);
    const l2 = lum(bg);
    const hi = Math.max(l1, l2);
    const lo = Math.min(l1, l2);
    return (hi + 0.05) / (lo + 0.05);
  }
  const style = getComputedStyle(el);
  const fg = parseRgb(style.color);
  if (!fg) return null;
  const ownBg = parseRgb(style.backgroundColor);
  if (ownBg && style.backgroundColor !== "rgba(0, 0, 0, 0)") {
    return contrast(fg, ownBg);
  }
  let node = el.parentElement;
  let bg = null;
  while (node) {
    const bgColor = getComputedStyle(node).backgroundColor;
    const parsed = parseRgb(bgColor);
    if (parsed && bgColor !== "rgba(0, 0, 0, 0)") {
      bg = parsed;
      break;
    }
    node = node.parentElement;
  }
  if (!bg) return null;
  return contrast(fg, bg);
}
"""


def run_button_hover_contrast_qa(base_url: str) -> list[str]:
    """Hover button-like CTAs; text/background contrast must stay >= 4.5:1."""
    failures: list[str] = []
    root = base_url.rstrip("/")
    button_selectors = (
        "a.alt-btn--primary",
        "a.alt-btn--ghost",
        "a.btn-primary",
        "a.btn-ghost",
        ".site-footer__cta",
        ".alt-nav__cta-desktop",
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            ctx = browser.new_context(
                viewport={"width": 1280, "height": 900},
                device_scale_factor=1,
            )
            page = ctx.new_page()
            for path in BUTTON_HOVER_CONTRAST_PAGES:
                page.goto(f"{root}{path}?qa=btn-contrast", wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(150)
                for selector in button_selectors:
                    loc = page.locator(selector)
                    count = loc.count()
                    for index in range(min(count, 12)):
                        el = loc.nth(index)
                        if not el.is_visible():
                            continue
                        try:
                            el.hover(force=True, timeout=5000)
                            page.wait_for_timeout(80)
                        except Exception:
                            continue
                        ratio = el.evaluate(_CONTRAST_RATIO_JS)
                        label = f"btn-hover-contrast{path}{selector}[{index}]"
                        if ratio is not None and ratio < 4.5:
                            failures.append(f"{label}: contrast {ratio:.2f} < 4.5")
                cta = page.locator(
                    ".event-ticket__stretched-link > .event-ticket__cta"
                ).first
                if cta.count() > 0:
                    cta.hover(force=True, timeout=5000)
                    page.wait_for_timeout(80)
                    ratio = cta.evaluate(_CONTRAST_RATIO_JS)
                    label = f"btn-hover-contrast{path}event-ticket-cta"
                    if ratio is not None and ratio < 4.5:
                        failures.append(f"{label}: contrast {ratio:.2f} < 4.5")
                offer = page.locator("a.alt-offer-card").first
                if offer.count() > 0:
                    offer.hover(force=True, timeout=5000)
                    page.wait_for_timeout(80)
                    ratio = offer.evaluate(_CONTRAST_RATIO_JS)
                    if ratio is not None and ratio < 4.5:
                        failures.append(
                            f"btn-hover-contrast{path}alt-offer-card: contrast {ratio:.2f} < 4.5"
                        )
            ctx.close()
        finally:
            browser.close()
    return failures


def run_event_ticket_stretched_link_qa(base_url: str) -> list[str]:
    """Concert cards: article shell + stretched-link CTA (not wrapper anchor)."""
    failures: list[str] = []
    url = base_url.rstrip("/") + "/konserter/?qa=stretched-link"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(200)
            if page.locator("a.event-ticket").count() > 0:
                failures.append("event-ticket-stretched: card must not be an <a> wrapper")
            cards = page.locator("article.event-ticket")
            if cards.count() == 0:
                failures.append("event-ticket-stretched: missing article.event-ticket")
            for index in range(cards.count()):
                card = cards.nth(index)
                links = card.locator(".event-ticket__stretched-link")
                if links.count() != 1:
                    failures.append(
                        f"event-ticket-stretched: card {index} expected 1 stretched link, "
                        f"got {links.count()}"
                    )
                    continue
                href = links.first.get_attribute("href") or ""
                if not href.startswith("http"):
                    failures.append(f"event-ticket-stretched: card {index} missing ticket href")
                after = links.first.evaluate(
                    """(el) => {
                      const s = getComputedStyle(el, '::after');
                      return s.position === 'absolute' && s.inset === '0px';
                    }"""
                )
                if not after:
                    failures.append(f"event-ticket-stretched: card {index} missing ::after overlay")
                poster = card.locator(".event-ticket__poster")
                if poster.count() > 0:
                    poster_box = poster.bounding_box()
                    if poster_box:
                        cx = poster_box["x"] + poster_box["width"] / 2
                        cy = poster_box["y"] + poster_box["height"] / 2
                        try:
                            with ctx.expect_page(timeout=8000) as new_page_info:
                                page.mouse.click(cx, cy)
                            new_page = new_page_info.value
                            new_url = new_page.url
                            new_page.close()
                            if href and href not in new_url:
                                failures.append(
                                    f"event-ticket-stretched: card {index} poster click "
                                    f"opened {new_url}, expected {href}"
                                )
                        except Exception as exc:
                            failures.append(
                                f"event-ticket-stretched: card {index} poster click "
                                f"did not open ticket tab ({exc})"
                            )
            ctx.close()
        finally:
            browser.close()
    return failures


def run_alt_facts_icons_qa(base_url: str) -> list[str]:
    """Home USP strip: inline check/pin SVGs before each fact item."""
    failures: list[str] = []
    url = base_url.rstrip("/") + "/?qa=alt-facts"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(200)
            items = page.locator(".alt-facts .alt-facts__item")
            if items.count() != 3:
                failures.append(
                    f"alt-facts-icons: expected 3 fact items, got {items.count()}"
                )
            icons = page.locator(".alt-facts .alt-facts__icon")
            if icons.count() != 3:
                failures.append(
                    f"alt-facts-icons: expected 3 inline icons, got {icons.count()}"
                )
            for index in range(icons.count()):
                hidden = icons.nth(index).get_attribute("aria-hidden")
                if hidden != "true":
                    failures.append(
                        f"alt-facts-icons: icon {index} missing aria-hidden=true"
                    )
            metrics = page.evaluate(
                """() => {
                  const strip = document.querySelector('.alt-facts');
                  if (!strip) return { missing: true };
                  const itemEls = [...strip.querySelectorAll('.alt-facts__item')];
                  const checks = itemEls.filter((el) => el.querySelector("path[d*='5.5 12.5']"));
                  const pins = itemEls.filter((el) => el.querySelector('circle[cx="12"]'));
                  const aligned = itemEls.every((el) => {
                    const icon = el.querySelector('.alt-facts__icon');
                    if (!icon) return false;
                    const ir = icon.getBoundingClientRect();
                    const tr = el.getBoundingClientRect();
                    const cy = ir.top + ir.height / 2;
                    const ty = tr.top + tr.height / 2;
                    return Math.abs(cy - ty) < 2;
                  });
                  return {
                    missing: false,
                    checks: checks.length,
                    pins: pins.length,
                    aligned,
                  };
                }"""
            )
            if metrics.get("missing"):
                failures.append("alt-facts-icons: missing .alt-facts strip")
            elif metrics.get("checks") != 2:
                failures.append(
                    f"alt-facts-icons: expected 2 check icons, got {metrics.get('checks')}"
                )
            elif metrics.get("pins") != 1:
                failures.append(
                    f"alt-facts-icons: expected 1 pin icon, got {metrics.get('pins')}"
                )
            elif not metrics.get("aligned"):
                failures.append("alt-facts-icons: icons not vertically centered in items")
        finally:
            browser.close()
    return failures


def run_om_oss_member_cards_qa(base_url: str) -> list[str]:
    """Om oss: member grid width, typography, and section spacing."""
    failures: list[str] = []
    url = base_url.rstrip("/") + "/om-oss/?qa=members"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for width, label in ((390, "mobile"), (1280, "desktop")):
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(200)
                metrics = page.evaluate(
                    """() => {
                      const section = document.querySelector('.om-oss-members-section');
                      if (!section) {
                        return { missing: true };
                      }
                      const grid = section.querySelector('.member-compact-grid');
                      const wrap = section.querySelector('.wrap');
                      const lead = section.querySelector('h2 + .muted');
                      const h2 = section.querySelector('h2');
                      const card = section.querySelector('.member-compact-card');
                      const line = card?.querySelector('.member-compact-card__line');
                      const avatar = card?.querySelector('.member-compact-card__avatar');
                      const gr = grid?.getBoundingClientRect();
                      const wr = wrap?.getBoundingClientRect();
                      const wrapStyle = wrap ? getComputedStyle(wrap) : null;
                      const padL = wrapStyle ? parseFloat(wrapStyle.paddingLeft) : 0;
                      const padR = wrapStyle ? parseFloat(wrapStyle.paddingRight) : 0;
                      const h2r = h2?.getBoundingClientRect();
                      const lr = lead?.getBoundingClientRect();
                      const lineStyle = line ? getComputedStyle(line) : null;
                      const gridStyle = grid ? getComputedStyle(grid) : null;
                      const contentLeft = wr ? wr.left + padL : null;
                      const contentWidth = wr ? wr.width - padL - padR : null;
                      return {
                        missing: false,
                        gridLeft: gr?.left,
                        contentLeft,
                        gridWidth: gr?.width,
                        contentWidth,
                        gridColCount: gridStyle
                          ? gridStyle.gridTemplateColumns.trim().split(/\\s+/).length
                          : 0,
                        titleLeadGap: lr && h2r ? lr.top - h2r.bottom : null,
                        leadGridGap: gr && lr ? gr.top - lr.bottom : null,
                        lineMaxWidth: lineStyle?.maxWidth,
                        gridCols: gridStyle?.gridTemplateColumns,
                        avatarPx: avatar ? avatar.getBoundingClientRect().width : null,
                      };
                    }"""
                )
                if metrics.get("missing"):
                    failures.append(f"om-oss-members/{label}: missing members section")
                    continue
                if abs(metrics["gridLeft"] - metrics["contentLeft"]) > 2:
                    failures.append(
                        f"om-oss-members/{label}: grid not aligned with content column "
                        f"({metrics['gridLeft']} vs {metrics['contentLeft']})"
                    )
                if abs(metrics["gridWidth"] - metrics["contentWidth"]) > 4:
                    failures.append(
                        f"om-oss-members/{label}: grid not full content width "
                        f"({metrics['gridWidth']:.0f} vs {metrics['contentWidth']:.0f})"
                    )
                if metrics.get("lineMaxWidth") not in ("none", "100%"):
                    failures.append(
                        f"om-oss-members/{label}: bio max-width {metrics.get('lineMaxWidth')}"
                    )
                title_lead = metrics.get("titleLeadGap")
                lead_grid = metrics.get("leadGridGap")
                if title_lead is None or title_lead > 14:
                    failures.append(
                        f"om-oss-members/{label}: title–lead gap too large ({title_lead})"
                    )
                if lead_grid is None or lead_grid < 28:
                    failures.append(
                        f"om-oss-members/{label}: lead–grid gap too small ({lead_grid})"
                    )
                if label == "desktop" and metrics.get("gridColCount") != 2:
                    failures.append(
                        f"om-oss-members/desktop: expected 2-col grid, "
                        f"got {metrics.get('gridColCount')} tracks"
                    )
                    avatar_px = metrics.get("avatarPx") or 0
                    if avatar_px < 115:
                        failures.append(
                            f"om-oss-members/desktop: avatar too small ({avatar_px:.0f}px)"
                        )
                if label == "mobile" and (metrics.get("avatarPx") or 0) < 82:
                    failures.append(
                        f"om-oss-members/mobile: avatar too small ({metrics.get('avatarPx')})"
                    )
                page.close()
        finally:
            browser.close()
    return failures


def run_service_hero_ken_burns_qa(base_url: str) -> list[str]:
    """Ken Burns hero: enabled on Bröllop only (reusable hook for other services later)."""
    failures: list[str] = []
    checks = (
        ("/brollop/", True, "halvfjorton-03-hero"),
        ("/foretag/", False, "halvfjorton-01"),
        ("/mingel/", False, "halvfjorton-04"),
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for path, expect_ken, stem in checks:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(
                    base_url.rstrip("/") + path,
                    wait_until="domcontentloaded",
                    timeout=45000,
                )
                data = page.evaluate(
                    """() => {
                      const media = document.querySelector('.alt-service-hero__media');
                      const img = document.querySelector('.alt-service-hero__img');
                      const imgStyle = img ? getComputedStyle(img) : null;
                      return {
                        hasKen: media?.classList.contains('alt-service-hero__media--ken-burns'),
                        src: img?.getAttribute('src') || '',
                        anim: imgStyle?.animationName,
                      };
                    }"""
                )
                label = path.strip("/")
                if expect_ken:
                    if not data.get("hasKen"):
                        failures.append(f"ken-burns/{label}: missing ken-burns media class")
                    if stem not in (data.get("src") or ""):
                        failures.append(
                            f"ken-burns/{label}: expected hero stem {stem}, got {data.get('src')}"
                        )
                    if data.get("anim") in (None, "none"):
                        failures.append(f"ken-burns/{label}: hero image animation not active")
                else:
                    if data.get("hasKen"):
                        failures.append(f"ken-burns/{label}: ken-burns must be off")
                    if data.get("anim") not in (None, "none"):
                        failures.append(f"ken-burns/{label}: unexpected hero animation")
                page.close()
        finally:
            browser.close()
    return failures


def run_title_desc_cta_spacing_qa(base_url: str) -> list[str]:
    """Title→copy gap must be clearly smaller than copy→CTA (site-wide tokens)."""
    failures: list[str] = []
    min_ratio = 1.65
    checks = (
        (
            "/brollop/",
            ".alt-svc-chapter--festspelning .alt-svc-chapter__title",
            ".alt-svc-chapter--festspelning .alt-svc-chapter__body > p:first-of-type",
            ".alt-svc-chapter--festspelning .actions",
            "festspelning",
        ),
        (
            "/brollop/",
            ".alt-service-hero h1",
            ".alt-service-hero__dek",
            ".alt-service-hero__actions",
            "brollop-hero",
        ),
        (
            "/",
            ".alt-hero h1",
            ".alt-hero__lead",
            ".alt-hero__actions",
            "home-hero",
        ),
        (
            "/kontakt/",
            ".alt-contact-page__intro h1",
            ".contact-offert__lead",
            ".contact-offert__mail",
            "kontakt-offert",
        ),
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            for path, title_sel, desc_sel, cta_sel, label in checks:
                page.goto(
                    base_url.rstrip("/") + path,
                    wait_until="domcontentloaded",
                    timeout=45000,
                )
                metrics = page.evaluate(
                    """([titleSel, descSel, ctaSel]) => {
                      const title = document.querySelector(titleSel);
                      const desc = document.querySelector(descSel);
                      const cta = document.querySelector(ctaSel);
                      if (!title || !desc || !cta) {
                        return { missing: true };
                      }
                      const tr = title.getBoundingClientRect();
                      const dr = desc.getBoundingClientRect();
                      const ar = cta.getBoundingClientRect();
                      const titleDesc = Math.max(0, dr.top - tr.bottom);
                      const descCta = Math.max(0, ar.top - dr.bottom);
                      return { missing: false, titleDesc, descCta };
                    }""",
                    [title_sel, desc_sel, cta_sel],
                )
                if metrics.get("missing"):
                    failures.append(f"title-desc-cta/{label}: missing title, copy, or CTA node")
                    continue
                td = float(metrics["titleDesc"])
                dc = float(metrics["descCta"])
                if dc < 18:
                    failures.append(
                        f"title-desc-cta/{label}: desc→CTA gap too small ({dc:.1f}px)"
                    )
                if td > 0 and dc < td * min_ratio:
                    failures.append(
                        f"title-desc-cta/{label}: desc→CTA ({dc:.1f}px) must be ≥ "
                        f"{min_ratio}× title→desc ({td:.1f}px)"
                    )
            page.close()
        finally:
            browser.close()
    return failures


def run_service_hero_dek_layout_qa(base_url: str) -> list[str]:
    """Service heroes: dek width (50% desktop) and spacing above CTA."""
    failures: list[str] = []
    paths = ("/brollop/", "/foretag/", "/mingel/")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for width, label, expect_half in ((1280, "desktop", True), (390, "mobile", False)):
                for path in paths:
                    page = browser.new_page(viewport={"width": width, "height": 900})
                    page.goto(
                        base_url.rstrip("/") + path,
                        wait_until="domcontentloaded",
                        timeout=45000,
                    )
                    metrics = page.evaluate(
                        """() => {
                          const content = document.querySelector('.alt-service-hero__content');
                          const dek = document.querySelector('.alt-service-hero__dek');
                          const actions = document.querySelector('.alt-service-hero__actions');
                          if (!content || !dek || !actions) return { missing: true };
                          const cr = content.getBoundingClientRect();
                          const dr = dek.getBoundingClientRect();
                          const ar = actions.getBoundingClientRect();
                          const ds = getComputedStyle(dek);
                          const innerW = cr.width
                            - parseFloat(getComputedStyle(content).paddingLeft)
                            - parseFloat(getComputedStyle(content).paddingRight);
                          return {
                            missing: false,
                            innerW,
                            dekW: dr.width,
                            maxWidth: ds.maxWidth,
                            gap: ar.top - dr.bottom,
                          };
                        }"""
                    )
                    slug = path.strip("/")
                    if metrics.get("missing"):
                        failures.append(f"svc-hero-dek/{label}/{slug}: missing hero dek or CTA")
                        page.close()
                        continue
                    if expect_half:
                        if metrics["dekW"] > metrics["innerW"] * 0.52:
                            failures.append(
                                f"svc-hero-dek/desktop/{slug}: dek too wide "
                                f"({metrics['dekW']:.0f}px vs inner {metrics['innerW']:.0f}px)"
                            )
                        if metrics.get("gap", 0) < 26:
                            failures.append(
                                f"svc-hero-dek/desktop/{slug}: dek–CTA gap too small "
                                f"({metrics.get('gap')})"
                            )
                    elif metrics["dekW"] < metrics["innerW"] * 0.85:
                        failures.append(
                            f"svc-hero-dek/mobile/{slug}: dek should be full width "
                            f"({metrics['dekW']:.0f}px vs inner {metrics['innerW']:.0f}px)"
                        )
                    page.close()
        finally:
            browser.close()
    return failures


def run_service_split_layout_qa(base_url: str) -> list[str]:
    """Service pages: first split/grid block aligned to content column."""
    failures: list[str] = []
    checks = (
        ("/brollop/", ".alt-svc-chapter--festspelning .alt-svc-chapter__split"),
        ("/foretag/", "main .wrap.split"),
        ("/mingel/", "main .wrap.grid-2"),
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for path, selector in checks:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(
                    base_url.rstrip("/") + path + "?qa=svc-split",
                    wait_until="domcontentloaded",
                    timeout=45000,
                )
                page.evaluate(
                    "() => document.querySelectorAll('[data-reveal]').forEach((el) => el.classList.add('is-in'))"
                )
                metrics = page.evaluate(
                    f"""() => {{
                      const header = document.querySelector('.alt-header__inner');
                      const grid = document.querySelector('{selector}');
                      if (!header || !grid) return {{ missing: true }};
                      const pad = parseFloat(getComputedStyle(header).paddingLeft);
                      const contentLeft = header.getBoundingClientRect().left + pad;
                      const gr = grid.getBoundingClientRect();
                      const kids = [...grid.children].slice(0, 2);
                      const tops = kids.map((el) => el.getBoundingClientRect().top);
                      const gridStyle = getComputedStyle(grid);
                      const gridPad = parseFloat(gridStyle.paddingLeft);
                      return {{
                        missing: false,
                        contentLeft,
                        gridContentLeft: gr.left + gridPad,
                        gridWidth: gr.width,
                        maxWidth: gridStyle.maxWidth,
                        topDelta: tops.length === 2 ? Math.abs(tops[0] - tops[1]) : 99,
                        colCount: gridStyle.gridTemplateColumns.trim().split(/\\s+/).length,
                      }};
                    }}"""
                )
                label = path.strip("/")
                if metrics.get("missing"):
                    failures.append(f"svc-split/{label}: missing header or split grid")
                    continue
                if metrics.get("maxWidth") == "none":
                    failures.append(f"svc-split/{label}: split grid max-width is none")
                if abs(metrics["gridContentLeft"] - metrics["contentLeft"]) > 3:
                    failures.append(
                        f"svc-split/{label}: grid misaligned with nav column "
                        f"(grid {metrics['gridContentLeft']}, content {metrics['contentLeft']})"
                    )
                if metrics.get("topDelta", 99) > 2:
                    failures.append(
                        f"svc-split/{label}: columns not top-aligned (delta {metrics.get('topDelta')})"
                    )
                if metrics.get("colCount") != 2:
                    failures.append(
                        f"svc-split/{label}: expected 2 columns, got {metrics.get('colCount')}"
                    )
                page.close()
        finally:
            browser.close()
    return failures


def run_konserter_ticket_layout_qa(base_url: str) -> list[str]:
    """Desktop: concert cards align with H1 and fill the content column."""
    failures: list[str] = []
    url = base_url.rstrip("/") + "/konserter/?qa=ticket-layout"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for width in (1280, 1440):
                ctx = browser.new_context(
                    viewport={"width": width, "height": 900},
                    device_scale_factor=1,
                )
                page = ctx.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(200)
                label = f"konserter-ticket-layout/{width}"
                metrics = page.evaluate(
                    """() => {
                      const layout = document.querySelector('.alt-konserter-page');
                      const h1 = document.querySelector('.page-hero-copy h1');
                      const brand = document.querySelector('.alt-brand');
                      const tickets = [...document.querySelectorAll('.event-ticket')];
                      if (!layout || !h1 || !brand || tickets.length === 0) {
                        return { ok: false, reason: 'missing nodes' };
                      }
                      const layoutBox = layout.getBoundingClientRect();
                      const h1Left = h1.getBoundingClientRect().left;
                      const brandLeft = brand.getBoundingClientRect().left;
                      const contentLeft = layoutBox.left + parseFloat(getComputedStyle(layout).paddingLeft);
                      const contentRight = layoutBox.right - parseFloat(getComputedStyle(layout).paddingRight);
                      const ticketMetrics = tickets.map((el) => {
                        const r = el.getBoundingClientRect();
                        return { left: r.left, right: r.right, width: r.width };
                      });
                      return {
                        ok: true,
                        h1Left,
                        brandLeft,
                        contentLeft,
                        contentRight,
                        contentWidth: contentRight - contentLeft,
                        ticketMetrics,
                      };
                    }"""
                )
                if not metrics.get("ok"):
                    failures.append(f"{label}: {metrics.get('reason', 'layout check failed')}")
                    ctx.close()
                    continue
                if abs(metrics["h1Left"] - metrics["brandLeft"]) > 2:
                    failures.append(
                        f"{label}: H1 left {metrics['h1Left']} != brand left {metrics['brandLeft']}"
                    )
                for index, ticket in enumerate(metrics["ticketMetrics"]):
                    if abs(ticket["left"] - metrics["contentLeft"]) > 2:
                        failures.append(
                            f"{label}: ticket {index} left {ticket['left']} "
                            f"!= content left {metrics['contentLeft']}"
                        )
                    if abs(ticket["right"] - metrics["contentRight"]) > 2:
                        failures.append(
                            f"{label}: ticket {index} right {ticket['right']} "
                            f"!= content right {metrics['contentRight']}"
                        )
                    if abs(ticket["width"] - metrics["contentWidth"]) > 3:
                        failures.append(
                            f"{label}: ticket {index} width {ticket['width']} "
                            f"!= content width {metrics['contentWidth']}"
                        )
                ctx.close()
        finally:
            browser.close()
    return failures


def run_faq_collapsed_row_spacing_qa(base_url: str) -> list[str]:
    """All collapsed FAQ rows: equal item height and tight row rhythm (no answer spill)."""
    failures: list[str] = []
    paths = FAQ_COLUMN_STABILITY_PATHS
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            for path in paths:
                page.goto(
                    base_url.rstrip("/") + path + "?qa=faq-collapsed",
                    wait_until="domcontentloaded",
                    timeout=45000,
                )
                page.wait_for_timeout(150)
                metrics = page.evaluate(
                    """() => {
                      const items = [...document.querySelectorAll('[data-faq] .alt-faq__item')];
                      if (!items.length) return { missing: true };
                      const open = items.filter((el) => el.open);
                      if (open.length) {
                        items.forEach((el) => { el.open = false; });
                      }
                      const rows = items.map((el) => {
                        const er = el.getBoundingClientRect();
                        const sum = el.querySelector('summary');
                        const ans = el.querySelector('.alt-faq__answer');
                        const sr = sum.getBoundingClientRect();
                        const ar = ans ? ans.getBoundingClientRect() : null;
                        return {
                          top: er.top,
                          bottom: er.bottom,
                          height: er.height,
                          sumH: sr.height,
                          spill: ar ? Math.max(0, ar.bottom - er.bottom) : 0,
                        };
                      });
                      const heights = rows.map((r) => r.height);
                      const minH = Math.min(...heights);
                      const maxH = Math.max(...heights);
                      const col0 = rows.filter((_, i) => i % 2 === 0);
                      const pitches = [];
                      for (let i = 1; i < col0.length; i++) {
                        pitches.push(col0[i].top - col0[i - 1].top);
                      }
                      const rowGaps = [];
                      for (let i = 0; i < rows.length - 2; i += 2) {
                        rowGaps.push(rows[i + 2].top - rows[i].bottom);
                      }
                      return {
                        missing: false,
                        count: items.length,
                        minH,
                        maxH,
                        pitches,
                        rowGaps,
                        maxSpill: Math.max(...rows.map((r) => r.spill)),
                      };
                    }"""
                )
                slug = path.strip("/") or "home"
                if metrics.get("missing"):
                    failures.append(f"faq-collapsed/{slug}: missing FAQ list")
                    continue
                if metrics["maxH"] - metrics["minH"] > 2:
                    failures.append(
                        f"faq-collapsed/{slug}: item heights differ "
                        f"({metrics['minH']:.1f}–{metrics['maxH']:.1f}px)"
                    )
                if metrics.get("maxSpill", 0) > 1:
                    failures.append(
                        f"faq-collapsed/{slug}: answer spills below item "
                        f"({metrics['maxSpill']:.1f}px)"
                    )
                pitches = metrics.get("pitches") or []
                if pitches:
                    spread = max(pitches) - min(pitches)
                    if spread > 2:
                        failures.append(
                            f"faq-collapsed/{slug}: uneven row pitch in column "
                            f"({min(pitches):.1f}–{max(pitches):.1f}px)"
                        )
                for gap in metrics.get("rowGaps") or []:
                    if gap > 4:
                        failures.append(
                            f"faq-collapsed/{slug}: extra gap between rows ({gap:.1f}px)"
                        )
            page.close()
        finally:
            browser.close()
    return failures


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
        failures.extend(run_title_desc_cta_spacing_qa(base))
        failures.extend(run_faq_collapsed_row_spacing_qa(base))
        if not args.quick:
            failures.extend(run_desktop_tjanster_dropdown_qa(base))
            failures.extend(run_konserter_ticket_layout_qa(base))
            failures.extend(run_event_ticket_stretched_link_qa(base))
            failures.extend(run_button_hover_contrast_qa(base))
            failures.extend(run_alt_facts_icons_qa(base))
            failures.extend(run_om_oss_member_cards_qa(base))
            failures.extend(run_service_split_layout_qa(base))
            failures.extend(run_service_hero_ken_burns_qa(base))
            failures.extend(run_service_hero_dek_layout_qa(base))
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
