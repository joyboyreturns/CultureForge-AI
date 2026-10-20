#!/usr/bin/env python3
"""Remux an MP4 so the moov atom precedes mdat ("faststart").

Why this matters for Safari: when `moov` sits at the end of the file, the
browser cannot know the track layout, duration, or codec until it has fetched
the tail of the file. Chromium starts playing once enough of `mdat` has
arrived; Safari does not - it waits for the metadata, so a 13 MB background
video shows a black frame for the whole download and often never starts.

Moving `moov` ahead of `mdat` is a container reordering: the encoded video and
audio bytes are copied verbatim, so there is no re-encoding and no quality
loss. It is the container-only equivalent of `ffmpeg -movflags +faststart` and
needs no ffmpeg install.

The subtlety that makes this more than a byte copy: the sample tables inside
`moov` store the absolute byte offsets of the media chunks (`stco`, or `co64`
for 64-bit files). Moving `mdat` shifts every one of those offsets, so the
script rewrites them in place. Without that step the file still parses but
every frame decodes as black - the metadata is fine, the sample data is
unreachable.

Usage:
    python3 scripts/fix_mp4_faststart.py <file.mp4> [--check]
"""
from __future__ import annotations

import argparse
import os
import shutil
import struct
import sys
import tempfile
from pathlib import Path

# Boxes that must stay ahead of mdat for the file to start playing promptly.
PREAMBLE_BOXES = {b"ftyp", b"moov", b"uuid", b"free", b"skip", b"wide", b"pnot"}
# Boxes that carry the media payload.
MEDIA_BOXES = {b"mdat"}


def _boxes(data: bytes, start: int, end: int) -> list[tuple[bytes, int, int, int]]:
    """Return (type, box_start, payload_start, size) for boxes in [start, end)."""
    found = []
    pos = start
    while pos + 8 <= end:
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        box_type = data[pos + 4:pos + 8]
        header = 8
        if size == 1:
            size = struct.unpack(">Q", data[pos + 8:pos + 16])[0]
            header = 16
        elif size == 0:
            size = end - pos
        if size < header:
            break
        found.append((box_type, pos, pos + header, size))
        pos += size
    return found


def _find(data: bytes, start: int, end: int, want: bytes):
    """Find a box by type; returns (payload_start, box_end) or None."""
    for box_type, box_start, payload_start, size in _boxes(data, start, end):
        if box_type == want:
            return (payload_start, box_start + size)
    return None


def _child(data: bytes, container: tuple, want: bytes):
    """Find `want` inside a container payload range."""
    if container is None:
        return None
    return _find(data, container[0], container[1], want)


def _path(data: bytes, start: int, end: int, names: list[bytes]):
    current = (start, end)
    for name in names:
        current = _child(data, current, name)
        if current is None:
            return None
    return current


def _stco_offsets(data: bytes, stco: tuple) -> list[int]:
    """Absolute file offsets listed in an stco box."""
    start = stco[0]
    count = struct.unpack(">I", data[start + 4:start + 8])[0]
    offsets = list(struct.unpack(f">{count}I", data[start + 8:start + 8 + count * 4]))
    return offsets


def _patch_stco(data: bytearray, stco: tuple, delta: int) -> int:
    start = stco[0]
    count = struct.unpack(">I", data[start + 4:start + 8])[0]
    values = struct.unpack(f">{count}I", bytes(data[start + 8:start + 8 + count * 4]))
    patched = [(value + delta) & 0xFFFFFFFF for value in values]
    data[start + 8:start + 8 + count * 4] = struct.pack(f">{count}I", *patched)
    return count


def _patch_co64(data: bytearray, co64: tuple, delta: int) -> int:
    start = co64[0]
    count = struct.unpack(">I", data[start + 4:start + 8])[0]
    values = struct.unpack(f">{count}Q", bytes(data[start + 8:start + 8 + count * 8]))
    patched = [value + delta for value in values]
    data[start + 8:start + 8 + count * 8] = struct.pack(f">{count}Q", *patched)
    return count


def analyze(data: bytes) -> dict:
    """Describe the top-level layout and locate the sample tables."""
    boxes = _boxes(data, 0, len(data))
    info = {
        "boxes": [(box_type.decode("latin1"), size, box_start) for box_type, box_start, _p, size in boxes],
        "moov": None,
        "mdat": None,
        "stco": None,
        "co64": None,
    }
    for box_type, box_start, payload_start, size in boxes:
        if box_type == b"moov":
            info["moov"] = (payload_start, box_start + size)
        elif box_type == b"mdat":
            info["mdat"] = (box_start, payload_start, box_start + size)
    if info["moov"]:
        traks = _boxes(data, info["moov"][0], info["moov"][1])
        for box_type, box_start, payload_start, size in traks:
            if box_type != b"trak":
                continue
            trak = (payload_start, box_start + size)
            stbl = _path(data, trak[0], trak[1], [b"mdia", b"minf", b"stbl"])
            if not stbl:
                continue
            stco = _child(data, stbl, b"stco")
            co64 = _child(data, stbl, b"co64")
            if stco:
                info["stco"] = stco
            elif co64:
                info["co64"] = co64
    return info


def is_faststart(info: dict) -> bool:
    if not info["moov"] or not info["mdat"]:
        return True
    return info["moov"][1] <= info["mdat"][0]


def remux(path: Path) -> bool:
    data = bytearray(path.read_bytes())
    info = analyze(bytes(data))
    if is_faststart(info):
        print(f"{path}: already faststart")
        return False
    if not info["moov"] or not info["mdat"]:
        print(f"{path}: missing moov or mdat; nothing to do", file=sys.stderr)
        return False

    boxes = _boxes(bytes(data), 0, len(data))
    preamble = [b for b in boxes if b[0] in PREAMBLE_BOXES]
    media = [b for b in boxes if b[0] in MEDIA_BOXES]
    other = [b for b in boxes if b[0] not in PREAMBLE_BOXES and b[0] not in MEDIA_BOXES]
    ordered = preamble + other + media

    # New position of the mdat payload versus the old one. The output layout
    # is the ordered boxes back to back, so mdat's payload starts at the sum of
    # the sizes of everything queued before it, plus its own header length.
    old_mdat_payload = info["mdat"][1]
    new_mdat_payload = old_mdat_payload
    written = 0
    for box_type, box_start, payload_start, size in ordered:
        if box_type == b"mdat":
            new_mdat_payload = written + (payload_start - box_start)
            break
        written += size
    delta = new_mdat_payload - old_mdat_payload

    patched = 0
    if info["stco"]:
        patched = _patch_stco(data, info["stco"], delta)
    elif info["co64"]:
        patched = _patch_co64(data, info["co64"], delta)

    out = bytearray()
    for box_type, box_start, payload_start, size in ordered:
        out += data[box_start:box_start + size]

    mode = path.stat().st_mode & 0o777
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False, suffix=".mp4") as tmp:
        tmp.write(bytes(out))
        tmp_path = Path(tmp.name)
    os.chmod(tmp_path, mode)
    shutil.move(str(tmp_path), str(path))

    print(
        f"{path}: faststart applied - moov moved ahead of mdat, "
        f"{patched} chunk offset(s) shifted by {delta:+d} bytes"
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", type=Path, help="the MP4 file to fix")
    parser.add_argument("--check", action="store_true", help="report status without rewriting")
    args = parser.parse_args()

    if not args.path.is_file():
        print(f"{args.path}: not a file", file=sys.stderr)
        return 1

    data = args.path.read_bytes()
    info = analyze(data)
    print(f"{args.path}: {len(data):,} bytes, top-level boxes:")
    for box_type, size, offset in info["boxes"]:
        print(f"  {box_type:6s} size={size:>12,} offset={offset:>12,}")

    if is_faststart(info):
        print("status: faststart OK (moov precedes mdat)")
        return 0
    print("status: NOT faststart - Safari waits for the whole file before it can play")
    if args.check:
        return 1
    remux(args.path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
