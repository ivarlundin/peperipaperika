#!/usr/bin/env python3
"""Apply a CMS mode JSON export back into _src sources (best-effort)."""

from __future__ import annotations

import argparse
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
    # Replace data-typewriter-phrases="..." when old phrases match
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


def apply_change(root: Path, change: dict) -> bool:
    source = change.get("sourceFile", "")
    if source.startswith("_src/halfbandnew2026/"):
        source = source.removeprefix("_src/halfbandnew2026/")
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
        help="Site root (_src/halfbandnew2026)",
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
