#!/usr/bin/env python3
"""Check a built site directory before deployment.

Usage: python3 scripts/site_check.py _site [--source .]

Fails (exit 1) on: em or en dashes in rendered text, exclamation marks in prose,
banned phrases (plus any listed in _local/banned-words.txt), internal links or asset references that do not resolve, images
without alt text, a generator meta tag, and leftover template placeholders.
Only the standard library is used so the check runs anywhere.
"""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

BANNED = [
    "world-leading", "cutting-edge", "pioneering", "groundbreaking", "state-of-the-art", "passionate",
    "seamless", "leverage", "unleash", "elevate", "top-tier", "lorem ipsum", "al-folio", "your name",
    "16% success", "MIST v1.2", "APOGEE-quality",
]
LOCAL_WORDS = Path(__file__).resolve().parent.parent / "_local" / "banned-words.txt"
DASHES = re.compile("[–—]")
SKIP_DIRS = {"stellar-explorer"}  # self-contained app with its own conventions


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text: list[str] = []
        self.links: list[str] = []
        self.assets: list[str] = []
        self.images_without_alt = 0
        self.generator = False
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self._skip += 1
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag in ("img", "script", "source") and a.get("src"):
            self.assets.append(a["src"])
        if tag == "link" and a.get("href") and a.get("rel") in ("stylesheet", "icon", "preload"):
            self.assets.append(a["href"])
        if tag == "img" and not a.get("alt", "").strip() and a.get("role") != "presentation":
            self.images_without_alt += 1
        if tag == "meta" and a.get("name") == "generator":
            self.generator = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.text.append(data)


def local_target(site: Path, page: Path, ref: str) -> Path | None:
    parts = urlsplit(ref)
    if parts.scheme or parts.netloc or ref.startswith("mailto:") or ref.startswith("#"):
        return None
    path = unquote(parts.path)
    if not path:
        return None
    target = site / path.lstrip("/") if path.startswith("/") else page.parent / path
    if target.is_dir():
        target = target / "index.html"
    return target


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    site = Path(argv[1]).resolve()
    banned = list(BANNED)
    if LOCAL_WORDS.exists():
        banned += [w.strip() for w in LOCAL_WORDS.read_text().splitlines() if w.strip() and not w.startswith("#")]
    findings: list[str] = []
    pages = [p for p in site.rglob("*.html") if not any(part in SKIP_DIRS for part in p.relative_to(site).parts)]
    for page in pages:
        rel = page.relative_to(site)
        parser = Page()
        parser.feed(page.read_text(errors="replace"))
        text = " ".join(parser.text)
        if DASHES.search(text):
            findings.append(f"{rel}: em or en dash in text")
        if "!" in re.sub(r"\s+", " ", text):
            findings.append(f"{rel}: exclamation mark in text")
        low = text.lower()
        for w in banned:
            if w.lower() in low:
                findings.append(f"{rel}: banned phrase {w!r}")
        if parser.generator:
            findings.append(f"{rel}: generator meta tag present")
        if parser.images_without_alt:
            findings.append(f"{rel}: {parser.images_without_alt} image(s) without alt text")
        if "{{" in text or "{%" in text:
            findings.append(f"{rel}: unrendered template syntax")
        for ref in parser.links + parser.assets:
            target = local_target(site, page, ref)
            if target is not None and not target.exists():
                findings.append(f"{rel}: broken local reference {ref}")
    for f in findings:
        print(f)
    print(f"{len(pages)} pages checked, {len(findings)} findings")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
