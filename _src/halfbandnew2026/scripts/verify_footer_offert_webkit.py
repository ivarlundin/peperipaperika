#!/usr/bin/env python3
"""WebKit + Chromium: mobile footer layout and home offert band."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = Path("/opt/cursor/artifacts/screenshots")
BASE_URL = "http://127.0.0.1:8768/testing/halfbandnew2026/"
MOBILE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 900}


def assert_footer_mobile(page, label: str) -> None:
    page.evaluate("() => document.querySelector('.site-footer').scrollIntoView()")
    page.wait_for_timeout(250)
    data = page.evaluate(
        """() => {
          const inner = document.querySelector('.site-footer__inner');
          const ul = document.querySelector('.site-footer__links');
          const link = document.querySelector('.site-footer__links a');
          const social = document.querySelector('.site-footer__social');
          const cta = document.querySelector('.site-footer__cta');
          const aside = document.querySelector('.site-footer__aside');
          const title = document.querySelector('.site-footer__title');
          const org = document.querySelector('.site-footer__legal-org');
          const copy = document.querySelector('.site-footer__legal-line');
          const legal = document.querySelector('.site-footer__legal');
          const hero = document.querySelector('.alt-hero__content') || document.querySelector('.alt-header__inner');
          const padInner = inner ? parseFloat(getComputedStyle(inner).paddingLeft) : 0;
          const padHero = hero ? parseFloat(getComputedStyle(hero).paddingLeft) : 0;
          const legalStyle = legal ? getComputedStyle(legal) : null;
          const copyY = copy ? copy.getBoundingClientRect().top : 0;
          const orgY = org ? org.getBoundingClientRect().top : 0;
          return {
            listStyle: ul ? getComputedStyle(ul).listStyleType : '',
            linkDecoration: link ? getComputedStyle(link).textDecorationLine : '',
            socialDecoration: social ? getComputedStyle(social).textDecorationLine : '',
            asideDirection: getComputedStyle(document.querySelector('.site-footer__aside')).flexDirection,
            socialY: social ? social.getBoundingClientRect().top : 0,
            ctaY: cta ? cta.getBoundingClientRect().top : 0,
            ctaWidth: cta ? cta.getBoundingClientRect().width : 0,
            asideWidth: aside ? aside.getBoundingClientRect().width : 0,
            titleText: title ? title.textContent.trim() : '',
            titleFont: title ? getComputedStyle(title).fontFamily : '',
            orgTag: org ? org.tagName : '',
            orgDecoration: org ? getComputedStyle(org).textDecorationLine : '',
            legalJustify: legalStyle ? legalStyle.justifyContent : '',
            legalSameRow: Math.abs(copyY - orgY) < 6,
            padInner,
            padHero,
          };
        }"""
    )
    assert data["listStyle"] == "none", f"{label}: footer list should be unstyled, got {data['listStyle']}"
    assert data["linkDecoration"] == "none", f"{label}: footer link underline {data['linkDecoration']}"
    assert data["socialDecoration"] == "none", f"{label}: social underline {data['socialDecoration']}"
    assert data["asideDirection"] == "column", f"{label}: aside flex {data['asideDirection']}"
    assert data["socialY"] < data["ctaY"] - 4, f"{label}: Instagram should sit above CTA"
    assert data["ctaWidth"] >= data["asideWidth"] * 0.92, f"{label}: CTA not full width"
    assert data["titleText"] == "Halv Fjorton", f"{label}: footer title missing"
    assert "Outfit" in data["titleFont"], f"{label}: title should use Outfit, got {data['titleFont']}"
    assert data["orgTag"] == "SPAN", f"{label}: org.nr should be plain text, got {data['orgTag']}"
    assert data["orgDecoration"] == "none", f"{label}: org.nr decorated {data['orgDecoration']}"
    assert data["legalJustify"] == "space-between", (
        f"{label}: legal row should use space-between, got {data['legalJustify']}"
    )
    assert data["legalSameRow"], f"{label}: copyright and org.nr should share one row"
    assert abs(data["padInner"] - data["padHero"]) < 6, (
        f"{label}: footer padding {data['padInner']} != content {data['padHero']}"
    )


def assert_footer_desktop(page, label: str) -> None:
    page.set_viewport_size(DESKTOP)
    page.reload(wait_until="networkidle")
    page.evaluate("() => document.querySelector('.site-footer').scrollIntoView()")
    page.wait_for_timeout(200)
    cols = page.evaluate(
        """() => getComputedStyle(document.querySelector('.site-footer__grid')).gridTemplateColumns"""
    )
    assert cols.count(" ") >= 2, f"{label}: expected 3-column footer grid, got {cols}"


def assert_offert_mobile(page, label: str) -> None:
    page.set_viewport_size(MOBILE)
    page.reload(wait_until="networkidle")
    page.locator("#offert").scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    offert = page.evaluate(
        """() => {
          const section = document.querySelector('#offert');
          const bg = section ? getComputedStyle(section).backgroundColor : '';
          const grid = document.querySelector('#offert .contact-offert__grid');
          const cols = grid ? getComputedStyle(grid).gridTemplateColumns : '';
          return { bg, cols };
        }"""
    )
    assert "1fr" in offert["cols"] or offert["cols"].count(" ") == 0, (
        f"{label}: offert should be single column on mobile, got {offert['cols']}"
    )
    assert offert["bg"] not in ("", "rgba(0, 0, 0, 0)", "transparent"), (
        f"{label}: offert section should have mobile surface background, got {offert['bg']}"
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8768", "--bind", "127.0.0.1"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.35)
    try:
        with sync_playwright() as p:
            browser = p.webkit.launch()
            mobile_ctx = browser.new_context(
                viewport=MOBILE,
                device_scale_factor=3,
                is_mobile=True,
                has_touch=True,
            )
            page = mobile_ctx.new_page()
            page.goto(BASE_URL, wait_until="networkidle")
            assert_footer_mobile(page, "webkit-mobile")
            page.screenshot(path=str(OUT / "footer-mobile-webkit.png"), full_page=False)
            assert_offert_mobile(page, "webkit-offert")
            page.screenshot(path=str(OUT / "offert-mobile-webkit.png"), full_page=False)
            assert_footer_desktop(page, "webkit-desktop")
            page.screenshot(path=str(OUT / "footer-desktop-webkit.png"), full_page=False)
            mobile_ctx.close()
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print("OK: WebKit footer (mobile + desktop) and mobile offert band")
    return 0


if __name__ == "__main__":
    sys.exit(main())
