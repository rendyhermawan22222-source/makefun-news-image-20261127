#!/usr/bin/env python3
"""Friday 27 November 2026 in one picture: the graded program.

The make.fun grader runs this file with Python 3.13 and the standard library
only (nothing is installed), so it cannot draw with Pillow. The front page is
drawn by render.py (Pillow, run locally) into entry.png, which is committed
next to this file. This program checks that entry.png is a complete PNG and
writes it, byte for byte, to $MAKEFUN_OUTPUT_DIR/entry.png.
"""
import hashlib
import os
import sys
import zlib

HERE = os.environ.get("MAKEFUN_BOT_DIR") or os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "output")
OUT = os.path.join(OUT_DIR, "entry.png")
SIG = b"\x89PNG\r\n\x1a\n"


def check_png(data):
    """Walk every chunk and verify its CRC, ending at IEND."""
    if data[:8] != SIG:
        raise ValueError("entry.png is not a PNG")
    pos, seen_iend = 8, False
    while pos < len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        crc = int.from_bytes(data[pos + 8 + length:pos + 12 + length], "big")
        if len(body) != length or zlib.crc32(ctype + body) & 0xFFFFFFFF != crc:
            raise ValueError("bad PNG chunk %r" % ctype)
        pos += 12 + length
        if ctype == b"IEND":
            seen_iend = True
            break
    if not seen_iend or pos != len(data):
        raise ValueError("PNG does not end cleanly at IEND")


def main():
    with open(SRC, "rb") as f:
        data = f.read()
    check_png(data)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(data)
    print("wrote %s  %d bytes  sha256=%s"
          % (OUT, len(data), hashlib.sha256(data).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
