#!/usr/bin/env python3
"""neonglass-tray-mirror: themable tray icons for apps that send raw images.

Some apps (Electron apps like Discord or Heroic, GPU Screen Recorder's UI) put
a tray icon that is a raw image instead of an icon name, so icon themes can't
restyle it. For each of them, this service shows a tray item of its own that
uses named icons, and:

- follows the app's state, by comparing the image it sends with the app's own
  reference images (Discord: unread, in a call, muted…; GSR: recording, paused)
- relays the app's real menu (right click) and its clicks
- disappears when the app's own item goes away

Hide the apps' own items in the tray settings (Entries → … → Hidden).
"""
from __future__ import annotations

import glob
import os
import subprocess
import sys

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

SNI = "org.kde.StatusNotifierItem"
MENU = "com.canonical.dbusmenu"
PROPS = "org.freedesktop.DBus.Properties"
WATCHER = ("org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher")
POLL_MS = 1000


def flatpak_dir(app):
    try:
        return subprocess.run(["flatpak", "info", "--show-location", app], capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def gsr_refs():
    base = flatpak_dir("com.dec05eba.gpu_screen_recorder")
    return {s: glob.glob(f"{base}/files/share/icons/hicolor/*/status/com.dec05eba.gpu_screen_recorder.tray-{s}.png")
            for s in ("idle", "recording", "paused")}


def discord_refs():
    base = flatpak_dir("com.discordapp.Discord") + "/files/discord/modules/discord_desktop_core/app/images/systemtray/linux"
    if not os.path.isdir(base):   # non-flatpak installs
        base = next(iter(glob.glob("/opt/discord*/resources/**/systemtray/linux", recursive=True)), base)
    names = {"tray": "", "tray-unread": "-unread", "tray-connected": "-connected", "tray-speaking": "-speaking",
             "tray-muted": "-muted", "tray-deafened": "-deafened"}
    return {suffix: [f"{base}/{n}.png"] for n, suffix in names.items()}


def gsr_cli(*args):
    subprocess.Popen(["flatpak", "run", "--command=gsr-ui-cli", "com.dec05eba.gpu_screen_recorder", *args],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


# app → how to find its item, its reference images per state, our icon per state
MIRRORS = {
    "gsr": dict(title="GPU Screen Recorder", match_id="gpu-screen-recorder-ui", refs=gsr_refs,
                icon="com.dec05eba.gpu_screen_recorder.tray-{state}", default="idle",
                activate=lambda: gsr_cli("toggle-show"), secondary=lambda: gsr_cli("toggle-record")),
    "discord": dict(title="Discord", match_id="discord_status_icon", refs=discord_refs,
                    icon="neonglass-discord-tray{state}", default=""),
    "heroic": dict(title="Heroic Games Launcher", match_cmdline="heroic-games-launcher", refs=lambda: {},
                   icon="neonglass-heroic-tray{state}", default=""),
}


def load_refs(spec):
    """{state: [ARGB32 bytes, size]} from the app's reference PNGs."""
    from PIL import Image

    out = []
    for state, files in spec().items():
        for f in files:
            try:
                im = Image.open(f).convert("RGBA")
            except OSError:
                continue
            r, g, b, a = im.split()
            out.append((state, im.width, Image.merge("RGBA", (a, r, g, b)).tobytes()))   # SNI pixmaps: ARGB32
    return out


def pid_cmdline(bus, service):
    try:
        pid = bus.get_object("org.freedesktop.DBus", "/").GetConnectionUnixProcessID(service, dbus_interface="org.freedesktop.DBus")
        return open(f"/proc/{int(pid)}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace")
    except Exception:
        return ""


class Item(dbus.service.Object):
    def __init__(self, bus, key, cfg):
        self.bus, self.key, self.cfg = bus, key, cfg
        self.path = f"/NeonGlass/{key}"
        self.state = cfg["default"]
        self.active = False
        self.src = None          # (service, path) of the app's own item
        self.src_menu = None
        self.refs = load_refs(cfg["refs"])
        super().__init__(bus, self.path + "/StatusNotifierItem")
        self.menu = Menu(bus, self.path + "/MenuBar", self)

    def props(self):
        return {
            "Category": "ApplicationStatus",
            "Id": f"neonglass-{self.key}-tray",
            "Title": self.cfg["title"],
            "Status": "Active" if self.active else "Passive",
            "IconName": self.cfg["icon"].format(state=self.state),
            "IconThemePath": "",
            "ItemIsMenu": dbus.Boolean(False),
            "Menu": dbus.ObjectPath(self.path + "/MenuBar"),
            "ToolTip": dbus.Struct(("", dbus.Array([], signature="(iiay)"), self.cfg["title"], ""), signature="sa(iiay)ss"),
        }

    @dbus.service.method(PROPS, in_signature="ss", out_signature="v")
    def Get(self, iface, prop):
        return self.props()[prop]

    @dbus.service.method(PROPS, in_signature="s", out_signature="a{sv}")
    def GetAll(self, iface):
        return self.props()

    def forward(self, method, *args):
        """Pass a click on to the app's own item."""
        if self.src:
            try:
                getattr(dbus.Interface(self.bus.get_object(*self.src), SNI), method)(*args)
            except dbus.DBusException:
                pass

    @dbus.service.method(SNI, in_signature="ii")
    def Activate(self, x, y):
        (self.cfg.get("activate") or (lambda: self.forward("Activate", x, y)))()

    @dbus.service.method(SNI, in_signature="ii")
    def SecondaryActivate(self, x, y):
        (self.cfg.get("secondary") or (lambda: self.forward("SecondaryActivate", x, y)))()

    @dbus.service.method(SNI, in_signature="ii")
    def ContextMenu(self, x, y):
        self.forward("ContextMenu", x, y)

    @dbus.service.method(SNI, in_signature="is")
    def Scroll(self, delta, orientation):
        self.forward("Scroll", delta, orientation)

    @dbus.service.signal(SNI)
    def NewIcon(self):
        pass

    @dbus.service.signal(SNI, signature="s")
    def NewStatus(self, status):
        pass

    # ── follow the app's own item ──
    def matches(self, svc, obj):
        if "match_id" in self.cfg:
            return str(obj.Get(SNI, "Id", dbus_interface=PROPS)).startswith(self.cfg["match_id"])
        return self.cfg["match_cmdline"] in pid_cmdline(self.bus, svc)

    def find(self, items, own):
        for it in items:
            svc, _, path = it.partition("/")
            path = "/" + path if path else "/StatusNotifierItem"
            if svc == own:
                continue
            try:
                obj = self.bus.get_object(svc, path)
                if self.matches(svc, obj):
                    self.src_menu = obj.Get(SNI, "Menu", dbus_interface=PROPS)
                    return svc, path
            except dbus.DBusException:
                continue
        return None

    def read_state(self):
        if not self.refs:
            return self.cfg["default"]
        pixmaps = self.bus.get_object(*self.src).Get(SNI, "IconPixmap", dbus_interface=PROPS)
        if not pixmaps:
            return self.state
        w, h, data = max(pixmaps, key=lambda p: int(p[0]))
        data = bytes(data)
        best, best_d = self.state, None
        for state, size, ref in self.refs:
            if size != int(w) or len(ref) != len(data):
                continue
            d = sum(abs(a - b) for a, b in zip(data[::5], ref[::5]))
            if best_d is None or d < best_d:
                best, best_d = state, d
        return best

    def poll(self, items, own):
        try:
            if self.src is None or f"{self.src[0]}{self.src[1]}" not in {i if "/" in i else i + "/StatusNotifierItem" for i in items}:
                self.src = self.find(items, own)
            active = self.src is not None
            state = self.read_state() if active else self.cfg["default"]
        except dbus.DBusException:
            self.src, active, state = None, False, self.cfg["default"]
        if active != self.active:
            self.active = active
            self.NewStatus("Active" if active else "Passive")
        if state != self.state:
            self.state = state
            self.NewIcon()


class Menu(dbus.service.Object):
    """Relays the app's dbusmenu, so right click shows its real menu."""

    def __init__(self, bus, path, item):
        self.item = item
        super().__init__(bus, path)

    def target(self):
        if not self.item.src or not self.item.src_menu:
            raise dbus.DBusException(f"{self.item.cfg['title']} is not running")
        return dbus.Interface(self.item.bus.get_object(self.item.src[0], self.item.src_menu), MENU)

    @dbus.service.method(MENU, in_signature="iias", out_signature="u(ia{sv}av)")
    def GetLayout(self, parent, depth, props):
        return self.target().GetLayout(parent, depth, props)

    @dbus.service.method(MENU, in_signature="aias", out_signature="a(ia{sv})")
    def GetGroupProperties(self, ids, props):
        return self.target().GetGroupProperties(ids, props)

    @dbus.service.method(MENU, in_signature="is", out_signature="v")
    def GetProperty(self, id_, name):
        return self.target().GetProperty(id_, name)

    @dbus.service.method(MENU, in_signature="isvu")
    def Event(self, id_, event, data, timestamp):
        self.target().Event(id_, event, data, timestamp)

    @dbus.service.method(MENU, in_signature="a(isvu)", out_signature="ai")
    def EventGroup(self, events):
        return self.target().EventGroup(events)

    @dbus.service.method(MENU, in_signature="i", out_signature="b")
    def AboutToShow(self, id_):
        return self.target().AboutToShow(id_)

    @dbus.service.method(MENU, in_signature="ai", out_signature="aiai")
    def AboutToShowGroup(self, ids):
        return self.target().AboutToShowGroup(ids)

    @dbus.service.method(PROPS, in_signature="ss", out_signature="v")
    def Get(self, iface, prop):
        return {"Version": dbus.UInt32(3), "TextDirection": "ltr", "Status": "normal"}.get(prop, "")

    @dbus.service.method(PROPS, in_signature="s", out_signature="a{sv}")
    def GetAll(self, iface):
        return {"Version": dbus.UInt32(3), "TextDirection": "ltr", "Status": "normal"}


def main():
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    own = bus.get_unique_name()
    enabled = sys.argv[1:] or list(MIRRORS)
    items = [Item(bus, k, MIRRORS[k]) for k in enabled if k in MIRRORS]

    def register():
        try:
            w = dbus.Interface(bus.get_object(*WATCHER), "org.kde.StatusNotifierWatcher")
            for it in items:
                w.RegisterStatusNotifierItem(it.path + "/StatusNotifierItem")
        except dbus.DBusException as e:
            print("watcher not ready:", e, file=sys.stderr)
            return True
        return False

    def poll():
        try:
            registered = [str(i) for i in bus.get_object(*WATCHER).Get(
                "org.kde.StatusNotifierWatcher", "RegisteredStatusNotifierItems", dbus_interface=PROPS)]
        except dbus.DBusException:
            return True
        for it in items:
            it.poll(registered, own)
        return True

    if register():
        GLib.timeout_add_seconds(5, register)
    bus.add_signal_receiver(lambda n, old, new: new and register(), "NameOwnerChanged",
                            "org.freedesktop.DBus", arg0=WATCHER[0])
    poll()
    GLib.timeout_add(POLL_MS, poll)
    GLib.MainLoop().run()


if __name__ == "__main__":
    main()
