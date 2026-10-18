"""Build a multi-size Windows .ico from the server favicon (or assets/app_src.ico)."""
from __future__ import annotations

import struct
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC_CANDIDATES = (
    ROOT / "assets" / "app_src.ico",
    Path(
        r"D:\JoseCarlos\Programacion\Python\Cursor\Remote-Task-Manager"
        r"\serverbot\static\images\icons\favicon.ico"
    ),
)
OUT = ROOT / "assets" / "app.ico"
SIZES = (16, 32, 48, 64, 128, 256)


def _png_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def write_ico(images: list[Image.Image], dest: Path) -> None:
    """Write ICO with PNG-compressed images (Vista+), one entry per size."""
    payloads = [_png_bytes(im.convert("RGBA")) for im in images]
    count = len(payloads)
    offset = 6 + 16 * count
    header = struct.pack("<HHH", 0, 1, count)
    entries = []
    for im, data in zip(images, payloads):
        w = 0 if im.width >= 256 else im.width
        h = 0 if im.height >= 256 else im.height
        entries.append(struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(header + b"".join(entries) + b"".join(payloads))


def main() -> None:
    src = next((p for p in SRC_CANDIDATES if p.is_file()), None)
    if src is None:
        raise SystemExit("No source favicon found")
    base = Image.open(src).convert("RGBA")
    if base.size != (256, 256):
        base = base.resize((256, 256), Image.Resampling.LANCZOS)
    images = [base.resize((s, s), Image.Resampling.LANCZOS) for s in SIZES]
    write_ico(images, OUT)
    data = OUT.read_bytes()
    n = struct.unpack_from("<H", data, 4)[0]
    print(f"wrote {OUT} bytes={OUT.stat().st_size} entries={n}")
    off = 6
    for i in range(n):
        w, h, _c, _r, _p, bpp, size, _o = struct.unpack_from("<BBBBHHII", data, off)
        print(f"  [{i}] {w or 256}x{h or 256} bpp={bpp} size={size}")
        off += 16


if __name__ == "__main__":
    main()
