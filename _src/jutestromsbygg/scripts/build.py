#!/usr/bin/env python3
"""Generate the Juteströms Bygg static site."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from cms_build import run_cms_build_steps  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT
LABS_BUILD_PREFIX = ""

SITE = "https://www.jutestromsbygg.se"
LABS_SUBPATH_DEFAULT = "/testing/jutestromsbygg"
BUILD_YEAR = datetime.now(timezone.utc).year

HOME_HERO_IMAGE = "gallery/byggbil-projekt.svg"
HOME_HERO_ALT = "Platshållarbild byggbil vid projekt"

LOREM_SHORT = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor "
    "incididunt ut labore et dolore magna aliqua."
)
LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor "
    "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
    "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
)
LOREM_LONG = (
    LOREM
    + " Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore "
    "eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
    "culpa qui officia deserunt mollit anim id est laborum."
)

NAV = [
    ("/", "Hem"),
    ("/tjanster/", "Tjänster"),
    ("/referenser/", "Referenser"),
    ("/kontakt/", "Kontakt"),
]

SITEMAP_PATHS = [p for p, _ in NAV]

GALLERY_ITEMS = [
    ("projekt-01.svg", "Projekt #1"),
    ("projekt-02.svg", "Projekt #2"),
    ("projekt-03.svg", "Projekt #3"),
    ("projekt-04.svg", "Projekt #4"),
    ("projekt-05.svg", "Projekt #5"),
    ("projekt-06.svg", "Projekt #6"),
]

SERVICES = [
    ("Tjänst #1", LOREM),
    ("Tjänst #2", LOREM),
    ("Tjänst #3", LOREM),
    ("Tjänst #4", LOREM),
]

BENEFITS = [
    ("Fördel #1", LOREM_SHORT),
    ("Fördel #2", LOREM_SHORT),
    ("Fördel #3", LOREM_SHORT),
]

PAGE_META: dict[str, dict[str, str]] = {
    "/": {
        "title": "Juteströms Bygg | Byggfirma",
        "description": "Juteströms Bygg är Sams byggfirma. Platshållarbeskrivning för startsidan.",
    },
    "/tjanster/": {
        "title": "Tjänster | Juteströms Bygg",
        "description": "Platshållarbeskrivning av tjänster från Juteströms Bygg.",
    },
    "/referenser/": {
        "title": "Referenser | Juteströms Bygg",
        "description": "Platshållarbeskrivning av referensprojekt från Juteströms Bygg.",
    },
    "/kontakt/": {
        "title": "Kontakt | Juteströms Bygg",
        "description": "Platshållarbeskrivning för kontakt och offertförfrågan.",
    },
}


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def nav_path(href: str, prefix: str = "") -> str:
    if href == "/":
        return prefix + "/" if prefix else "/"
    if not prefix:
        return href
    depth = prefix.count("/") - 1
    up = "../" * depth if depth > 0 else ""
    return up + href.lstrip("/")


def normalize_subpath(subpath: str) -> str:
    subpath = subpath.strip()
    if not subpath:
        return ""
    if not subpath.startswith("/"):
        subpath = "/" + subpath
    return subpath.rstrip("/")


def head_block(
    path: str,
    *,
    labs_prefix: str,
    canonical_base: str,
) -> str:
    meta = PAGE_META[path]
    canonical = f"{canonical_base}{path if path != '/' else '/'}"
    og_url = canonical
    asset_root = "/assets"
    robots = "noindex,nofollow" if labs_prefix else "index,follow"
    org = json.loads((ROOT / "assets/schema/organization.json").read_text(encoding="utf-8"))
    ld = json.dumps(org, ensure_ascii=False, indent=2)
    ld_indented = "\n".join(f"  {line}" for line in ld.splitlines())
    return f"""  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{esc(meta["title"])}</title>
  <meta name="description" content="{esc(meta["description"])}">
  <meta name="robots" content="{robots}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{esc(meta["title"])}">
  <meta property="og:description" content="{esc(meta["description"])}">
  <meta property="og:url" content="{og_url}">
  <meta property="og:locale" content="sv_SE">
  <meta property="og:site_name" content="Juteströms Bygg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Jost:wght@500;600&family=Work+Sans:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{asset_root}/css/site.css">
  <script type="application/ld+json">
{ld_indented}
  </script>"""


def header_markup(current: str) -> str:
    nav_items = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == current else ""
        nav_items.append(
            f'          <li><a href="{nav_path(href, "")}"{cur}>{esc(label)}</a></li>'
        )
    nav_html = "\n".join(nav_items)
    mobile_items = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == current else ""
        mobile_items.append(
            f'        <li><a href="{nav_path(href, "")}"{cur}>{esc(label)}</a></li>'
        )
    mobile_html = "\n".join(mobile_items)
    logo = "/assets/img/logo-dark.svg"
    return f"""  <header class="site-header">
    <div class="wrap site-header__inner">
      <a class="site-logo" href="{nav_path('/', "")}" aria-label="Juteströms Bygg, startsida">
        <img src="{logo}" alt="Juteströms Bygg" width="160" height="72" decoding="async">
      </a>
      <nav aria-label="Huvudmeny">
        <ul class="site-nav">
{nav_html}
        </ul>
      </nav>
      <button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="mobile-menu" aria-label="Öppna meny">
        <span class="nav-toggle__bars" aria-hidden="true"></span>
      </button>
    </div>
  </header>
  <div class="mobile-menu" id="mobile-menu" hidden>
    <button type="button" class="mobile-menu__close" data-nav-close aria-label="Stäng meny">
      <span class="mobile-menu__close-icon" aria-hidden="true"></span>
    </button>
    <ul class="mobile-menu__list">
{mobile_html}
    </ul>
  </div>"""


def footer_markup() -> str:
    links = []
    for href, label in NAV:
        links.append(f'            <li><a href="{nav_path(href, "")}">{esc(label)}</a></li>')
    links_html = "\n".join(links)
    logo = "/assets/img/logo-inverted.svg"
    asset_js = "/assets/js/nav.js"
    return f"""  <footer class="site-footer">
    <div class="wrap site-footer__grid">
      <div class="site-footer__col site-footer__brand">
        <a class="site-footer__logo" href="{nav_path('/', "")}" aria-label="Juteströms Bygg">
          <img src="{logo}" alt="Juteströms Bygg" width="140" height="64" loading="lazy" decoding="async">
        </a>
        <p class="site-footer__meta">© {BUILD_YEAR} Juteströms Bygg</p>
      </div>
      <div class="site-footer__col">
        <p class="site-footer__col-title">Titel lorem</p>
        <ul class="site-footer__links">
{links_html}
        </ul>
      </div>
      <div class="site-footer__col site-footer__contact">
        <p class="site-footer__col-title">Titel lorem</p>
        <ul class="site-footer__contact-list">
          <li>[Gatuadress 1]</li>
          <li>[000 00 Ort]</li>
          <li><a href="mailto:kontakt@exempel.se">kontakt@exempel.se</a></li>
          <li><a href="tel:+46000000000">[00-000 00 00]</a></li>
          <li>Org.nr [000000-0000]</li>
        </ul>
      </div>
    </div>
  </footer>
  <script src="{asset_js}" defer></script>
  <script src="/assets/js/hero-bg.js" defer></script>"""


def page_hero_band(modifier: str, title: str, lead: str) -> str:
    return f"""    <section class="page-hero page-hero--{modifier}">
      <div class="wrap">
        <h1>{esc(title)}</h1>
        <p class="page-hero__lead">{esc(lead)}</p>
      </div>
    </section>"""


def page_shell(path: str, main_body: str) -> str:
    labs_prefix = LABS_BUILD_PREFIX
    canonical_base = f"https://labs.ivarlundin.se{labs_prefix}" if labs_prefix else SITE
    return f"""<!DOCTYPE html>
<html lang="sv">
<head>
{head_block(path, labs_prefix=labs_prefix, canonical_base=canonical_base)}
</head>
<body>
{header_markup(path)}
  <main id="main">
{main_body}
  </main>
{footer_markup()}
</body>
</html>
"""


def home_body() -> str:
    cards = []
    for title, body in BENEFITS:
        cards.append(
            f"""          <article class="card">
            <h3>{esc(title)}</h3>
            <p>{esc(body)}</p>
          </article>"""
        )
    cards_html = "\n".join(cards)
    hero_src = f"/assets/img/{HOME_HERO_IMAGE}"
    hero_style = f"--hero-bg-image: url('{hero_src}');"
    return f"""    <section class="home-hero">
      <div class="home-hero__media" data-cms-hero="home" style="{hero_style}" aria-hidden="true">
        <img class="home-hero__img" src="{hero_src}" alt="" width="1600" height="900" decoding="async" fetchpriority="high" role="presentation" data-cms-alt="{esc(HOME_HERO_ALT)}">
      </div>
      <div class="home-hero__scrim" aria-hidden="true"></div>
      <div class="wrap home-hero__content">
        <h1>Juteströms Bygg</h1>
        <p class="home-hero__lead">{esc(LOREM)}</p>
      </div>
    </section>
    <section class="section section--tight">
      <div class="wrap">
        <h2>Titel lorem</h2>
        <div class="card-grid card-grid--3">
{cards_html}
        </div>
      </div>
    </section>
    <section class="section">
      <div class="wrap about-split">
        <div class="about-split__img">
          <img src="/assets/img/gallery/sam-portratt.svg" alt="Platshållarbild #1" width="800" height="1000" loading="lazy" decoding="async">
        </div>
        <div>
          <h2>Titel lorem</h2>
          <p>{esc(LOREM_LONG)}</p>
          <p>{esc(LOREM)}</p>
        </div>
      </div>
    </section>
    <section class="section section--tight">
      <div class="wrap">
        <div class="home-contact-card">
          <h2>Titel lorem</h2>
          <p>{esc(LOREM_SHORT)}</p>
          <p class="home-contact-card__lines">
            <a href="tel:+46000000000">[00-000 00 00]</a><br>
            <a href="mailto:kontakt@exempel.se">kontakt@exempel.se</a>
          </p>
          <a class="btn" href="/kontakt/">Kontakt</a>
        </div>
      </div>
    </section>"""


def tjanster_body() -> str:
    cards = []
    for title, body in SERVICES:
        cards.append(
            f"""          <article class="card">
            <h3>{esc(title)}</h3>
            <p>{esc(body)}</p>
          </article>"""
        )
    return f"""{page_hero_band("forest", "Tjänster", LOREM)}
    <section class="section">
      <div class="wrap">
        <div class="card-grid card-grid--2">
{chr(10).join(cards)}
        </div>
      </div>
    </section>"""


def referenser_body() -> str:
    figures = []
    for file, caption in GALLERY_ITEMS:
        figures.append(
            f"""        <figure>
          <img src="/assets/img/gallery/{file}" alt="Platshållarbild {esc(caption)}" width="1200" height="800" loading="lazy" decoding="async">
          <figcaption>{esc(caption)}</figcaption>
        </figure>"""
        )
    return f"""{page_hero_band("sage", "Referenser", LOREM)}
    <section class="section">
      <div class="wrap">
        <div class="gallery-grid" data-cms-gallery>
{chr(10).join(figures)}
        </div>
      </div>
    </section>"""


def kontakt_body() -> str:
    return f"""{page_hero_band("kalk", "Kontakt", LOREM_SHORT)}
    <section class="section">
      <div class="wrap contact-grid">
        <div>
          <h2>Titel lorem</h2>
          <p>{esc(LOREM_SHORT)}</p>
          <ul class="contact-details">
            <li>Telefon: <span>[00-000 00 00]</span></li>
            <li>E-post: <span>kontakt@exempel.se</span></li>
            <li>Område: <span>[Platshållare ort och omnejd]</span></li>
          </ul>
        </div>
        <div>
          <h2>Titel lorem</h2>
          <p>{esc(LOREM_SHORT)}</p>
          <form class="offert-form" action="#" method="post" data-offert-placeholder>
            <label>
              Namn
              <input type="text" name="namn" autocomplete="name" placeholder="För- och efternamn">
            </label>
            <label>
              E-post
              <input type="email" name="epost" autocomplete="email" placeholder="namn@exempel.se">
            </label>
            <label>
              Telefon
              <input type="tel" name="telefon" autocomplete="tel" placeholder="00-000 00 00">
            </label>
            <label>
              Meddelande
              <textarea name="meddelande" placeholder="Beskriv projektet kort"></textarea>
            </label>
            <button type="submit" class="btn">Skicka (platshållare)</button>
            <p class="page-hero__lead">Formuläret är en platshållare utan backend.</p>
          </form>
        </div>
      </div>
    </section>"""


def write_page(rel_dir: str, path_key: str, body_fn) -> None:
    body = body_fn()
    html = page_shell(path_key, body)
    if rel_dir:
        dest = OUT_ROOT / rel_dir / "index.html"
    else:
        dest = OUT_ROOT / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
    print("wrote", dest.relative_to(OUT_ROOT))


def write_sitemap(subpath: str) -> None:
    prefix = normalize_subpath(subpath)
    base = f"https://labs.ivarlundin.se{prefix}" if prefix else SITE
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path in SITEMAP_PATHS:
        loc = base + (path if path != "/" else "/")
        lines.append("  <url>")
        lines.append(f"    <loc>{loc}</loc>")
        lines.append("  </url>")
    lines.append("</urlset>")
    (OUT_ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote sitemap.xml")


def write_robots(subpath: str) -> None:
    prefix = normalize_subpath(subpath)
    sitemap = f"https://labs.ivarlundin.se{prefix}/sitemap.xml" if prefix else f"{SITE}/sitemap.xml"
    (OUT_ROOT / "robots.txt").write_text(f"Sitemap: {sitemap}\n", encoding="utf-8")


def prepare_output_directory(target: Path) -> None:
    if target.resolve() == ROOT.resolve():
        return
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    shutil.copytree(ROOT / "assets", target / "assets")
    for name in (".nojekyll",):
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, target / name)
    (target / ".nojekyll").write_text("", encoding="utf-8")


_ROOT_RELATIVE_URL = re.compile(
    r'(?P<attr>href|src|content|srcset|imagesrcset)=(?P<q>["\'])(?P<path>/[^"\']*)(?P=q)'
)


def _prefix_asset_root(path: str, prefix: str) -> str:
    if path.startswith("//"):
        return path
    if path.startswith("/assets/") or path.startswith("/"):
        if path.startswith("/assets/") or path in ("/",) or path.startswith("/tjanster"):
            return f"{prefix}{path}"
    return path


def _prefix_bare_asset_urls(text: str, prefix: str) -> str:
    return re.sub(
        r'(?P<attr>href|src|srcset|imagesrcset|content)=(?P<q>["\'])/assets/',
        lambda m: f'{m.group("attr")}={m.group("q")}{prefix}/assets/',
        text,
    )


_STYLE_ASSET_URL = re.compile(r"url\((['\"]?)(/assets/[^'\"\)\s]+)\1\)")


def _prefix_style_asset_urls(text: str, prefix: str) -> str:
    def repl(match: re.Match[str]) -> str:
        quote = match.group(1) or ""
        path = match.group(2)
        return f"url({quote}{prefix}{path}{quote})"

    return _STYLE_ASSET_URL.sub(repl, text)


def rewrite_root_relative_urls(target: Path, subpath: str) -> None:
    prefix = normalize_subpath(subpath)
    if not prefix:
        return

    def replace_url(match: re.Match[str]) -> str:
        path = match.group("path")
        if path.startswith("//") or path.startswith("http"):
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
            if path.startswith("/"):
                path = f"{prefix}{path}"
        return f"{attr}={q}{path}{q}"

    extensions = {".html", ".xml", ".css", ".js", ".txt"}
    for file_path in target.rglob("*"):
        if not file_path.is_file() or file_path.suffix not in extensions:
            continue
        text = file_path.read_text(encoding="utf-8")
        updated = _ROOT_RELATIVE_URL.sub(replace_url, text)
        updated = _prefix_bare_asset_urls(updated, prefix)
        updated = _prefix_style_asset_urls(updated, prefix)
        if updated != text:
            file_path.write_text(updated, encoding="utf-8")


_UNPREFIXED_LABS_ASSET = re.compile(
    r"""(?P<attr>href|src|srcset|imagesrcset|content)=(?P<q>["'])/assets/"""
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
        sample = "\n".join(f"  - {line}" for line in offenders[:15])
        raise SystemExit(f"Build check failed: unprefixed /assets/ URLs:\n{sample}")


def assert_one_h1_per_page(target: Path) -> None:
    for file_path in target.rglob("*.html"):
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8")
        count = len(re.findall(r"<h1\b", text, flags=re.IGNORECASE))
        if count != 1:
            raise SystemExit(f"Build check failed: expected 1 h1 in {file_path.name}, got {count}")


def run_build(output_dir: Path | None = None, subpath: str = "") -> None:
    global OUT_ROOT, LABS_BUILD_PREFIX
    OUT_ROOT = output_dir.resolve() if output_dir else ROOT
    LABS_BUILD_PREFIX = normalize_subpath(subpath) if output_dir else ""
    if output_dir and OUT_ROOT != ROOT.resolve():
        prepare_output_directory(OUT_ROOT)
    else:
        OUT_ROOT.mkdir(parents=True, exist_ok=True)

    write_page("", "/", home_body)
    write_page("tjanster", "/tjanster/", tjanster_body)
    write_page("referenser", "/referenser/", referenser_body)
    write_page("kontakt", "/kontakt/", kontakt_body)
    write_sitemap(subpath)
    write_robots(subpath)
    rewrite_root_relative_urls(OUT_ROOT, subpath)
    run_cms_build_steps(OUT_ROOT, ROOT, normalize_subpath(subpath))
    assert_labs_asset_urls(OUT_ROOT, subpath)
    assert_one_h1_per_page(OUT_ROOT)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the Juteströms Bygg static site.")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--subpath", default="", help=f"Labs subpath (default: {LABS_SUBPATH_DEFAULT})")
    args = parser.parse_args()
    subpath = args.subpath
    if args.output_dir and not subpath:
        subpath = LABS_SUBPATH_DEFAULT
    run_build(output_dir=args.output_dir, subpath=subpath)
