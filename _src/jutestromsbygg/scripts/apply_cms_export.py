#!/usr/bin/env python3
"""Apply a CMS mode JSON export back into _src sources (best-effort)."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _replace_unique(text: str, old: str, new: str, label: str) -> str:
    if old == new:
        return text
    count = text.count(old)
    if count == 0:
        print(f"skip {label}: old value not found", file=sys.stderr)
        return text
    if count > 1:
        print(f"warn {label}: old value appears {count} times; replacing all", file=sys.stderr)
    return text.replace(old, new)


def apply_typewriter(text: str, change: dict) -> str:
    meta = change.get("meta") or {}
    phrases = meta.get("phrases")
    if not phrases:
        return text
    attr = json.dumps(phrases, ensure_ascii=False)
    old_phrases = meta.get("originalPhrases") or []
    if old_phrases:
        old_attr = json.dumps(old_phrases, ensure_ascii=False)
        pattern = r'data-typewriter-phrases="' + re.escape(old_attr).replace("\\ ", " ") + r'"'
        if re.search(pattern, text):
            return re.sub(
                r'data-typewriter-phrases="[^"]*"',
                f'data-typewriter-phrases="{attr}"',
                text,
                count=1,
            )
    return text


def _stem_from_manifest_id(manifest_id: str) -> str:
    return Path(manifest_id).stem


def _hero_slide_markup(item: dict, index: int) -> str:
    manifest_id = item.get("manifestId", "")
    alt = html.escape(item.get("alt") or "", quote=True)
    stem = _stem_from_manifest_id(manifest_id)
    if manifest_id == "stage.jpg":
        base = "/assets/img/stage.jpg"
        return (
            f'          <div class="alt-hero__slide">\n'
            f'            <img src="{base}" sizes="100vw" alt="{alt}" '
            f'width="2400" height="1600" loading="lazy" decoding="async">\n'
            f"          </div>"
        )
    base = f"/assets/img/gallery/{stem}"
    first = index == 0
    loading = "eager" if first else "lazy"
    fp = ' fetchpriority="high"' if first else ""
    width, height = ("1280", "853") if "04" in stem or "05" in stem else ("2400", "1600")
    return (
        f'          <div class="alt-hero__slide">\n'
        f'            <img src="{base}-1200w.webp" '
        f'srcset="{base}-480w.webp 480w, {base}-800w.webp 800w, '
        f'{base}-1200w.webp 1200w, {base}-1920w.webp 1920w" sizes="100vw" '
        f'alt="{alt}" width="{width}" height="{height}" loading="{loading}" '
        f'decoding="async"{fp}>\n'
        f"          </div>"
    )


def apply_image_list_home(text: str, change: dict) -> str:
    meta = change.get("meta") or {}
    new_list = meta.get("newList")
    if not new_list and change.get("newValue"):
        try:
            new_list = json.loads(change["newValue"])
        except json.JSONDecodeError:
            new_list = []
    if not new_list:
        return text
    slides = "\n".join(_hero_slide_markup(item, i) for i, item in enumerate(new_list))
    pattern = (
        r'(<div class="alt-hero__carousel" data-cms-hero="home">\s*)'
        r"(.*?)(\s*</div>\s*</div>\s*<div class=\"alt-hero__scrim\")"
    )
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        print("skip imageList home: carousel block not found", file=sys.stderr)
        return text
    return text[: match.start(2)] + "\n" + slides + "\n        " + text[match.start(3) :]


def _service_slide_dims(stem: str) -> tuple[int, int]:
    if stem in ("halvfjorton-04",) or "04" in stem and "hero" not in stem:
        return 1280, 853
    return 2400, 1600


def _service_slide_position(stem: str) -> str:
    if stem == "halvfjorton-03-hero":
        return "center 38%"
    return "center"


def _format_service_hero_slide(item: dict) -> str:
    stem = _stem_from_manifest_id(item.get("manifestId", ""))
    alt = json.dumps(item.get("alt") or "", ensure_ascii=False)
    w, h = _service_slide_dims(stem)
    pos = _service_slide_position(stem)
    return (
        f"        (\n"
        f'            "{stem}",\n'
        f"            {alt},\n"
        f"            {w},\n"
        f"            {h},\n"
        f'            "{pos}",\n'
        f"        )"
    )


def apply_image_list_service_build(text: str, hero_key: str, new_list: list[dict]) -> str:
    slides_body = ",\n".join(_format_service_hero_slide(item) for item in new_list)
    pattern = rf'("{hero_key}": \[)(.*?)(\n    \],)'
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        print(
            f"skip imageList service {hero_key}: SERVICE_HERO_SLIDES entry not found",
            file=sys.stderr,
        )
        return text
    replacement = match.group(1) + "\n" + slides_body + match.group(3)
    return text[: match.start()] + replacement + text[match.end() :]


def apply_image_list(change: dict, text: str, source: str) -> str:
    meta = change.get("meta") or {}
    hero_key = meta.get("heroKey", "")
    new_list = meta.get("newList") or []
    if hero_key == "home" and source.endswith("home/index.html"):
        return apply_image_list_home(text, change)
    if source.endswith("scripts/build.py") and hero_key in ("brollop", "foretag", "mingel"):
        if not new_list:
            return text
        return apply_image_list_service_build(text, hero_key, new_list)
    print(f"skip imageList: unsupported target {hero_key} in {source}", file=sys.stderr)
    return text


def apply_change(root: Path, change: dict) -> bool:
    source = change.get("sourceFile", "")
    if source.startswith("_src/jutestromsbygg/"):
        source = source.removeprefix("_src/jutestromsbygg/")
    path = root / source
    if not path.is_file():
        print(f"missing source: {path}", file=sys.stderr)
        return False

    text = path.read_text(encoding="utf-8")
    ctype = change.get("type")
    old = change.get("oldValue", "")
    new = change.get("newValue", "")

    if ctype == "text":
        updated = _replace_unique(text, old, new, change.get("cmsId", "text"))
    elif ctype == "image":
        old_src = old.split("/assets/")[-1] if "/assets/" in old else old
        new_src = new.split("/assets/")[-1] if "/assets/" in new else new
        updated = text.replace(f"/assets/img/{old_src}", f"/assets/img/{new_src}")
        meta = change.get("meta") or {}
        alt = meta.get("alt")
        orig_alt = meta.get("originalAlt")
        if alt and orig_alt and orig_alt in updated:
            updated = updated.replace(f'alt="{orig_alt}"', f'alt="{alt}"', 1)
    elif ctype == "typewriter":
        updated = apply_typewriter(text, change)
        if meta := change.get("meta") or {}:
            phrases = meta.get("phrases") or []
            if phrases:
                longest = max(phrases, key=len)
                first = phrases[0]
                if meta.get("originalGhost") and meta["originalGhost"] in updated:
                    updated = updated.replace(meta["originalGhost"], longest, 1)
                if first and meta.get("originalPhrases"):
                    old_first = meta["originalPhrases"][0]
                    if old_first in updated:
                        updated = updated.replace(old_first, first, 1)
    elif ctype == "imageList":
        updated = apply_image_list(change, text, source)
    else:
        print(f"unknown type {ctype}", file=sys.stderr)
        return False

    if updated != text:
        path.write_text(updated, encoding="utf-8")
        print("updated", path.relative_to(root))
        return True
    print(f"no-op {change.get('cmsId')}", file=sys.stderr)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply cmsmode export JSON to _src.")
    parser.add_argument("export_json", type=Path, help="Exported cms-*.json file")
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Site root (_src/jutestromsbygg)",
    )
    args = parser.parse_args()
    data = json.loads(args.export_json.read_text(encoding="utf-8"))
    changes = data.get("changes") or []
    applied = 0
    for change in changes:
        if apply_change(args.root.resolve(), change):
            applied += 1
    print(f"Applied {applied}/{len(changes)} changes. Re-run scripts/build.py after reviewing.")


if __name__ == "__main__":
    main()
