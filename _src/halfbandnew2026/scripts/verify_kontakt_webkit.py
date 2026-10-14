#!/usr/bin/env python3
"""WebKit: kontakt page structure (single H1, short USPs, Tally, email/Instagram)."""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = Path("/opt/cursor/artifacts/screenshots")
KONTAKT_URL = "http://127.0.0.1:8769/testing/halfbandnew2026/kontakt/"
MOBILE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 900}
OFFERT_EMAIL_LINK_TEXT = "Föredrar du e-post? Mejla oss här"
KONTAKT_SURFACE = "rgb(238, 235, 230)"


def assert_kontakt(page, label: str, mobile: bool) -> None:
    data = page.evaluate(
        """() => {
          const main = document.querySelector('main#innehall');
          const h1s = main ? [...main.querySelectorAll('h1')] : [];
          const hero = main ? main.querySelector('.page-hero') : null;
          const h2Offert = main ? main.querySelector('#offert-rubrik') : null;
          const items = main ? [...main.querySelectorAll('#offert .list-check > li')] : [];
          const iframe = main ? main.querySelector('#offert iframe[data-tally-src]') : null;
          const mailBtn = main ? main.querySelector('.contact-offert__mail') : null;
          const channels = main ? main.querySelector('.alt-contact-page__channels') : null;
          const links = channels ? [...channels.querySelectorAll('a')] : [];
          const tel = main ? main.querySelector('a[href^="tel:"]') : null;
          const orgStrip = main ? [...main.querySelectorAll('p.small.muted')].some(
            (p) => p.textContent.includes('Org.nr')
          ) : false;
          const mainText = main ? main.innerText : '';
          const mailLink = main ? main.querySelector('.contact-offert__mail a') : null;
          const h1 = main ? main.querySelector('#kontakt-rubrik') : null;
          const tallyCard = main ? main.querySelector('#offert .tally-card') : null;
          const mainBg = main ? getComputedStyle(main).backgroundColor : '';
          const tallyBg = tallyCard ? getComputedStyle(tallyCard).backgroundColor : '';
          const tallyPad = tallyCard ? parseFloat(getComputedStyle(tallyCard).paddingTop) : 0;
          const h1Color = h1 ? getComputedStyle(h1).color : '';
          return {
            h1Count: h1s.length,
            h1Text: h1s[0] ? h1s[0].textContent.trim() : '',
            hasHero: !!hero,
            h2Text: h2Offert ? h2Offert.textContent.trim() : '',
            uspCount: items.length,
            uspTexts: items.map((li) => li.textContent.trim()),
            hasIframe: !!iframe,
            mailText: mailLink ? mailLink.textContent.trim() : '',
            mailHref: mailLink ? mailLink.getAttribute('href') : '',
            channelHrefs: links.map((a) => a.getAttribute('href') || ''),
            hasTel: !!tel,
            orgStrip,
            hasEnDash: mainText.includes('–') || mainText.includes('—'),
            mainBg,
            tallyBg,
            tallyPad,
            h1Color,
            bodyClass: document.body.className,
          };
        }"""
    )
    assert data["h1Count"] == 1, f"{label}: expected 1 h1, got {data['h1Count']}"
    assert data["h1Text"] == "Kontakta oss", f"{label}: h1 text {data['h1Text']}"
    assert not data["hasHero"], f"{label}: page-hero should be removed"
    assert not data["h2Text"], f"{label}: offert h2 should be removed, got {data['h2Text']}"
    assert data["uspCount"] == 3, f"{label}: expected 3 USPs, got {data['uspCount']}"
    assert "Skräddarsytt efter era önskemål" in data["uspTexts"], f"{label}: missing skräddarsytt USP"
    assert "Åttamannaband med blås" in data["uspTexts"], f"{label}: missing blås USP"
    assert data["hasIframe"], f"{label}: Tally iframe missing"
    assert data["mailText"] == OFFERT_EMAIL_LINK_TEXT, f"{label}: mail link text {data['mailText']}"
    assert data["mailHref"] == "mailto:halvfjorton@gmail.com", f"{label}: mail href {data['mailHref']}"
    assert "alt-page--kontakt" in data["bodyClass"], f"{label}: missing kontakt body class"
    if mobile:
        assert data["mainBg"] == KONTAKT_SURFACE, f"{label}: main bg {data['mainBg']}"
        assert data["tallyBg"] in ("rgba(0, 0, 0, 0)", "transparent"), (
            f"{label}: tally card should be transparent, got {data['tallyBg']}"
        )
        assert data["tallyPad"] < 2, f"{label}: tally card padding {data['tallyPad']}"
        assert data["h1Color"] == "rgb(26, 24, 22)", f"{label}: h1 contrast {data['h1Color']}"
    assert len(data["channelHrefs"]) >= 2, f"{label}: email + Instagram links expected"
    assert data["channelHrefs"][0].startswith("mailto:"), f"{label}: email should be first channel"
    assert "instagram.com" in data["channelHrefs"][1], f"{label}: Instagram link missing"
    assert not data["hasTel"], f"{label}: telephone links not allowed"
    assert not data["orgStrip"], f"{label}: org.nr strip should be removed from main"
    assert not data["hasEnDash"], f"{label}: em/en dash in main copy"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8769", "--bind", "127.0.0.1"],
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
            page.goto(KONTAKT_URL, wait_until="networkidle")
            assert_kontakt(page, "webkit-mobile", mobile=True)
            page.screenshot(path=str(OUT / "kontakt-mobile-webkit.png"), full_page=True)

            page.set_viewport_size(DESKTOP)
            page.reload(wait_until="networkidle")
            assert_kontakt(page, "webkit-desktop", mobile=False)
            page.screenshot(path=str(OUT / "kontakt-desktop-webkit.png"), full_page=False)

            mobile_ctx.close()
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=5)
    print("OK: WebKit kontakt page (mobile + desktop)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
