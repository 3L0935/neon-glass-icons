#!/usr/bin/env python3
"""Re-trace System Settings' module icons into kcm.json.

The icon names come from the System Settings modules installed here. Each is
resolved like Plasma would (Papirus-Dark → Papirus → breeze-dark → breeze →
hicolor), its symbol is pulled out of its colored background, and build.py
puts it on a glass tile in the gradient matching its original hue.

  tools/trace_kcm.py   → kcm.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from PIL import Image, ImageFilter  # noqa: E402
from trace_mime import area, family, masks, render, trace  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
THEMES = ["Papirus-Dark", "Papirus", "breeze-dark", "breeze", "hicolor"]
# modules that don't declare their icon in their plugin metadata
EXTRA = {"kwalletmanager", "kwalletmanager2"}
SKIP = {"preferences-system", "system-file-manager"}   # already drawn as apps (Settings, Dolphin)
# drawn as several flat shapes (panels, screens, windows): keep the silhouette, not one inner shape
OBJECTS = {"preferences-desktop-activities", "preferences-desktop-display", "preferences-desktop-plasma-theme",
           "preferences-system-windows", "preferences-desktop-tablet"}
# originals too plain to trace well: hand-drawn masks instead
DRAWN = {"smartphone": "sources/drawn/smartphone.png", "preferences-system-network-connection": "sources/drawn/ethernet.png"}


def module_icons() -> list[str]:
    script = r'''for f in /usr/lib/qt6/plugins/plasma/kcms/systemsettings/*.so /usr/lib/qt6/plugins/plasma/kcms/systemsettings_qwidgets/*.so; do
      strings "$f" | grep -o '"Icon": *"[^"]*"' | head -1; done
    grep -h "^Icon=" /usr/share/applications/kcm_*.desktop /usr/share/systemsettings/categories/*.desktop 2>/dev/null | sed "s/Icon=/\"Icon\": \"/;s/$/\"/"'''
    out = subprocess.run(["bash", "-c", script], capture_output=True, text=True).stdout
    names = {line.split('"')[3] for line in out.splitlines() if line.count('"') >= 4}
    names |= EXTRA
    return sorted(n for n in names if n and n not in SKIP)


def resolve(name: str) -> Path | None:
    """The full-color file Plasma shows for `name` today (biggest non-symbolic one)."""
    for theme in THEMES:
        base = Path("/usr/share/icons") / theme
        hits = [p for p in base.glob(f"*/*/{name}.svg") if "symbolic" not in p.parts[-2]] + \
               [p for p in base.glob(f"*/*/*/{name}.svg")]
        hits = [p for p in hits if p.exists()]
        if hits:
            def size(p):
                for part in p.parts:
                    head = part.split("x")[0].split("@")[0]
                    if head.isdigit():
                        return int(head)
                return 999 if "scalable" in p.parts else 0
            return max(hits, key=size).resolve()
    return None


def object_mask(img):
    """No background plate (a bell, a screen, a padlock): the whole silhouette,
    with thin cuts where clearly different colors meet so inner details show."""
    px = img.load()
    W, H = img.size
    alpha = img.getchannel("A").point(lambda a: 255 if a > 160 else 0)
    cut = Image.new("L", img.size, 0)
    cp = cut.load()
    def far(p, q):
        return p[3] > 200 and q[3] > 200 and abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) > 120
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if far(px[x, y], px[x + 1, y]) or far(px[x, y], px[x, y + 1]):
                cp[x, y] = 255
    m = Image.composite(Image.new("L", img.size, 0), alpha, cut.filter(ImageFilter.MaxFilter(5)))
    return m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))


def has_plate(img) -> bool:
    """A round or square colored background behind a symbol."""
    alpha = img.getchannel("A").point(lambda a: 255 if a > 200 else 0)
    x0, y0, x1, y1 = alpha.getbbox()
    w, h = x1 - x0, y1 - y0
    return 0.85 < w / h < 1.18 and area(alpha.crop((x0, y0, x1, y1))) / (w * h) > 0.74


def main():
    glyphs, missing = {}, []
    for name in module_icons():
        src = resolve(name)
        if not src:
            missing.append(name)
            continue
        img = render(src)
        sym, bg = masks(img, whole_shape=False, fold=False)
        if name in DRAWN:
            drawn = Image.open(ROOT / DRAWN[name]).convert("RGBA").getchannel("A").point(lambda v: 255 if v > 127 else 0)
            g = trace(drawn)
            g["family"], g["source"] = family(bg), DRAWN[name]
            glyphs[name] = g
            continue
        alpha_area = area(img.getchannel("A").point(lambda v: 255 if v > 200 else 0))
        if name in OBJECTS or not has_plate(img) or area(sym) < alpha_area * 0.08:   # no plate, or the "symbol" is a sliver
            sym = object_mask(img)
        g = trace(sym)
        if not g:
            missing.append(name)
            continue
        g["family"] = family(bg)
        g["source"] = str(src)
        glyphs[name] = g
    (ROOT / "kcm.json").write_text(json.dumps(glyphs))
    print(f"{len(glyphs)} module icons traced; not found: {', '.join(missing) or 'none'}")


if __name__ == "__main__":
    main()
