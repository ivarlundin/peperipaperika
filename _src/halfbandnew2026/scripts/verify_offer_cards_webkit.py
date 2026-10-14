#!/usr/bin/env python3
"""WebKit iPhone: home offer card image ratio and flat mobile rows; inner page media frame."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = Path("/opt/cursor/artifacts/screenshots")
VIEWPORT = {"width": 390, "height": 844}
BASE = "http://127.0.0.1:8765/testing/halfbandnew2026"


def assert_home_offers(page) -> None:
    page.goto(f"{BASE}/", wait_until="networkidle")
    page.locator("#tjanster").scroll_into_view_if_needed()
    page.wait_for_timeout(500)

    media = page.locator(".alt-offer-card__media").first
    box = media.bounding_box()
    assert box, "offer media wrapper missing box"
    ratio = box["width"] / box["height"]
    assert 0.94 < ratio < 1.06, f"expected 1:1 media frame, got {ratio:.2f}"

    img_fit = page.locator(".alt-offer-card__img").first.evaluate(
        "el => getComputedStyle(el).objectFit"
    )
    assert img_fit == "cover", f"offer image should use object-fit cover, got {img_fit}"

    gap_px = page.evaluate(
        """() => parseFloat(getComputedStyle(document.querySelector('.alt-offers__grid')).rowGap)"""
    )
    assert gap_px >= 24, f"expected larger row gap on mobile, got {gap_px}px"

    spacing = page.evaluate(
        """() => {
          const offers = document.querySelector('.alt-offers');
          const gallery = document.querySelector('.alt-gallery');
          const offersPad = offers ? parseFloat(getComputedStyle(offers).paddingBottom) : 0;
          const galleryPad = gallery ? parseFloat(getComputedStyle(gallery).paddingTop) : 0;
          return offersPad + galleryPad;
        }"""
    )
    assert spacing >= 80, f"expected larger offers-to-gallery spacing, got {spacing}px"

    foretag = page.locator(".alt-offer-card", has_text="Företag").locator("p").inner_text()
    assert foretag == (
        "Personalfest, kickoff och jubileum. Vi skräddarsyr ett upplägg efter era önskemål, "
        "oavsett om det gäller mingel eller artistkomp vid större evenemang."
    ), f"unexpected företag copy: {foretag}"

    fest = page.locator(".alt-offer-card", has_text="Fest och mingel")
    assert fest.count() == 1, "fest och mingel card missing"
    fest_href = fest.get_attribute("href") or ""
    assert fest_href.endswith("/mingel/"), fest_href
    assert fest.locator("h2").inner_text() == "Fest och mingel"
    assert fest.locator(".alt-offer-card__arrow").inner_text() == "Läs om fest och mingel"

    media_width = box["width"]
    vp = page.viewport_size["width"]
    assert media_width <= vp * 0.32, (
        f"offer image column should be ~30% smaller, got {media_width}px of {vp}px"
    )

    card = page.locator(".alt-offer-card").first
    styles = card.evaluate(
        """el => {
          const s = getComputedStyle(el);
          return {
            borderWidth: s.borderTopWidth,
            background: s.backgroundColor,
            paddingTop: s.paddingTop,
          };
        }"""
    )
    assert styles["borderWidth"] == "0px", f"card should have no border: {styles}"
    assert styles["paddingTop"] == "0px", f"card should have no padding: {styles}"

    page.screenshot(path=str(OUT / "offer-cards-mobile-webkit.png"), full_page=False)


def assert_inner_video_frame(page) -> None:
    page.goto(f"{BASE}/brollop/", wait_until="networkidle")
    facade = page.locator(".video-facade").first
    facade.scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    box = facade.bounding_box()
    assert box, "video facade missing"
    ratio = box["width"] / box["height"]
    assert 1.65 < ratio < 1.85, f"expected ~16:9 facade, got {ratio:.2f}"
    thumb = page.locator(".video-facade__play img").first
    tbox = thumb.bounding_box()
    assert tbox and tbox["height"] <= box["height"] + 2, "thumbnail should not exceed facade height"


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
            page = browser.new_context(
                viewport=VIEWPORT,
                device_scale_factor=3,
                is_mobile=True,
                has_touch=True,
            ).new_page()
            assert_home_offers(page)
            assert_inner_video_frame(page)
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print("OK: WebKit offer cards and inner media frames")
    return 0


if __name__ == "__main__":
    sys.exit(main())
