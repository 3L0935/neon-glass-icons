#!/usr/bin/env python3
"""Render screenshots/showcase.png from a built theme: tools/showcase.py THEME_DIR"""
import io
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

P = Path(sys.argv[1]) / "scalable"
OUT = Path(__file__).resolve().parent.parent / "screenshots/showcase.png"
ROWS = [
    ("apps", ["apps/zen-browser", "apps/firefox", "apps/google-chrome", "apps/brave-browser", "apps/steam", "apps/com.discordapp.Discord",
              "apps/obsidian", "apps/zed", "apps/kitty", "apps/org.kde.dolphin", "apps/com.github.taiko2k.tauonmb", "apps/com.heroicgameslauncher.hgl"]),
    ("settings", ["apps/preferences-desktop-mouse", "apps/preferences-desktop-keyboard", "apps/preferences-system-bluetooth",
                  "apps/preferences-desktop-notification-bell", "apps/preferences-security", "apps/preferences-desktop-gaming",
                  "apps/preferences-system-time", "apps/preferences-desktop-wallpaper", "apps/preferences-online-accounts",
                  "apps/preferences-system-users", "apps/user-trash", "apps/preferences-system-power-management"]),
    ("folders", ["places/folder", "places/folder-cyan-home", "places/folder-violet-music", "places/folder-pink-pictures", "places/folder-mint-download",
                 "places/folder-lagoon-github", "places/folder-dusk-games", "places/folder-aurora-steam", "places/folder-lagoon-development",
                 "places/folder-cyan-videos", "places/document-open-recent", "places/folder-network"]),
    ("files", ["mimetypes/audio-mpeg", "mimetypes/image-png", "mimetypes/video-mp4", "mimetypes/application-pdf", "mimetypes/text-x-python",
               "mimetypes/application-json", "mimetypes/text-x-script", "mimetypes/application-zip", "mimetypes/text-markdown",
               "mimetypes/text-html", "mimetypes/font-ttf", "mimetypes/text-plain"]),
]


def icon(rel, size):
    png = subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), str(P / f"{rel}.svg")], capture_output=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGBA") if png else None


def font(name, size):
    try:
        return ImageFont.truetype(f"/usr/share/fonts/TTF/{name}", size)
    except OSError:
        return ImageFont.load_default()


W, pad, cell, size = 1200, 40, 92, 72
H = pad * 2 + len(ROWS) * (cell + 34) + 70
im = Image.new("RGBA", (W, H), (13, 11, 31, 255))
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
for r in range(420, 0, -6):   # soft neon glow from the bottom, like the wallpaper
    gd.ellipse((W / 2 - r * 2, H - r * 0.6, W / 2 + r * 2, H + r * 0.9), fill=(70, 120, 231, int(40 * (1 - r / 420))))
im = Image.alpha_composite(im, glow)
d = ImageDraw.Draw(im)
d.text((pad, pad - 6), "NeonGlass", font=font("JetBrainsMonoNerdFont-Bold.ttf", 34), fill=(232, 230, 255))
small = font("JetBrainsMonoNerdFont-Regular.ttf", 15)
d.text((pad + 210, pad + 8), "glass tiles · neon gradient glyphs · KDE Plasma icon theme", font=small, fill=(154, 148, 208))
y = pad + 62
for label, items in ROWS:
    d.text((pad, y), label.upper(), font=small, fill=(93, 87, 154))
    for i, rel in enumerate(items):
        ic = icon(rel, size)
        if ic:
            im.alpha_composite(ic, (pad + i * cell + (cell - size) // 2, y + 22))
        else:
            print("missing", rel)
    y += cell + 34
OUT.parent.mkdir(exist_ok=True)
im.convert("RGB").save(OUT)
print("wrote", OUT)
