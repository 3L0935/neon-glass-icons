#!/usr/bin/env python3
"""neonglass-gsr-tray: a themable tray icon for GPU Screen Recorder.

GPU Screen Recorder's UI (gsr-ui) puts a tray icon that sends a raw image
instead of an icon name, so icon themes can't restyle it. This service mirrors
it with a tray item of its own that uses named icons:

  com.dec05eba.gpu_screen_recorder.tray-idle / -recording / -paused

- state: the image gsr-ui sends is compared with its own reference images
- menu: gsr-ui's real menu is relayed as is (right click)
- left click: show/hide the GSR UI · middle click: start/stop recording
Hide gsr-ui's own item in the tray settings (Entries → GPU Screen Recorder → Hidden).
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

APP = "com.dec05eba.gpu_screen_recorder"
GSR_ID = "gpu-screen-recorder-ui"
SNI = "org.kde.StatusNotifierItem"
MENU = "com.canonical.dbusmenu"
PROPS = "org.freedesktop.DBus.Properties"
WATCHER = ("org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher")
STATES = ("idle", "recording", "paused")
POLL_MS = 1000


def cli(*args):
    subprocess.Popen(["flatpak", "run", "--command=gsr-ui-cli", APP, *args],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def references():
    """gsr-ui's own tray images, as ARGB32 bytes per (state, size)."""
    from PIL import Image

    out = {}
    try:
        base = subprocess.run(["flatpak", "info", "--show-location", APP], capture_output=True, text=True).stdout.strip()
    except OSError:
        return out
    for state in STATES:
        for f in glob.glob(f"{base}/files/share/icons/hicolor/*/status/{APP}.tray-{state}.png"):
            im = Image.open(f).convert("RGBA")
            r, g, b, a = im.split()
            argb = Image.merge("RGBA", (a, r, g, b)).tobytes()   # SNI pixmaps are ARGB32, big endian
            out[(state, im.width)] = argb
    return out


class Item(dbus.service.Object):
    def __init__(self, bus, name):
        self.bus, self.name = bus, name
        self.state = "idle"
        self.active = False
        self.gsr = None          # (service, path) of gsr-ui's own item
        self.gsr_menu = None     # its dbusmenu path
        self.refs = references()
        super().__init__(bus, "/StatusNotifierItem")
        self.menu = Menu(bus, self)

    # ── SNI properties ──
    def props(self):
        return {
            "Category": "ApplicationStatus",
            "Id": "neonglass-gsr-tray",
            "Title": "GPU Screen Recorder",
            "Status": "Active" if self.active else "Passive",
            "IconName": f"{APP}.tray-{self.state}",
            "IconThemePath": "",
            "ItemIsMenu": dbus.Boolean(False),
            "Menu": dbus.ObjectPath("/MenuBar"),
            "ToolTip": dbus.Struct(("", dbus.Array([], signature="(iiay)"), "GPU Screen Recorder",
                                    {"idle": "Idle", "recording": "Recording", "paused": "Paused"}[self.state]),
                                   signature="sa(iiay)ss"),
        }

    @dbus.service.method(PROPS, in_signature="ss", out_signature="v")
    def Get(self, iface, prop):
        return self.props()[prop]

    @dbus.service.method(PROPS, in_signature="s", out_signature="a{sv}")
    def GetAll(self, iface):
        return self.props()

    @dbus.service.method(SNI, in_signature="ii")
    def Activate(self, x, y):
        cli("toggle-show")

    @dbus.service.method(SNI, in_signature="ii")
    def SecondaryActivate(self, x, y):
        cli("toggle-record")

    @dbus.service.method(SNI, in_signature="ii")
    def ContextMenu(self, x, y):
        cli("toggle-show")

    @dbus.service.method(SNI, in_signature="is")
    def Scroll(self, delta, orientation):
        pass

    @dbus.service.signal(SNI)
    def NewIcon(self):
        pass

    @dbus.service.signal(SNI)
    def NewToolTip(self):
        pass

    @dbus.service.signal(SNI, signature="s")
    def NewStatus(self, status):
        pass

    # ── follow gsr-ui ──
    def find_gsr(self):
        try:
            watcher = self.bus.get_object(*WATCHER)
            items = watcher.Get("org.kde.StatusNotifierWatcher", "RegisteredStatusNotifierItems", dbus_interface=PROPS)
        except dbus.DBusException:
            return None
        for it in items:
            svc, _, path = it.partition("/")
            path = "/" + path if path else "/StatusNotifierItem"
            if svc == self.name:
                continue
            try:
                obj = self.bus.get_object(svc, path)
                if obj.Get(SNI, "Id", dbus_interface=PROPS) == GSR_ID:
                    self.gsr_menu = obj.Get(SNI, "Menu", dbus_interface=PROPS)
                    return svc, path
            except dbus.DBusException:
                continue
        return None

    def read_state(self):
        obj = self.bus.get_object(*self.gsr)
        pixmaps = obj.Get(SNI, "IconPixmap", dbus_interface=PROPS)
        if not pixmaps:
            return self.state
        w, h, data = max(pixmaps, key=lambda p: int(p[0]))
        data = bytes(data)
        best, best_d = self.state, None
        for (state, size), ref in self.refs.items():
            if size != int(w) or len(ref) != len(data):
                continue
            d = sum(abs(a - b) for a, b in zip(data[::7], ref[::7]))
            if best_d is None or d < best_d:
                best, best_d = state, d
        return best

    def poll(self):
        try:
            if self.gsr is None:
                self.gsr = self.find_gsr()
            active = self.gsr is not None
            state = self.read_state() if active else "idle"
        except dbus.DBusException:   # gsr-ui went away
            self.gsr, active, state = None, False, "idle"
        if active != self.active:
            self.active = active
            self.NewStatus("Active" if active else "Passive")
        if state != self.state:
            self.state = state
            self.NewIcon()
            self.NewToolTip()
        return True


class Menu(dbus.service.Object):
    """Relays gsr-ui's dbusmenu, so right click shows its real menu."""

    def __init__(self, bus, item):
        self.item = item
        super().__init__(bus, "/MenuBar")

    def target(self):
        if not self.item.gsr or not self.item.gsr_menu:
            raise dbus.DBusException("GPU Screen Recorder is not running")
        return dbus.Interface(self.item.bus.get_object(self.item.gsr[0], self.item.gsr_menu), MENU)

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
    name = f"org.kde.StatusNotifierItem-{os.getpid()}-1"
    bus_name = dbus.service.BusName(name, bus)
    item = Item(bus, name)
    item.poll()

    def register():
        try:
            bus.get_object(*WATCHER).RegisterStatusNotifierItem(name, dbus_interface="org.kde.StatusNotifierWatcher")
        except dbus.DBusException as e:
            print("watcher not ready:", e, file=sys.stderr)
            return True   # retry
        return False

    if register():
        GLib.timeout_add_seconds(5, register)
    # re-register if Plasma restarts
    bus.add_signal_receiver(lambda n, old, new: new and register(), "NameOwnerChanged",
                            "org.freedesktop.DBus", arg0=WATCHER[0])
    GLib.timeout_add(POLL_MS, item.poll)
    _ = bus_name
    GLib.MainLoop().run()


if __name__ == "__main__":
    main()
