#!/usr/bin/env python3
"""Embed copyright metadata in my own media, with no change to a pixel or a stream.

Run from anywhere, and again after installing new renders; files already stamped are left alone.

    python3 scripts/stamp_media.py           stamp and verify
    python3 scripts/stamp_media.py --check   report what is unstamped, change nothing
    python3 scripts/stamp_media.py --list    print the files this script treats as mine

WebP: an XMP chunk appended to the RIFF container (with a VP8X header where the file had none). The
image chunks are copied as bytes; the decoded pixels are compared before anything is written.
MP4: ffmpeg stream copy with artist, copyright and comment tags and faststart; the stream's md5 and
per-packet checksums are compared before the original is replaced.
SVG: a <metadata> element at the end of each top-level <svg>.

Only the files named by OWN are touched. Third-party images and pictures of me are not on it and must
not be added: NOT_OWN names what sits beside the renders, and anything matching neither is reported.
"""

from __future__ import annotations

import fnmatch
import hashlib
import io
import json
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CREATOR = "Andreas W. Neitzel"
COPYRIGHT = "© Andreas W. Neitzel. All rights reserved."
SITE = "https://andreaswneitzel.github.io"

OWN = [
    "assets/img/heroes/*.poster.webp",
    "assets/img/heroes/card_*.webp",
    "assets/img/heroes/line_*.webp",
    "assets/img/heroes/research_*.webp",
    "assets/img/heroes/software_*.webp",
    "assets/img/heroes/ariel.webp",
    "assets/img/heroes/ariel_card.webp",
    "assets/img/heroes/plato.webp",
    "assets/img/heroes/plato_card.webp",
    "assets/img/heroes/publications.webp",
    "assets/img/heroes/portal/line_*.webp",
    "assets/img/heroes/portal/research_*.webp",
    "assets/img/heroes/portal/software_*.webp",
    "assets/img/figures/janus-gaia.webp",
    "assets/img/guide/paranal-*.webp",
    "assets/img/tellurion/*.webp",
    "assets/img/visualisations/*.webp",
    "assets/img/papers/neitzel-2022-kippenhahn.webp",
    "assets/video/*.mp4",
    "assets/img/favicon.svg",
    "assets/img/kind-marks.svg",
    "assets/img/map/world_map.svg",
    "_includes/figures/*.svg",
]
# Beside the renders, never stamped: pictures of me, photographs from my collection, the grain textures.
NOT_OWN = [
    "assets/img/heroes/eso_*.webp",
    "assets/img/heroes/headshot_*.webp",
    "assets/img/heroes/hero_*.webp",
    "assets/img/heroes/talk_*.webp",
    "assets/img/heroes/grain-*.webp",
    "assets/img/heroes/portal/talk_*.webp",
    "assets/img/heroes/portal/ut-frame.webp",
]
WATCHED = ["assets/img/heroes/*", "assets/img/heroes/portal/*", "assets/video/*"]

XMP = (
    '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    '<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/">'
    f"<dc:creator><rdf:Seq><rdf:li>{CREATOR}</rdf:li></rdf:Seq></dc:creator>"
    f'<dc:rights><rdf:Alt><rdf:li xml:lang="x-default">{COPYRIGHT}</rdf:li></rdf:Alt></dc:rights>'
    f"<xmpRights:Marked>True</xmpRights:Marked><xmpRights:WebStatement>{SITE}</xmpRights:WebStatement>"
    "</rdf:Description></rdf:RDF></x:xmpmeta>"
).encode()
SVG_NOTE = f"<metadata>Creator: {CREATOR}. {COPYRIGHT} {SITE}</metadata>"
IMAGE_CHUNKS = {b"VP8 ", b"VP8L", b"ALPH", b"ANIM", b"ANMF"}
FLAG_ANIM, FLAG_XMP, FLAG_EXIF, FLAG_ALPHA, FLAG_ICC = 0x02, 0x04, 0x08, 0x10, 0x20


def own_files() -> list[Path]:
    found: set[Path] = set()
    for pattern in OWN:
        found.update(p for p in ROOT.glob(pattern) if p.is_file())
    return sorted(found)


def unlisted() -> list[str]:
    rel = {p.relative_to(ROOT).as_posix() for w in WATCHED for p in ROOT.glob(w) if p.is_file()}
    known = OWN + NOT_OWN
    return sorted(r for r in rel if not any(fnmatch.fnmatch(r, k) for k in known))


# ---- WebP ---------------------------------------------------------------------------------------
def riff_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError("not a WebP file")
    chunks, pos, end = [], 12, 8 + struct.unpack("<I", data[4:8])[0]
    while pos + 8 <= end:
        tag, size = data[pos : pos + 4], struct.unpack("<I", data[pos + 4 : pos + 8])[0]
        chunks.append((tag, data[pos + 8 : pos + 8 + size]))
        pos += 8 + size + (size & 1)
    return chunks


def riff_bytes(chunks: list[tuple[bytes, bytes]]) -> bytes:
    body = b"WEBP"
    for tag, payload in chunks:
        body += tag + struct.pack("<I", len(payload)) + payload + b"\0" * (len(payload) & 1)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def vp8x_for(chunks: list[tuple[bytes, bytes]], size: tuple[int, int]) -> bytes:
    flags = FLAG_XMP
    for tag, payload in chunks:
        if tag == b"VP8L" and payload[4] & 0x10:
            flags |= FLAG_ALPHA
        flags |= {b"ALPH": FLAG_ALPHA, b"EXIF": FLAG_EXIF, b"ICCP": FLAG_ICC}.get(tag, 0)
    return bytes([flags, 0, 0, 0]) + (size[0] - 1).to_bytes(3, "little") + (size[1] - 1).to_bytes(3, "little")


def pixels(data: bytes) -> tuple[tuple[int, int], str]:
    with Image.open(io.BytesIO(data)) as im:
        return im.size, hashlib.sha256(im.convert("RGBA").tobytes()).hexdigest()


def image_hash(chunks: list[tuple[bytes, bytes]]) -> str:
    return hashlib.sha256(b"".join(p for t, p in chunks if t in IMAGE_CHUNKS)).hexdigest()


def webp_stamped(path: Path) -> bool:
    return any(t == b"XMP " and p == XMP for t, p in riff_chunks(path.read_bytes()))


def stamp_webp(path: Path) -> None:
    old = path.read_bytes()
    chunks = riff_chunks(old)
    size, before = pixels(old)
    kept = [(t, p) for t, p in chunks if t != b"XMP "]
    if kept[0][0] == b"VP8X":
        head = bytearray(kept[0][1])
        head[0] |= FLAG_XMP
        kept[0] = (b"VP8X", bytes(head))
    else:
        kept.insert(0, (b"VP8X", vp8x_for(kept, size)))
    new = riff_bytes([*kept, (b"XMP ", XMP)])
    if pixels(new) != (size, before) or image_hash(riff_chunks(new)) != image_hash(chunks):
        raise RuntimeError(f"{path}: pixels changed, file left as it was")
    path.write_bytes(new)


# ---- MP4 ----------------------------------------------------------------------------------------
def mp4_tags(path: Path) -> dict[str, str]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format_tags", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    return json.loads(out).get("format", {}).get("tags", {})


def moov_first(path: Path) -> bool:
    with path.open("rb") as f:
        while head := f.read(8):
            size, tag = struct.unpack(">I", head[:4])[0], head[4:]
            if tag in (b"moov", b"mdat"):
                return tag == b"moov"
            if size == 1:
                size = struct.unpack(">Q", f.read(8))[0] - 8
            f.seek(size - 8, 1)
    return False


def stream_digests(path: Path) -> tuple[str, str]:
    """The stream's md5 and the per-packet list with timestamps, which also catches a shifted timeline."""
    base = ["ffmpeg", "-v", "error", "-i", str(path), "-map", "0", "-c", "copy"]
    md5 = subprocess.run([*base, "-f", "md5", "-"], check=True, capture_output=True, text=True).stdout.strip()
    packets = subprocess.run([*base, "-f", "framecrc", "-"], check=True, capture_output=True, text=True).stdout
    return md5, hashlib.sha256(packets.encode()).hexdigest()


def mp4_stamped(path: Path) -> bool:
    tags = mp4_tags(path)
    return tags.get("copyright") == COPYRIGHT and tags.get("artist") == CREATOR and moov_first(path)


def stamp_mp4(path: Path) -> None:
    with tempfile.TemporaryDirectory(dir=path.parent) as tmp:
        out = Path(tmp) / path.name
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(path), "-map", "0", "-c", "copy", "-map_metadata", "0",
             "-movflags", "+faststart", "-metadata", f"artist={CREATOR}", "-metadata", f"copyright={COPYRIGHT}",
             "-metadata", f"comment={SITE}", str(out)],
            check=True,
        )
        if stream_digests(out) != stream_digests(path):
            raise RuntimeError(f"{path}: stream changed, file left as it was")
        if not mp4_stamped(out):
            raise RuntimeError(f"{path}: tags or faststart missing, file left as it was")
        out.replace(path)


# ---- SVG ----------------------------------------------------------------------------------------
def svg_stamped(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return SVG_NOTE in text and stamp_svg_text(text.replace(SVG_NOTE, "")) == text


def stamp_svg_text(text: str) -> str:
    """Put the note before the </svg> of every top-level root; an include may hold a wide and a narrow one."""
    out, last, depth = [], 0, 0
    for m in re.finditer(r"<svg\b[^>]*?(/?)>|</svg>", text):
        if m.group(0) == "</svg>":
            depth -= 1
            if depth == 0:
                out += [text[last : m.start()], SVG_NOTE]
                last = m.start()
        elif not m.group(1):
            depth += 1
    return "".join(out) + text[last:]


def stamp_svg(path: Path) -> None:
    text = path.read_text(encoding="utf-8").replace(SVG_NOTE, "")
    new = stamp_svg_text(text)
    if new.replace(SVG_NOTE, "") != text:
        raise RuntimeError(f"{path}: drawing changed, file left as it was")
    path.write_text(new, encoding="utf-8")


KINDS = {".webp": (webp_stamped, stamp_webp), ".mp4": (mp4_stamped, stamp_mp4), ".svg": (svg_stamped, stamp_svg)}


def main() -> int:
    files = own_files()
    if "--list" in sys.argv:
        print("\n".join(p.relative_to(ROOT).as_posix() for p in files))
        return 0
    check = "--check" in sys.argv
    todo = [p for p in files if not KINDS[p.suffix][0](p)]
    for p in todo:
        if check:
            print("unstamped", p.relative_to(ROOT))
        else:
            KINDS[p.suffix][1](p)
            print("stamped", p.relative_to(ROOT))
    for r in unlisted():
        print("not listed, not stamped:", r)
    print(f"{len(files)} own files, {len(todo)} {'unstamped' if check else 'stamped now'}")
    return 1 if check and todo else 0


if __name__ == "__main__":
    sys.exit(main())
