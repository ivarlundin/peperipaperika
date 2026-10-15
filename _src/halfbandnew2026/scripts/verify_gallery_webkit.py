#!/usr/bin/env python3
"""Playwright WebKit iPhone + desktop: home gallery bento grid."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
BASE_URL = "http://127.0.0.1:8765/testing/halfbandnew2026/"


def main() -> int:
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.35)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_context(
                viewport={"width": 390, "height": 844},
                device_scale_factor=3,
                is_mobile=True,
                has_touch=True,
            ).new_page()
            page.goto(BASE_URL, wait_until="networkidle")
            page.locator(".alt-gallery").scroll_into_view_if_needed()
            page.evaluate(
                """() => {
                  document.querySelectorAll('.alt-gallery__card, .alt-gallery__quote-tile')
                    .forEach((el) => el.classList.add('is-in'));
                }"""
            )
            page.wait_for_timeout(400)

            card_count = page.locator(".alt-gallery__drift-layer .alt-gallery__card").count()
            assert card_count == 6, f"expected 6 bento tiles, got {card_count}"

            mobile_bento_h = page.evaluate(
                """() => {
                  const bento = document.querySelector('.alt-gallery__bento');
                  return bento ? bento.getBoundingClientRect().height : 0;
                }"""
            )
            assert mobile_bento_h <= page.viewport_size["height"] * 1.02
            assert page.locator(".alt-gallery__quote-tile").count() == 1

            bounds = page.evaluate(
                """() => {
                  const inner = document.querySelector('.alt-gallery__inner');
                  const bento = document.querySelector('.alt-gallery__bento');
                  const ir = inner.getBoundingClientRect();
                  const br = bento.getBoundingClientRect();
                  const padL = parseFloat(getComputedStyle(inner).paddingLeft) || 0;
                  const padR = parseFloat(getComputedStyle(inner).paddingRight) || 0;
                  return {
                    contentLeft: ir.left + padL,
                    contentRight: ir.right - padR,
                    bLeft: br.left,
                    bRight: br.right,
                  };
                }"""
            )
            assert abs(bounds["bLeft"] - bounds["contentLeft"]) < 2
            assert abs(bounds["bRight"] - bounds["contentRight"]) < 3

            desktop = browser.new_context(viewport={"width": 1280, "height": 900}).new_page()
            desktop.goto(BASE_URL, wait_until="networkidle")
            desktop.locator(".alt-gallery").scroll_into_view_if_needed()
            desktop.evaluate(
                """() => {
                  document.querySelectorAll('.alt-gallery__card, .alt-gallery__quote-tile')
                    .forEach((el) => el.classList.add('is-in'));
                }"""
            )
            desktop.wait_for_timeout(300)

            metrics = desktop.evaluate(
                """() => {
                  const inner = document.querySelector('.alt-gallery__inner');
                  const bento = document.querySelector('.alt-gallery__bento');
                  const header = document.querySelector('.alt-header__inner');
                  const ir = inner.getBoundingClientRect();
                  const br = bento.getBoundingClientRect();
                  const hr = header.getBoundingClientRect();
                  const padL = parseFloat(getComputedStyle(inner).paddingLeft) || 0;
                  const padR = parseFloat(getComputedStyle(inner).paddingRight) || 0;
                  const contentLeft = ir.left + padL;
                  const contentRight = ir.right - padR;
                  const vh = window.innerHeight;
                  return {
                    bentoH: br.height,
                    vh,
                    insideGrid:
                      br.left >= contentLeft - 1 &&
                      br.right <= contentRight + 1 &&
                      br.left >= hr.left + padL - 1 &&
                      br.right <= hr.right - padR + 1,
                    cols: getComputedStyle(bento).gridTemplateColumns.split(' ').length,
                    feature: document.querySelector('.alt-gallery__card--feature')?.getBoundingClientRect(),
                    wide: document.querySelector('.alt-gallery__card--wide-top')?.getBoundingClientRect(),
                    sm: document.querySelector('.alt-gallery__card--sm')?.getBoundingClientRect(),
                    kenAnim: getComputedStyle(
                      document.querySelector('.alt-gallery__card--feature .alt-gallery__ken')
                    ).animationName,
                    featFilter: getComputedStyle(
                      document.querySelector('.alt-gallery__card--feature .alt-gallery__ken')
                    ).filter,
                    tall: document.querySelector('.alt-gallery__card--tall')?.getBoundingClientRect(),
                  };
                }"""
            )
            assert metrics["insideGrid"], "bento must stay inside site content grid"
            assert metrics["bentoH"] >= metrics["vh"] * 0.68, (
                f"bento too short: {metrics['bentoH']} vs vh {metrics['vh']}"
            )
            assert metrics["cols"] == 6, f"desktop bento should use 6 columns, got {metrics['cols']}"
            assert metrics["kenAnim"] in (None, "none"), "gallery must not use CSS Ken Burns"
            assert "grayscale" not in (metrics.get("featFilter") or ""), "feature tile must be in color"
            tall = metrics.get("tall")
            if tall and tall["height"] > 0:
                assert tall["width"] / tall["height"] >= 0.42, "keyboard tile aspect too extreme"
            feat = metrics["feature"]
            wide = metrics["wide"]
            sm = metrics["sm"]
            wide_bottom = desktop.evaluate(
                """() => document.querySelector('.alt-gallery__card--wide-bottom')?.getBoundingClientRect()"""
            )
            assert feat and wide and feat["width"] > wide["width"] * 1.05
            tall_kb = desktop.evaluate(
                """() => document.querySelector('.alt-gallery__card--tall')?.getBoundingClientRect()"""
            )
            assert tall_kb and sm and tall_kb["width"] > sm["width"] * 1.35
            quote_top = desktop.evaluate(
                """() => Math.round(document.querySelector('.alt-gallery__quote-tile')?.getBoundingClientRect().top || 0)"""
            )
            wb_top = desktop.evaluate(
                """() => Math.round(document.querySelector('.alt-gallery__card--wide-bottom')?.getBoundingClientRect().top || 0)"""
            )
            wt_top = desktop.evaluate(
                """() => Math.round(document.querySelector('.alt-gallery__card--wide-top')?.getBoundingClientRect().top || 0)"""
            )
            row2_delta = min(abs(quote_top - wb_top), abs(quote_top - wt_top))
            assert row2_delta <= 18, "quote must share row 2 with photo tiles"

            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)

    print("OK: home gallery bento (mobile 2-col + desktop grid)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
