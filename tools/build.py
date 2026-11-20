#!/usr/bin/env python3
"""Build the NeonGlass icon theme from glyphs.json.

  tools/build.py [--folders lagoon] [--out NeonGlass]

- apps:    glass tile + gradient-filled logo glyph (one gradient per family)
- places:  glass folders, 14 symbols × 7 colors (folder-<color>-<type>), the
           default color also as plain names (folder-music, user-home…)
- panel:   tray icons, plain lavender glyph + a colored state dot; every other
           tray icon is Papirus' panel set recolored to the palette
Everything not drawn here is inherited from Papirus-Dark.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLYPHS = json.loads((ROOT / "glyphs.json").read_text())
# personal icons (self-hosted web apps…) live in an untracked personal.json:
# {"glyphs": {name: glyph}, "apps": {name: [family, [icon names]]}}
PERSONAL_DATA = json.loads((ROOT / "personal.json").read_text()) if (ROOT / "personal.json").exists() else {}
GLYPHS.update(PERSONAL_DATA.get("glyphs", {}))
BROWSERS = json.loads((ROOT / "browsers.json").read_text()) if (ROOT / "browsers.json").exists() else {}
KCM = json.loads((ROOT / "kcm.json").read_text()) if (ROOT / "kcm.json").exists() else {}
MIME = json.loads((ROOT / "mime.json").read_text()) if (ROOT / "mime.json").exists() else {"glyphs": {}, "aliases": {}}
# file-type families (from the Papirus page hue) → gradient
MIME_FAMILIES = {"text": ("#6cc8f2", "#a55ae9"), "warm": ("#e45ad8", "#a55ae9"), "green": ("#8af0c0", "#46b5e7"),
                 "blue": ("#46b5e7", "#a55ae9"), "purple": ("#a55ae9", "#e45ad8")}

PALETTE = {"cyan": "#46b5e7", "violet": "#a55ae9", "pink": "#e45ad8", "mint": "#8af0c0",
           "text": "#d6d3f5", "tile": "#171339", "folder": "#1d1846", "bg": "#0d0b1f", "red": "#ff6ba8", "yellow": "#ffe08a"}
FAMILIES = {"sys": ("#46b5e7", "#a55ae9"), "media": ("#a55ae9", "#e45ad8"), "game": ("#e45ad8", "#46b5e7")}
PAPIRUS = Path("/usr/share/icons/Papirus")
TRAY_GRADIENT = ("#46b5e7", "#a55ae9")   # tray icons: cyan → violet, like the app glyphs
# Papirus' symbolic color classes → palette
RECOLOR = {"color:#dfdfdf": "color:#d6d3f5", "fill:#dfdfdf": "fill:#d6d3f5", "color:#4285f4": "color:#46b5e7",
           "color:#4caf50": "color:#8af0c0", "color:#ff9800": "color:#ffe08a", "color:#f44336": "color:#ff6ba8"}
FOLDER_COLORS = {"cyan": ("#46b5e7", "#6cc8f2"), "violet": ("#a55ae9", "#c08af5"), "pink": ("#e45ad8", "#ff8fbd"),
                 "mint": ("#8af0c0", "#46b5e7"), "lagoon": ("#46b5e7", "#a55ae9"), "dusk": ("#a55ae9", "#e45ad8"),
                 "aurora": ("#e45ad8", "#46b5e7")}

# glyph -> (family, icon names it provides)
APPS = {
    "zen":         ("media", ["zen-browser", "zen", "app.zen_browser.zen"]),
    "dolphin":     ("sys",   ["org.kde.dolphin", "system-file-manager"]),
    "tauon":       ("media", ["com.github.taiko2k.tauonmb", "tauonmb"]),
    "steam":       ("game",  ["steam", "com.valvesoftware.Steam"]),
    "discord":     ("media", ["com.discordapp.Discord", "discord"]),
    "obsidian":    ("sys",   ["obsidian", "md.obsidian.Obsidian"]),
    "zed":         ("sys",   ["zed", "dev.zed.Zed"]),
    "kitty":       ("sys",   ["kitty"]),
    "settings":    ("sys",   ["preferences-system", "systemsettings", "org.kde.systemsettings"]),
    "discover":    ("sys",   ["plasmadiscover", "org.kde.discover"]),
    "heroic":      ("game",  ["com.heroicgameslauncher.hgl", "heroic"]),
    "protonplus":  ("game",  ["com.vysp3r.ProtonPlus"]),
    "mango":       ("game",  ["io.github.radiolamp.mangojuice"]),
    "lsfg":        ("game",  ["gay.pancake.lsfg-vk-ui"]),
    "btop":        ("sys",   ["btop"]),
    "easyeffects": ("media", ["com.github.wwmm.easyeffects", "easyeffects"]),
    "kdeconnect":  ("sys",   ["kdeconnect", "org.kde.kdeconnect.app"]),
    "spectacle":   ("media", ["spectacle", "org.kde.spectacle"]),
    "kate":        ("sys",   ["kate", "org.kde.kate"]),
    "haruna":      ("media", ["haruna", "org.kde.haruna"]),
    "cachy":       ("sys",   ["org.cachyos.hello", "cachyos-hello"]),
    "partition":   ("sys",   ["partitionmanager", "org.kde.partitionmanager"]),
}
# personal apps: left out of the public build
APPS.update({k: (v[0], v[1]) for k, v in PERSONAL_DATA.get("apps", {}).items()})
PERSONAL = set(PERSONAL_DATA.get("apps", {}))
# apps whose small sizes (16/22 px: tray, small menus) are a plain glyph, not a tile
MINI_APPS = ["easyeffects"]

# folder symbol -> names of the default-color icon
FOLDERS = {
    "":            ["folder", "inode-directory", "folder-blue"],
    "home":        ["user-home", "folder-home", "folder_home"],
    "desktop":     ["user-desktop", "folder-desktop"],
    "documents":   ["folder-documents", "folder-document"],
    "download":    ["folder-download", "folder-downloads"],
    "music":       ["folder-music", "folder-sound"],
    "pictures":    ["folder-pictures", "folder-picture", "folder-images"],
    "videos":      ["folder-videos", "folder-video"],
    "development": ["folder-development", "folder-code", "folder-projects"],
    "git":         ["folder-git"],
    "github":      ["folder-github"],
    "games":       ["folder-games"],
    "steam":       ["folder-steam"],
    "publicshare": ["folder-publicshare", "folder-public"],
    "recent":      ["document-open-recent", "folder-open-recent", "folder-recent"],
    "network":     ["folder-network", "folder-remote", "network-workgroup"],
}
# tray glyph, state dot -> names
PANEL = {
    ("steam", ""):          ["steam_tray_mono"],
    ("t-check", ""):        ["update-none"],
    ("t-update", "pink"):   ["update-low", "update-medium", "update-high"],
    ("t-bell", ""):         ["notification-inactive", "notifications"],
    ("t-bell", "cyan"):     ["notification-active", "notification-new"],
    ("t-bell", "slash"):    ["notification-disabled", "notifications-disabled"],
    ("t-gsr", ""):          ["com.dec05eba.gpu_screen_recorder.tray-idle"],
    ("t-gsr", "red"):       ["com.dec05eba.gpu_screen_recorder.tray-recording"],
    ("t-gsr", "yellow"):    ["com.dec05eba.gpu_screen_recorder.tray-paused"],
}


def glyph(name, box: float, cx: float, cy: float, paint: str) -> str:
    """The traced glyph (a name in glyphs.json, or a glyph dict), fitted in a `box`-wide square centered on (cx, cy)."""
    g = GLYPHS[name] if isinstance(name, str) else name
    x0, y0, x1, y1 = g["bbox"]
    k = box / max(x1 - x0, y1 - y0)
    return (f'<g transform="translate({cx} {cy}) scale({k:.5f}) translate({-(x0 + x1) / 2} {-(y0 + y1) / 2})">'
            f'<g transform="{g["transform"]}"><path d="{g["d"]}" {paint} fill-rule="evenodd"/></g></g>')


def grads(a: str, b: str) -> str:
    return (f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}"/>'
            f'<stop offset="1" stop-color="{b}"/></linearGradient>'
            f'<linearGradient id="e" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}" stop-opacity=".55"/>'
            f'<stop offset="1" stop-color="{b}" stop-opacity=".18"/></linearGradient></defs>')


def svg(body: str) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">{body}</svg>\n'


def app_icon(name, fam: str) -> str:
    a, b = FAMILIES[fam] if fam in FAMILIES else MIME_FAMILIES[fam]
    return svg(grads(a, b)
               + f'<rect x="1" y="1" width="22" height="22" rx="6" fill="{PALETTE["tile"]}" fill-opacity=".92" stroke="url(#e)" stroke-width=".5"/>'
               + '<path d="M3 7.5C3 4.5 4.5 3 7.5 3h9C19.5 3 21 4.5 21 7.5" fill="none" stroke="#fff" stroke-opacity=".07" stroke-width=".6"/>'
               + glyph(name, 14, 12, 12, 'fill="url(#g)"'))


def mini_icon(name: str, dot: str = "") -> str:
    badge = ""
    if dot == "slash":
        badge = (f'<path d="M4 20 20 4" stroke="{PALETTE["bg"]}" stroke-width="3.2" stroke-linecap="round"/>'
                 f'<path d="M4 20 20 4" stroke="{PALETTE["red"]}" stroke-width="1.6" stroke-linecap="round"/>')
    elif dot:
        badge = f'<circle cx="19" cy="5" r="4" fill="{PALETTE["bg"]}"/><circle cx="19" cy="5" r="2.8" fill="{PALETTE[dot]}"/>'
    a, b = TRAY_GRADIENT
    return svg(f'<defs><linearGradient id="t" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">'
               f'<stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient></defs>'
               + glyph(name, 17, 12, 12, 'fill="url(#t)"') + badge)


def folder_icon(sym: str, a: str, b: str) -> str:
    inner = (glyph("f-" + sym, 9.2, 12, 14.5, 'fill="url(#g)"') if sym
             else '<path d="M6 17.6h12" stroke="url(#g)" stroke-width="1.1" stroke-linecap="round"/>')
    return svg(f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>'
               f'<linearGradient id="e" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}" stop-opacity=".85"/><stop offset="1" stop-color="{b}" stop-opacity=".35"/></linearGradient></defs>'
               f'<path d="M2.5 6.5A1.5 1.5 0 0 1 4 5h5.2l2 2H20a1.5 1.5 0 0 1 1.5 1.5V10h-19z" fill="{PALETTE["tile"]}" stroke="url(#e)" stroke-width=".5"/>'
               f'<rect x="2.5" y="8.6" width="19" height="11.6" rx="2" fill="{PALETTE["folder"]}" fill-opacity=".96" stroke="url(#e)" stroke-width=".6"/>'
               '<path d="M4.5 9.4h15" stroke="#fff" stroke-opacity=".08" stroke-width=".5"/>' + inner)


def gradient_panel(t: str, size: int) -> str:
    """Recolor a Papirus panel SVG: state colors to the palette, and the
    parts drawn in the text color (class ColorScheme-Text) to the tray gradient."""
    for old, new in RECOLOR.items():
        t = t.replace(old, new)
    a, b = TRAY_GRADIENT
    grad = (f'<linearGradient id="ngTray" x1="0" y1="0" x2="{size}" y2="{size}" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>')
    t = re.sub(r'<[^<>]*class="ColorScheme-Text"[^<>]*>',
               lambda m: m.group(0).replace("fill:currentColor", "fill:url(#ngTray)")
                                   .replace("stroke:currentColor", "stroke:url(#ngTray)"), t)
    if "url(#ngTray)" in t:
        t = t.replace("<defs>", "<defs>" + grad, 1) if "<defs>" in t else re.sub(r"(<svg[^>]*>)", r"\1<defs>" + grad + "</defs>", t, count=1)
    return t


def mime_icon(g: dict) -> str:
    """A glass page with a folded corner, the file-type symbol in its family gradient."""
    a, b = MIME_FAMILIES[g["family"]]
    x0, y0, x1, y1 = g["bbox"]
    k = 9.6 / max(x1 - x0, y1 - y0)
    sym = (f'<g transform="translate(12 14.6) scale({k:.5f}) translate({-(x0 + x1) / 2} {-(y0 + y1) / 2})">'
           f'<g transform="{g["transform"]}"><path d="{g["d"]}" fill="url(#g)" fill-rule="evenodd"/></g></g>')
    return svg(grads(a, b)
               + f'<path d="M6 2.5h8.2L19 7.3v13.2a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-17a1 1 0 0 1 1-1z" fill="{PALETTE["tile"]}" fill-opacity=".94" stroke="url(#e)" stroke-width=".55"/>'
               + '<path d="M14.2 2.5v3.8a1 1 0 0 0 1 1H19z" fill="url(#g)" fill-opacity=".45"/>'
               + '<path d="M6.5 3.4h6.8" stroke="#fff" stroke-opacity=".08" stroke-width=".5"/>'
               + sym)


def write(path: Path, text: str, aliases=()):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    for alias in aliases:
        link = path.with_name(alias + ".svg")
        if link != path:
            link.unlink(missing_ok=True)
            link.symlink_to(path.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folders", default="lagoon", choices=FOLDER_COLORS, help="default folder color")
    ap.add_argument("--out", type=Path, default=ROOT / "NeonGlass")
    ap.add_argument("--public", action="store_true", help="leave out personal icons (for releases)")
    a = ap.parse_args()
    out = a.out
    if out.exists():
        shutil.rmtree(out)

    for name, (fam, names) in APPS.items():
        if name not in GLYPHS or (a.public and name in PERSONAL):
            continue
        write(out / "scalable/apps" / f"{names[0]}.svg", app_icon(name, fam), names)
        if name in MINI_APPS:
            for size in (16, 22):
                write(out / f"{size}/apps" / f"{names[0]}.svg", mini_icon(name), names)

    for color, (c1, c2) in FOLDER_COLORS.items():
        for sym, names in FOLDERS.items():
            base = f"folder-{color}" + (f"-{sym}" if sym else "")
            write(out / "scalable/places" / f"{base}.svg", folder_icon(sym, c1, c2))
    for sym, names in FOLDERS.items():   # default color under the plain names
        for n in names:
            link = out / "scalable/places" / f"{n}.svg"
            link.symlink_to(f"folder-{a.folders}" + (f"-{sym}" if sym else "") + ".svg")

    for (name, dot), names in PANEL.items():
        write(out / "scalable/panel" / f"{names[0]}.svg", mini_icon(name, dot), names)

    # common web browsers (Zen is drawn with the other apps)
    for key, g in BROWSERS.items():
        names = g["names"]
        target = out / "scalable/apps" / f"{names[0]}.svg"
        if not target.exists():
            write(target, app_icon(g, g["family"]), [n for n in names if not (out / "scalable/apps" / f"{n}.svg").exists()])

    # System Settings modules: their symbol on a glass tile, gradient from the original hue
    for name, g in KCM.items():
        target = out / "scalable/apps" / f"{name}.svg"
        if not target.exists():
            write(target, app_icon(g, g["family"]))

    # file types: every Papirus mimetype symbol on a glass page
    mdir = out / "scalable/mimetypes"
    for name, g in MIME["glyphs"].items():
        write(mdir / f"{name}.svg", mime_icon(g))
    for alias, target in MIME["aliases"].items():
        seen = set()
        while target in MIME["aliases"] and target not in seen:   # follow alias chains
            seen.add(target)
            target = MIME["aliases"][target]
        if target in MIME["glyphs"] and not (mdir / f"{alias}.svg").exists():
            (mdir / f"{alias}.svg").symlink_to(f"{target}.svg")

    # every other tray / panel icon: Papirus' panel set, recolored to the palette
    hand_made = {n for names in PANEL.values() for n in names}
    panel_dirs = []
    for size in (16, 22, 24):
        src = PAPIRUS / f"{size}x{size}/panel"
        if not src.is_dir():
            continue
        dst = out / f"{size}/panel"
        shutil.copytree(src.resolve(), dst, symlinks=True)
        for f in dst.iterdir():
            if f.stem in hand_made:
                f.unlink()
            elif f.is_file() and not f.is_symlink():
                f.write_text(gradient_panel(f.read_text(), size))
        # Papirus aliases of the icons drawn here now point at our versions
        for f in dst.iterdir():
            if f.is_symlink() and not f.exists():
                target = Path(f.readlink()).name
                f.unlink()
                f.symlink_to(f"../../scalable/panel/{target}")
        panel_dirs.append(size)

    (out / "index.theme").write_text(f"""[Icon Theme]
Name=NeonGlass
Comment=Hairline Glass: glass tiles and neon gradient glyphs (default folders: {a.folders})
Inherits=Papirus-Dark,breeze-dark,hicolor
Example=folder
FollowsColorScheme=false
DisplayDepth=32
DesktopDefault=48
DesktopSizes=16,22,32,48,64,128
ToolbarDefault=22
ToolbarSizes=16,22,32,48
MainToolbarDefault=22
MainToolbarSizes=16,22,32,48
SmallDefault=16
SmallSizes=16
PanelDefault=48
PanelSizes=16,22,32,48,64,128
Directories=16/apps,22/apps,scalable/apps,scalable/places,scalable/mimetypes,scalable/panel,{",".join(f"{z}/panel" for z in panel_dirs)}

[16/apps]
Size=16
Context=Applications
Type=Fixed

[22/apps]
Size=22
Context=Applications
Type=Fixed

[scalable/apps]
Size=48
MinSize=16
MaxSize=512
Context=Applications
Type=Scalable

[scalable/places]
Size=48
MinSize=16
MaxSize=512
Context=Places
Type=Scalable

[scalable/mimetypes]
Size=48
MinSize=16
MaxSize=512
Context=MimeTypes
Type=Scalable

[scalable/panel]
Size=22
MinSize=16
MaxSize=48
Context=Status
Type=Scalable
""" + "".join(f"\n[{z}/panel]\nSize={z}\nContext=Status\nType=Fixed\n" for z in panel_dirs))
    n = sum(1 for _ in out.rglob("*.svg"))
    print(f"built {out} · {n} icons (incl. aliases) · default folders: {a.folders}")


if __name__ == "__main__":
    main()
