#!/usr/bin/env python3
"""WebKit: bröllop wireframe layout and no horizontal overflow (iPhone + desktop)."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
URL = "http://127.0.0.1:8770/testing/halfbandnew2026/brollop/"
MOBILE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 900}


def assert_layout(page, label: str) -> None:
    data = page.evaluate(
        """() => {
          const main = document.querySelector('main#innehall');
          const hero = document.querySelector('.alt-service-hero');
          const fest = document.querySelector('.alt-brollop-fest');
          const faqList = document.querySelector('.alt-brollop-faq .alt-faq__list');
          const text = main ? main.innerText : '';
          const stems = [...document.querySelectorAll('main img[src*="/gallery/halvfjorton-"]')]
            .map((img) => (img.getAttribute('src') || '').match(/halvfjorton-\\d+/)?.[0])
            .filter(Boolean);
          const dup = stems.find((s, i) => stems.indexOf(s) !== i);
          return {
            bodyClass: document.body.className,
            hasHero: !!hero,
            heroH: hero ? hero.getBoundingClientRect().height : 0,
            hasFest: !!fest,
            faqCount: faqList ? faqList.querySelectorAll('.alt-faq__item').length : 0,
            dup,
            docSW: document.documentElement.scrollWidth,
            docCW: document.documentElement.clientWidth,
            hasEyebrow: !!document.querySelector('.eyebrow'),
            hasDash: text.includes('–') || text.includes('—'),
            headerCount: document.querySelectorAll('.alt-header').length,
            footerCount: document.querySelectorAll('.site-footer').length,
          };
        }"""
    )
    assert "alt-page--wedding" in data["bodyClass"], f"{label}: wedding body class"
    assert data["hasHero"], f"{label}: missing wedding hero"
    assert data["heroH"] >= 170, f"{label}: hero too short ({data['heroH']})"
    assert data["hasFest"], f"{label}: missing Festspelning section"
    assert data["faqCount"] == 5, f"{label}: FAQ count"
    assert not data["dup"], f"{label}: duplicate gallery image {data['dup']}"
    assert data["docSW"] <= data["docCW"] + 1, (
        f"{label}: horizontal overflow {data['docSW']} > {data['docCW']}"
    )
    assert not data["hasEyebrow"], f"{label}: eyebrow present"
    assert not data["hasDash"], f"{label}: dash in copy"
    assert data["headerCount"] == 1 and data["footerCount"] == 1, (
        f"{label}: header/footer count"
    )

    hero_img = page.locator(".alt-service-hero__img")
    fit = hero_img.evaluate("el => getComputedStyle(el).objectFit")
    assert fit == "cover", f"{label}: hero image must use cover, got {fit}"

    display = page.locator(".alt-svc-chapter__title").first
    fs = display.evaluate("el => parseFloat(getComputedStyle(el).fontSize)")
    assert fs >= 22, f"{label}: section title too small ({fs}px)"


def run_viewport(browser, viewport: dict, mobile: bool, tag: str) -> None:
    ctx = browser.new_context(
        viewport=viewport,
        device_scale_factor=3 if mobile else 1,
        is_mobile=mobile,
        has_touch=mobile,
    )
    page = ctx.new_page()
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(400)
    page.evaluate(
        """() => {
          document.querySelectorAll('[data-reveal]').forEach((el) => el.classList.add('is-in'));
        }"""
    )
    assert_layout(page, tag)
    ctx.close()


def main() -> int:
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8770", "--bind", "127.0.0.1"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.35)
    try:
        with sync_playwright() as p:
            browser = p.webkit.launch()
            run_viewport(browser, MOBILE, True, "iphone")
            run_viewport(browser, DESKTOP, False, "desktop")
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print("OK: WebKit bröllop design (iPhone + desktop)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
