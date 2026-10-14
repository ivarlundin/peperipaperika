#!/usr/bin/env python3
"""Generate the Halv Fjorton static site."""

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

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

CONTACT_USPS = [
    "Vi svarar inom 24 timmar",
    "Skräddarsytt efter era önskemål",
    "En kontakt hela vägen från förfrågan till sista låten",
    "Åttamannaband med blås",
    "Spelar i Småland och Skåne: Växjö, Kalmar, Jönköping, Malmö, Lund, Helsingborg",
    "Sedan 2018",
]

HOME_CONTACT_USPS = [
    "Vi svarar inom 24 timmar",
    "Skräddarsytt efter era önskemål",
    "Åttamannaband med blås",
]

NAV_SERVICES = [
    ("/brollop/", "Bröllop"),
    ("/foretag/", "Företag"),
    ("/kompband/", "Kompband för artist"),
    ("/50-arsfest/", "50-årsfest"),
    ("/brollopsband-smaland/", "Bröllopsband Småland"),
    ("/coverband-skane-malmo/", "Coverband Skåne & Malmö"),
]

NAV_PRIMARY = [
    ("/", "Hem"),
    ("/for-eventbolag/", "Eventbolag"),
    ("/om-oss/", "Om oss"),
    ("/lyssna/", "Lyssna"),
    ("/faq/", "FAQ"),
    ("/kontakt/", "Kontakt"),
]

SITEMAP_PATHS = [
    "/",
    "/brollop/",
    "/foretag/",
    "/kompband/",
    "/50-arsfest/",
    "/julkonsert/",
    "/konserter/",
    "/repertoar/",
    "/mingel/",
    "/om-oss/",
    "/lyssna/",
    "/for-eventbolag/",
    "/faq/",
    "/kontakt/",
    "/brollopsband-smaland/",
    "/coverband-skane-malmo/",
]

HOME_NAV_LINKS = [
    ("/konserter/", "Konserter"),
    ("/repertoar/", "Repertoar"),
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


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


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


def contact_offert_section(
    heading: str = "Begär offert",
    lead: str | None = None,
    section_class: str = "contact-offert section",
    wrap_class: str = "wrap contact-offert__grid",
    usps: list[str] | None = None,
) -> str:
    usp_items = "\n".join(f"            <li>{esc(u)}</li>" for u in (usps if usps is not None else CONTACT_USPS))
    lead_html = f'        <p class="contact-offert__lead">{esc(lead)}</p>\n' if lead else ""
    return f"""    <section class="{section_class}" id="offert" aria-labelledby="offert-rubrik">
      <div class="{wrap_class}">
        <div class="contact-offert__copy">
          <h2 id="offert-rubrik">{esc(heading)}</h2>
{lead_html}          <ul class="list-check">
{usp_items}
          </ul>
          <p class="contact-offert__mail">
            <a class="alt-btn alt-btn--primary" href="mailto:halvfjorton@gmail.com">Mejla oss</a>
          </p>
        </div>
        <div class="contact-offert__form tally-card">
          <noscript>
            <p><a href="{TALLY_PUBLIC_URL}">Öppna offertformuläret på Tally</a> om det inte visas här.</p>
          </noscript>
{tally_iframe_markup()}
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
    return f"""  <footer class="site-footer" aria-label="Sidfot">
    <div class="site-footer__inner">
      <div class="site-footer__grid">
        <p class="site-footer__tagline">Coverband från Växjö, Småland</p>
        <nav class="site-footer__nav" aria-label="Sidfot länkar">
          <ul class="site-footer__links">
            <li><a href="/#tjanster">Tjänster</a></li>
            <li><a href="/kontakt/">Kontakt</a></li>
            <li><a href="/faq/">FAQ</a></li>
            <li><a href="/lyssna/">Lyssna</a></li>
          </ul>
        </nav>
        <div class="site-footer__aside">
          <a class="site-footer__social" href="https://www.instagram.com/halvfjorton/" target="_blank" rel="noopener noreferrer">
            <svg class="site-footer__ig-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <rect x="3" y="3" width="18" height="18" rx="5" stroke="currentColor" stroke-width="1.75"/>
              <circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="1.75"/>
              <circle cx="17.5" cy="6.5" r="1" fill="currentColor"/>
            </svg>
            <span>Följ oss på Instagram</span>
          </a>
          <a class="alt-btn alt-btn--primary site-footer__cta" href="/kontakt/">Kontakta oss</a>
        </div>
      </div>
      <hr class="site-footer__rule" />
      <p class="site-footer__legal">
        <span class="site-footer__legal-line">© <span data-footer-year>{BUILD_YEAR}</span> Halv Fjorton ek. för.</span>
        <span class="site-footer__legal-line">Org.nr 769641-5418</span>
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


def wedding_video_ld() -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": WEDDING_VIDEO_TITLE,
        "description": "Livevideo med Halv Fjorton som cover- och bröllopsband i södra Sverige.",
        "thumbnailUrl": f"https://i.ytimg.com/vi/{WEDDING_VIDEO_ID}/hqdefault.jpg",
        "embedUrl": f"https://www.youtube-nocookie.com/embed/{WEDDING_VIDEO_ID}",
        "contentUrl": f"https://www.youtube.com/watch?v={WEDDING_VIDEO_ID}",
        "publisher": {
            "@type": "Organization",
            "name": "Halv Fjorton",
            "url": f"{SITE}/",
        },
    }
    return _indent_ld(data)


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
          <div class="event-ticket__status" aria-live="polite">
            <span class="event-ticket__badge" data-event-badge>Kommande</span>
            <span class="event-ticket__countdown" data-event-countdown></span>
          </div>
          <div class="event-ticket__grid">
            <div class="event-ticket__date" aria-hidden="true">
              <span class="event-ticket__dow">LÖR</span>
              <span class="event-ticket__day">12</span>
              <span class="event-ticket__mon">DEC</span>
            </div>
            <div class="event-ticket__poster">
              <img
                src="{base}-800w.webp"
                srcset="{base}-480w.webp 480w, {base}-800w.webp 800w, {base}-1200w.webp 1200w"
                sizes="(max-width: 767px) 100vw, 11rem"
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
              <p class="visually-hidden">Lördag 12 december 2026 · Nygatan 6, Växjö · Två föreställningar: 16:00 och 19:30</p>
              <p class="event-ticket__when">Lördag 12 december 2026</p>
              <div class="event-ticket__shows">
                <span class="event-ticket__shows-label">Två föreställningar:</span>
                <ul class="event-ticket__times">
                  <li><span class="event-ticket__chip">16:00</span></li>
                  <li><span class="event-ticket__chip">19:30</span></li>
                </ul>
              </div>
              <p class="event-ticket__place">
                <svg class="event-ticket__pin" width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M12 21s7-4.5 7-11a7 7 0 1 0-14 0c0 6.5 7 11 7 11Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                  <circle cx="12" cy="10" r="2.25" stroke="currentColor" stroke-width="1.5"/>
                </svg>
                <span>Nygatan 6, Växjö</span>
              </p>
              <p class="event-ticket__text">Växjö stad i juleglans, och vad passar då bättre än en julkonsert? Halv Fjorton återvänder och bjuder på svängig julstämning med soul, funk, jazz och komiska inslag. Julklassikerna får en skrud du aldrig hört förut, och kanske smyger sig en och annan sketch in.</p>
              <div class="event-ticket__actions">
                <a class="btn btn-primary event-ticket__cta" href="{SOULFUL_CHRISTMAS_TICKETS}" target="_blank" rel="noopener noreferrer">Köp biljetter</a>
              </div>
            </div>
          </div>
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
    nav_block = home_nav_block(path, "/#offert")
    mobile_menu = mobile_menu_block(path, "/#offert")
    toggle = alt_header_mobile_controls_markup("mobile-menu")
    html = f"""<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{canonical}">
  <meta name="robots" content="index,follow">
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
  <header class="alt-header site-header is-solid" data-nav>
    <div class="alt-header__inner header-inner">
      <a class="alt-brand brand" href="/" aria-label="Halv Fjorton">
{brand_logo_markup()}
      </a>
{toggle}
{nav_block}
    </div>
  </header>
{mobile_menu}
  <main id="innehall" class="alt-inner-main">
{body}
  </main>
{modern_footer_markup()}
  <script src="/assets/js/nav.js"></script>
  <script src="/assets/js/alt-nav.js" defer></script>
  <script src="/assets/js/alt-header-logo.js" defer></script>
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
    wedding_video_block = video_facade(
        WEDDING_VIDEO_ID,
        WEDDING_VIDEO_TITLE,
        "Förhandsbild: Halv Fjorton spelar live på bröllopsfest i södra Sverige",
    )
    page(
        "/brollop/",
        f"Bröllopsband Växjö, Kalmar och Småland | {BRAND_TITLE}",
        "Bröllopsband med två set partymusik, egen blåssektion och tillval: mingel, vigselmusik och komp till solist. Bokas i Växjö, Småland och Skåne.",
        breadcrumb_name="Bröllop",
        extra_ld=[
            service_ld(
                "Bröllopsband",
                "Bröllopsband med två set partymusik. Tillval: mingelmusik, vigselmusik med solist, helband eller komp till solist.",
                "/brollop/",
            ),
            wedding_video_ld(),
        ],
        body=f"""    <header class="page-hero">
      <div class="page-hero-copy">
        <h1>Bröllopsband med dans, blås och svenska klassiker</h1>
{aeo_answer("Halv Fjorton är ett åtta man starkt bröllopsband från Växjö med egen blåssektion. På festen spelar vi två set partymusik med soul, funk, rock och svenska favoriter.")}
        <p class="lead">Tillval: mingel, vigselmusik med solist, helband eller komp till solist. En kontakt från offert till spelning.</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap grid-2">
        <div>
          <h2>Så brukar kvällen se ut</h2>
          <ul class="list-check">
            <li><strong>Två set partymusik</strong> med dansgolv i fokus.</li>
            <li><strong>Mingelmusik</strong> före middag eller under mottagning.</li>
            <li><strong>Vigselmusik</strong> med solist, helband eller komp till solist.</li>
            <li><strong>Egen blåssektion</strong> och komplett liveband.</li>
          </ul>
          <p>Vi spelar i Växjö, Kalmar, Älmhult, Jönköping, Lund, Malmö, Helsingborg och resten av Småland och Skåne. Andra orter går att diskutera.</p>
        </div>
        <div>
          <h2>Smakprov från scen</h2>
{wedding_video_block}
          <p class="small muted" style="margin-top:0.75rem">Signed Sealed Delivered, inspelat live med bandet.</p>
        </div>
      </div>
    </section>
    <section class="section section-alt">
      <div class="wrap">
        <h2>Vanliga önskemål</h2>
        <div class="faq-grid">
          <article><h3>Första dansen</h3><p>Vi lär in er låt om den inte redan finns i repertoaren, så länge den funkar live med band.</p></article>
          <article><h3>Mingel och fest</h3><p>Samma kväll, samma band: mingel i lugnare tempo och sedan två set dansmusik.</p></article>
          <article><h3>Komp till solist</h3><p>Psalmer, vigsel eller gästsång? Se <a href="/kompband/">kompband för artist</a>.</p></article>
        </div>
        <div class="actions">
          <a class="btn btn-primary" href="/kontakt/">Hör av er</a>
          <a class="btn btn-ghost" href="/brollopsband-smaland/">Bröllop i Småland</a>
        </div>
      </div>
    </section>
""",
    )

    page(
        "/foretag/",
        f"Coverband till företagsfest Malmö och Skåne | {BRAND_TITLE}",
        "Festband till personalfest, kickoff och jubileum i Malmö, Lund, Växjö och Småland. Artistkomp och särskilda musikmoment går att boka.",
        breadcrumb_name="Företag",
        extra_ld=[
            service_ld(
                "Företagsfest och festband",
                "Musikunderhållning och festmusik till personalfest och företagsevent. Artistkomp för inhyrda artister och specialarrangerad musik.",
                "/foretag/",
            )
        ],
        body=f"""    <header class="page-hero">
      <div class="page-hero-copy">
        <h1>Personalfest, kickoff och jubileum</h1>
{aeo_answer("Halv Fjorton spelar på företagsfester i Skåne och Småland med åtta musiker och egen blåssektion. Vanligt är två set festmusik, ofta efter mingel.")}
        <p class="lead">Vi planerar kvällen med er: mingel, tal, dans. Artistkomp och särskilda musikmoment går att boka.</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap">
        <h2>När företag hör av sig</h2>
        <div class="faq-grid">
          <article><h3>Personalfest och julbord</h3><p>Kvällar där kollegor faktiskt dansar. Soul och funk som fungerar även om gästlistan är blandad.</p></article>
          <article><h3>Kickoff och konferens</h3><p>Mingel till fördrinken, mer tryck efter middagen. Vi anpassar volym och repertoar efter lokalen och programmet.</p></article>
          <article><h3>Jubileum och kundkväll</h3><p>När ni vill visa något mer än en spellista. Ett komplett band med blås ger tyngd utan att bli stelt.</p></article>
        </div>
      </div>
    </section>
    <section class="section section-alt">
      <div class="wrap split">
        <div>
          <h2>Det som ofta spelar roll</h2>
          <ul class="list-check">
            <li><strong>Blåssektion.</strong> Trumpet, sax och kör - mer än gitarr, bas och trummor i ett hörn.</li>
            <li><strong>Lokal och logistik.</strong> {LOKAL_TEKNIK_COPY}</li>
            <li><strong>Bred repertoar.</strong> Från Stevie Wonder till Björn Skifs. Det gör att både vd och sommarjobbare känner igen något.</li>
            <li><strong>Södra Sverige som hemmaplan.</strong> Växjö i botten, medlemmar i bland annat Malmö och Skåne. Rimliga restider i södern.</li>
            <li><strong>En motpart.</strong> Ekonomisk förening med organisationsnummer, faktura och en bokningskontakt.</li>
          </ul>
        </div>
        <div>
          <h2>Ett typiskt upplägg</h2>
          <p>Mingel 45-90 minuter medan gästerna kommer in. Paus under middag och tal. Därefter ett längre dansblock. Tider justeras efter er agenda - inte tvärtom.</p>
          <p>Vill ni ha fanfar, extra akt eller bakgrund under mingelmat? Säg till. Vi tar fram ett konkret förslag när vi vet datum, plats, antal gäster och ungefärlig sluttid.</p>
        </div>
      </div>
    </section>
    <section class="section">
      <div class="wrap">
        <h2>Praktiskt vid bokning</h2>
        <div class="grid-2">
          <article class="card">
            <h3>Vad som följer med</h3>
            <p>Band och liveupplevelse med egen blåssektion. {LOKAL_TEKNIK_COPY}</p>
          </article>
          <article class="card">
            <h3>Vad vi behöver av er</h3>
            <p>Datum, adress, ungefärligt antal, om det är mingel plus fest, och om lokalen har begränsningar. Resten kan vi ta i ett samtal.</p>
          </article>
        </div>
        <div class="quote-placeholder">
          <p><strong>Citat från arrangörer | läggs till</strong></p>
          <p>Här kan referenser från företag och eventbyråer publiceras när de finns. Inga påhittade omdömen.</p>
        </div>
        <div class="actions">
          <a class="btn btn-primary" href="/kontakt/">Hör av er</a>
          <a class="btn btn-ghost" href="/for-eventbolag/">Information till eventbolag</a>
        </div>
      </div>
    </section>
""",
    )

    page(
        "/mingel/",
        "Mingelband och jazz till mottagning | Halv Fjorton",
        "Halv Fjorton spelar mingel med jazz och svenska klassiker. Passar konferensmiddag, bröllopsmottagning och företagsmingel i södra Sverige.",
        extra_ld=[
            service_ld(
                "Mingel och mottagning",
                "Live mingelmusik från traditionell jazz till svenska klassiker.",
                "/mingel/",
            )
        ],
        body="""    <header class="page-hero">
      <div class="page-hero-copy">
        <h1>Mingelmusik som håller tonen låg</h1>
        <p class="lead">Vi spelar mingel med blandad repertoar, från jazz till svenska klassiker. Det passar när gästerna ska kunna prata och ändå höra att det är livemusik.</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap grid-2">
        <div>
          <h2>När mingel är rätt val</h2>
          <p>Innan middagen, under fördrink, i foajén eller på en sommaräng. Vi spelar lägre, mer akustiskt i känslan, men med samma musiker - så kvällen kan växa till fest utan att byta band.</p>
          <ul class="list-check">
            <li>Bröllopsmottagning mellan vigsel och middag</li>
            <li>Konferensmiddag och after work</li>
            <li>Jubileum där första timmen ska vara samtal, inte diskotek</li>
          </ul>
        </div>
        <div>
          <h2>Repertoaren i korthet</h2>
          <p>Jazzstandard, soul i dämpat tempo, svenska visor och klassiker. Vill ni ha en tydlig tråd - till exempel bara jazz, eller mest svenskt - säger ni det så styr vi dit.</p>
          <p>Många bokar mingel plus fest samma kväll. Det är vårt vanligaste kombinerade upplägg, och det vi rekommenderar när tiden räcker.</p>
          <div class="actions">
            <a class="btn btn-primary" href="/kontakt/">Hör av er</a>
            <a class="btn btn-ghost" href="/brollop/">Se bröllop</a>
          </div>
        </div>
      </div>
    </section>
""",
    )

    page(
        "/kompband/",
        f"Kompband för artist i Småland och Skåne | {BRAND_TITLE}",
        "Kompband för solist eller inhyrd artist på bröllop, fest och företagsevent. Växjö, Malmö, Lund och övriga södra Sverige.",
        breadcrumb_name="Kompband",
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
        extra_ld=soulful_christmas_event_ld(),
        extra_scripts='  <script src="/assets/js/event-ticket-card.js" defer></script>\n',
        body=f"""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Konserter</h1>
        <p class="lead">Vi spelar inte alltid för privata sammankomster utan gör ibland publika konserter, håll utkik här.</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap event-ticket-wrap">
{soulful_christmas_ticket_card()}
      </div>
    </section>
""",
    )

    page(
        "/repertoar/",
        f"Repertoar | {BRAND_TITLE}",
        "Repertoar för Halv Fjorton: soul, funk, rock och svenska klassiker med åtta musiker och egen blåssektion.",
        breadcrumb_name="Repertoar",
        body="""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Repertoar</h1>
        <p class="lead">Här kommer en lista med soul, funk, rock och svenska klassiker.</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap">
        <p>Platshållare tills listan är klar. Mejla <a href="mailto:halvfjorton@gmail.com">halvfjorton@gmail.com</a> om ni vill diskutera låtönskemål inför bokning.</p>
      </div>
    </section>
""",
    )

    page(
        "/brollopsband-smaland/",
        f"Bröllopsband Småland, Växjö, Kalmar, Älmhult | {BRAND_TITLE}",
        "Bröllopsband i Småland: Växjö, Kalmar, Älmhult och Jönköping. Två set partymusik, mingel och vigselmusik. Egen blåssektion.",
        breadcrumb_name="Bröllopsband Småland",
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
          <a class="btn btn-ghost" href="/coverband-skane-malmo/">Skåne och Malmö</a>
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
        "Coverband grundat 2018 i Växjö. Egen julkonsert med soul och funk, spelningar på Nygatan 6 sedan 2023. Åtta musiker med egen blåssektion.",
        breadcrumb_name="Om oss",
        body="""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Coverband från Växjö sedan 2018</h1>
        <p class="lead">Ett partyband med rötter i Växjö och musiker över södra Sverige. Namnet kommer från att vi började som sju, alltså halva fjorton. Idag är vi åtta musiker med egen blåssektion.</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap">
        <h2>Musiken</h2>
        <p>Vi spelar funk och soul: Stevie Wonder, Ray Charles, Earth, Wind &amp; Fire. Därtill svenska favoriter som Björn Skifs och Tomas Ledin.</p>
        <p>Repertoaren är bred nog för att passa olika åldrar och smaker. När ni bokar oss vill vi att kvällen ska kännas som er fest, inte som en generisk coverkväll.</p>
      </div>
    </section>
    <section class="section section-alt">
      <div class="wrap">
        <h2>Julkonsert och Nygatan 6</h2>
        <p>Sedan starten 2018 har vi nästan varje år arrangerat en egen julkonsert med egna jullåtar och covers i soul- och funkstil. Sedan 2023 spelar vi den på <strong>Nygatan 6</strong> i Växjö. Läs mer under <a href="/julkonsert/">julkonsert</a> och se filmer på <a href="/lyssna/">Lyssna</a>.</p>
      </div>
    </section>
    <section class="section">
      <div class="wrap">
        <h2>Föreningen</h2>
        <p>Vi är <strong>Halv Fjorton EK. FÖR.</strong>, organisationsnummer <strong>769641-5418</strong>. Kontakt: <a href="mailto:halvfjorton@gmail.com">halvfjorton@gmail.com</a>, Instagram <a href="https://www.instagram.com/halvfjorton/">@halvfjorton</a>, YouTube <a href="https://www.youtube.com/@halvfjorton9292" rel="noopener noreferrer">@halvfjorton9292</a>.</p>
      </div>
    </section>
""",
    )

    page(
        "/lyssna/",
        "Lyssna på Halv Fjorton | film, reel och julkonserter",
        "Se Halv Fjorton live: Signed Sealed Delivered 2025, reel 2022 och julkonserterna A Soulful Christmas.",
        body="""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Lyssna på oss</h1>
        <p class="lead">Filmer från scen och julkonserter. Samma band som ni bokar till bröllop, företag och mingel.</p>
      </div>
    </header>
    <section class="section">
      <div class="wrap media-grid">
        <article class="media-card">
          <div class="embed">
            <iframe src="https://www.youtube-nocookie.com/embed/V2Nb8jMKUCk" title="Signed Sealed Delivered - Halv Fjorton 2025" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy"></iframe>
          </div>
          <div class="meta">
            <h2>Signed Sealed Delivered - 2025</h2>
            <p>Aktuell livefilm. Smakprov på hur vi låter med blås och sång.</p>
          </div>
        </article>
        <article class="media-card">
          <div class="embed">
            <iframe src="https://www.youtube-nocookie.com/embed/gm5C41wqYuU" title="Halv Fjorton Reel 2022" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy"></iframe>
          </div>
          <div class="meta">
            <h2>Reel 2022</h2>
            <p>Kortare klipp från spelningar - bra att skicka vidare till den som inte var med.</p>
          </div>
        </article>
      </div>
    </section>
    <section class="section section-alt">
      <div class="wrap">
        <h2>Julkonserter på film</h2>
        <p class="muted">A Soulful Christmas och en julmässa med vänner. Inbäddade från bandets tidigare mediasida.</p>
        <div class="media-grid">
          <article class="media-card">
            <div class="embed"><iframe src="https://www.youtube-nocookie.com/embed/vV8aavPxYss" title="A Soulful Christmas 2024 - 8 december, Nygatan 6" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy"></iframe></div>
            <div class="meta"><h3>A Soulful Christmas 2024</h3><p>8 december, Nygatan 6.</p></div>
          </article>
          <article class="media-card">
            <div class="embed"><iframe src="https://www.youtube-nocookie.com/embed/UytyTLnKDWQ" title="A Soulful Christmas 2023 - 3 december, Nygatan 6" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy"></iframe></div>
            <div class="meta"><h3>A Soulful Christmas 2023</h3><p>3 december, Nygatan 6.</p></div>
          </article>
          <article class="media-card">
            <div class="embed"><iframe src="https://www.youtube-nocookie.com/embed/lAmSo6wGjqo" title="Halv Fjorton med vänner och mässa - 26 december 2022" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy"></iframe></div>
            <div class="meta"><h3>Med vänner och mässa</h3><p>26 december 2022.</p></div>
          </article>
          <article class="media-card">
            <div class="embed"><iframe src="https://www.youtube-nocookie.com/embed/R0fqTXcAbgc" title="A Soulful Christmas 2018" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy"></iframe></div>
            <div class="meta"><h3>A Soulful Christmas 2018</h3><p>Tidigare julkonsert.</p></div>
          </article>
        </div>
        <p class="small muted">Fler klipp och pressbilder kan läggas här. Se även <a href="https://www.instagram.com/halvfjorton/">Instagram @halvfjorton</a>.</p>
      </div>
    </section>
""",
    )

    page(
        "/for-eventbolag/",
        "Boka Halv Fjorton via eventbolag | underlag för bokare",
        "Underlag för eventbolag: kort bio, vad som ingår, teknik, presskit, organisationsuppgifter och bokningsgång för Halv Fjorton.",
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
            "Ja. Vi kan spela vigselmusik med helband, komp till solist eller kombinera med psalmer. Läs mer under bröllop och kompband.",
        ),
        (
            "Kan ni kompa en artist?",
            "Ja. Vi fungerar som kompband för solist, gästsång eller inhyrd artist. Se sidan kompband för artist.",
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
    faq_items = "\n".join(
        f"""          <details class="alt-faq__item">
            <summary class="alt-faq__question">{esc(q)}</summary>
            <div class="alt-faq__answer">
              <p>{esc(a)}</p>
            </div>
          </details>"""
        for q, a in faqs
    )
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
        extra_ld=[
            faq_ld,
            service_ld(
                "Kompband för artist",
                "Livekompri för solist eller artist på bröllop, fest och event i södra Sverige.",
                "/kompband/",
            ),
        ],
        extra_scripts='  <script src="/assets/js/alt-faq-accordion.js" defer></script>\n',
        body=f"""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Vanliga frågor</h1>
        <p class="lead">Svar på det vi oftast får frågor om.</p>
        <p class="page-hero__actions">
          <a class="alt-btn alt-btn--ghost" href="/kontakt/">Frågor? Kontakta oss</a>
        </p>
      </div>
    </header>
    <section class="section">
      <div class="wrap alt-faq">
        <div class="alt-faq__list" data-faq>
{faq_items}
        </div>
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
        body=f"""    <header class="page-hero compact">
      <div class="page-hero-copy">
        <h1>Hör av er</h1>
        <p class="lead">Fyll i formuläret så återkommer vi, oftast inom 24 timmar.</p>
      </div>
    </header>
{contact_offert_section(
    lead="Skriv datum, plats och vad ni planerar. Vi återkommer med förslag.",
)}
    <section class="section section--tight">
      <div class="wrap">
        <p class="small muted">Halv Fjorton EK. FÖR. · Org.nr 769641-5418 · <a href="https://www.instagram.com/halvfjorton/" rel="noopener noreferrer">Instagram @halvfjorton</a></p>
      </div>
    </section>
""",
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
- Bröllopsband: två set partymusik; tillval mingel, vigselmusik, komp till solist
- Företagsfest / festband: live på företagsfest, artistkomp, särskilda musikmoment
- Kompband för artist: /kompband/
- 50-årsfest och privatfest: /50-arsfest/
- Egen julkonsert (A Soulful Christmas, Nygatan 6 Växjö sedan 2023): /julkonsert/

## Viktiga sidor
- Startsida: {SITE}/
- Bröllop: {SITE}/brollop/
- Företag: {SITE}/foretag/
- FAQ: {SITE}/faq/
- Kontakt: {SITE}/kontakt/
- Konserter: {SITE}/konserter/
- Repertoar: {SITE}/repertoar/
- Bröllopsband Småland: {SITE}/brollopsband-smaland/
- Coverband Skåne: {SITE}/coverband-skane-malmo/
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
    if "data-mobile-menu" not in html:
        html = html.replace(
            "  </header>\n\n  <main id=\"innehall\">",
            "  </header>\n\n" + mobile_menu_block("/", "#offert") + "\n\n  <main id=\"innehall\">",
            1,
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
        lead="Skriv datum, plats och vad ni planerar. Vi återkommer med förslag.",
        usps=HOME_CONTACT_USPS,
    )
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


def assert_labs_asset_urls(target: Path, subpath: str) -> None:
    prefix = normalize_subpath(subpath)
    if not prefix:
        return
    needles = (
        'srcset="/assets/',
        "srcset='/assets/",
        'imagesrcset="/assets/',
        "imagesrcset='/assets/",
    )
    offenders: list[str] = []
    for file_path in target.rglob("*.html"):
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8")
        for needle in needles:
            if needle in text:
                offenders.append(f"{file_path.relative_to(target)} ({needle})")
                break
    if offenders:
        sample = "\n".join(f"  - {line}" for line in offenders[:20])
        raise SystemExit(f"Build check failed: unprefixed asset URLs in labs output:\n{sample}")


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
    assert_no_ai_dashes_in_build(OUT_ROOT)
    assert_no_eyebrows_in_build(OUT_ROOT)
    assert_labs_asset_urls(OUT_ROOT, subpath)
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
