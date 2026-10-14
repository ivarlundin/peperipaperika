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
LOGO_MENU_LARGE_MIN = 100
LOGO_HERO_LARGE_MIN = 74
LOGO_HERO_LARGE_MAX = 92
LOGO_NORMAL_MAX = 80
ALT_BG_RGB = "rgb(10, 10, 11)"


def header_logo_width(page) -> float:
    return float(
        page.locator(".alt-header .brand-mark").evaluate(
            "el => el.getBoundingClientRect().width"
        )
    )


def assert_logo_size(page, label: str, mode: str) -> None:
    width = header_logo_width(page)
    if mode == "menu":
        assert width >= LOGO_MENU_LARGE_MIN, (
            f"{label}: menu logo should be large ({width}px)"
        )
    elif mode == "hero":
        assert LOGO_HERO_LARGE_MIN <= width <= LOGO_HERO_LARGE_MAX, (
            f"{label}: hero logo should be ~25% smaller than menu ({width}px)"
        )
    else:
        assert width <= LOGO_NORMAL_MAX, (
            f"{label}: header logo should be normal size ({width}px)"
        )


def assert_solid_menu_surface(page, label: str) -> None:
    data = page.evaluate(
        """() => {
          const menu = document.querySelector('[data-mobile-menu]');
          const header = document.querySelector('.alt-header');
          const menuStyle = menu ? getComputedStyle(menu) : null;
          const headerStyle = header ? getComputedStyle(header) : null;
          return {
            menuBg: menuStyle ? menuStyle.backgroundColor : '',
            menuBackdrop: menuStyle ? menuStyle.backdropFilter : '',
            headerBg: headerStyle ? headerStyle.backgroundColor : '',
            headerBackdrop: headerStyle ? headerStyle.backdropFilter : '',
          };
        }"""
    )
    assert data["menuBg"] == ALT_BG_RGB, f"{label}: menu bg {data['menuBg']}"
    assert data["menuBackdrop"] in ("none", ""), (
        f"{label}: menu backdrop {data['menuBackdrop']}"
    )
    assert data["headerBg"] == ALT_BG_RGB, f"{label}: header bg {data['headerBg']}"
    assert data["headerBackdrop"] in ("none", ""), (
        f"{label}: header backdrop {data['headerBackdrop']}"
    )


def assert_header_border_hidden_when_menu_open(page, label: str) -> None:
    styles = page.evaluate(
        """() => {
          const el = document.querySelector('.alt-header');
          if (!el) return null;
          const s = getComputedStyle(el);
          return {
            borderWidth: s.borderBottomWidth,
            borderColor: s.borderBottomColor,
            boxShadow: s.boxShadow,
          };
        }"""
    )
    assert styles, f"{label}: header missing"
    assert styles["borderWidth"] in ("0px", "0"), (
        f"{label}: header border width {styles['borderWidth']}"
    )
    assert styles["boxShadow"] in ("none", ""), (
        f"{label}: header box-shadow {styles['boxShadow']}"
    )


def assert_header_close_visible(page, label: str) -> None:
    close = page.locator(".alt-header__menu-close")
    assert close.count() == 1, f"{label}: expected one header close control"
    assert close.is_visible(), f"{label}: header close should be visible"
    page.evaluate(
        '() => document.querySelector(".alt-header")?.classList.add("is-solid")'
    )
    assert close.is_visible(), f"{label}: close hidden under solid header"
    hit = page.evaluate(
        """() => {
          const el = document.querySelector('.alt-header__menu-close');
          if (!el) return false;
          const r = el.getBoundingClientRect();
          const x = r.left + r.width / 2;
          const y = r.top + r.height / 2;
          const top = document.elementFromPoint(x, y);
          return top === el || el.contains(top);
        }"""
    )
    assert hit, f"{label}: close button is covered at scroll"
    box = close.bounding_box()
    vp = page.viewport_size
    assert box and vp, f"{label}: close box missing"
    assert box["x"] + box["width"] >= vp["width"] - 56, (
        f"{label}: close should stay top-right (x={box['x']})"
    )


def assert_menu_cta_full_width(page, label: str) -> None:
    vp = page.viewport_size
    assert vp, f"{label}: no viewport"
    cta_w = float(page.locator(".mobile-menu__cta").evaluate(
        "el => el.getBoundingClientRect().width"
    ))
    foot = page.locator(".mobile-menu__foot")
    foot_styles = foot.evaluate(
        """el => {
          const r = el.getBoundingClientRect();
          const s = getComputedStyle(el);
          return { width: r.width, padL: parseFloat(s.paddingLeft), padR: parseFloat(s.paddingRight) };
        }"""
    )
    inner_w = foot_styles["width"] - foot_styles["padL"] - foot_styles["padR"]
    assert cta_w >= inner_w * 0.98, (
        f"{label}: CTA width {cta_w} should fill menu foot inner {inner_w}"
    )


def assert_logo_in_viewport(page, label: str) -> None:
    box = page.locator(".alt-header .brand-mark").bounding_box()
    assert box, f"{label}: logo missing box"
    assert box["width"] >= LOGO_MENU_LARGE_MIN, f"{label}: logo too small ({box['width']}px)"
    assert -8 < box["y"] < 180, f"{label}: logo top {box['y']} outside viewport band"
    assert box["x"] >= -4, f"{label}: logo left {box['x']} clipped"


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


def assert_single_scaled_header_logo(page, label: str) -> None:
    assert page.locator(".mobile-menu__brand--feature").count() == 0, (
        f"{label}: duplicate menu feature logo should be removed"
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


def open_menu(page) -> None:
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
        f"menu opacity never entered mid-open range, last={mid_opacity}"
    )
    page.wait_for_timeout(MENU_MOTION_MS)


def assert_menu_opens_with_motion(page, label: str) -> None:
    open_menu(page)
    assert_menu_fullscreen(page, label)
    assert_solid_menu_surface(page, label)
    assert_header_border_hidden_when_menu_open(page, label)
    assert_single_scaled_header_logo(page, label)
    assert_logo_size(page, label, "menu")
    assert_logo_in_viewport(page, label)
    assert_header_close_visible(page, label)
    assert_menu_cta_full_width(page, label)


def wait_for_hero_logo_size(page, label: str) -> None:
    for _ in range(24):
        width = header_logo_width(page)
        if LOGO_HERO_LARGE_MIN <= width <= LOGO_HERO_LARGE_MAX:
            return
        page.wait_for_timeout(40)
    assert_logo_size(page, label, "hero")


def assert_home_hero_logo_at_top(page, label: str) -> None:
    assert page.evaluate("window.scrollY") < 40, f"{label}: expected near top scroll"
    assert page.evaluate(
        "document.body.classList.contains('alt-logo-hero-large')"
    ), f"{label}: body should have alt-logo-hero-large at top"
    assert_single_scaled_header_logo(page, label)
    wait_for_hero_logo_size(page, label)


def wait_for_header_logo_normal(page, label: str) -> None:
    for _ in range(24):
        width = header_logo_width(page)
        if width <= LOGO_NORMAL_MAX:
            return
        page.wait_for_timeout(40)
    assert_logo_size(page, label, "normal")


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


def assert_close_at_scroll_positions(page) -> None:
    positions = (
        ("top", 0),
        ("mid", SCROLL_Y),
        ("bottom", None),
    )
    for name, y in positions:
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(100)
        if y is None:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        else:
            page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(120)
        assert_menu_opens_with_motion(page, f"menu-open-{name}")
        page.screenshot(
            path=str(OUT / f"mobile-menu-open-iphone-{name}.png"),
            full_page=False,
        )
        page.locator("[data-nav-close]").click()
        page.wait_for_timeout(MENU_MOTION_MS + 80)


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

            assert_menu_opens_with_motion(page, "scrollY=0")
            assert_tjanster_dropdown_animates(page, "scrollY=0")
            page.screenshot(path=str(OUT / "mobile-menu-open-iphone.png"), full_page=False)

            page.locator("[data-nav-close]").click()
            page.wait_for_timeout(MENU_MOTION_MS + 80)
            assert_home_hero_logo_at_top(page, "home-top-after-close")

            page.evaluate(f"window.scrollTo(0, {SCROLL_Y})")
            page.wait_for_timeout(80)
            assert page.evaluate("window.scrollY") >= SCROLL_Y - 20
            assert_home_hero_logo_scrolled(page, "home-scrolled-closed")

            assert_menu_opens_with_motion(page, f"scrollY={SCROLL_Y}")
            page.screenshot(
                path=str(OUT / "mobile-menu-webkit-scrolled.png"), full_page=False
            )

            page.locator("[data-nav-close]").click()
            page.wait_for_timeout(MENU_MOTION_MS + 80)
            assert_home_hero_logo_scrolled(page, "home-scrolled-after-close")

            assert_close_at_scroll_positions(page)

            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)

    print("OK: WebKit iPhone mobile menu motion, header logo scale, and dropdown")
    return 0


if __name__ == "__main__":
    sys.exit(main())
