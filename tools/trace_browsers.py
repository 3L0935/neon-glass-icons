#!/usr/bin/env python3
"""Re-trace common web browsers' logos (from Papirus) into browsers.json.

Multi-colored logos keep their silhouette with thin cuts between colors
("object"); logos drawn as a symbol on a plate keep the symbol ("symbol").

  tools/trace_browsers.py   → browsers.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trace_kcm import object_mask  # noqa: E402
from trace_mime import family, masks, render, trace  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PAPIRUS = Path("/usr/share/icons/Papirus/64x64/apps")

# source icon, mode, icon names it provides (package, flatpak and desktop-file variants)
BROWSERS = {
    "firefox":     ("firefox", "object", ["firefox", "org.mozilla.firefox", "firefox-esr", "firefox-developer-edition", "firefox-nightly"]),
    "chrome":      ("google-chrome", "object", ["google-chrome", "com.google.Chrome", "google-chrome-stable", "google-chrome-beta", "google-chrome-unstable"]),
    "chromium":    ("chromium", "object", ["chromium", "chromium-browser", "org.chromium.Chromium", "ungoogled-chromium", "io.github.ungoogled_software.ungoogled_chromium"]),
    "brave":       ("brave-browser", "object", ["brave-browser", "brave", "com.brave.Browser", "brave-browser-beta", "brave-browser-nightly"]),
    "vivaldi":     ("vivaldi", "symbol", ["vivaldi", "com.vivaldi.Vivaldi", "vivaldi-stable", "vivaldi-snapshot"]),
    "opera":       ("opera", "object", ["opera", "com.opera.Opera", "opera-beta", "opera-developer", "opera-gx"]),
    "edge":        ("microsoft-edge", "object", ["microsoft-edge", "com.microsoft.Edge", "microsoft-edge-stable", "microsoft-edge-beta", "microsoft-edge-dev"]),
    "librewolf":   ("librewolf", "symbol", ["librewolf", "io.gitlab.librewolf-community"]),
    "tor":         ("torbrowser", "object", ["torbrowser", "tor-browser", "org.torproject.torbrowser-launcher", "torbrowser-launcher"]),
    "epiphany":    ("org.gnome.Epiphany", "drawn:sources/drawn/globe.png", ["org.gnome.Epiphany", "epiphany", "web-browser"]),
    "falkon":      ("falkon", "object", ["falkon", "org.kde.falkon"]),
    "thorium":     ("thorium-browser", "object", ["thorium-browser", "thorium", "io.github.thorium_browser"]),
    "waterfox":    ("waterfox", "object", ["waterfox", "net.waterfox.waterfox", "waterfox-g"]),
    "mullvad":     ("mullvad-browser", "symbol", ["mullvad-browser", "net.mullvad.MullvadBrowser"]),
    "konqueror":   ("konqueror", "object", ["konqueror", "org.kde.konqueror"]),
    "qutebrowser": ("qutebrowser", "object", ["qutebrowser", "org.qutebrowser.qutebrowser"]),
    "midori":      ("midori", "object", ["midori", "org.midori_browser.Midori"]),
}


def main():
    out = {}
    for key, (src, mode, names) in BROWSERS.items():
        f = (PAPIRUS / f"{src}.svg").resolve()
        if not f.exists():
            print("missing", src)
            continue
        img = render(f)
        sym, bg = masks(img, whole_shape=False, fold=False)
        if mode.startswith("drawn:"):   # logo too fragmented to trace: hand-drawn mask
            from PIL import Image
            mask = Image.open(ROOT / mode[6:]).convert("RGBA").getchannel("A").point(lambda v: 255 if v > 127 else 0)
        else:
            mask = object_mask(img) if mode == "object" else sym
        g = trace(mask)
        g["family"], g["names"] = family(bg), names
        out[key] = g
    (ROOT / "browsers.json").write_text(json.dumps(out))
    print(f"{len(out)} browsers traced")


if __name__ == "__main__":
    main()
