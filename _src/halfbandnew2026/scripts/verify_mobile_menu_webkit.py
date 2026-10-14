#!/usr/bin/env python3
"""Playwright WebKit iPhone: mobile menu layout, motion, logo scale, and Tjänster dropdown."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = Path("/opt/cursor/artifacts/screenshots")
SCROLL_Y = 1500
VIEWPORT = {"width": 390, "height": 844}
BASE_URL = "http://127.0.0.1:8765/testing/halfbandnew2026/"
MENU_MOTION_MS = 400
LOGO_LARGE_MIN = 100
LOGO_NORMAL_MAX = 80


def header_logo_width(page) -> float:
    return float(
        page.locator(".alt-header .brand-mark").evaluate(
            "el => el.getBoundingClientRect().width"
        )
    )


def assert_menu_fullscreen(page, label: str) -> None:
    menu = page.locator("[data-mobile-menu]")
    assert menu.evaluate("el => el.classList.contains('mobile-menu--open')"), (
        f"{label}: menu should have open class"
    )
    box = menu.bounding_box()
    assert box, f"{label}: menu has no bounding box"
    vp = page.viewport_size
    assert vp, f"{label}: no viewport"
    assert abs(box["height"] - vp["height"]) < 8, (
        f"{label}: menu height {box['height']} != viewport {vp['height']}"
    )
    assert box["y"] < 5, f"{label}: menu y={box['y']} not at top"
    kontakt = page.locator(".mobile-menu__list a", has_text="Kontakt")
    assert kontakt.is_visible(), f"{label}: Kontakt link not visible"
    cta = page.locator(".mobile-menu__cta")
    assert cta.is_visible(), f"{label}: CTA not visible"
    in_menu = cta.evaluate("el => !!el.closest('[data-mobile-menu]')")
    assert in_menu, f"{label}: CTA not inside mobile menu"
    header_cta = page.locator(".alt-header .alt-nav__cta-desktop")
    assert not header_cta.is_visible(), f"{label}: desktop CTA visible in header"


def assert_single_scaled_header_logo(page, label: str, expect_large: bool) -> None:
    assert page.locator(".mobile-menu__brand--feature").count() == 0, (
        f"{label}: duplicate menu feature logo should be removed"
    )
    assert page.locator(".mobile-menu__brand--bar").count() == 0, (
        f"{label}: bar logo markup should be removed"
    )
    assert page.locator(".alt-header .brand-mark").count() == 1, (
        f"{label}: expected one header brand mark"
    )
    header_vis = page.evaluate(
        """() => {
          const el = document.querySelector('.alt-header .alt-brand');
          return el ? getComputedStyle(el).visibility : '';
        }"""
    )
    assert header_vis != "hidden", (
        f"{label}: header brand should stay visible, got {header_vis}"
    )
    width = header_logo_width(page)
    if expect_large:
        assert width >= LOGO_LARGE_MIN, (
            f"{label}: header logo should be scaled large ({width}px)"
        )
    else:
        assert width <= LOGO_NORMAL_MAX, (
            f"{label}: header logo should be normal size ({width}px)"
        )


def assert_menu_opens_with_motion(page, label: str, expect_large_logo: bool) -> None:
    page.locator("[data-nav-toggle]").click()
    mid_opacity = None
    for _ in range(12):
        page.wait_for_timeout(35)
        mid_opacity = float(
            page.locator("[data-mobile-menu]").evaluate(
                "el => parseFloat(getComputedStyle(el).opacity)"
            )
        )
        if 0.05 < mid_opacity < 0.98:
            break
    assert mid_opacity is not None and 0.05 < mid_opacity < 0.98, (
        f"{label}: menu opacity never entered mid-open range, last={mid_opacity}"
    )
    page.wait_for_timeout(MENU_MOTION_MS)
    assert_menu_fullscreen(page, label)
    assert_single_scaled_header_logo(page, label, expect_large_logo)


def assert_home_hero_logo_at_top(page, label: str) -> None:
    assert page.evaluate("window.scrollY") < 40, f"{label}: expected near top scroll"
    assert page.evaluate(
        "document.body.classList.contains('alt-logo-hero-large')"
    ), f"{label}: body should have alt-logo-hero-large at top"
    assert_single_scaled_header_logo(page, label, True)


def wait_for_header_logo_normal(page, label: str) -> None:
    for _ in range(24):
        width = header_logo_width(page)
        if width <= LOGO_NORMAL_MAX:
            return
        page.wait_for_timeout(40)
    assert_single_scaled_header_logo(page, label, False)


def assert_home_hero_logo_scrolled(page, label: str) -> None:
    assert not page.evaluate(
        "document.body.classList.contains('nav-open')"
    ), f"{label}: menu should be closed"
    assert not page.evaluate(
        "document.body.classList.contains('alt-logo-hero-large')"
    ), f"{label}: hero large class should be off when scrolled"
    wait_for_header_logo_normal(page, label)


def assert_tjanster_dropdown_animates(page, label: str) -> None:
    trigger = page.locator(
        "[data-mobile-menu] [data-nav-dropdown-trigger]", has_text="Tjänster"
    )
    submenu = page.locator("[data-mobile-menu] .mobile-menu__submenu").first
    trigger.click()
    page.wait_for_timeout(50)
    h_early = submenu.evaluate("el => el.getBoundingClientRect().height")
    page.wait_for_timeout(380)
    h_late = submenu.evaluate("el => el.getBoundingClientRect().height")
    assert h_late > h_early + 24, (
        f"{label}: submenu should grow (early={h_early}, late={h_late})"
    )
    chevron_rot = page.evaluate(
        """() => {
          const el = document.querySelector('[data-mobile-menu] .nav-dropdown__chevron');
          if (!el) return '';
          const t = getComputedStyle(el).transform;
          return t && t !== 'none' ? t : '';
        }"""
    )
    assert chevron_rot, f"{label}: chevron should be rotated when open"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

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
            context = browser.new_context(
                viewport=VIEWPORT,
                device_scale_factor=3,
                is_mobile=True,
                has_touch=True,
                reduced_motion="no-preference",
            )
            page = context.new_page()
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(120)

            assert_home_hero_logo_at_top(page, "home-top-closed")

            assert_menu_opens_with_motion(page, "scrollY=0", True)
            assert_tjanster_dropdown_animates(page, "scrollY=0")
            page.screenshot(path=str(OUT / "mobile-menu-webkit-top.png"), full_page=False)

            page.locator("[data-nav-close]").click()
            page.wait_for_timeout(MENU_MOTION_MS + 80)
            assert_home_hero_logo_at_top(page, "home-top-after-close")

            page.evaluate(f"window.scrollTo(0, {SCROLL_Y})")
            page.wait_for_timeout(80)
            assert page.evaluate("window.scrollY") >= SCROLL_Y - 20
            assert_home_hero_logo_scrolled(page, "home-scrolled-closed")

            assert_menu_opens_with_motion(page, f"scrollY={SCROLL_Y}", True)
            page.screenshot(
                path=str(OUT / "mobile-menu-webkit-scrolled.png"), full_page=False
            )

            page.locator("[data-nav-close]").click()
            page.wait_for_timeout(MENU_MOTION_MS + 80)
            assert_home_hero_logo_scrolled(page, "home-scrolled-after-close")

            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)

    print("OK: WebKit iPhone mobile menu motion, header logo scale, and dropdown")
    return 0


if __name__ == "__main__":
    sys.exit(main())
