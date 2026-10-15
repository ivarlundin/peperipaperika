#!/usr/bin/env python3
"""Generate the Halv Fjorton static site."""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from cms_build import run_cms_build_steps  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT
SITE = "https://halvfjorton.se"
OG = f"{SITE}/assets/img/og.jpg"
ORGANIZATION_JSON = ROOT / "assets/schema/organization.json"
H14_LOGO = ROOT / "assets/img/h14-logo.svg"
BRAND_TITLE = "Halv Fjorton | coverband & bröllopsband i Småland och Skåne"
WEDDING_VIDEO_ID = "V2Nb8jMKUCk"
WEDDING_VIDEO_TITLE = "Signed Sealed Delivered - Halv Fjorton"
TALLY_EMBED_SRC = (
    "https://tally.so/embed/n0xyqQ?alignLeft=1&hideTitle=1&transparentBackground=1&dynamicHeight=1"
)
TALLY_PUBLIC_URL = "https://tally.so/r/n0xyqQ"
OFFERT_URL = f"{SITE}/kontakt/#offert"
SOULFUL_CHRISTMAS_TICKETS = "https://www.nygatan6.se/kalender/a-soulful-christmas/"
SOULFUL_CHRISTMAS_IMG = "/assets/img/events/a-soulful-christmas-2026"
SOULFUL_CHRISTMAS_START = "2026-12-12T00:00:00+01:00"
SOULFUL_CHRISTMAS_END = "2026-12-12T22:00:00+01:00"
SOULFUL_LUCIA_2025_VIDEO_ID = "CFr_XLrILmY"
SOULFUL_LUCIA_2025_START = 5491
SOULFUL_LUCIA_2025_IMG = "/assets/img/events/a-soulful-lucia-2025"

CONTACT_USPS = [
    "Vi svarar inom 24 timmar",
    "Skräddarsytt efter era önskemål",
    "En kontakt hela vägen från förfrågan till sista låten",
    "Åttamannaband med blås",
    "Spelar i Småland och Skåne: Växjö, Kalmar, Jönköping, Malmö, Lund, Helsingborg",
    "Sedan 2018",
]

HOME_OFFERT_USPS: list[tuple[str, str]] = [
    ("Svar inom 24 timmar", "check"),
    ("Åttamannaband med blåssektion", "check"),
]

ALT_ICON_CHECK_SVG = (
    '<svg class="alt-facts__icon" width="18" height="18" viewBox="0 0 24 24" fill="none" '
    'aria-hidden="true">'
    '<path d="M5.5 12.5 9.5 16.5 18.5 7.5" stroke="currentColor" stroke-width="1.75" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    "</svg>"
)

ALT_ICON_PIN_SVG = (
    '<svg class="alt-facts__icon" width="18" height="18" viewBox="0 0 24 24" fill="none" '
    'aria-hidden="true">'
    '<path d="M12 21s7-4.5 7-11a7 7 0 1 0-14 0c0 6.5 7 11 7 11Z" stroke="currentColor" '
    'stroke-width="1.5" stroke-linejoin="round"/>'
    '<circle cx="12" cy="10" r="2.25" stroke="currentColor" stroke-width="1.5"/>'
    "</svg>"
)


def home_alt_facts_block() -> str:
    return f"""      <div class="alt-facts">
        <div class="alt-facts__inner">
          <div class="alt-facts__items">
            <span class="alt-facts__item">{ALT_ICON_CHECK_SVG}Åttamannaband</span>
            <span class="alt-facts__item">{ALT_ICON_CHECK_SVG}Blåssektion</span>
          </div>
          <span class="alt-facts__region alt-facts__item">{ALT_ICON_PIN_SVG}Växjö, Småland</span>
        </div>
      </div>"""


def offert_usp_list_markup(usps: list[tuple[str, str]] | list[str]) -> str:
    lines: list[str] = []
    for item in usps:
        if isinstance(item, tuple):
            label, kind = item
            cls = ' class="list-check__item--pin"' if kind == "pin" else ""
        else:
            label, cls = item, ""
        lines.append(f"            <li{cls}>{esc(label)}</li>")
    return "\n".join(lines)

OFFERT_EMAIL_LINK_TEXT = "Föredrar du e-post? Mejla oss här"

FOOTER_INTEGRITETSPOLICY_HREF = "/integritetspolicy/"


def contact_form_consent_markup() -> str:
    return f"""            <p class="contact-offert__consent">Genom att skicka godkänner du att vi sparar dina uppgifter för att besvara din förfrågan. Läs mer i vår <a href="{FOOTER_INTEGRITETSPOLICY_HREF}">integritetspolicy</a>.</p>"""


def offert_email_mail_markup() -> str:
    return f"""          <p class="contact-offert__mail">
            <a class="alt-btn alt-btn--primary" href="mailto:halvfjorton@gmail.com">{OFFERT_EMAIL_LINK_TEXT}</a>
          </p>
"""


NAV_SERVICES = [
    ("/brollop/", "Bröllop"),
    ("/foretag/", "Företag"),
    ("/fest-och-mingel/", "Fest och mingel"),
]

# Service landing pages kept in build output but omitted from nav, sitemap, and llms.txt.
HIDDEN_SERVICE_PATHS = frozenset(
    {
        "/kompband/",
        "/50-arsfest/",
        "/brollopsband-smaland/",
        "/coverband-skane-malmo/",
        "/for-eventbolag/",
    }
)

SERVICE_LINK_REDIRECTS = {
    "/kompband/": "/brollop/",
    "/50-arsfest/": "/fest-och-mingel/",
    "/mingel/": "/fest-och-mingel/",
    "/brollopsband-smaland/": "/brollop/",
    "/coverband-skane-malmo/": "/foretag/",
    "/for-eventbolag/": "/foretag/",
}

NAV_PRIMARY = [
    ("/", "Hem"),
    ("/om-oss/", "Om oss"),
    ("/lyssna/", "Lyssna"),
    ("/faq/", "FAQ"),
    ("/kontakt/", "Kontakt"),
]

SITEMAP_PATHS = [
    "/",
    "/brollop/",
    "/foretag/",
    "/julkonsert/",
    "/konserter/",
    "/fest-och-mingel/",
    "/om-oss/",
    "/lyssna/",
    "/faq/",
    "/kontakt/",
    "/integritetspolicy/",
]

HOME_NAV_LINKS = [
    ("/konserter/", "Konserter"),
    ("/om-oss/", "Om oss"),
    ("/faq/", "FAQ"),
    ("/lyssna/", "Lyssna"),
    ("/kontakt/", "Kontakt"),
]

LOKAL_TEKNIK_COPY = (
    "Tekniska behov tar vi i offerten utifrån lokal och program. "
    "Vid större saler eller särskilda önskemål har vi kontakter bland uthyrare."
)

LABS_SUBPATH_DEFAULT = "/testing/halfbandnew2026"
BUILD_YEAR = datetime.now(timezone.utc).year

ORG_STREET_ADDRESS = "Fabriksgatan 12"
ORG_POSTAL_CITY_LINE = "342 50 Vislanda"
ORG_POSTAL_ADDRESS_LD = {
    "@type": "PostalAddress",
    "streetAddress": ORG_STREET_ADDRESS,
    "postalCode": "342 50",
    "addressLocality": "Vislanda",
    "addressCountry": "SE",
}

INSTAGRAM_PROFILE_URL = "https://www.instagram.com/halvfjorton/"
INSTAGRAM_ICON_BTN = """            <svg class="alt-btn__icon" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <rect x="3" y="3" width="18" height="18" rx="5" stroke="currentColor" stroke-width="1.75"/>
              <circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="1.75"/>
              <circle cx="17.5" cy="6.5" r="1" fill="currentColor"/>
            </svg>"""

FOOTER_SOCIAL_ICON_SVG = (
    '<svg class="alt-btn__icon" width="18" height="18" viewBox="0 0 24 24" fill="none" '
    'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">{inner}</svg>'
)
FOOTER_INSTAGRAM_ICON = FOOTER_SOCIAL_ICON_SVG.format(
    inner=(
        '<rect x="3" y="3" width="18" height="18" rx="5" stroke="currentColor" stroke-width="1.75"/>'
        '<circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="1.75"/>'
        '<circle cx="17.5" cy="6.5" r="1" fill="currentColor"/>'
    )
)
FOOTER_YOUTUBE_ICON = FOOTER_SOCIAL_ICON_SVG.format(
    inner=(
        '<path d="M20.5 7.2a1.6 1.6 0 0 0-1.12-.74C17.7 6.25 12 6.25 12 6.25s-5.7 0-7.38.21a1.6 1.6 0 0 0-1.12.74A16.8 16.8 0 0 0 3 12a16.8 16.8 0 0 0 .5 4.8 1.6 1.6 0 0 0 1.12.74c1.68.21 7.38.21 7.38.21s5.7 0 7.38-.21a1.6 1.6 0 0 0 1.12-.74A16.8 16.8 0 0 0 21 12a16.8 16.8 0 0 0-.5-4.8z" stroke="currentColor" stroke-width="1.75" stroke-linejoin="round"/>'
        '<path d="M10.25 15.02V8.98L15.5 12l-5.25 3.02z" fill="currentColor"/>'
    )
)


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def faq_item_markup(question: str, answer: str) -> str:
    return f"""          <details class="alt-faq__item">
            <summary class="alt-faq__question">{esc(question)}</summary>
            <div class="alt-faq__answer">
              <p>{esc(answer)}</p>
            </div>
          </details>"""


def faq_list_two_columns(qa_pairs: list[tuple[str, str]]) -> str:
    """Two-column CSS grid (row order); stable columns + paired row heights when collapsed."""
    items = "\n".join(faq_item_markup(q, a) for q, a in qa_pairs)
    return f"""        <div class="alt-faq__list alt-faq__list--cols" data-faq>
{items}
        </div>"""


def _indent_ld(data: dict) -> str:
    raw = json.dumps(data, indent=2, ensure_ascii=False)
    return "\n".join(f"  {line}" for line in raw.splitlines())


def music_group_ld() -> str:
    data = json.loads(ORGANIZATION_JSON.read_text(encoding="utf-8"))
    return _indent_ld(data)


def load_org() -> dict:
    return json.loads(ORGANIZATION_JSON.read_text(encoding="utf-8"))


BRAND_MARK_PX = 56

def contact_page_ld() -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "ContactPage",
        "url": f"{SITE}/kontakt/",
        "name": "Kontakta Halv Fjorton",
        "description": "Begär offert till Halv Fjorton | coverband för bröllop, företag och fest i södra Sverige.",
        "mainEntity": {
            "@type": "Organization",
            "name": "Halv Fjorton",
            "url": f"{SITE}/",
            "email": "halvfjorton@gmail.com",
            "address": ORG_POSTAL_ADDRESS_LD,
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "booking",
                "email": "halvfjorton@gmail.com",
                "areaServed": "SE",
                "availableLanguage": ["sv", "en"],
            },
        },
    }
    return _indent_ld(data)


def tally_iframe_markup() -> str:
    return f"""          <iframe
            data-tally-src="{TALLY_EMBED_SRC}"
            loading="lazy"
            title="Offertförfrågan Halv Fjorton"
            width="100%"
            height="420"
            frameborder="0"
            marginheight="0"
            marginwidth="0"
          ></iframe>"""


def integritetspolicy_page_body() -> str:
    return f"""    <section class="section alt-legal-page">
      <div class="alt-svc-wrap alt-legal-page__inner">
        <h1 class="alt-svc-chapter__title alt-legal-page__title">Integritetspolicy</h1>
        <div class="alt-svc-chapter__body alt-legal-page__body">
          <p>Denna policy beskriver hur Halv Fjorton ekonomisk förening behandlar personuppgifter när du kontaktar oss via webbplatsen.</p>
          <h2 class="alt-svc-chapter__title alt-legal-page__heading">Personuppgiftsansvarig</h2>
          <p>Halv Fjorton ekonomisk förening, organisationsnummer 769641-5418.<br>
{ORG_STREET_ADDRESS}<br>
{ORG_POSTAL_CITY_LINE}<br>
Kontakt: <a href="mailto:halvfjorton@gmail.com">halvfjorton@gmail.com</a>.</p>
          <h2 class="alt-svc-chapter__title alt-legal-page__heading">Vad vi samlar in</h2>
          <p>Namn, e-postadress, telefonnummer om du anger det, och meddelandet du skickar i kontaktformuläret.</p>
          <h2 class="alt-svc-chapter__title alt-legal-page__heading">Varför</h2>
          <p>Vi använder uppgifterna för att besvara din förfrågan och ta fram offert när det behövs.</p>
          <h2 class="alt-svc-chapter__title alt-legal-page__heading">Hur länge</h2>
          <p>Förfrågningar som inte leder till en bokning raderar vi senast 24 månader efter att de kom in. Uppgifter som hör till en bokning, som avtal och fakturor, sparar vi så länge bokföringslagen kräver.</p>
          <h2 class="alt-svc-chapter__title alt-legal-page__heading">Delning</h2>
          <p>Vi säljer inte personuppgifter och delar dem inte med tredje part i marknadsföringssyfte.</p>
          <h2 class="alt-svc-chapter__title alt-legal-page__heading">Dina rättigheter</h2>
          <p>Du kan begära tillgång, rättelse eller radering av dina uppgifter. Mejla <a href="mailto:halvfjorton@gmail.com">halvfjorton@gmail.com</a>.</p>
        </div>
      </div>
    </section>"""


def kontakt_page_body() -> str:
    usp_items = offert_usp_list_markup(HOME_OFFERT_USPS)
    return f"""    <section class="alt-contact-page section" id="offert" aria-labelledby="kontakt-rubrik">
      <div class="alt-contact-offert__wrap alt-contact-page__stack">
        <div class="contact-offert__grid">
          <div class="contact-offert__copy">
            <header class="alt-contact-page__intro">
              <h1 id="kontakt-rubrik">Kontakta oss</h1>
              <p class="contact-offert__lead">Fyll i formuläret så återkommer vi, oftast inom 24 timmar.</p>
            </header>
            <ul class="list-check">
{usp_items}
            </ul>
{offert_email_mail_markup()}
          </div>
          <div class="contact-offert__form-col">
            <div class="contact-offert__form tally-card">
              <noscript>
                <p><a href="{TALLY_PUBLIC_URL}">Öppna offertformuläret på Tally</a> om det inte visas här.</p>
              </noscript>
{tally_iframe_markup()}
            </div>
{contact_form_consent_markup()}
          </div>
        </div>
      </div>
    </section>
    <section class="alt-contact-page__channels section section--tight" aria-label="Direktkontakt">
      <div class="alt-contact-offert__wrap alt-contact-page__channels-inner">
        <a class="alt-contact-page__link" href="mailto:halvfjorton@gmail.com">halvfjorton@gmail.com</a>
        <a class="alt-contact-page__link" href="https://www.instagram.com/halvfjorton/" rel="noopener noreferrer">Instagram @halvfjorton</a>
      </div>
    </section>"""


def contact_offert_section(
    heading: str = "Begär offert",
    lead: str | None = None,
    section_class: str = "contact-offert section",
    wrap_class: str = "wrap contact-offert__grid",
    usps: list[str] | None = None,
    include_mail_button: bool = True,
) -> str:
    usp_source = usps if usps is not None else CONTACT_USPS
    usp_items = offert_usp_list_markup(usp_source[:3])
    lead_html = f'        <p class="contact-offert__lead">{esc(lead)}</p>\n' if lead else ""
    mail_html = offert_email_mail_markup() if include_mail_button else ""
    return f"""    <section class="{section_class}" id="offert" aria-labelledby="offert-rubrik">
      <div class="{wrap_class}">
        <div class="contact-offert__copy">
          <h2 id="offert-rubrik">{esc(heading)}</h2>
{lead_html}          <ul class="list-check">
{usp_items}
          </ul>
{mail_html}        </div>
        <div class="contact-offert__form-col">
          <div class="contact-offert__form tally-card">
            <noscript>
              <p><a href="{TALLY_PUBLIC_URL}">Öppna offertformuläret på Tally</a> om det inte visas här.</p>
            </noscript>
{tally_iframe_markup()}
          </div>
{contact_form_consent_markup()}
        </div>
      </div>
    </section>"""


def font_preloads(asset_root: str = "/assets") -> str:
    root = asset_root.rstrip("/")
    return f"""  <link rel="preload" href="{root}/fonts/InterVariable.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="{root}/fonts/Outfit-Variable.woff2" as="font" type="font/woff2" crossorigin>"""


def nav_path(href: str, prefix: str = "") -> str:
    if not prefix:
        return href
    return "../" + href.lstrip("/")


def nav_toggle_markup(panel_id: str = "meny") -> str:
    return f"""      <button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="{panel_id}" aria-label="Öppna meny">
        <span class="nav-toggle__bars" aria-hidden="true"></span>
      </button>"""


def alt_nav_toggle_markup(panel_id: str = "mobile-menu") -> str:
    return f"""      <button class="nav-toggle alt-nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="{panel_id}" aria-label="Öppna meny">
        <span class="nav-toggle__bars" aria-hidden="true"></span>
      </button>"""


def alt_header_mobile_controls_markup(panel_id: str = "mobile-menu") -> str:
    close = mobile_menu_close_markup().replace(
        'class="mobile-menu__close"',
        'class="mobile-menu__close alt-header__menu-close"',
        1,
    )
    return alt_nav_toggle_markup(panel_id) + "\n" + close


def mobile_menu_close_markup() -> str:
    return """      <button type="button" class="mobile-menu__close" data-nav-close aria-label="Stäng meny">
        <span class="mobile-menu__close-icon" aria-hidden="true"></span>
      </button>"""


def alt_header_scroll_bootstrap_script() -> str:
    return """  <script>
(function () {
  document.documentElement.classList.add("alt-header-state-init");
  var header = document.querySelector(".alt-header");
  if (!header) return;
  if ((window.scrollY || document.documentElement.scrollTop || 0) > 10) {
    header.classList.add("is-solid");
  }
})();
  </script>"""


def nav_services_dropdown(current_path: str, prefix: str = "", menu_id: str = "nav-tjanster") -> str:
    service_paths = {p for p, _ in NAV_SERVICES}
    expanded = "true" if current_path in service_paths else "false"
    items = []
    for href, label in NAV_SERVICES:
        current = ' aria-current="page"' if href == current_path else ""
        items.append(
            f'              <li role="none"><a role="menuitem" href="{nav_path(href, prefix)}"{current}>{label}</a></li>'
        )
    submenu = "\n".join(items)
    return f"""          <li class="nav-item nav-item--dropdown" data-nav-dropdown>
            <button type="button" class="nav-dropdown__trigger" data-nav-dropdown-trigger aria-expanded="{expanded}" aria-controls="{menu_id}" id="{menu_id}-btn">
              Tjänster
              <span class="nav-dropdown__chevron" aria-hidden="true"></span>
            </button>
            <ul class="nav-dropdown__menu" id="{menu_id}" role="menu" aria-labelledby="{menu_id}-btn" data-nav-dropdown-menu>
{submenu}
            </ul>
          </li>"""


def mobile_nav_services_dropdown(current_path: str, prefix: str = "", menu_id: str = "mobile-nav-tjanster") -> str:
    service_paths = {p for p, _ in NAV_SERVICES}
    expanded = "true" if current_path in service_paths else "false"
    items = []
    for href, label in NAV_SERVICES:
        current = ' aria-current="page"' if href == current_path else ""
        items.append(
            f'              <li role="none"><a role="menuitem" href="{nav_path(href, prefix)}"{current}>{label}</a></li>'
        )
    submenu = "\n".join(items)
    return f"""          <li class="nav-item nav-item--dropdown" data-nav-dropdown>
            <button type="button" class="nav-dropdown__trigger" data-nav-dropdown-trigger aria-expanded="{expanded}" aria-controls="{menu_id}" id="{menu_id}-btn">
              Tjänster
              <span class="nav-dropdown__chevron" aria-hidden="true"></span>
            </button>
            <div class="mobile-menu__submenu">
              <div class="mobile-menu__submenu-inner">
                <ul class="nav-dropdown__menu" id="{menu_id}" role="menu" aria-labelledby="{menu_id}-btn" data-nav-dropdown-menu>
{submenu}
                </ul>
              </div>
            </div>
          </li>"""


def render_nav_list(current_path: str, prefix: str = "", include_home: bool = True, menu_id: str = "nav-tjanster") -> str:
    items = []
    if include_home:
        current = ' aria-current="page"' if current_path == "/" else ""
        items.append(f'          <li><a href="{nav_path("/", prefix)}"{current}>Hem</a></li>')
    items.append(nav_services_dropdown(current_path, prefix, menu_id))
    for href, label in NAV_PRIMARY:
        if href == "/":
            continue
        current = ' aria-current="page"' if href == current_path else ""
        items.append(f'          <li><a href="{nav_path(href, prefix)}"{current}>{label}</a></li>')
    return "\n".join(items)


def home_nav_links_markup(
    current_path: str = "/",
    prefix: str = "",
    menu_id: str = "nav-tjanster",
) -> str:
    items = [nav_services_dropdown(current_path, prefix, menu_id)]
    for href, label in HOME_NAV_LINKS:
        current = ' aria-current="page"' if href == current_path else ""
        items.append(f'          <li><a href="{nav_path(href, prefix)}"{current}>{label}</a></li>')
    return "\n".join(items)


def mobile_nav_links_markup(
    current_path: str = "/",
    prefix: str = "",
    menu_id: str = "mobile-nav-tjanster",
) -> str:
    items = [mobile_nav_services_dropdown(current_path, prefix, menu_id)]
    for href, label in HOME_NAV_LINKS:
        current = ' aria-current="page"' if href == current_path else ""
        items.append(f'          <li><a href="{nav_path(href, prefix)}"{current}>{label}</a></li>')
    return "\n".join(items)


def home_nav_block(current_path: str = "/", offert_href: str = "#offert", prefix: str = "") -> str:
    return f"""      <nav class="alt-nav" aria-label="Huvudmeny">
        <ul class="alt-nav__links nav-list" id="alt-meny">
{home_nav_links_markup(current_path, prefix, "nav-tjanster")}
        </ul>
        <a class="alt-btn alt-btn--primary alt-nav__cta-desktop" href="{offert_href}">Begär offert</a>
      </nav>"""


def mobile_menu_block(
    current_path: str = "/",
    offert_href: str = "#offert",
    prefix: str = "",
) -> str:
    return f"""  <div class="mobile-menu" id="mobile-menu" data-mobile-menu hidden aria-hidden="true">
    <nav class="mobile-menu__nav" aria-label="Mobilmeny">
      <ul class="mobile-menu__list nav-list" data-nav-panel>
{mobile_nav_links_markup(current_path, prefix, "mobile-nav-tjanster")}
      </ul>
    </nav>
    <div class="mobile-menu__foot">
      <a class="alt-btn alt-btn--primary mobile-menu__cta" href="{offert_href}">Begär offert</a>
    </div>
  </div>"""


def modern_footer_markup() -> str:
    return f"""  <footer class="site-footer site-footer--columns" aria-label="Sidfot">
    <div class="site-footer__inner">
      <div class="site-footer__columns">
        <div class="site-footer__brand">
          <a class="site-footer__brand-mark" href="/" aria-label="Halv Fjorton">
            <span class="site-footer__title">Halv Fjorton</span>
          </a>
          <p class="site-footer__tagline">Coverband och partyband med rötter i Växjö, Småland.</p>
        </div>
        <div class="site-footer__col">
          <p class="site-footer__col-label">Tjänster</p>
          <ul class="site-footer__links">
            <li><a href="/brollop/">Bröllop</a></li>
            <li><a href="/foretag/">Företag</a></li>
            <li><a href="/fest-och-mingel/">Fest och mingel</a></li>
          </ul>
        </div>
        <div class="site-footer__col">
          <p class="site-footer__col-label">Läs mer</p>
          <ul class="site-footer__links">
            <li><a href="/om-oss/">Om oss</a></li>
            <li><a href="/faq/">FAQ</a></li>
            <li><a href="/lyssna/">Lyssna</a></li>
            <li><a href="/konserter/">Konserter</a></li>
            <li><a href="{FOOTER_INTEGRITETSPOLICY_HREF}">Integritetspolicy</a></li>
          </ul>
        </div>
        <div class="site-footer__col">
          <p class="site-footer__col-label">Följ oss</p>
          <ul class="site-footer__links">
            <li><a class="site-footer__social-link" href="https://www.instagram.com/halvfjorton/" target="_blank" rel="noopener noreferrer">{FOOTER_INSTAGRAM_ICON}<span>Instagram</span></a></li>
            <li><a class="site-footer__social-link" href="https://www.youtube.com/@halvfjorton9292" target="_blank" rel="noopener noreferrer">{FOOTER_YOUTUBE_ICON}<span>YouTube</span></a></li>
          </ul>
        </div>
        <div class="site-footer__col site-footer__col--contact">
          <p class="site-footer__col-label">Kontakt</p>
          <ul class="site-footer__links site-footer__links--plain">
            <li>
              <address class="site-footer__address">
                {ORG_STREET_ADDRESS}<br>
                {ORG_POSTAL_CITY_LINE}
              </address>
            </li>
            <li><span class="site-footer__contact-line">Org.nr 769641-5418</span></li>
            <li><a class="site-footer__email" href="mailto:halvfjorton@gmail.com">halvfjorton@gmail.com</a></li>
          </ul>
        </div>
      </div>
      <hr class="site-footer__rule" />
      <p class="site-footer__legal site-footer__legal--bar">
        <span class="site-footer__legal-line">© <span data-footer-year>{BUILD_YEAR}</span> Halv Fjorton</span>
        <span class="site-footer__legal-place">Växjö, Småland</span>
      </p>
    </div>
  </footer>"""


def brand_logo_markup() -> str:
    svg = H14_LOGO.read_text(encoding="utf-8")
    svg = re.sub(
        r'<svg\s+',
        '<svg class="brand-mark" focusable="false" ',
        svg,
        count=1,
    )
    svg = re.sub(r'\bwidth="[^"]*"', f'width="{BRAND_MARK_PX}"', svg, count=1)
    svg = re.sub(r'\bheight="[^"]*"', f'height="{BRAND_MARK_PX}"', svg, count=1)
    return svg


def aeo_answer(text: str) -> str:
    return f'        <p class="aeo-answer">{text}</p>'


def video_facade(
    video_id: str,
    title: str,
    alt: str,
    width: int = 1280,
    height: int = 720,
) -> str:
    return f"""        <div class="embed video-facade" data-video-facade="{video_id}" data-video-title="{esc(title)}">
          <button type="button" class="video-facade__play" aria-label="Spela video: {esc(title)}">
            <img src="https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" alt="{esc(alt)}" width="{width}" height="{height}" loading="lazy" decoding="async">
          </button>
        </div>"""


LYSSNA_VIDEO_MODAL_SCRIPT = (
    '  <script src="/assets/js/lyssna-video-modal.js" defer></script>\n'
)
LYSSNA_REPERTOIRE_JSON = ROOT / "assets/data/lyssna-repertoire.json"
SPOTIFY_REPERTOIRE_EMBED = (
    "https://open.spotify.com/embed/playlist/0q8DLuLfZE25an41tppmvu?utm_source=generator"
)

LYSSNA_TILE_PLAY_ICON = """            <svg class="lyssna-video-tile__play-icon" viewBox="8.6 6.9 9.4 10.2" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M9.15 7.35v9.3l8.7-4.65-8.7-4.65z" fill="currentColor" stroke="currentColor" stroke-width="1.15" stroke-linejoin="round" stroke-linecap="round"/>
            </svg>"""


def _lyssna_poster_srcset(poster: str) -> str:
    if not poster.endswith("-1200w.webp"):
        return ""
    stem = poster[: -len("-1200w.webp")]
    if "/assets/img/gallery/halvfjorton-" in poster:
        return (
            f' srcset="{stem}-480w.webp 480w, {stem}-800w.webp 800w, '
            f'{stem}-1200w.webp 1200w, {stem}-1920w.webp 1920w"'
        )
    if "/assets/img/events/" in poster:
        return (
            f' srcset="{stem}-480w.webp 480w, {stem}-800w.webp 800w, '
            f'{stem}-1200w.webp 1200w"'
        )
    return ""


def lyssna_video_tile(
    video_id: str,
    label: str,
    title: str,
    poster: str | None = None,
    start_seconds: int | None = None,
) -> str:
    yt_max = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
    yt_hq = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    thumb_src = poster or yt_max
    thumb_fallback = yt_hq
    srcset = _lyssna_poster_srcset(poster) if poster else ""
    sizes = ' sizes="(max-width: 640px) 50vw, (max-width: 900px) 50vw, 36rem"'
    start_attr = f' data-lyssna-start="{start_seconds}"' if start_seconds else ""
    return f"""        <button type="button" class="lyssna-video-tile" data-lyssna-video="{video_id}" data-lyssna-title="{esc(title)}"{start_attr} aria-label="Spela video: {esc(title)}">
          <span class="lyssna-video-tile__media">
            <img class="lyssna-video-tile__thumb" src="{esc(thumb_src)}"{srcset}{sizes} alt="" width="1280" height="720" loading="lazy" decoding="async" data-lyssna-thumb-fallback="{thumb_fallback}">
          </span>
          <span class="lyssna-video-tile__meta">
            <span class="lyssna-video-tile__label">{esc(label)}</span>
            <span class="lyssna-video-tile__play" aria-hidden="true">
{LYSSNA_TILE_PLAY_ICON}
            </span>
          </span>
        </button>"""


def lyssna_video_grid(*tiles: str) -> str:
    return "        <div class=\"lyssna-video-grid\">\n" + "\n".join(tiles) + "\n        </div>"


def lyssna_repertoire_song_list_markup() -> str:
    songs = json.loads(LYSSNA_REPERTOIRE_JSON.read_text(encoding="utf-8"))
    items = "\n".join(
        f'            <li><span class="lyssna-song-list__track">{esc(s["title"])}</span> '
        f'<span class="lyssna-song-list__artist">{esc(s["artist"])}</span></li>'
        for s in songs
    )
    return f"""        <ol class="lyssna-song-list" aria-label="Låtar i repertoaren">
{items}
        </ol>"""


def lyssna_spotify_embed_markup() -> str:
    return f"""        <div class="lyssna-spotify">
          <iframe class="lyssna-spotify__embed" src="{SPOTIFY_REPERTOIRE_EMBED}" title="Halv Fjorton repertoar 2026 på Spotify" loading="lazy" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" allowfullscreen></iframe>
        </div>"""


THE_LICK_VIDEO_URL = "https://www.youtube.com/watch?v=krDxhnaKD7Q"

OM_OSS_MEMBERS = [
    (
        "Adam Blidstål",
        "member-adam.jpg",
        "Sångare och bandets crooner som charmar hela publiken med sin vassa röst. Lärare på dagarna, frontfigur på kvällarna, och ingen i lokalen går säker.",
    ),
    (
        'Gustav "Gema" Kerrolf',
        "member-gustav.jpg",
        "Sångare och slagverkare som sjunger med ena halvan av hjärnan och håller takten med den andra. Ger du honom en bil med släp backar han in i vilken lastficka som helst.",
    ),
    (
        "Edvin Sydmark",
        "member-edvin.jpg",
        "Gitarrist och musiklärare med tajta funkkomp och hjältesolon med dist. Ser du honom lägga ifrån sig gitarren och le: spring. En lek är på väg.",
    ),
    (
        "Ivar Lundin",
        "member-ivar.jpg",
        None,
        (
            "Keyboardist och mångsysslare som lever för fusion och groove. Han hjälper varje treklang på traven "
            f'med några extra ackord och väntar bara på rätt tillfälle att slänga in <a href="{THE_LICK_VIDEO_URL}" '
            'target="_blank" rel="noopener noreferrer">The Lick</a>. Håll utkik!'
        ),
    ),
    (
        "Zacharias Averin",
        "member-zacharias.jpg",
        "Basist som säljer bokföring på dagarna och spelar 32-delar på sin femsträngade på kvällarna. Börjar dansgolvet vibrera är det inte en jordbävning, det är Averin som har satt igång förstärkaren.",
    ),
    (
        "Jonathan Eryd",
        "member-jonathan.jpg",
        "Trummis och bandets äldste som byter cymbaler oftare än vi byter låtordning. Han kan varenda låt och skickar in till Nyacht or Yacht, podden för yachtrocknördar.",
    ),
    (
        'Nils "Nisse" Biström',
        "member-nils.jpg",
        "Trumpetare och ljudtekniker. Ser du en mörk skugga glida längs dansgolvets kant är den inte där för att ta dig. Den är där för att dra ner 3 dB på 250 Hz.",
    ),
    (
        "Olof Ingelsten",
        "member-olof.jpg",
        "Saxofonist vars instrumentsamling börjar likna en liten orkester. Syns inte dansgolvet för rök vet du vem som varit i farten. Olof kör nämligen även ljuset.",
    ),
]


def member_avatar_alt(name: str, line: str) -> str:
    plain = re.sub(r"<[^>]+>", "", line)
    role = plain.split(".", 1)[0]
    if len(role) > 48:
        role = plain.split(",", 1)[0]
    return f"{name}, {role.lower()}"


def member_compact_card(
    name: str = "",
    img_file: str = "",
    line: str = "",
    line_html: str | None = None,
    placeholder: bool = False,
) -> str:
    if placeholder:
        return """          <article class="member-compact-card member-compact-card--placeholder">
            <span class="member-compact-card__avatar member-compact-card__avatar--empty" aria-hidden="true"></span>
            <div class="member-compact-card__body">
              <h3 class="member-compact-card__name">Namn</h3>
              <p class="member-compact-card__line">Instrument</p>
            </div>
          </article>"""
    bio_plain = line if line else re.sub(r"<[^>]+>", "", line_html or "")
    alt = member_avatar_alt(name, bio_plain)
    bio_markup = line_html if line_html is not None else esc(line)
    return f"""          <article class="member-compact-card">
            <img class="member-compact-card__avatar" src="/assets/img/{img_file}" alt="{esc(alt)}" width="160" height="160" loading="lazy" decoding="async">
            <div class="member-compact-card__body">
              <h3 class="member-compact-card__name">{esc(name)}</h3>
              <p class="member-compact-card__line">{bio_markup}</p>
            </div>
          </article>"""


def om_oss_member_card(entry: tuple) -> str:
    name, img, *rest = entry
    if len(rest) == 2 and rest[0] is None:
        return member_compact_card(name, img, line="", line_html=rest[1])
    return member_compact_card(name, img, rest[0])


def members_compact_grid(cards: str) -> str:
    return f"""        <div class="member-compact-grid">
{cards}
        </div>"""


def write_redirect_page(path: str, target: str, link_label: str = "Lyssna") -> None:
    canonical = f"{SITE}{target.split('#')[0]}"
    html = f"""<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta http-equiv="refresh" content="0; url={target}">
  <link rel="canonical" href="{canonical}">
  <title>Repertoar | omdirigering</title>
  <meta name="robots" content="noindex,follow">
  <script>location.replace("{target}");</script>
</head>
<body>
  <p>Repertoaren finns nu under Lyssna. <a href="{target}">Fortsätt till {esc(link_label)}</a>.</p>
</body>
</html>
"""
    dest = OUT_ROOT / path.strip("/") / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
    print("wrote", dest.relative_to(OUT_ROOT), "(redirect)")


SERVICE_HERO_TYPEWRITER_SCRIPT = (
    '  <script src="/assets/js/alt-hero-typewriter.js" defer></script>\n'
)


SERVICE_HERO_TYPEWRITER_PREFIX = "Liveband till "


def service_hero_typewriter_h1(
    h1: str,
    *,
    loop_suffixes: tuple[str, ...] | None = None,
) -> str:
    if loop_suffixes:
        prefix = SERVICE_HERO_TYPEWRITER_PREFIX
        if not h1.startswith(prefix):
            raise ValueError(f"loop hero h1 must start with {prefix!r}: {h1!r}")
        if h1 != f"{prefix}{loop_suffixes[0]}":
            raise ValueError(
                f"hero_h1 must match first loop suffix: {h1!r} vs {prefix}{loop_suffixes[0]!r}"
            )
        longest_suffix = max(loop_suffixes, key=len)
        longest_full = f"{prefix}{longest_suffix}"
        phrases_attr = esc(json.dumps(list(loop_suffixes), ensure_ascii=False))
        first = loop_suffixes[0]
        return f"""        <h1 data-reveal-item data-reveal-i="0">
          <span class="visually-hidden">{esc(h1)}</span>
          <span class="alt-service-hero__h1-stack" aria-hidden="true">
            <span class="alt-service-hero__h1-ghost">{esc(longest_full)}</span>
            <span class="alt-service-hero__h1-live">
              <span class="alt-hero__title-line">{esc(prefix)}</span><span class="alt-hero__typewriter" data-alt-typewriter data-typewriter-phrases="{phrases_attr}">
              <span class="alt-hero__typewriter-ghost">{esc(longest_suffix)}</span>
              <span class="alt-hero__typewriter-live">
                <span class="alt-hero__typewriter-text" data-typewriter-text>{esc(first)}</span><span class="alt-hero__caret" aria-hidden="true"></span>
              </span>
            </span>
            </span>
          </span>
        </h1>"""
    phrases_attr = esc(json.dumps([h1], ensure_ascii=False))
    return f"""        <h1 data-reveal-item data-reveal-i="0">
          <span class="visually-hidden">{esc(h1)}</span>
          <span class="alt-hero__typewriter" data-alt-typewriter data-typewriter-once data-typewriter-phrases="{phrases_attr}" aria-hidden="true">
            <span class="alt-hero__typewriter-ghost">{esc(h1)}</span>
            <span class="alt-hero__typewriter-live">
              <span class="alt-hero__typewriter-text" data-typewriter-text>{esc(h1)}</span><span class="alt-hero__caret" aria-hidden="true"></span>
            </span>
          </span>
        </h1>"""


BROLLOP_FAQS: tuple[tuple[str, str], ...] = (
    (
        "Spelar ni utanför Växjö?",
        "Ja. Vi utgår från Växjö och spelar på bröllop i hela Småland och Skåne. "
        "Längre resor går också bra om vi kommer överens om upplägget.",
    ),
    (
        "Hur långt i förväg behöver vi boka?",
        "För populära datum är det bra att höra av sig ungefär ett år i förväg. "
        "Hör av er så snart ni har datum och lokal klart.",
    ),
    (
        "Kan vi önska låtar?",
        "Ja. Skicka era önskemål i förväg så spelar vi dem om vi kan. Vi har också bra koll på vad som får fart på dansgolvet. "
        "Er första dans ingår alltid, live eller från Spotify genom vårt ljud.",
    ),
    (
        "Spelar ni utomhus?",
        "Det beror på plats, väder och vad som skyddar bandet och utrustningen. "
        "Berätta tidigt om ni vill ha musik utomhus, så kan vi ta ställning till det när ni bokar.",
    ),
    (
        "Samarbetar ni med några bröllopslokaler?",
        "Vi spelar på bröllop i hela Småland och Skåne och återkommer ofta till Asa Herrgård och Norraby gård.",
    ),
)

SERVICE_HERO_SLIDESHOW_KEYS = frozenset({"brollop", "foretag"})
SERVICE_HERO_SLIDESHOW_SCRIPT = (
    '  <script src="/assets/js/alt-service-hero-slideshow.js" defer></script>\n'
)

SERVICE_FAQ_ACCORDION_SCRIPT = (
    '  <script src="/assets/js/alt-faq-accordion.js" defer></script>\n'
)
TALLY_EMBED_SCRIPT = '  <script src="/assets/js/tally-embed.js" defer></script>\n'
FORETAG_PAGE_SCRIPTS = f"{SERVICE_FAQ_ACCORDION_SCRIPT}{TALLY_EMBED_SCRIPT}"
MINGEL_PAGE_SCRIPTS = FORETAG_PAGE_SCRIPTS

# stem, alt, width, height, object-position per slide (ordered list for CMS Hero-bilder).
SERVICE_HERO_SLIDES: dict[str, list[tuple[str, str, int, int, str]]] = {
    "brollop": [
        (
            "halvfjorton-03-hero",
            "Fest med guldkonfetti och trummor bland gäster vid bord",
            2400,
            1600,
            "center 38%",
        ),
        (
            "halvfjorton-trumpet-barn-wedding",
            "Trumpetare och brudpar på dansgolvet",
            2400,
            1600,
            "center",
        ),
    ],
    "foretag": [
        (
            "halvfjorton-01",
            "Band på stor scen med varmt ljus och publik i festsal",
            2400,
            1600,
            "center",
        ),
    ],
    "mingel": [
        (
            "halvfjorton-04",
            "Sångare och band på rustik träscen med professionellt scenljus",
            1280,
            853,
            "center",
        ),
    ],
}


def _service_hero_img_urls(stem: str) -> tuple[str, str]:
    base = f"/assets/img/gallery/{stem}"
    if stem == "halvfjorton-trumpet-barn-wedding":
        return (
            f"{base}-800w.webp",
            f"{base}.webp 2400w, {base}-800w.webp 800w",
        )
    return (
        f"{base}-800w.webp",
        (
            f"{base}-480w.webp 480w, {base}-800w.webp 800w, "
            f"{base}-1200w.webp 1200w, {base}-1920w.webp 1920w"
        ),
    )


def _service_hero_slide_markup(
    stem: str,
    alt: str,
    width: int,
    height: int,
    position: str,
    *,
    first: bool,
) -> str:
    src, srcset = _service_hero_img_urls(stem)
    pos = f' style="object-position: {position};"' if position else ""
    loading = "eager" if first else "lazy"
    fp = ' fetchpriority="high"' if first else ""
    return f"""          <div class="alt-service-hero__slide">
            <img
              class="alt-service-hero__img"
              src="{src}"
              srcset="{srcset}"
              sizes="100vw"
              alt="{esc(alt)}"
              width="{width}"
              height="{height}"
              loading="{loading}"
              decoding="async"{fp}{pos}
            >
          </div>"""


def service_hero_banner(
    service_key: str,
    h1: str,
    description: str,
    *,
    loop_suffixes: tuple[str, ...] | None = None,
) -> str:
    slides = SERVICE_HERO_SLIDES[service_key]
    if service_key in SERVICE_HERO_SLIDESHOW_KEYS:
        slide_html = "\n".join(
            _service_hero_slide_markup(stem, alt, w, h, pos, first=i == 0)
            for i, (stem, alt, w, h, pos) in enumerate(slides)
        )
        return f"""    <header class="alt-service-hero">
      <div class="alt-service-hero__media alt-service-hero__media--slideshow" data-cms-hero="{service_key}" aria-hidden="true">
        <div class="alt-service-hero__carousel">
{slide_html}
        </div>
      </div>
      <div class="alt-service-hero__scrim" aria-hidden="true"></div>
      <div class="alt-service-hero__content" data-reveal-group="hero">
{service_hero_typewriter_h1(h1, loop_suffixes=loop_suffixes)}
        <p class="alt-service-hero__dek" data-reveal-item data-reveal-i="1">{esc(description)}</p>
        <div class="alt-service-hero__actions" data-reveal-item data-reveal-i="2">
          <a class="alt-btn alt-btn--primary" href="/kontakt/#offert">Kontakta oss</a>
        </div>
      </div>
    </header>"""
    stem, alt, width, height, position = slides[0]
    src, srcset = _service_hero_img_urls(stem)
    position_attr = f' style="object-position: {position};"' if position else ""
    return f"""    <header class="alt-service-hero">
      <div class="alt-service-hero__media" data-cms-hero="{service_key}" aria-hidden="true">
        <img
          class="alt-service-hero__img"
          src="{src}"
          srcset="{srcset}"
          sizes="100vw"
          alt="{esc(alt)}"
          width="{width}"
          height="{height}"
          loading="eager"
          decoding="async"{position_attr}
        >
      </div>
      <div class="alt-service-hero__scrim" aria-hidden="true"></div>
      <div class="alt-service-hero__content" data-reveal-group="hero">
{service_hero_typewriter_h1(h1, loop_suffixes=loop_suffixes)}
        <p class="alt-service-hero__dek" data-reveal-item data-reveal-i="1">{esc(description)}</p>
        <div class="alt-service-hero__actions" data-reveal-item data-reveal-i="2">
          <a class="alt-btn alt-btn--primary" href="/kontakt/#offert">Kontakta oss</a>
        </div>
      </div>
    </header>"""


def service_chapter(title: str, paragraphs: list[str], extra_html: str = "", modifier: str = "") -> str:
    mod = f" alt-svc-chapter--{modifier}" if modifier else ""
    ps = "\n".join(f"          <p>{p}</p>" for p in paragraphs)
    extra = f"\n{extra_html}" if extra_html else ""
    return f"""    <section class="alt-svc-chapter section{mod}" data-reveal>
      <div class="alt-svc-wrap alt-svc-chapter__inner">
        <h2 class="alt-svc-chapter__title">{esc(title)}</h2>
        <div class="alt-svc-chapter__body">
{ps}{extra}
        </div>
      </div>
    </section>"""


def service_addon_figure(
    stem: str,
    alt: str,
    *,
    width: int = 2400,
    height: int = 1600,
) -> str:
    return wedding_figure(
        stem,
        alt,
        "(max-width: 900px) 100vw, min(42vw, 520px)",
        width=width,
        height=height,
        figure_class="alt-svc-addon__figure",
    )


GALLERY_STEMS_800_1600 = frozenset(
    {
        "halvfjorton-band-pink-haze",
        "halvfjorton-barn-purple-stage",
        "halvfjorton-garden-mingel",
        "halvfjorton-garden-sax-barn",
        "halvfjorton-keys-guitarists-pink",
        "halvfjorton-stage-blue-dining-hall",
        "halvfjorton-stage-from-above-blue",
        "halvfjorton-warehouse-green-stage",
    }
)


def _gallery_src_and_srcset(stem: str) -> tuple[str, str]:
    base = f"/assets/img/gallery/{stem}"
    if stem in GALLERY_STEMS_800_1600:
        return (
            f"{base}-800w.webp",
            f"{base}-800w.webp 800w, {base}-1600w.webp 1600w",
        )
    return (
        f"{base}-800w.webp",
        (
            f"{base}-480w.webp 480w, {base}-800w.webp 800w, "
            f"{base}-1200w.webp 1200w, {base}-1920w.webp 1920w"
        ),
    )


def wedding_figure(
    stem: str,
    alt: str,
    sizes: str,
    width: int = 2400,
    height: int = 1600,
    figure_class: str = "alt-wedding-figure",
    loading: str = "lazy",
) -> str:
    src, srcset = _gallery_src_and_srcset(stem)
    return f"""          <figure class="{figure_class}">
            <img
              src="{src}"
              srcset="{srcset}"
              sizes="{sizes}"
              alt="{esc(alt)}"
              width="{width}"
              height="{height}"
              loading="{loading}"
              decoding="async"
            >
          </figure>"""


def faq_page_ld(qa_pairs: tuple[tuple[str, str], ...]) -> str:
    entities = [
        {
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a},
        }
        for q, a in qa_pairs
    ]
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities,
    }
    return _indent_ld(data)


def wedding_faq_ld() -> str:
    return faq_page_ld(BROLLOP_FAQS)


def wedding_service_ld() -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": "Bröllopsband",
        "description": (
            "Bröllopsband från Växjö med åtta musiker och blås. "
            "Fest, mingel och vigselmusik på bröllop i Småland och Skåne."
        ),
        "url": f"{SITE}/brollop/",
        "areaServed": [
            {"@type": "City", "name": "Växjö"},
            {"@type": "AdministrativeArea", "name": "Småland"},
            {"@type": "AdministrativeArea", "name": "Skåne"},
        ],
        "provider": {
            "@type": "MusicGroup",
            "name": "Halv Fjorton",
            "url": f"{SITE}/",
        },
    }
    return _indent_ld(data)


class ServiceAddon(NamedTuple):
    stem: str
    alt: str
    title: str
    body: str
    width: int = 1280
    height: int = 720


class StandardServicePage(NamedTuple):
    service_key: str
    hero_h1: str
    hero_dek: str
    split_title: str
    split_paragraphs: tuple[str, ...]
    split_stem: str
    split_alt: str
    addons: tuple[ServiceAddon, ...]
    faqs: tuple[tuple[str, str], ...]
    closing_text: str
    split_sizes: str = "(max-width: 900px) 100vw, min(46vw, 640px)"
    closing_embed_form: bool = False
    closing_email_link: str | None = None
    hero_typewriter_suffixes: tuple[str, ...] | None = None


FORETAG_FAQS: tuple[tuple[str, str], ...] = (
    (
        "Hur länge spelar ni?",
        "På de flesta företagsfester spelar vi två set partymusik. Mingel eller andra delar planeras separat i offerten.",
    ),
    (
        "Kan ni ta mingel och fest samma kväll?",
        "Ja, det är ett av våra vanligaste upplägg. Mingel i mer återhållen stil, sedan två set dans när rummet är redo.",
    ),
    (
        "Ingår ljud och ljus?",
        "Vi kan ordna ljud och ljus om ni saknar leverantör till tillställningen. Har ni redan extern teknik samarbetar vi gärna med dem så att kvällen hänger ihop.",
    ),
    (
        "Kan ni fakturera?",
        "Ja. Vi har F-skatt och skickar faktura.",
    ),
    (
        "Vad behöver ni veta innan offert?",
        "Datum, adress, ungefärligt antal, om det är mingel plus fest, och om lokalen har begränsningar. Resten tar vi i dialogen med er.",
    ),
)

MINGEL_FAQS: tuple[tuple[str, str], ...] = (
    (
        "Kan ni spela både mingel och fest?",
        "Ja. Många väljer att vi tar hela kvällen, från lugnare musik när gästerna kommer till fullt dansgolv senare.",
    ),
    (
        "Kan ni spela under middagen?",
        "Ja, vi spelar gärna någon låt vid utvalda tillfällen under sittningen, eller håller i ett musikquiz med gästerna.",
    ),
    (
        "Måste man boka alla åtta musiker?",
        "När man bokar Halv Fjorton får man hela bandet, alltid. Åtta musiker med full blåssektion ger ett tryck som gör oss till ett coverband utöver det vanliga.",
    ),
    (
        "Spelar ni i hela södra Sverige?",
        "Ja, på förfrågan. Vi spelar ofta i Malmö, Lund, Helsingborg, Växjö, Jönköping, Kalmar, Karlskrona och på Österlen.",
    ),
    (
        "Ingår ljud och ljus?",
        "Det beror på hur stort eventet är. Vi kan ta med egen utrustning eller använda er leverantör, och ser till att ljudet passar lokalen.",
    ),
)


BROLLOP_STANDARD_PAGE = StandardServicePage(
    service_key="brollop",
    hero_h1="Liveband till bröllop",
    hero_dek=(
        "Avsluta dagen på ett storslaget sätt med ett bröllopsband som ger er och era gäster en kväll ni sent glömmer."
    ),
    split_title="Festspelning",
    split_paragraphs=(
        "När middagen är över och första valsen är dansad drar vi igång festen på riktigt. Vi är ett bröllopsband från Växjö med åtta musiker och blåssektion, och vi tar er genom flera genrer under kvällen. Vi har lång erfarenhet av bröllop och vet vad som får dansgolvet att leva.",
    ),
    split_stem="halvfjorton-05",
    split_alt="Band i rustik lokal med publik i silhuett och blå scenbelysning",
    addons=(
        ServiceAddon(
            "halvfjorton-garden-mingel",
            "Musiker som spelar utomhus",
            "Mingelmusik",
            "Före middagen spelar vi lugnare och jazzigare musik medan gästerna minglar. Vi tar med ett eget ljudsystem för detta.",
        ),
        ServiceAddon(
            "halvfjorton-garden-sax-barn",
            "Sång och slagverk på scen i dramatiskt ljus",
            "Vigselmusik",
            "Till vigseln har vi solist och komp, och låtarna väljer vi tillsammans med er. Har ni andra önskemål för vigseln löser vi det efter dem.",
            width=1280,
            height=720,
        ),
    ),
    faqs=BROLLOP_FAQS,
    closing_text="Berätta om ert bröllop, så återkommer vi med ett förslag.",
)

FORETAG_STANDARD_PAGE = StandardServicePage(
    service_key="foretag",
    hero_h1="Liveband till företagsfest",
    hero_dek=(
        "Oavsett tillfälle levererar vi en medryckande upplevelse som lyfter stämningen. "
        "Åtta musiker med blåssektion, från första minglet till sista dansen."
    ),
    split_title="Upplägg efter ert program",
    split_paragraphs=(
        "Ni berättar hur kvällen ska löpa: mingel, middag, tal, dans. Vi är flexibla och tar fram ett specialupplägg för just er tillställning, med volym och tider som passar lokalen och gästerna.",
        "Vanligt upplägg är mingel 45 till 90 minuter medan gästerna kommer in, paus under middag och tal, därefter tar vi över och ställer till med ösigt dansgolv!",
    ),
    split_stem="halvfjorton-stage-blue-dining-hall",
    split_alt="Scen med blått ljus i festlokal",
    addons=(
        ServiceAddon(
            "halvfjorton-barn-purple-stage",
            "Scen i lada med lila ljus och rök",
            "Mingelmusik",
            "När gästerna strömmar in spelar vi lugnare musik som låter samtalen flyta. Jazz, soul och svenska visor i en blandning som sätter tonen för kvällen.",
        ),
        ServiceAddon(
            "halvfjorton-01",
            "Band på stor scen med varmt ljus och publik i festsal",
            "Artistkomp",
            "Planerar ni att boka en artist till ert event? Vi har lång erfarenhet av att kompa artister, oavsett genre och sättning, och gör framträdandet komplett.",
            width=1280,
            height=720,
        ),
        ServiceAddon(
            "halvfjorton-warehouse-green-stage",
            "Keyboard på scen i lagerlokal",
            "Middagsunderhållning",
            "Vi spelar gärna en eller två låtar vid utvalda tillfällen under sittningen. Ett uppskattat inslag är ett interaktivt musikquiz med gästerna, som alltid går hem.",
        ),
    ),
    faqs=FORETAG_FAQS,
    closing_text=(
        "Hör av er via formuläret på kontaktsidan. Vi återkommer med upplägg och offert när vi vet plats, tider och vilka delar ni vill boka."
    ),
    closing_embed_form=True,
    closing_email_link="E-post? Klicka här",
    hero_typewriter_suffixes=("företagsfest", "personalfest", "kickoff", "jubileum"),
)

MINGEL_STANDARD_PAGE = StandardServicePage(
    service_key="mingel",
    hero_h1="Liveband till fest och mingel",
    hero_dek=(
        "Åttamannaband som sätter stämningen, oavsett om kvällen börjar med skål eller går rakt ut på dansgolvet."
    ),
    split_title="Från första glaset till sista låten",
    split_paragraphs=(
        "Oavsett om det är 50-årsfest, jubileum eller sommarfest på en äng bär vi kvällen hela vägen. "
        "Vi börjar lågmält medan gästerna minglar, och när talen är hållna och borden dukats av drar vi igång festen på riktigt. "
        "Vi är flexibla och anpassar upplägget efter er kväll.",
    ),
    split_stem="halvfjorton-band-pink-haze",
    split_alt="Musiker på scen med ljus och scenrök",
    addons=(
        ServiceAddon(
            "halvfjorton-keys-guitarists-pink",
            "Band som gör sig redo på scen inför publik",
            "Festspelning",
            "När det är dags att dansa tar vi över och ställer till med ösigt dansgolv. Två set fullt ös med blåssektion, anpassat efter er publik och kvällens tempo.",
        ),
        ServiceAddon(
            "halvfjorton-stage-from-above-blue",
            "Scen med instrument sett ovanifrån",
            "Middagsunderhållning",
            "Vi spelar gärna en eller två låtar vid utvalda tillfällen under sittningen. Ett uppskattat inslag är ett interaktivt musikquiz med gästerna, som alltid går hem.",
            width=1280,
            height=720,
        ),
        ServiceAddon(
            "halvfjorton-garden-mingel",
            "Musiker som spelar utomhus",
            "Mingel",
            "När gästerna strömmar in spelar vi lugnare musik som låter samtalen flyta. Jazz, soul och svenska visor i en blandning som sätter tonen för kvällen.",
            width=1280,
            height=720,
        ),
    ),
    faqs=MINGEL_FAQS,
    closing_text=(
        "Hör av er via formuläret på kontaktsidan. Vi återkommer med upplägg och offert när vi vet plats, tider och vilka delar ni vill boka."
    ),
    closing_embed_form=True,
    closing_email_link="E-post? Klicka här",
    hero_typewriter_suffixes=("fest och mingel", "50-årsfesten", "jubileet", "sommarfesten"),
)


def standard_service_page_body(page: StandardServicePage) -> str:
    hero = service_hero_banner(
        page.service_key,
        page.hero_h1,
        page.hero_dek,
        loop_suffixes=page.hero_typewriter_suffixes,
    )
    split_ps = "\n".join(f"            <p>{esc(p)}</p>" for p in page.split_paragraphs)
    split_figure = wedding_figure(
        page.split_stem,
        page.split_alt,
        page.split_sizes,
        figure_class="alt-svc-inline-figure",
    )
    addon_blocks: list[str] = []
    for addon in page.addons:
        addon_blocks.append(
            f"""          <div class="alt-svc-addon">
{service_addon_figure(addon.stem, addon.alt, width=addon.width, height=addon.height)}
            <h3 class="alt-svc-addon__title">{esc(addon.title)}</h3>
            <p>{esc(addon.body)}</p>
          </div>"""
        )
    faq_list = faq_list_two_columns(list(page.faqs))
    addon_grid_class = "alt-svc-addon-grid alt-svc-chapter__body"
    if len(page.addons) >= 3:
        addon_grid_class += " alt-svc-addon-grid--cols-3"
    if page.closing_embed_form:
        closing_actions = f"""          <div class="alt-svc-closing-form contact-offert__form tally-card">
{tally_iframe_markup()}
{contact_form_consent_markup()}
          </div>"""
        if page.closing_email_link:
            closing_actions += f"""
          <p class="alt-svc-closing__email">
            <a href="mailto:halvfjorton@gmail.com">{esc(page.closing_email_link)}</a>
          </p>"""
    else:
        closing_actions = """          <div class="actions">
            <a class="alt-btn alt-btn--primary" href="/kontakt/">Kontakta oss</a>
          </div>"""
    return f"""{hero}
    <section class="alt-svc-chapter section alt-svc-chapter--split alt-svc-chapter--festspelning" data-reveal>
      <div class="alt-svc-wrap alt-svc-chapter__split alt-svc-chapter__layout--copy-first">
        <div class="alt-svc-chapter__split-copy">
          <h2 class="alt-svc-chapter__title">{esc(page.split_title)}</h2>
          <div class="alt-svc-chapter__body">
{split_ps}
          </div>
        </div>
        <div class="alt-svc-chapter__split-media">
{split_figure}
        </div>
      </div>
    </section>
    <section class="alt-svc-chapter section alt-svc-chapter--addons" data-reveal aria-labelledby="tillaggstjanster">
      <div class="alt-svc-wrap">
        <h2 class="alt-svc-section-label" id="tillaggstjanster">Tilläggstjänster</h2>
        <div class="{addon_grid_class}">
{chr(10).join(addon_blocks)}
        </div>
      </div>
    </section>
    <section class="alt-svc-chapter section" data-reveal>
      <div class="alt-svc-wrap alt-faq">
        <h2 class="alt-svc-chapter__title">Vanliga frågor</h2>
{faq_list}
      </div>
    </section>
    <section class="alt-svc-chapter section alt-svc-chapter--closing" data-reveal>
      <div class="alt-svc-wrap">
        <h2 class="alt-svc-chapter__title">Kontakta oss</h2>
        <div class="alt-svc-chapter__body">
          <p>{esc(page.closing_text)}</p>
{closing_actions}
        </div>
      </div>
    </section>"""


def wedding_page_body() -> str:
    return standard_service_page_body(BROLLOP_STANDARD_PAGE)


def gallery_img(
    stem: str,
    alt: str,
    sizes: str = "(max-width: 900px) 100vw, 46vw",
    width: int = 2400,
    height: int = 1600,
    extra_class: str = "",
) -> str:
    base = f"/assets/img/gallery/{stem}"
    cls = f"content-photo{extra_class}"
    return f"""          <figure class="{cls}">
            <img
              src="{base}-800w.webp"
              srcset="{base}-480w.webp 480w, {base}-800w.webp 800w, {base}-1200w.webp 1200w, {base}-1920w.webp 1920w"
              sizes="{sizes}"
              alt="{esc(alt)}"
              width="{width}"
              height="{height}"
              loading="lazy"
              decoding="async"
            >
          </figure>"""


def youtube_video_object_ld(
    name: str,
    description: str,
    video_id: str,
    thumbnail_url: str,
    start_seconds: int | None = None,
) -> str:
    embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}"
    content_url = f"https://www.youtube.com/watch?v={video_id}"
    if start_seconds:
        embed_url += f"?start={start_seconds}"
        content_url += f"&t={start_seconds}"
    data = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": name,
        "description": description,
        "thumbnailUrl": thumbnail_url,
        "embedUrl": embed_url,
        "contentUrl": content_url,
        "publisher": {
            "@type": "Organization",
            "name": "Halv Fjorton",
            "url": f"{SITE}/",
        },
    }
    return _indent_ld(data)


def wedding_video_ld() -> str:
    return youtube_video_object_ld(
        WEDDING_VIDEO_TITLE,
        "Livevideo med Halv Fjorton som cover- och bröllopsband i södra Sverige.",
        WEDDING_VIDEO_ID,
        f"https://i.ytimg.com/vi/{WEDDING_VIDEO_ID}/hqdefault.jpg",
    )


def lyssna_page_video_ld() -> list[str]:
    yt_thumb = lambda vid: f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    return [
        youtube_video_object_ld(
            "Signed Sealed Delivered - Halv Fjorton 2025",
            "Livefilm med Halv Fjorton från 2025.",
            "V2Nb8jMKUCk",
            f"{SITE}/assets/img/gallery/halvfjorton-01-1200w.webp",
        ),
        youtube_video_object_ld(
            "Halv Fjorton Reel 2022",
            "Kortare klipp från spelningar 2022.",
            "gm5C41wqYuU",
            yt_thumb("gm5C41wqYuU"),
        ),
        youtube_video_object_ld(
            "A Soulful Lucia 2025",
            "Julkonsert med Halv Fjorton, inspelning från lucia 2025.",
            SOULFUL_LUCIA_2025_VIDEO_ID,
            f"{SITE}{SOULFUL_LUCIA_2025_IMG}-1200w.webp",
            SOULFUL_LUCIA_2025_START,
        ),
        youtube_video_object_ld(
            "A Soulful Christmas 2024 - 8 december, Nygatan 6",
            "Julkonsert A Soulful Christmas 2024 på Nygatan 6 i Växjö.",
            "vV8aavPxYss",
            yt_thumb("vV8aavPxYss"),
        ),
        youtube_video_object_ld(
            "A Soulful Christmas 2023 - 3 december, Nygatan 6",
            "Julkonsert A Soulful Christmas 2023 på Nygatan 6 i Växjö.",
            "UytyTLnKDWQ",
            yt_thumb("UytyTLnKDWQ"),
        ),
    ]


def breadcrumb_ld(items):
    elements = ",\n".join(
        f'''      {{
        "@type": "ListItem",
        "position": {i},
        "name": "{name}",
        "item": "{SITE}{path}"
      }}'''
        for i, (path, name) in enumerate(items, 1)
    )
    return f"""{{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
{elements}
    ]
  }}"""


def service_ld(name, desc, url):
    data = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": name,
        "description": desc,
        "url": f"{SITE}{url}",
        "areaServed": load_org()["areaServed"],
        "provider": {
            "@type": "MusicGroup",
            "name": "Halv Fjorton",
            "url": f"{SITE}/",
        },
    }
    return _indent_ld(data)


def music_event_ld(name: str, start: str, description: str, ticket_url: str, image_path: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "MusicEvent",
        "name": name,
        "description": description,
        "startDate": start,
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "image": f"{SITE}{image_path}-1200w.webp",
        "url": ticket_url,
        "location": {
            "@type": "Place",
            "name": "Nygatan 6",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "Nygatan 6",
                "addressLocality": "Växjö",
                "postalCode": "352 33",
                "addressCountry": "SE",
            },
        },
        "performer": {
            "@type": "MusicGroup",
            "name": "Halv Fjorton",
            "url": f"{SITE}/",
        },
        "organizer": {
            "@type": "Organization",
            "name": "Nygatan 6",
            "url": "https://www.nygatan6.se/",
        },
        "offers": {
            "@type": "Offer",
            "url": ticket_url,
            "availability": "https://schema.org/InStock",
        },
    }
    return _indent_ld(data)


def soulful_christmas_event_ld() -> list[str]:
    desc = (
        "Julkonsert med soul, funk, jazz och komiska inslag. Halv Fjorton och gäster på Nygatan 6 i Växjö."
    )
    return [
        music_event_ld(
            "A Soulful Christmas (16:00)",
            "2026-12-12T16:00:00+01:00",
            desc,
            SOULFUL_CHRISTMAS_TICKETS,
            SOULFUL_CHRISTMAS_IMG,
        ),
        music_event_ld(
            "A Soulful Christmas (19:30)",
            "2026-12-12T19:30:00+01:00",
            desc,
            SOULFUL_CHRISTMAS_TICKETS,
            SOULFUL_CHRISTMAS_IMG,
        ),
    ]


def soulful_christmas_ticket_card() -> str:
    base = SOULFUL_CHRISTMAS_IMG
    return f"""        <article
          class="event-ticket"
          data-event-ticket
          data-event-start="{SOULFUL_CHRISTMAS_START}"
          data-event-end="{SOULFUL_CHRISTMAS_END}"
        >
          <div class="event-ticket__grid">
            <div class="event-ticket__poster">
              <div class="event-ticket__status" aria-live="polite">
                <span class="event-ticket__badge" data-event-badge>Kommande</span>
                <span class="event-ticket__countdown" data-event-countdown></span>
              </div>
              <img
                src="{base}-800w.webp"
                srcset="{base}-480w.webp 480w, {base}-800w.webp 800w, {base}-1200w.webp 1200w"
                sizes="(max-width: 767px) 100vw, 38vw"
                alt="Affisch för A Soulful Christmas med Halv Fjorton på Nygatan 6"
                width="1200"
                height="900"
                loading="lazy"
                decoding="async"
              >
            </div>
            <div class="event-ticket__main">
              <h2 class="event-ticket__title">A Soulful Christmas</h2>
              <p class="event-ticket__subtitle">med Halv Fjorton &amp; gäster</p>
              <p class="visually-hidden">Lördag 12 december 2026 · Nygatan 6, Växjö · 16:00 och 19:30</p>
              <p class="event-ticket__when">Lördag 12 december 2026</p>
              <ul class="event-ticket__times">
                <li><span class="event-ticket__chip">16:00</span></li>
                <li><span class="event-ticket__chip">19:30</span></li>
              </ul>
              <p class="event-ticket__place">
                <svg class="event-ticket__pin" width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M12 21s7-4.5 7-11a7 7 0 1 0-14 0c0 6.5 7 11 7 11Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                  <circle cx="12" cy="10" r="2.25" stroke="currentColor" stroke-width="1.5"/>
                </svg>
                <span>Nygatan 6, Växjö</span>
              </p>
              <p class="event-ticket__text">Växjö stad i juleglans, och vad passar då bättre än en julkonsert? Halv Fjorton återvänder och bjuder på svängig julstämning med soul, funk, jazz och komiska inslag. Julklassikerna får en skrud du aldrig hört förut, och kanske smyger sig en och annan sketch in…</p>
              <div class="event-ticket__actions" aria-hidden="true">
                <span class="alt-btn alt-btn--primary event-ticket__cta event-ticket__cta-spacer">Köp biljetter</span>
              </div>
            </div>
          </div>
          <a
            class="event-ticket__stretched-link"
            href="{SOULFUL_CHRISTMAS_TICKETS}"
            target="_blank"
            rel="noopener noreferrer"
          >
            <span class="alt-btn alt-btn--primary event-ticket__cta">Köp biljetter</span>
          </a>
        </article>"""


def page(
    path: str,
    title: str,
    description: str,
    extra_ld: list[str] | None = None,
    body: str = "",
    page_class: str = "",
    outfile: Path | None = None,
    breadcrumb_name: str | None = None,
    extra_scripts: str = "",
    hidden: bool = False,
):
    canonical = f"{SITE}{path}"
    crumb_label = breadcrumb_name or title.split(" | ")[0].split(", ")[0]
    graphs = [music_group_ld(), breadcrumb_ld([("/", "Hem")] + ([] if path == "/" else [(path, crumb_label)]))]
    if extra_ld:
        graphs.extend(extra_ld)
    jsonld = ",\n  ".join(graphs)
    body_class = "alt-page alt-page--inner"
    if page_class:
        body_class = f"{body_class} {page_class}"
    if "alt-page--service-banner" in page_class:
        if "alt-hero-typewriter.js" not in extra_scripts:
            extra_scripts = f"{extra_scripts}{SERVICE_HERO_TYPEWRITER_SCRIPT}"
    nav_block = home_nav_block(path, "/#offert")
    mobile_menu = mobile_menu_block(path, "/#offert")
    toggle = alt_header_mobile_controls_markup("mobile-menu")
    if hidden and path not in HIDDEN_SERVICE_PATHS:
        raise ValueError(f"hidden=True requires path in HIDDEN_SERVICE_PATHS, got {path}")
    if not hidden and path in HIDDEN_SERVICE_PATHS:
        raise ValueError(f"path {path} must use hidden=True")
    robots = "noindex,nofollow" if hidden else "index,follow"
    html = f"""<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="format-detection" content="telephone=no, date=no, email=no, address=no">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{canonical}">
  <meta name="robots" content="{robots}">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="sv_SE">
  <meta property="og:site_name" content="Halv Fjorton">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{OG}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{OG}">
  <link rel="icon" href="/assets/img/favicon.png" type="image/png">
  <link rel="apple-touch-icon" href="/assets/img/favicon.png">
{font_preloads('/assets')}
  <link rel="stylesheet" href="/assets/css/alt.css">
  <script type="application/ld+json">
  {jsonld}
  </script>
</head>
<body class="{body_class}">
  <a class="skip-link" href="#innehall">Hoppa till innehållet</a>
  <header class="alt-header site-header" data-nav>
    <div class="alt-header__inner header-inner">
      <a class="alt-brand brand" href="/" aria-label="Halv Fjorton">
{brand_logo_markup()}
      </a>
{toggle}
{nav_block}
    </div>
  </header>
{alt_header_scroll_bootstrap_script()}
{mobile_menu}
  <main id="innehall" class="alt-inner-main">
{body}
  </main>
{modern_footer_markup()}
  <script src="/assets/js/nav.js"></script>
  <script src="/assets/js/alt-nav.js" defer></script>
  <script src="/assets/js/footer-year.js" defer></script>
  <script src="/assets/js/video-facade.js" defer></script>
{extra_scripts}</body>
</html>
"""
    dest = outfile
    if dest is None:
        dest = OUT_ROOT / (path.lstrip("/") + ("index.html" if path.endswith("/") else ""))
        if path == "/":
            dest = OUT_ROOT / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
    print("wrote", dest.relative_to(OUT_ROOT))


def write_pages():
    om_oss_member_cards = "\n".join(om_oss_member_card(entry) for entry in OM_OSS_MEMBERS)
    page(
        "/brollop/",
        "Bröllopsband från Växjö | Halv Fjorton",
        "Bröllopsband från Växjö med åtta musiker och blås. Fest, mingel och vigselmusik på bröllop i Småland och Skåne.",
        breadcrumb_name="Bröllop",
        extra_ld=[wedding_service_ld(), wedding_faq_ld()],
        extra_scripts=f"{SERVICE_FAQ_ACCORDION_SCRIPT}{SERVICE_HERO_SLIDESHOW_SCRIPT}",
        body=wedding_page_body(),
        page_class="alt-page--wedding alt-page--service-banner",
    )

    page(
        "/foretag/",
        f"Coverband till företagsfest Malmö och Skåne | {BRAND_TITLE}",
        (
            "Personalfest, kickoff och jubileum med åtta musiker och blåssektion. "
            "Mingelmusik, artistkomp och middagsunderhållning i Skåne och Småland."
        ),
        breadcrumb_name="Företag",
        extra_ld=[
            service_ld(
                "Företagsfest och festband",
                "Musikunderhållning till personalfest, kickoff och jubileum. Mingelmusik, artistkomp och middagsunderhållning.",
                "/foretag/",
            ),
            faq_page_ld(FORETAG_FAQS),
        ],
        extra_scripts=f"{FORETAG_PAGE_SCRIPTS}{SERVICE_HERO_SLIDESHOW_SCRIPT}",
        page_class="alt-page--service-banner",
        body=standard_service_page_body(FORETAG_STANDARD_PAGE),
    )

    page(
        "/fest-och-mingel/",
        f"Liveband till fest och mingel | {BRAND_TITLE}",
        (
            "Åttamannaband till fest och mingel med blåssektion. "
            "Från lugn stämning till fullt dansgolv i samma kväll."
        ),
        breadcrumb_name="Fest och mingel",
        extra_ld=[
            service_ld(
                "Fest och mingel",
                "Liveband till fest och mingel med mingel, middagsunderhållning och festspelning.",
                "/fest-och-mingel/",
            ),
            faq_page_ld(MINGEL_FAQS),
        ],
        extra_scripts=MINGEL_PAGE_SCRIPTS,
        page_class="alt-page--service-banner",
        body=standard_service_page_body(MINGEL_STANDARD_PAGE),
    )

    page(
        "/kompband/",
        f"Kompband för artist i Småland och Skåne | {BRAND_TITLE}",
        "Kompband för solist eller inhyrd artist på bröllop, fest och företagsevent. Växjö, Malmö, Lund och övriga södra Sverige.",
        breadcrumb_name="Kompband",
        hidden=True,
        extra_ld=[
            service_ld(
                "Kompband för artist",
                "Livekompri för solist eller inhyrd artist på bröllop, fest och företagsevent.",
                "/kompband/",
            )
        ],
        body=f"""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Kompband för solist och artist</h1>
{aeo_answer("Halv Fjorton fungerar som kompband när ni vill att en solist, gäst eller inhyrd artist ska framföras med fullt liveband. Samma åtta musiker och egen blåssektion som på våra vanliga gig.")}
        <p class="lead">Vanligt vid vigsel, psalmer, gästsång eller när eventbolag tar in en artist som behöver ordnat komp.</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap grid-2">
        <div>
          <h2>När det passar</h2>
          <ul class="list-check">
            <li>Bröllopsvigsel med solist eller psalmer</li>
            <li>Gäst som vill sjunga med band</li>
            <li>Företagsevent med inhyrd artist</li>
            <li>Specialmoment under fest eller mingel</li>
          </ul>
        </div>
        <div>
          <p>Skicka låtlista, tonart och ungefärliga tider i god tid. Vi återkommer med förslag och offert via <a href="mailto:halvfjorton@gmail.com">halvfjorton@gmail.com</a>.</p>
          <div class="actions">
            <a class="btn btn-primary" href="/kontakt/#offert">Begär offert</a>
            <a class="btn btn-ghost" href="/brollop/">Bröllop</a>
          </div>
        </div>
      </div>
    </section>
""",
    )

    page(
        "/50-arsfest/",
        f"50-årsfest och privatfest | liveband {BRAND_TITLE.split(' | ')[0]}",
        "Liveband till 50-årsfest, privatfest och födelsedag i Växjö, Småland och Skåne. Två set soul, funk och svenska klassiker.",
        breadcrumb_name="50-årsfest",
        hidden=True,
        extra_ld=[
            service_ld(
                "50-årsfest och privatfest",
                "Festmusik till 50-årsfest, privatfest och födelsedag med två set live.",
                "/50-arsfest/",
            )
        ],
        body=f"""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Liveband till 50-årsfest och privatfest</h1>
{aeo_answer("Vi spelar 50-årsfester och andra privata tillställningar med samma sättning som till bröllop och företag: två set med dans, blås och igenkännbara låtar.")}
        <p class="lead">Lokal, loge eller hembygdsgård i Småland eller Skåne. Hör av er med datum och ort.</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap">
        <p>Repertoaren växlar mellan soul, funk, rock och svenska klassiker så att både dansgolv och generationsmix fungerar. Mingel samma kväll går att kombinera.</p>
        <div class="actions">
          <a class="btn btn-primary" href="/kontakt/">Hör av er</a>
          <a class="btn btn-ghost" href="/faq/">Vanliga frågor</a>
        </div>
      </div>
    </section>
""",
    )

    page(
        "/julkonsert/",
        f"Julkonsert A Soulful Christmas i Växjö | {BRAND_TITLE}",
        "Halv Fjortons egen julkonsert med soul och funk sedan 2018. Spelas på Nygatan 6 i Växjö sedan 2023.",
        breadcrumb_name="Julkonsert",
        extra_ld=[
            service_ld(
                "Julkonsert",
                "Egen årlig julkonsert med egna jullåtar och covers i soul- och funkstil, Växjö.",
                "/julkonsert/",
            )
        ],
        body="""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>A Soulful Christmas i Växjö</h1>
        <p class="aeo-answer">Sedan 2018 arrangerar Halv Fjorton en egen julkonsert med egna låtar och jultolkningar i soul och funk. Sedan 2023 spelar vi på Nygatan 6 i Växjö, nästan varje år.</p>
        <p class="lead">Det här är bandets egna konsert, inte en bokningstjänst. Följ datum via <a href="/lyssna/">Lyssna</a> och sociala medier.</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap">
        <p>Vill ni boka bandet till er egen julfest eller företagsjul? Se <a href="/foretag/">företag</a> eller <a href="/kontakt/">kontakt</a>.</p>
      </div>
    </section>
""",
    )

    page(
        "/konserter/",
        f"Konserter | {BRAND_TITLE}",
        "Publik konsert A Soulful Christmas 12 december 2026 på Nygatan 6 i Växjö. Två föreställningar med Halv Fjorton och gäster.",
        breadcrumb_name="Konserter",
        page_class="alt-page--konserter",
        extra_ld=soulful_christmas_event_ld(),
        extra_scripts='  <script src="/assets/js/event-ticket-card.js" defer></script>\n',
        body=f"""    <div class="wrap alt-konserter-page">
      <header class="page-hero compact alt-konserter-page__hero">
        <div class="page-hero-copy">
          <h1>Konserter</h1>
          <p class="lead">Vi spelar inte alltid för privata sammankomster utan gör ibland publika konserter, håll utkik här.</p>
        </div>
      </header>
      <div class="event-ticket-wrap alt-konserter-page__tickets">
{soulful_christmas_ticket_card()}
      </div>
    </div>
""",
    )

    page(
        "/brollopsband-smaland/",
        f"Bröllopsband Småland, Växjö, Kalmar, Älmhult | {BRAND_TITLE}",
        "Bröllopsband i Småland: Växjö, Kalmar, Älmhult och Jönköping. Två set partymusik, mingel och vigselmusik. Egen blåssektion.",
        breadcrumb_name="Bröllopsband Småland",
        hidden=True,
        extra_ld=[
            service_ld(
                "Bröllopsband Småland",
                "Bröllopsband i Småland med två set partymusik till bröllop i Växjö, Kalmar, Älmhult och Jönköping.",
                "/brollopsband-smaland/",
            )
        ],
        body=f"""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Bröllopsband i Småland</h1>
{aeo_answer("Halv Fjorton är hemmahörande i Växjö och spelar bröllop i hela Småland, från Kalmar och Älmhult till Jönköping. Två set dansmusik med egen blåssektion.")}
        <p class="lead">Samma band till mingel, vigsel och fest. Andra orter utanför listan kan fungera - fråga i mejlet.</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap">
        <p>Se hela upplägget på <a href="/brollop/">bröllop</a> eller begär offert direkt.</p>
        <div class="actions">
          <a class="btn btn-primary" href="/kontakt/#offert">Begär offert</a>
          <a class="btn btn-ghost" href="/foretag/">Skåne och Malmö</a>
        </div>
      </div>
    </section>
""",
    )

    page(
        "/coverband-skane-malmo/",
        f"Coverband Skåne, Malmö, Lund, Helsingborg | {BRAND_TITLE}",
        "Coverband och festband i Skåne: Malmö, Lund och Helsingborg. Bröllop, företagsfest och privatfest med åtta musiker.",
        breadcrumb_name="Coverband Skåne",
        hidden=True,
        extra_ld=[
            service_ld(
                "Coverband Skåne",
                "Coverband och festband i Malmö, Lund, Helsingborg och övriga Skåne.",
                "/coverband-skane-malmo/",
            )
        ],
        body=f"""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Coverband i Malmö och Skåne</h1>
{aeo_answer("Vi spelar regelbundet i Skåne med bas i södra Sverige: Malmö, Lund och Helsingborg är vanliga orter. Samma åtta mannasband med soul, funk och svenska klassiker.")}
        <p class="lead">Personalfest, bröllop eller privatfest. Spelningar utanför Skåne och Småland går att diskutera.</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap">
        <p>Läs mer om <a href="/foretag/">företagsfest</a> och <a href="/brollop/">bröllop</a>, eller maila <a href="mailto:halvfjorton@gmail.com">halvfjorton@gmail.com</a>.</p>
      </div>
    </section>
""",
    )

    page(
        "/om-oss/",
        f"Om Halv Fjorton | grundat 2018 i Växjö | {BRAND_TITLE}",
        "Coverband från Växjö. Soul, funk och svenska allsångslåtar med blåssektion. Möt bandet och medlemmarna här.",
        breadcrumb_name="Om oss",
        body=f"""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Om oss</h1>
      </div>
    </header>
    <section class="section">
      <div class="wrap">
        <h2>Vilka är vi?</h2>
        <p>Halv Fjorton är ett coverband från Växjö. Vi var sju från början, och hälften av fjorton är ju sju. Nu är vi åtta, men namnet fick stå kvar. Vårt mål är att ni ska minnas festen länge, och att gästerna fortfarande nynnar på låtarna dagen efter.</p>
      </div>
    </section>
    <section class="section section-alt">
      <div class="wrap split">
        <div>
          <h2>Vad spelar vi?</h2>
          <p>Vår grund är soul och funk, och därifrån tar vi oss vidare till schlager, rock och svenska allsångslåtar. Det viktigaste är att det svänger. Har vi kul på scen har ni kul på dansgolvet.</p>
          <p>Vi är ett coverband med blåssektion, så vi spelar gärna låtar med blåsriff och saxofonsolon. Kort och gott: vi har repertoar för både farfar och de yngre.</p>
        </div>
        <div>
{gallery_img("halvfjorton-01", "Hela bandet på scen i festsal med publik")}
        </div>
      </div>
    </section>
    <section class="section">
      <div class="wrap">
        <h2>Bandet</h2>
        <p>Vi består av åtta fasta musiker: sångare, kompmusiker, slagverk och en eminent blåssektion.</p>
      </div>
    </section>
    <section class="section section-alt om-oss-members-section">
      <div class="wrap">
        <h2>Medlemmarna</h2>
{members_compact_grid(om_oss_member_cards)}
      </div>
    </section>
""",
    )

    page(
        "/lyssna/",
        "Lyssna på Halv Fjorton | film, reel och julkonserter",
        "Se Halv Fjorton live: Signed Sealed Delivered 2025, reel 2022 och julkonserterna A Soulful Christmas.",
        page_class="alt-page--lyssna",
        extra_scripts=LYSSNA_VIDEO_MODAL_SCRIPT,
        extra_ld=lyssna_page_video_ld(),
        body=f"""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Lyssna på oss</h1>
        <p class="lead">Filmer från scen och julkonserter, plus en överblick av repertoaren. Samma band som ni bokar till bröllop, företag och mingel.</p>
        <p class="page-hero__actions">
          <a class="alt-btn alt-btn--primary" href="{INSTAGRAM_PROFILE_URL}" target="_blank" rel="noopener noreferrer">
{INSTAGRAM_ICON_BTN}
            <span>Instagram @halvfjorton</span>
          </a>
        </p>
      </div>
    </header>
    <section class="section" aria-label="Livefilmer">
      <div class="wrap">
{lyssna_video_grid(
    lyssna_video_tile(
        "V2Nb8jMKUCk",
        "Signed Sealed Delivered",
        "Signed Sealed Delivered - Halv Fjorton 2025",
        poster="/assets/img/gallery/halvfjorton-01-1200w.webp",
    ),
    lyssna_video_tile("gm5C41wqYuU", "Reel 2022", "Halv Fjorton Reel 2022"),
)}
      </div>
    </section>
    <section class="section section-alt">
      <div class="wrap">
        <h2>Lyssna på våra julkonserter</h2>
{lyssna_video_grid(
    lyssna_video_tile(
        SOULFUL_LUCIA_2025_VIDEO_ID,
        "A Soulful Lucia 2025",
        "A Soulful Lucia 2025",
        poster=f"{SOULFUL_LUCIA_2025_IMG}-1200w.webp",
        start_seconds=SOULFUL_LUCIA_2025_START,
    ),
    lyssna_video_tile(
        "vV8aavPxYss",
        "A Soulful Christmas 2024",
        "A Soulful Christmas 2024 - 8 december, Nygatan 6",
    ),
    lyssna_video_tile(
        "UytyTLnKDWQ",
        "A Soulful Christmas 2023",
        "A Soulful Christmas 2023 - 3 december, Nygatan 6",
    ),
)}
      </div>
    </section>
    <section class="section" id="repertoar">
      <div class="wrap">
        <div class="lyssna-repertoire-split">
          <div class="lyssna-repertoire-split__copy">
            <h2>Repertoar</h2>
            <p>Vi bygger kvällar kring funk och soul: Stevie Wonder, Ray Charles, Earth, Wind &amp; Fire. Därtill kommer svenska favoriter som Björn Skifs och Tomas Ledin, och repertoaren är bred nog för blandade sällskap och generationer. Vi tar gärna emot önskemål inför bokning, mejla <a href="mailto:halvfjorton@gmail.com">halvfjorton@gmail.com</a> så tar vi dialogen där.</p>
          </div>
          <div class="lyssna-repertoire-split__spotify">
{lyssna_spotify_embed_markup()}
          </div>
        </div>
      </div>
    </section>
""",
    )

    page(
        "/for-eventbolag/",
        "Boka Halv Fjorton via eventbolag | underlag för bokare",
        "Underlag för eventbolag: kort bio, vad som ingår, teknik, presskit, organisationsuppgifter och bokningsgång för Halv Fjorton.",
        hidden=True,
        extra_ld=[
            service_ld(
                "Bokning via eventbolag",
                "Coverband för eventbyråer i södra Sverige.",
                "/for-eventbolag/",
            )
        ],
        body=f"""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Info för eventbolag</h1>
        <p class="lead">Halv Fjorton är åtta musiker med egen blåssektion. Rötter i Växjö, spelningar i södra Sverige. Soul, funk, rock och svenska klassiker.</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap grid-2">
        <div>
          <h2>Kort bio</h2>
          <p>Halv Fjorton är ett cover- och partyband från södra Sverige. Bandet har åtta permanenta medlemmar, egen blåssektion och en repertoar med tyngdpunkt i soul och funk - Stevie Wonder, Ray Charles, Earth, Wind &amp; Fire - plus svenska klassiker som Björn Skifs och Tomas Ledin. Vanliga bokningar: bröllop (även vigsel/psalmer), mingel, personalfest, kickoff och jubileum.</p>
        </div>
        <div>
          <h2>Det här ingår</h2>
          <ul class="list-check">
            <li>8 musiker på scen (sång, gitarr, bas, trummor, klaviatur, slagverk, trumpet, saxofon)</li>
            <li>Egen blåssektion och komplett sättning på scen.</li>
            <li>{LOKAL_TEKNIK_COPY}</li>
            <li>Möjlighet att kombinera mingel och dansspelning samma kväll</li>
            <li>Specialönskemål: middag, sambatåg, fanfar, utvald första dans</li>
          </ul>
        </div>
      </div>
    </section>
    <section class="section section-alt">
      <div class="wrap">
        <h2>Teknik i korthet</h2>
        <p>{LOKAL_TEKNIK_COPY} Exakt inputlista, scenskiss och strömbehov skickas per spelning - underlaget här är en sammanfattning, inte ett färdigt rider.</p>
        <div class="faq-grid">
          <article><h3>Ljud</h3><p>{LOKAL_TEKNIK_COPY}</p></article>
          <article><h3>Scen</h3><p>Åtta musiker på scen. Bekräfta scendmått och bärväg i lokalen så att vi inte gissar lastning.</p></article>
          <article><h3>Rider</h3><p><em>Teknisk rider, kanallista och scenskiss läggs till som nedladdningsbara PDF:er här.</em></p></article>
        </div>
      </div>
    </section>
    <section class="section">
      <div class="wrap grid-2">
        <div>
          <h2>Presskit</h2>
          <ul class="list-check">
            <li>Film: <a href="/lyssna/">Signed Sealed Delivered 2025</a> och <a href="/lyssna/">Reel 2022</a></li>
            <li>Foton: scenfoton på den här sajten</li>
            <li><em>Högupplösta pressfoton och logotyppaket läggs till</em></li>
            <li>Instagram: <a href="https://www.instagram.com/halvfjorton/">@halvfjorton</a></li>
          </ul>
        </div>
        <div>
          <h2>Organisation och avtal</h2>
          <p>Halv Fjorton EK. FÖR.<br>Org.nr 769641-5418<br><a href="mailto:halvfjorton@gmail.com">halvfjorton@gmail.com</a></p>
          <p>Faktura mot företag och byrå. En bokningskontakt från vår sida. Inga påhittade referenslogotyper här - be oss om aktuella referenser till liknande event.</p>
        </div>
      </div>
    </section>
    <section class="section section-alt">
      <div class="wrap">
        <h2>Bokningsgång</h2>
        <div class="faq-grid">
          <article><h3>Förfrågan</h3><p>Datum, ort, typ av event, antal gäster, mingel plus fest eller bara en del, sluttid.</p></article>
          <article><h3>Förslag</h3><p>Vi återkommer om tillgänglighet, sättning och ett konkret upplägg. Därefter offert.</p></article>
          <article><h3>Bekräftelse</h3><p>Skriftlig bokning. Teknikdetaljer och tidsplan närmare eventet. Deposition enligt överenskommelse.</p></article>
        </div>
        <p>Säsongstoppar är lördagar vår-sommar och julperioder. Hör av er tidigt om datumet är låst.</p>
        <div class="actions">
          <a class="btn btn-primary" href="/kontakt/">Hör av er</a>
          <a class="btn btn-ghost" href="/faq/">FAQ</a>
        </div>
      </div>
    </section>
""",
    )

    faqs = [
        (
            "Spelar ni i Småland och Skåne?",
            "Ja. Vår kärnregion är Växjö, Älmhult, Kalmar, Jönköping, Lund, Malmö och Helsingborg, det vill säga Småland och Skåne.",
        ),
        (
            "Spelar ni utanför ert område?",
            "Oftast ja, om datum och logistik går ihop. Maila plats och datum så återkommer vi med vad som är rimligt.",
        ),
        (
            "Sedan när finns Halv Fjorton?",
            "Bandet grundades 2018 i Växjö. Sedan dess har vi bland annat arrangerat egen julkonsert nästan varje år.",
        ),
        (
            "Hur stort är bandet?",
            "Vi är åtta musiker med sång, rytmsektion och egen blåssektion. Namnet kommer från att vi började som sju, alltså halva fjorton.",
        ),
        (
            "Hur länge spelar ni?",
            "På de flesta fester spelar vi två set partymusik. Mingel eller vigsel utöver det planeras separat i offerten.",
        ),
        (
            "Kan ni spela både mingel och fest?",
            "Ja, det är ett av våra vanligaste upplägg. Mingel i mer återhållen stil, sedan två set dans när rummet är redo.",
        ),
        (
            "Kan ni spela till vigseln?",
            "Ja. Vi kan spela vigselmusik med helband, komp till solist eller kombinera med psalmer. Läs mer under bröllop.",
        ),
        (
            "Kan ni kompa en artist?",
            "Ja. Vi fungerar som kompband för solist, gästsång eller inhyrd artist. Se sidan bröllop.",
        ),
        (
            "Kan ni göra specialarrangemang?",
            "Ja. Första dans, fanfar, musik under middag eller sambatåg går ofta att lösa om ni hör av er i tid.",
        ),
        (
            "Hur bokar man?",
            "Maila halvfjorton@gmail.com med datum, plats och typ av tillställning. Vi återkommer med upplägg och offert, som PDF på begäran.",
        ),
        (
            "Hur löser ni ljud och teknik?",
            f"{LOKAL_TEKNIK_COPY} Detaljer följer i offert och rider närmare spelningen.",
        ),
        (
            "Hur lång framförhållning behövs?",
            "Så tidigt ni kan, särskilt lördagar under bröllopssäsong. Kortare varsel kan funka - fråga hellre än att anta att det är fullt.",
        ),
        (
            "Vem fakturerar?",
            "Halv Fjorton EK. FÖR., organisationsnummer 769641-5418. Mejl halvfjorton@gmail.com.",
        ),
    ]
    faq_list = faq_list_two_columns(faqs)
    faq_ld_entities = ",\n".join(
        f'''      {{
        "@type": "Question",
        "name": "{q}",
        "acceptedAnswer": {{
          "@type": "Answer",
          "text": "{a.replace('"', '\\"')}"
        }}
      }}'''
        for q, a in faqs
    )
    faq_ld = f"""{{
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
{faq_ld_entities}
    ]
  }}"""

    page(
        "/faq/",
        "Vanliga frågor om Halv Fjorton | bokning, teknik och repertoar",
        "FAQ om Halv Fjorton: bandstorlek, teknik, tillfällen, södra Sverige, bokning, framförhållning och skräddarsydd repertoar.",
        extra_ld=[faq_ld],
        extra_scripts='  <script src="/assets/js/alt-faq-accordion.js" defer></script>\n',
        body=f"""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Vanliga frågor</h1>
        <p class="lead">Svar på det vi oftast får frågor om.</p>
        <p class="page-hero__actions">
          <a class="alt-btn alt-btn--primary" href="/kontakt/">Frågor? Kontakta oss</a>
        </p>
      </div>
    </header>
    <section class="section">
      <div class="wrap alt-faq">
{faq_list}
      </div>
    </section>
""",
    )

    page(
        "/kontakt/",
        "Kontakta Halv Fjorton | boka coverband i södra Sverige",
        "Kontakta Halv Fjorton för bokning: halvfjorton@gmail.com. Coverband till bröllop, företag och fest i Växjö och södra Sverige.",
        extra_ld=[contact_page_ld()],
        extra_scripts='  <script src="/assets/js/tally-embed.js" defer></script>\n',
        body=kontakt_page_body(),
        page_class="alt-page--kontakt alt-page--header-light-top",
    )

    page(
        "/integritetspolicy/",
        "Integritetspolicy | Halv Fjorton",
        "Så behandlar Halv Fjorton personuppgifter från kontaktformuläret: vad vi samlar in, varför, hur länge vi sparar och dina rättigheter.",
        breadcrumb_name="Integritetspolicy",
        body=integritetspolicy_page_body(),
    )

    page(
        "/404.html",
        "Sidan hittades inte | Halv Fjorton",
        "Sidan finns inte. Gå till startsidan eller kontakta Halv Fjorton.",
        outfile=OUT_ROOT / "404.html",
        body="""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Sidan finns inte</h1>
        <p class="lead">Länken kan vara gammal. Prova startsidan eller kontakta oss om ni letade efter en bokning.</p>
        <div class="actions">
          <a class="btn btn-primary" href="/">Till startsidan</a>
          <a class="btn btn-ghost" href="/kontakt/">Kontakt</a>
        </div>
      </div>
    </header>
""",
    )

    write_redirect_page("/repertoar/", "/lyssna/#repertoar")
    write_redirect_page("/mingel/", "/fest-och-mingel/", "Fest och mingel")


def write_sitemap():
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path in SITEMAP_PATHS:
        priority = "1.0" if path == "/" else "0.8"
        lines.extend(
            [
                "  <url>",
                f"    <loc>{SITE}{path}</loc>",
                "    <changefreq>monthly</changefreq>",
                f"    <priority>{priority}</priority>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    dest = OUT_ROOT / "sitemap.xml"
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", dest.relative_to(OUT_ROOT))


def write_llms_txt():
    text = f"""# Halv Fjorton

> Cover- och partyband med åtta musiker och egen blåssektion från Växjö. Grundat 2018. Soul, funk, rock och svenska klassiker.

## Kontakt
- E-post: halvfjorton@gmail.com
- Bokning: en kontakt, offert som PDF på begäran
- Instagram: https://www.instagram.com/halvfjorton/
- YouTube: https://www.youtube.com/@halvfjorton9292

## Område
Kärnregion: Växjö, Älmhult, Kalmar, Jönköping, Lund, Malmö, Helsingborg (Småland och Skåne). Spelningar utanför går att diskutera.

## Tjänster
- Bröllop: {SITE}/brollop/
- Företag: {SITE}/foretag/
- Fest och mingel: {SITE}/fest-och-mingel/
- Egen julkonsert (A Soulful Christmas, Nygatan 6 Växjö sedan 2023): /julkonsert/

## Viktiga sidor
- Startsida: {SITE}/
- FAQ: {SITE}/faq/
- Kontakt: {SITE}/kontakt/
- Konserter: {SITE}/konserter/
- Repertoar: {SITE}/lyssna/#repertoar
"""
    dest = OUT_ROOT / "llms.txt"
    dest.write_text(text, encoding="utf-8")
    print("wrote", dest.relative_to(OUT_ROOT))


def write_home_jsonld():
    home_path = OUT_ROOT / "index.html"
    html = home_path.read_text(encoding="utf-8")
    org = music_group_ld()
    crumb = breadcrumb_ld([("/", "Hem")])
    block = f"""  <script type="application/ld+json">
  {org},
  {crumb}
  </script>
"""
    if re.search(r'<script type="application/ld\+json">', html):
        html = re.sub(
            r'  <script type="application/ld\+json">.*?</script>\n',
            block,
            html,
            count=1,
            flags=re.DOTALL,
        )
    else:
        html = html.replace(
            '  <link rel="stylesheet" href="/assets/css/alt.css">\n',
            f'  <link rel="stylesheet" href="/assets/css/alt.css">\n{block}',
        )
    home_path.write_text(html, encoding="utf-8")
    print("wrote", home_path.relative_to(OUT_ROOT), "(json-ld)")


def patch_home_page():
    home_path = OUT_ROOT / "index.html"
    html = home_path.read_text(encoding="utf-8")
    html = html.replace(
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
    )
    logo = "\n".join("        " + line for line in brand_logo_markup().splitlines())
    html = re.sub(
        r'<img src="/assets/img/logo-mark\.png"[^>]*>\s*',
        logo + "\n",
        html,
    )
    html = re.sub(
        r"\s*<svg class=\"brand-mark\".*?</svg>\s*",
        "\n" + logo + "\n",
        html,
        count=1,
        flags=re.DOTALL,
    )
    if 'aria-label="Halv Fjorton"' not in html.split("<header", 1)[-1][:800]:
        html = html.replace(
            '<a class="alt-brand brand" href="/">',
            '<a class="alt-brand brand" href="/" aria-label="Halv Fjorton">',
            1,
        )
    html = html.replace(
        '<span class="alt-facts__placeholder">Grundat [ÅR - fyll i]</span>',
        "<span>Grundat 2018</span>",
    )
    html = re.sub(
        r"      <div class=\"alt-facts\">[\s\S]*?      </div>\n    </section>",
        home_alt_facts_block() + "\n    </section>",
        html,
        count=1,
    )
    if 'src="/assets/js/alt-nav.js"' not in html:
        html = html.replace(
            '  <script src="/assets/js/nav.js"></script>',
            '  <script src="/assets/js/nav.js"></script>\n  <script src="/assets/js/alt-nav.js" defer></script>',
        )
    html = re.sub(
        r'^[ \t]*<nav class="alt-nav" aria-label="Huvudmeny">[\s\S]*?</nav>',
        home_nav_block("/", "#offert"),
        html,
        count=1,
        flags=re.MULTILINE,
    )
    bootstrap = alt_header_scroll_bootstrap_script()
    if "alt-header-state-init" not in html:
        html = html.replace(
            "  </header>\n",
            "  </header>\n" + bootstrap + "\n",
            1,
        )
    if "data-mobile-menu" not in html:
        html = html.replace(
            "  </header>\n\n  <main id=\"innehall\">",
            "  </header>\n\n" + mobile_menu_block("/", "#offert") + "\n\n  <main id=\"innehall\">",
            1,
        )
    else:
        html = re.sub(
            r'  <div class="mobile-menu" id="mobile-menu"[\s\S]*?</div>\n\n  <main',
            mobile_menu_block("/", "#offert") + "\n\n  <main",
            html,
            count=1,
        )
    html = re.sub(
        r'href="mailto:halvfjorton@gmail.com\?subject=Beg%C3%A4r%20offert[^"]*"',
        'href="#offert"',
        html,
    )
    html = re.sub(
        r'    <section class="alt-intro"[\s\S]*?</section>\n\n',
        "",
        html,
        count=1,
    )
    alt_offert = contact_offert_section(
        section_class="alt-contact-offert",
        wrap_class="alt-contact-offert__wrap contact-offert__grid",
        lead="Skriv datum, plats och vad ni planerar, så återkommer vi med tillgänglighet och förslag.",
        usps=HOME_OFFERT_USPS,
    )
    if re.search(r'<section class="alt-contact-offert"', html):
        html = re.sub(
            r'    <section class="alt-contact-offert"[\s\S]*?</section>',
            alt_offert,
            html,
            count=1,
        )
    else:
        html = re.sub(
            r'    <section class="alt-cta"[\s\S]*?</section>',
            alt_offert,
            html,
            count=1,
        )
    if 'tally-embed.js' not in html:
        html = html.replace(
            '  <script src="/assets/js/alt-nav.js" defer></script>',
            '  <script src="/assets/js/alt-nav.js" defer></script>\n  <script src="/assets/js/tally-embed.js" defer></script>',
        )
    home_tw_phrases = esc(
        json.dumps(
            ["bröllopsfesten", "kickoffen", "50-årsfesten", "julfesten", "företagsfesten"],
            ensure_ascii=False,
        )
    )
    html = re.sub(
        r'(<span class="alt-hero__typewriter" data-alt-typewriter)(?!\s+data-typewriter-phrases)',
        rf'\1 data-typewriter-phrases="{home_tw_phrases}"',
        html,
        count=1,
    )
    if 'alt-hero-typewriter.js' not in html:
        html = html.replace(
            '  <script src="/assets/js/alt-nav.js" defer></script>',
            '  <script src="/assets/js/alt-nav.js" defer></script>\n  <script src="/assets/js/alt-hero-typewriter.js" defer></script>',
        )
    if 'alt-section-typewriter.js' not in html:
        html = html.replace(
            '  <script src="/assets/js/alt-hero-typewriter.js" defer></script>',
            '  <script src="/assets/js/alt-hero-typewriter.js" defer></script>\n  <script src="/assets/js/alt-section-typewriter.js" defer></script>',
        )
    toggle = alt_header_mobile_controls_markup("mobile-menu")
    html = re.sub(
        r'<button class="(?:alt-nav-toggle )?nav-toggle"[^>]*>.*?</button>',
        toggle.strip(),
        html,
        count=1,
        flags=re.DOTALL,
    )
    html = re.sub(
        r'\s*<div class="nav-backdrop" data-nav-backdrop hidden></div>\s*',
        "\n",
        html,
        count=1,
    )
    html = re.sub(
        r"  <link rel=\"preconnect\" href=\"https://fonts\.googleapis\.com\">[^\n]*\n(?:  <link rel=\"preconnect\" href=\"https://fonts\.gstatic\.com\" crossorigin>\n)?  <link href=\"https://fonts\.googleapis\.com/css2[^\"]*\" rel=\"stylesheet\">\n",
        font_preloads("/assets") + "\n",
        html,
        count=1,
    )
    if "InterVariable.woff2" not in html:
        html = html.replace(
            '  <link rel="stylesheet" href="/assets/css/alt.css">\n',
            font_preloads("/assets") + '\n  <link rel="stylesheet" href="/assets/css/alt.css">\n',
        )
    html = re.sub(
        r'  <footer class="site-footer"[\s\S]*?  </footer>',
        modern_footer_markup(),
        html,
        count=1,
    )
    home_path.write_text(html, encoding="utf-8")
    print("wrote", home_path.relative_to(OUT_ROOT), "(home patches)")


def normalize_subpath(subpath: str) -> str:
    subpath = subpath.strip()
    if not subpath:
        return ""
    if not subpath.startswith("/"):
        subpath = "/" + subpath
    return subpath.rstrip("/")


def prepare_output_directory(target: Path) -> None:
    if target.resolve() == ROOT.resolve():
        return
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    shutil.copytree(ROOT / "assets", target / "assets")
    shutil.copy2(ROOT / "home/index.html", target / "index.html")
    for name in ("robots.txt", ".nojekyll"):
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, target / name)


_ROOT_RELATIVE_URL = re.compile(
    r'(?P<attr>href|src|content|data-tally-src|srcset|imagesrcset)=(?P<q>["\'])(?P<path>/[^"\']*)(?P=q)'
)


_DASH_CHARS = ("\u2013", "\u2014")  # en dash, em dash


def assert_no_ai_dashes_in_build(target: Path) -> None:
    """Fail the build if typographic dashes remain in shipped site files."""
    extensions = {".html", ".xml", ".txt", ".css", ".js"}
    offenders: list[str] = []
    for file_path in target.rglob("*"):
        if not file_path.is_file() or file_path.suffix not in extensions:
            continue
        text = file_path.read_text(encoding="utf-8")
        for ch in _DASH_CHARS:
            if ch in text:
                offenders.append(f"{file_path.relative_to(target)} ({ch!r})")
                break
    if offenders:
        sample = "\n".join(f"  - {line}" for line in offenders[:20])
        extra = f"\n  ... and {len(offenders) - 20} more" if len(offenders) > 20 else ""
        raise SystemExit(f"Build check failed: en/em dash found in output:\n{sample}{extra}")


def _prefix_asset_root(url: str, prefix: str) -> str:
    if not prefix or not url.startswith("/assets/"):
        return url
    if url.startswith(f"{prefix}/"):
        return url
    return f"{prefix}{url}"


def _prefix_bare_asset_urls(text: str, prefix: str) -> str:
    """Ensure srcset/imagesrcset candidates use the labs subpath (idempotent)."""
    if not prefix:
        return text

    def fix_set(match: re.Match[str]) -> str:
        attr, q, value = match.group(1), match.group(2), match.group(3)
        parts: list[str] = []
        for candidate in value.split(","):
            candidate = candidate.strip()
            if not candidate:
                continue
            bits = candidate.split()
            bits[0] = _prefix_asset_root(bits[0], prefix)
            parts.append(" ".join(bits))
        if not parts:
            return match.group(0)
        return f"{attr}={q}{', '.join(parts)}{q}"

    return re.sub(
        r'(?P<attr>srcset|imagesrcset)=(?P<q>["\'])(?P<val>[^"\']*)(?P=q)',
        fix_set,
        text,
    )


def rewrite_root_relative_urls(target: Path, subpath: str) -> None:
    prefix = normalize_subpath(subpath)
    if not prefix:
        return

    def replace_url(match: re.Match[str]) -> str:
        path = match.group("path")
        if path.startswith("//"):
            return match.group(0)
        attr = match.group("attr")
        q = match.group("q")
        if attr in ("srcset", "imagesrcset"):
            parts: list[str] = []
            for candidate in path.split(","):
                candidate = candidate.strip()
                if not candidate:
                    continue
                bits = candidate.split()
                bits[0] = _prefix_asset_root(bits[0], prefix)
                parts.append(" ".join(bits))
            path = ", ".join(parts) if parts else path
        else:
            path = f"{prefix}{path}"
        return f"{attr}={q}{path}{q}"

    extensions = {".html", ".xml", ".css", ".js", ".txt"}
    for file_path in target.rglob("*"):
        if not file_path.is_file() or file_path.suffix not in extensions:
            continue
        text = file_path.read_text(encoding="utf-8")
        updated = _ROOT_RELATIVE_URL.sub(replace_url, text)
        updated = _prefix_bare_asset_urls(updated, prefix)
        if updated != text:
            file_path.write_text(updated, encoding="utf-8")


_EYEBROW_IN_HTML = re.compile(r"""class\s*=\s*["'][^"']*\beyebrow\b""", re.IGNORECASE)


def assert_offert_bullet_cap(target: Path, max_items: int = 2) -> None:
    offenders: list[str] = []
    for file_path in target.rglob("*.html"):
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8")
        if 'id="offert"' not in text and "contact-offert__grid" not in text:
            continue
        count = text.count('<ul class="list-check">')
        if not count:
            continue
        # Count <li> inside first offert list-check block only (rough slice).
        start = text.find('<ul class="list-check">')
        if start < 0:
            continue
        end = text.find("</ul>", start)
        block = text[start:end] if end > start else ""
        li_count = block.count("<li>")
        if li_count > max_items:
            offenders.append(f"{file_path.relative_to(target)} ({li_count} bullets)")
    if offenders:
        sample = "\n".join(f"  - {line}" for line in offenders[:20])
        raise SystemExit(
            f"Build check failed: offert list-check exceeds {max_items} items:\n{sample}"
        )


_GALLERY_IMG_SRC_STEM = re.compile(
    r'<img[^>]*\ssrc="[^"]*/assets/img/gallery/(halvfjorton-\d+)-\d+w\.webp"',
    re.IGNORECASE,
)


def assert_no_duplicate_gallery_images_on_page(target: Path) -> None:
    offenders: list[str] = []
    for file_path in target.rglob("*.html"):
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8")
        if "alt-service-hero" not in text:
            continue
        hero_match = re.search(
            r'<header class="alt-service-hero">.*?</header>',
            text,
            flags=re.DOTALL,
        )
        hero_text = hero_match.group(0) if hero_match else ""
        body_text = text.replace(hero_text, "", 1) if hero_match else text
        body_stems = _GALLERY_IMG_SRC_STEM.findall(body_text)
        if not body_stems:
            continue
        counts: dict[str, int] = {}
        for stem in body_stems:
            counts[stem] = counts.get(stem, 0) + 1
        dupes = {stem for stem, n in counts.items() if n > 1}
        if dupes:
            offenders.append(
                f"{file_path.relative_to(target)} ({', '.join(sorted(dupes))})"
            )
    if offenders:
        sample = "\n".join(f"  - {line}" for line in offenders[:20])
        raise SystemExit(
            "Build check failed: duplicate gallery image on same page:\n" + sample
        )


def assert_no_eyebrows_in_build(target: Path) -> None:
    offenders: list[str] = []
    for file_path in target.rglob("*.html"):
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8")
        if _EYEBROW_IN_HTML.search(text):
            offenders.append(str(file_path.relative_to(target)))
    if offenders:
        sample = "\n".join(f"  - {line}" for line in offenders[:20])
        extra = f"\n  ... and {len(offenders) - 20} more" if len(offenders) > 20 else ""
        raise SystemExit(f"Build check failed: eyebrow kickers found in output:\n{sample}{extra}")


def assert_hidden_services_excluded(target: Path) -> None:
    sitemap = (target / "sitemap.xml").read_text(encoding="utf-8")
    for path in HIDDEN_SERVICE_PATHS:
        loc = f"{SITE}{path}"
        if loc in sitemap:
            raise SystemExit(f"Build check failed: hidden service {path} still in sitemap")
    llms = (target / "llms.txt").read_text(encoding="utf-8")
    for path in HIDDEN_SERVICE_PATHS:
        if path in llms or f"{SITE}{path}" in llms:
            raise SystemExit(f"Build check failed: hidden service {path} still in llms.txt")
    for path in HIDDEN_SERVICE_PATHS:
        page_file = target / path.lstrip("/") / "index.html"
        if not page_file.is_file():
            raise SystemExit(f"Build check failed: missing hidden page output {path}")
        html = page_file.read_text(encoding="utf-8")
        if 'name="robots" content="noindex,nofollow"' not in html:
            raise SystemExit(f"Build check failed: {path} missing noindex robots meta")
    visible_samples = (
        "index.html",
        "brollop/index.html",
        "foretag/index.html",
        "fest-och-mingel/index.html",
        "faq/index.html",
    )
    for rel in visible_samples:
        page_file = target / rel
        if not page_file.is_file():
            continue
        text = page_file.read_text(encoding="utf-8")
        for path in HIDDEN_SERVICE_PATHS:
            if f'href="{path}' in text:
                raise SystemExit(
                    f"Build check failed: visible page {rel} still links to hidden {path}"
                )


def assert_integritetspolicy_links_in_build(target: Path) -> None:
    footer_offenders: list[str] = []
    consent_offenders: list[str] = []
    for file_path in target.rglob("*.html"):
        if not file_path.is_file():
            continue
        rel = str(file_path.relative_to(target))
        if rel.startswith("repertoar/") or rel == "home/index.html":
            continue
        text = file_path.read_text(encoding="utf-8")
        if 'class="site-footer"' in text:
            if (
                'href="' not in text
                or "integritetspolicy/" not in text
                or ">Integritetspolicy</a>" not in text
            ):
                footer_offenders.append(rel)
        if "data-tally-src" in text or TALLY_EMBED_SRC in text:
            if "contact-offert__consent" not in text or "integritetspolicy/" not in text:
                consent_offenders.append(rel)
    if footer_offenders:
        sample = "\n".join(f"  - {line}" for line in footer_offenders[:20])
        raise SystemExit(
            "Build check failed: footer missing Integritetspolicy link:\n" + sample
        )
    if consent_offenders:
        sample = "\n".join(f"  - {line}" for line in consent_offenders[:20])
        raise SystemExit(
            "Build check failed: contact form missing GDPR consent line:\n" + sample
        )


def assert_footer_styles_in_css(alt_css: Path) -> None:
    if not alt_css.is_file():
        raise SystemExit(f"Build check failed: missing stylesheet {alt_css}")
    text = alt_css.read_text(encoding="utf-8")
    required = (
        ".alt-page .site-footer__links",
        "list-style: none",
        ".alt-page .site-footer__inner",
    )
    missing = [needle for needle in required if needle not in text]
    if missing:
        raise SystemExit(
            "Build check failed: alt.css footer rules missing: " + ", ".join(missing)
        )


_UNPREFIXED_LABS_ASSET = re.compile(
    r"""(?P<attr>href|src|data-tally-src|srcset|imagesrcset|content)=(?P<q>["'])/assets/"""
)


def assert_labs_asset_urls(target: Path, subpath: str) -> None:
    prefix = normalize_subpath(subpath)
    if not prefix:
        return
    offenders: list[str] = []
    extensions = {".html", ".css", ".js", ".xml", ".txt"}
    for file_path in target.rglob("*"):
        if not file_path.is_file() or file_path.suffix not in extensions:
            continue
        text = file_path.read_text(encoding="utf-8")
        if _UNPREFIXED_LABS_ASSET.search(text):
            offenders.append(str(file_path.relative_to(target)))
    if offenders:
        sample = "\n".join(f"  - {line}" for line in offenders[:25])
        extra = f"\n  ... and {len(offenders) - 25} more" if len(offenders) > 25 else ""
        raise SystemExit(
            "Build check failed: unprefixed /assets/ URLs in labs output "
            f"(expected prefix {prefix}):\n{sample}{extra}"
        )


def run_build(output_dir: Path | None = None, subpath: str = "") -> None:
    global OUT_ROOT
    OUT_ROOT = output_dir.resolve() if output_dir else ROOT
    if output_dir and OUT_ROOT != ROOT.resolve():
        prepare_output_directory(OUT_ROOT)
    else:
        OUT_ROOT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "home/index.html", OUT_ROOT / "index.html")
    write_pages()
    write_sitemap()
    write_llms_txt()
    write_home_jsonld()
    patch_home_page()
    rewrite_root_relative_urls(OUT_ROOT, subpath)
    run_cms_build_steps(OUT_ROOT, ROOT, normalize_subpath(subpath))
    # Labs output must never ship with root-absolute /assets/ (see b4a2667 manual-copy incident).
    assert_labs_asset_urls(OUT_ROOT, subpath)
    assert_no_ai_dashes_in_build(OUT_ROOT)
    assert_no_eyebrows_in_build(OUT_ROOT)
    assert_no_duplicate_gallery_images_on_page(OUT_ROOT)
    assert_offert_bullet_cap(OUT_ROOT)
    assert_hidden_services_excluded(OUT_ROOT)
    assert_integritetspolicy_links_in_build(OUT_ROOT)
    assert_footer_styles_in_css(OUT_ROOT / "assets" / "css" / "alt.css")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the Halv Fjorton static site.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Write generated site to this directory (copies assets/ and home/ source first).",
    )
    parser.add_argument(
        "--subpath",
        default="",
        help=f"Rewrite root-relative URLs for hosting under a path (default labs: {LABS_SUBPATH_DEFAULT}).",
    )
    args = parser.parse_args()
    subpath = args.subpath
    if args.output_dir and not subpath:
        subpath = LABS_SUBPATH_DEFAULT
    run_build(output_dir=args.output_dir, subpath=subpath)
