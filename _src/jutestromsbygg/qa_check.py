#!/usr/bin/env python3
"""Simple QA gate for Juteström Bygg (see README.md)."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

_SRC = Path(__file__).resolve().parent
REPO_ROOT = _SRC.parents[1]
TESTING_OUT = REPO_ROOT / "testing" / "jutestromsbygg"
SUBPATH = "/testing/jutestromsbygg"

PAGES = ["/", "/tjanster/", "/referenser/", "/kontakt/"]


def run_build() -> None:
    subprocess.run(
        [
            sys.executable,
            "scripts/build.py",
            "--output-dir",
            str(TESTING_OUT),
            "--subpath",
            SUBPATH,
        ],
        cwd=str(_SRC),
        check=True,
    )


def html_path(site_path: str) -> Path:
    if site_path == "/":
        return TESTING_OUT / "index.html"
    return TESTING_OUT / site_path.strip("/") / "index.html"


def check_meta_and_h1() -> list[str]:
    errors: list[str] = []
    for path in PAGES:
        file = html_path(path)
        text = file.read_text(encoding="utf-8")
        if len(re.findall(r"<h1\b", text, re.I)) != 1:
            errors.append(f"{path}: expected exactly one H1")
        if not re.search(r"<title>[^<]+</title>", text):
            errors.append(f"{path}: missing title")
        if not re.search(r'<meta name="description" content="[^"]+"', text):
            errors.append(f"{path}: missing meta description")
        if 'name="robots" content="noindex,nofollow"' not in text:
            errors.append(f"{path}: missing noindex robots meta")
    return errors


def resolve_href(href: str, page_path: str) -> Path | None:
    href = href.split("#")[0].split("?")[0].strip()
    if not href or href.startswith("mailto:") or href.startswith("tel:"):
        return None
    if href.startswith("http://") or href.startswith("https://"):
        return None
    if href.startswith(SUBPATH):
        href = href[len(SUBPATH) :] or "/"
    if href.startswith("/assets/"):
        return TESTING_OUT / "assets" / href[len("/assets/") :].lstrip("/")
    if href.startswith("/"):
        if href == "/":
            return TESTING_OUT / "index.html"
        rel = href.strip("/")
        if rel.startswith("assets/"):
            return TESTING_OUT / rel
        candidate = TESTING_OUT / rel
        if candidate.is_file():
            return candidate
        return TESTING_OUT / rel / "index.html"
    return None


def check_links_and_assets() -> list[str]:
    errors: list[str] = []
    for path in PAGES:
        text = html_path(path).read_text(encoding="utf-8")
        for m in re.finditer(r'(?:href|src)="([^"]+)"', text):
            href = m.group(1)
            target = resolve_href(href, path)
            if target is None:
                continue
            if not target.is_file():
                errors.append(f"{path}: missing target {href} -> {target}")
    manifest = TESTING_OUT / "assets" / "cms" / "image-manifest.json"
    if not manifest.is_file():
        errors.append("missing assets/cms/image-manifest.json")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    if not args.skip_build:
        run_build()
    errors = check_meta_and_h1() + check_links_and_assets()
    if errors:
        print("QA FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"QA OK ({len(PAGES)} pages, output {TESTING_OUT})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
