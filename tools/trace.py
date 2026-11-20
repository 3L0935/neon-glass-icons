"""Turn real app logos into Hairline Glass glyphs.

For each app: pick the symbol out of its logo (mode), vectorize it with
potrace, then emit an SVG path (24×24 box) that the preview fills/strokes with
the palette gradient inside a glass tile.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageFilter

HERE = Path(__file__).parent
OUT = HERE / "glyphs"
OUT.mkdir(exist_ok=True)

# app id -> (source png, mode, threshold)
APPS = {
    "zen":         ("src/zen-browser.png", "light", 150),
    "dolphin":     ("src/org.kde.dolphin.png", "dark", 150),
    "tauon":       ("src/com.github.taiko2k.tauonmb.png", "sat", 90),
    "steam":       ("cw/steam.png", "alpha", 128),
    "discord":     ("cw/com.discordapp.Discord.png", "alpha", 128),
    "obsidian":    ("src/obsidian.png", "facets-sat", 25),
    "zed":         ("src/zed.png", "light", 140),
    "kitty":       ("src/kitty.png", "alpha-light", 170),
    "settings":    ("cw/preferences-system.png", "alpha", 128),
    "discover":    ("cw/plasmadiscover.png", "alpha", 128),
    "heroic":      ("src/com.heroicgameslauncher.hgl.png", "sat", 90),
    "protonplus":  ("src/com.vysp3r.ProtonPlus.png", "sat", 90),
    "mango":       ("src/mango-glyph.png", "alpha", 128),
    "lsfg":        ("src/gay.pancake.lsfg-vk-ui.png", "facets", 128),
    "btop":        ("src/btop.png", "alpha", 128),
    "easyeffects": ("src/easyeffects-glyph.png", "alpha", 128),
    "kdeconnect":  ("cw/kdeconnect.png", "alpha", 128),
    "spectacle":   ("cw/spectacle.png", "alpha", 128),
    "kate":        ("src/kate.png", "light", 150),
    "haruna":      ("src/haruna.png", "light", 170),
    "cachy":       ("src/org.cachyos.hello.png", "sat", 90),
    "partition":   ("cw/partitionmanager.png", "alpha", 128),
}


def mask_of(img, mode, thr):
    if mode.startswith("facets"):
        base = mask_of(img, "sat" if mode == "facets-sat" else "alpha", thr)
        rgb = img.convert("RGBA").resize((256, 256), Image.LANCZOS).convert("RGB")
        q = rgb.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
        qp, bp = q.load(), base.load()
        cut = Image.new("L", base.size, 0)
        cp = cut.load()
        for y in range(1, 255):
            for x in range(1, 255):
                if bp[x, y] and (qp[x, y] != qp[x + 1, y] or qp[x, y] != qp[x, y + 1]):
                    cp[x, y] = 255
        cut = cut.filter(ImageFilter.MaxFilter(5))
        return Image.composite(Image.new("L", base.size, 0), base, cut)
    img = img.convert("RGBA").resize((256, 256), Image.LANCZOS)
    px = img.load()
    m = Image.new("L", img.size, 0)
    mp = m.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a < 128:
                continue
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            mx, mn = max(r, g, b), min(r, g, b)
            sat = 0 if mx == 0 else (mx - mn) * 255 / mx
            on = {"alpha": True, "alpha-light": lum < thr, "light": lum >= thr, "dark": lum < thr, "sat": sat >= thr and mx > 60}[mode]
            if on:
                mp[x, y] = 255
    # close pinholes, drop specks
    m = m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    return m


def trace(mask, name):
    pbm = OUT / f"{name}.pbm"
    # potrace: black = foreground
    Image.eval(mask, lambda v: 0 if v > 127 else 255).convert("1").save(pbm)
    svg = OUT / f"{name}.svg"
    subprocess.run(["potrace", str(pbm), "-s", "--flat", "-t", "12", "-a", "1.1", "-O", "0.4",
                    "-W", "256pt", "-H", "256pt", "-o", str(svg)], check=True)
    text = svg.read_text()
    paths = re.findall(r'<path d="([^"]+)"', text, re.S)
    tf = re.search(r'<g transform="([^"]+)"', text).group(1)
    bbox = mask.getbbox()
    return {"d": " ".join(p.replace("\n", " ") for p in paths), "transform": tf, "bbox": bbox}


FOLDERS = ["desktop", "development", "documents", "download", "games", "github", "git", "home",
           "music", "pictures", "publicshare", "steam", "templates", "videos", "recent", "network"]


def main():
    out = {}
    for t, (src, mode) in {"t-bell": ("tray/bell.png", "alpha"), "t-update": ("tray/update.png", "alpha"),
                           "t-check": ("tray/check.png", "alpha"), "t-gsr": ("tray/gsr-idle.png", "facets")}.items():
        APPS[t] = (src, mode, 128)
    for f in FOLDERS:
        APPS["f-" + f] = (f"fold/folder-{f}.png", "alpha", 128)
    for name, (src, mode, thr) in APPS.items():
        img = Image.open(HERE / src)
        m = mask_of(img, mode, thr)
        if not m.getbbox():
            print("EMPTY", name)
            continue
        m.save(OUT / f"{name}-mask.png")
        out[name] = trace(m, name)
        print("ok", name, out[name]["bbox"])
    (HERE / "glyphs.json").write_text(json.dumps(out))


main()
