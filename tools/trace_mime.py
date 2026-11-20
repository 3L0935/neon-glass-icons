#!/usr/bin/env python3
"""Vectorize the symbols of Papirus' file-type icons into mime.json.

For each unique Papirus mimetype icon: find the page color, keep the pixels
that contrast with it (the symbol), cut thin gaps between differently colored
parts (two-tone logos stay readable), trace with potrace. Icons that are not a
page (a gear, a tile) keep their whole silhouette minus the inner symbol.
The page hue picks the gradient family, so audio, images, code… stay apart.

  tools/trace_mime.py            → mime.json (glyphs + alias map)
"""
from __future__ import annotations

import colorsys
import io
import json
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = Path("/usr/share/icons/Papirus/64x64/mimetypes")
SIZE = 256


def render(svg: Path) -> Image.Image:
    png = subprocess.run(["rsvg-convert", "-w", str(SIZE), "-h", str(SIZE), str(svg)],
                         capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGBA")


def family(rgb) -> str:
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    if s < 0.18 or l > 0.85 or l < 0.12:
        return "text"
    deg = h * 360
    if deg < 75 or deg >= 335:
        return "warm"
    if deg < 190:
        return "green"
    if deg < 255:
        return "blue"
    return "purple"


def area(m: Image.Image) -> int:
    return sum(1 for v in m.get_flattened_data() if v) if hasattr(m, "get_flattened_data") else sum(1 for v in m.getdata() if v)


def masks(img: Image.Image, whole_shape: bool = True, fold: bool = True):
    px = img.load()
    alpha = img.getchannel("A").point(lambda a: 255 if a > 200 else 0)
    bbox = alpha.getbbox()
    cols = Counter(px[x, y][:3] for y in range(SIZE) for x in range(SIZE) if px[x, y][3] > 200)
    page = cols.most_common(1)[0][0]
    sym = Image.new("L", img.size, 0)
    sp = sym.load()
    for y in range(SIZE):
        for x in range(SIZE):
            r, g, b, a = px[x, y]
            if a > 200 and abs(r - page[0]) + abs(g - page[1]) + abs(b - page[2]) > 90:
                sp[x, y] = 255
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    is_page = w < h * 0.9
    if is_page and fold:   # drop the folded corner (top right of the page)
        for y in range(bbox[1], bbox[1] + int(h * 0.38)):
            for x in range(bbox[0] + int(w * 0.55), bbox[2] + 1):
                sp[x, y] = 0
    # clean specks, unless that eats a thin-stroked symbol (PDF, fonts…)
    cleaned = sym.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    if area(cleaned) > area(sym) * 0.7:
        sym = cleaned
    # thin cuts between clearly different colors inside the symbol (two-tone logos)
    sp = sym.load()
    cut = Image.new("L", img.size, 0)
    cp = cut.load()
    def core(p):   # a solid symbol pixel, not an anti-aliased edge blending into the page
        return p[3] > 200 and abs(p[0] - page[0]) + abs(p[1] - page[1]) + abs(p[2] - page[2]) > 200

    def far(p, q):
        return core(p) and core(q) and abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) > 150
    for y in range(1, SIZE - 1):
        for x in range(1, SIZE - 1):
            if sp[x, y] and (far(px[x, y], px[x + 1, y]) and sp[x + 1, y] or far(px[x, y], px[x, y + 1]) and sp[x, y + 1]):
                cp[x, y] = 255
    if area(cut) > 20:
        sym = Image.composite(Image.new("L", img.size, 0), sym, cut.filter(ImageFilter.MaxFilter(3)))
    # thin-stroked symbols (PDF swirl, font glyphs, zipper…) get thickened to stay readable
    if area(sym) and area(sym.filter(ImageFilter.MinFilter(7))) < area(sym) * 0.25:
        sym = sym.filter(ImageFilter.MaxFilter(5))
    # not a page and a lumpy outline (gear…): the shape itself is the symbol
    coverage = area(alpha.crop(bbox)) / max(1, w * h)
    if whole_shape and not is_page and coverage < 0.8:
        sym = Image.composite(Image.new("L", img.size, 0), alpha, sym)
    return sym, page


def trace(mask: Image.Image):
    if not mask.getbbox():
        return None
    with tempfile.TemporaryDirectory() as d:
        pbm, svg = Path(d) / "m.pbm", Path(d) / "m.svg"
        Image.eval(mask, lambda v: 0 if v > 127 else 255).convert("1").save(pbm)
        subprocess.run(["potrace", str(pbm), "-s", "--flat", "-t", "10", "-a", "1.1", "-O", "0.4",
                        "-W", f"{SIZE}pt", "-H", f"{SIZE}pt", "-o", str(svg)], check=True)
        text = svg.read_text()
    paths = re.findall(r'<path d="([^"]+)"', text, re.S)
    tf = re.search(r'<g transform="([^"]+)"', text).group(1)
    return {"d": " ".join(p.replace("\n", " ") for p in paths), "transform": tf, "bbox": mask.getbbox()}


def main():
    glyphs, aliases = {}, {}
    outside = {}   # resolved file outside the mimetypes dir -> first name traced for it
    for f in sorted(SRC.iterdir()):
        if f.suffix != ".svg":
            continue
        if f.is_symlink():
            real = f.resolve()
            if real.parent == SRC.resolve():
                aliases[f.stem] = Path(f.readlink()).stem
                continue
            if real in outside:   # e.g. application-zip → ../apps/ark.svg, already traced
                aliases[f.stem] = outside[real]
                continue
            outside[real] = f.stem
            f = real
            name = next(k for k, v in outside.items() if k == real) and outside[real]
        else:
            name = f.stem
        img = render(f)
        sym, page = masks(img)
        g = trace(sym)
        if g:
            g["family"] = family(page)
            glyphs[name] = g
    # aliases whose target was not traced are dropped (Papirus-Dark keeps them)
    aliases = {a: t for a, t in aliases.items() if t in glyphs}
    (ROOT / "mime.json").write_text(json.dumps({"glyphs": glyphs, "aliases": aliases}))
    fams = Counter(g["family"] for g in glyphs.values())
    print(f"{len(glyphs)} glyphs, {len(aliases)} aliases · {dict(fams)}")


if __name__ == "__main__":
    main()
