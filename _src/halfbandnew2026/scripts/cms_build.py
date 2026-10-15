"""CMS mode: build-time IDs, image manifest, and script injection."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

CMS_STUB_MARK = 'data-cms-stub="1"'


def cms_asset_version(source_root: Path) -> str:
    blobs: list[bytes] = []
    for rel in (
        "assets/js/cms-mode.js",
        "assets/js/cmsmode-stub.js",
        "assets/css/cms-mode.css",
    ):
        path = source_root / rel
        if path.is_file():
            blobs.append(path.read_bytes())
    if not blobs:
        return "0"
    return hashlib.sha256(b"".join(blobs)).hexdigest()[:10]


def cms_stub_script(url_prefix: str, version: str = "") -> str:
    query = f"?v={version}" if version else ""
    return (
        f'  <script src="{url_prefix}/assets/js/cmsmode-stub.js{query}" defer data-cms-stub="1"></script>\n'
    )

# Tags that receive data-cms-id for inline text editing (within main/footer).
_TEXT_TAGS = frozenset(
    {
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "p",
        "li",
        "dt",
        "dd",
        "summary",
        "button",
        "figcaption",
        "label",
        "span",
        "a",
        "td",
        "th",
        "blockquote",
    }
)

_SKIP_ANCESTOR_MARKERS = (
    "<script",
    "<style",
    "<svg",
    "<noscript",
    "class=\"alt-nav",
    "class=\"mobile-menu",
    "data-tally",
    "application/ld+json",
)

_IMAGE_EXTS = {".webp", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".avif"}


def _page_slug(rel_html: str) -> str:
    rel = rel_html.replace("\\", "/")
    if rel == "index.html":
        return "home"
    if rel.endswith("/index.html"):
        return rel[: -len("/index.html")].replace("/", "-")
    return rel.replace("/", "-").replace(".html", "")


def _source_file_for_page(rel_html: str) -> str:
    rel = rel_html.replace("\\", "/")
    if rel == "index.html":
        return "home/index.html"
    return "scripts/build.py"


def _should_skip_region(chunk: str, pos: int) -> bool:
    window = chunk[max(0, pos - 400) : pos].lower()
    for marker in _SKIP_ANCESTOR_MARKERS:
        if marker.lower() in window:
            # crude: skip if we're inside script/style/svg blocks
            if marker in ('<script', '<style', '<svg', '<noscript'):
                opens = window.count(marker)
                closes = window.count("</" + marker[1:])
                if opens > closes:
                    return True
    return False


def _in_editable_region(html: str, pos: int) -> bool:
    before = html[:pos]
    main_open = before.rfind("<main")
    main_close = before.rfind("</main>")
    footer_open = before.rfind('<footer class="site-footer"')
    footer_close = before.rfind("</footer>")
    in_main = main_open != -1 and main_open > main_close
    in_footer = footer_open != -1 and footer_open > footer_close
    return in_main or in_footer


_OPEN_TAG = re.compile(
    r"<(?P<tag>[a-zA-Z][a-zA-Z0-9]*)\b(?P<attrs>[^>]*?)(?P<slash>/)?>",
    re.DOTALL,
)


def _inject_attr(attrs: str, name: str, value: str) -> str:
    if re.search(rf"\b{name}\s*=", attrs):
        return attrs
    return f'{attrs} {name}="{value}"'


def _attr_value(attrs: str, name: str) -> str:
    m = re.search(rf'\b{name}="([^"]*)"', attrs)
    if m:
        return m.group(1)
    m = re.search(rf"\b{name}='([^']*)'", attrs)
    return m.group(1) if m else ""


def _text_location_key(tag: str, attrs: str, ordinal: int) -> str:
    el_id = _attr_value(attrs, "id")
    classes = _attr_value(attrs, "class").split()
    class_bit = "-".join(classes[:2]) if classes else ""
    if el_id:
        base = f"{tag}#id-{el_id}"
    elif class_bit:
        base = f"{tag}.{class_bit}"
    else:
        base = tag
    return f"{base}@{ordinal}"


def _stable_cms_hash(page_slug: str, kind: str, material: str) -> str:
    digest = hashlib.sha256(f"{page_slug}:{kind}:{material}".encode("utf-8")).hexdigest()
    return digest[:10]


def _make_text_cms_id(page_slug: str, tag: str, attrs: str, counters: dict[str, int]) -> str:
    el_id = _attr_value(attrs, "id")
    classes = _attr_value(attrs, "class").split()
    class_bit = "-".join(classes[:2]) if classes else ""
    bucket = f"{tag}|{el_id}|{class_bit}"
    ordinal = counters.get(bucket, 0)
    counters[bucket] = ordinal + 1
    location = _text_location_key(tag, attrs, ordinal)
    short = _stable_cms_hash(page_slug, "text", location)
    return f"cms-{page_slug}-t-{short}"


def _make_image_cms_id(page_slug: str, attrs: str) -> str:
    src = _attr_value(attrs, "src").split("?")[0]
    src = re.sub(r"^/assets/img/", "", src)
    short = _stable_cms_hash(page_slug, "img", src or attrs)
    return f"cms-{page_slug}-img-{short}"


def _skip_anchor_wrapper(attrs: str) -> bool:
    """Card/CTA links wrap block content; edit inner h2/p/span instead."""
    if re.search(r'\bclass="[^"]*\balt-offer-card\b', attrs):
        return True
    if re.search(r"\bclass='[^']*\balt-offer-card\b", attrs):
        return True
    if "alt-btn" in attrs:
        return True
    return False


def annotate_html(
    html: str,
    page_slug: str,
    source_file: str,
    url_prefix: str = "",
    cms_version: str = "",
) -> str:
    text_counters: dict[str, int] = {}

    def repl(match: re.Match[str]) -> str:
        tag = match.group("tag").lower()
        attrs = match.group("attrs") or ""
        slash = match.group("slash") or ""
        pos = match.start()

        if tag == "body" and "data-cms-page-source" not in attrs:
            attrs = _inject_attr(attrs, "data-cms-page-source", source_file)
            attrs = _inject_attr(attrs, "data-cms-page-slug", page_slug)
            return f"<{tag}{attrs}{slash}>"

        if tag == "img":
            if not _in_editable_region(html, pos) or _should_skip_region(html, pos):
                return match.group(0)
            if "data-cms-id" in attrs:
                return match.group(0)
            cid = _make_image_cms_id(page_slug, attrs)
            attrs = _inject_attr(attrs, "data-cms-id", cid)
            attrs = _inject_attr(attrs, "data-cms-type", "image")
            return f"<img{attrs}{slash}>"

        if tag not in _TEXT_TAGS:
            return match.group(0)
        if not _in_editable_region(html, pos) or _should_skip_region(html, pos):
            return match.group(0)
        if "data-cms-id" in attrs:
            return match.group(0)
        if tag == "a" and _skip_anchor_wrapper(attrs):
            return match.group(0)
        if tag == "a" and 'class="' in attrs and "alt-btn__icon" in attrs:
            return match.group(0)
        if "aria-hidden=\"true\"" in attrs or "aria-hidden='true'" in attrs:
            return match.group(0)

        cid = _make_text_cms_id(page_slug, tag, attrs, text_counters)
        attrs = _inject_attr(attrs, "data-cms-id", cid)
        attrs = _inject_attr(attrs, "data-cms-type", "text")
        return f"<{tag}{attrs}{slash}>"

    html = _OPEN_TAG.sub(repl, html)

    if CMS_STUB_MARK not in html:
        prefix = url_prefix.rstrip("/") if url_prefix else ""
        html = html.replace("</body>", f"{cms_stub_script(prefix, cms_version)}</body>")
    return html


def annotate_site_html(target: Path, url_prefix: str = "", cms_version: str = "") -> None:
    for file_path in sorted(target.rglob("*.html")):
        if not file_path.is_file():
            continue
        rel = str(file_path.relative_to(target))
        if rel.startswith("home/"):
            continue
        slug = _page_slug(rel)
        source = _source_file_for_page(rel)
        text = file_path.read_text(encoding="utf-8")
        patched = annotate_html(
            text, slug, source, url_prefix=url_prefix, cms_version=cms_version
        )
        if patched != text:
            file_path.write_text(patched, encoding="utf-8")
            print("cms-annotate", rel)


def _base_stem(stem: str) -> str:
    return re.sub(r"-(?:480|800|1200|1600|1920)w$", "", stem)


def _logical_image_key(rel_path: str) -> str | None:
    p = Path(rel_path)
    if p.suffix.lower() not in _IMAGE_EXTS:
        return None
    base_stem = _base_stem(p.stem)
    parent = p.parent.as_posix()
    if parent == ".":
        return f"{base_stem}{p.suffix.lower()}"
    return f"{parent}/{base_stem}{p.suffix.lower()}"


def _variant_width_from_name(stem: str) -> str | None:
    m = re.search(r"-(480|800|1200|1600|1920)w$", stem)
    if m:
        return f"{m.group(1)}w"
    return None


def write_image_manifest(img_root: Path, out_path: Path, url_prefix: str = "") -> None:
    groups: dict[str, dict] = {}

    if not img_root.is_dir():
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps({"version": 1, "images": []}, indent=2) + "\n", encoding="utf-8")
        return

    for file_path in sorted(img_root.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in _IMAGE_EXTS:
            continue
        rel = file_path.relative_to(img_root).as_posix()
        key = _logical_image_key(rel)
        if not key:
            continue
        entry = groups.setdefault(
            key,
            {
                "id": key,
                "label": Path(key).name,
                "variants": {},
                "paths": [],
            },
        )
        entry["paths"].append(rel)
        w = _variant_width_from_name(file_path.stem)
        url = f"{url_prefix}/assets/img/{rel}"
        if w:
            entry["variants"][w] = url
        else:
            entry["variants"]["default"] = url

    images = []
    for key in sorted(groups.keys()):
        g = groups[key]
        variants = g["variants"]
        if "default" not in variants and variants:
            # pick shortest path as default
            default_rel = min(g["paths"], key=len)
            variants["default"] = f"{url_prefix}/assets/img/{default_rel}"
        srcset_parts = []
        for w in ("480w", "800w", "1200w", "1600w", "1920w"):
            if w in variants:
                width = w.replace("w", "")
                srcset_parts.append(f"{variants[w]} {width}w")
        images.append(
            {
                "id": key,
                "label": g["label"],
                "default": variants.get("default", ""),
                "variants": variants,
                "srcset": ", ".join(srcset_parts),
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"version": 1, "generated": True, "images": images}, indent=2) + "\n",
        encoding="utf-8",
    )
    print("wrote", out_path)


def run_cms_build_steps(target: Path, source_root: Path, subpath: str) -> None:
    prefix = subpath.rstrip("/") if subpath else ""
    cms_version = cms_asset_version(source_root)
    manifest_out = target / "assets" / "cms" / "image-manifest.json"
    write_image_manifest(source_root / "assets" / "img", manifest_out, url_prefix=prefix)
    annotate_site_html(target, url_prefix=prefix, cms_version=cms_version)
