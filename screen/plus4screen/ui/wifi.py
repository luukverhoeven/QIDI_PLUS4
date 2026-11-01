"""Choosing a Wi-Fi network and typing its password."""

import logging
import time

from ..wpa import Wpa, signal_words
from .base import Screen
from .text import ACC, AMBER, RED, SUB, TEXT

log = logging.getLogger("plus4screen")

ROWS = 6
SCAN_WAIT = 3.0              # s between SCAN and reading the results
CONNECT_TIMEOUT = 30.0       # s to wait for a connection
CARD = (20, 26, 34)          # design colour of the list card (#141A22)
KEYS = {"lower": "qwertyuiopasdfghjkl-zxcvbnm",
        "upper": "QWERTYUIOPASDFGHJKL_ZXCVBNM",
        "symbols": "1234567890!@#$%&*()=.,?;:/+"}
MAX_PASSWORD = 63
MIN_PASSWORD = 8


def card_color():
    r, g, b = CARD
    return (r >> 3) << 11 | (g >> 2) << 5 | (b >> 3)


class Wifi(Screen):
    name = "wifi"

    def __init__(self, app):
        super().__init__(app)
        self.wpa = Wpa()
        self.networks = []
        self.known = {}
        self.status = {}
        self.error = None
        self.page = 0
        self.scanning = False
        self.connecting = None   # (ssid, started)
        self.checking = False
        self.blanked = set()

    # Data -----------------------------------------------------------------

    def scan(self):
        if self.scanning:
            return
        self.scanning = True
        wpa = self.wpa

        def work():
            wpa.scan()
            time.sleep(SCAN_WAIT)
            return wpa.status(), wpa.results(), wpa.known()

        def done(result, error):
            self.scanning = False
            if error is None:
                self.status, self.networks, self.known = result
                self.error = None
            else:
                self.error = str(error)
            if self.app.current == self.name:
                self.draw()
        self.app.runner.spawn(work, done)

    def connect(self, ssid, password=None):
        """Switch to ``ssid``; ``password`` "" means an open network and
        None a saved one."""
        log.info("wifi: connecting to %s", ssid)
        self.connecting = (ssid, self.app.clock())
        wpa = self.wpa

        def done(_result, error):
            if error is not None:
                self.connecting = None
                self.app.message("Wi-Fi", str(error))
        self.app.runner.spawn(lambda: wpa.connect(ssid, password), done)
        self.app.show(self.name, rescan=False)

    def follow(self, old, new):
        if not self.connecting or self.checking:
            return
        self.checking = True
        ssid, started = self.connecting
        wpa = self.wpa

        def done(status, error):
            self.checking = False
            if error is not None or not self.connecting:
                return
            self.status = status
            joined = status.get("wpa_state") == "COMPLETED" and \
                status.get("ssid") == ssid and status.get("ip_address")
            late = self.app.clock() - started > CONNECT_TIMEOUT
            if joined or late:
                self.connecting = None
                self.app.runner.spawn(wpa.keep_all, None)
                self.app.net_at = -1e9          # read the address again
                if joined:
                    self.app.message("Wi-Fi connected", "%s · %s" % (
                        ssid, status["ip_address"]))
                else:
                    self.app.message("Wi-Fi not connected",
                                     "Could not join %s. Check the "
                                     "password and try again." % ssid)
            elif self.app.current == self.name:
                self.draw()
        self.app.runner.spawn(wpa.status, done)

    # Drawing --------------------------------------------------------------

    def enter(self, rescan=True, **options):
        self.blanked = set()
        if rescan:
            self.scan()
        self.draw()

    def status_line(self):
        if self.connecting:
            return "Connecting to %s…" % self.connecting[0], AMBER
        if self.error:
            return self.error, RED
        st = self.status
        if st.get("wpa_state") == "COMPLETED" and st.get("ssid"):
            return "Connected to %s · %s" % (
                st["ssid"], st.get("ip_address", "no address yet")), ACC
        if self.scanning and not self.networks:
            return "Looking for networks…", SUB
        return "Not connected", SUB

    def pages(self):
        return max(1, (len(self.networks) + ROWS - 1) // ROWS)

    def draw(self):
        text, color = self.status_line()
        self.text("status", text, color)
        self.page = min(self.page, self.pages() - 1)
        self.text("page", "Page %d of %d" % (self.page + 1, self.pages()))
        shown = self.networks[self.page * ROWS:(self.page + 1) * ROWS]
        current = self.status.get("ssid") if \
            self.status.get("wpa_state") == "COMPLETED" else None
        for i in range(ROWS):
            rect = self.canvas.screen.hit("net%d" % i).rect
            if i < len(shown):
                net = shown[i]
                if i in self.blanked:
                    self.blanked.discard(i)
                    self.canvas.restore(rect)
                if net["ssid"] == current:
                    kind, color = "Connected", ACC
                elif net["ssid"] in self.known:
                    kind, color = "Saved", TEXT
                else:
                    kind = "Secured" if net["secured"] else "Open"
                    color = SUB
                self.text("ssid%d" % i, net["ssid"])
                self.text("info%d" % i, "%s · %s" % (
                    kind, signal_words(net["signal"])), color)
            elif i not in self.blanked:
                self.blanked.add(i)
                x, y, w, h = rect
                # Keep the card's edges and the line above the row.
                self.canvas.blank((x + 12, y + 1, w - 24, h - 2),
                                  card_color())

    def touch(self, hit_id):
        app = self.app
        if hit_id == "scan":
            self.scan()
            self.draw()
        elif hit_id == "close":
            app.show("settings")
        elif hit_id in ("prev", "next"):
            page = self.page + (1 if hit_id == "next" else -1)
            if 0 <= page < self.pages():
                self.page = page
                app.show(self.name, rescan=False)
        elif hit_id.startswith("net"):
            index = self.page * ROWS + int(hit_id[3:])
            if index < len(self.networks):
                self.choose(self.networks[index])

    def choose(self, net):
        app, ssid = self.app, net["ssid"]
        if self.status.get("ssid") == ssid and \
                self.status.get("wpa_state") == "COMPLETED":
            app.message("Wi-Fi", "Already connected to %s." % ssid)
        elif ssid in self.known:
            app.confirm("Connect to %s?" % ssid, "This network is saved.",
                        "Connect", lambda: self.connect(ssid))
        elif not net["secured"]:
            app.confirm("Connect to %s?" % ssid, "This network is open: "
                        "anyone nearby can read what is sent.", "Connect",
                        lambda: self.connect(ssid, ""))
        else:
            app.show("wifi_pass", ssid=ssid)


class WifiPassword(Screen):
    name = "wifi_pass"

    def __init__(self, app):
        super().__init__(app)
        self.ssid = ""
        self.entry = ""
        self.mode = "lower"
        self.visible = False

    def enter(self, ssid=None, **options):
        if ssid is not None:
            self.ssid, self.entry = ssid, ""
            self.mode, self.visible = "lower", False
        self.text("title", "Password for %s" % self.ssid)
        self.draw_keys()
        self.draw_entry()

    def draw_keys(self):
        for i, char in enumerate(KEYS[self.mode]):
            self.text("key%d" % i, char)
        self.text("mode", "abc" if self.mode == "symbols" else "123")
        self.canvas.toggle("shift", self.mode == "upper")
        self.canvas.toggle("show", self.visible)

    def draw_entry(self):
        shown = self.entry if self.visible else "*" * len(self.entry)
        room = 40                   # characters that fit the box
        self.text("entry", shown[-room:])

    def touch(self, hit_id):
        if hit_id.startswith("key"):
            if len(self.entry) < MAX_PASSWORD:
                self.entry += KEYS[self.mode][int(hit_id[3:])]
                self.draw_entry()
        elif hit_id == "space":
            if len(self.entry) < MAX_PASSWORD:
                self.entry += " "
                self.draw_entry()
        elif hit_id == "back":
            self.entry = self.entry[:-1]
            self.draw_entry()
        elif hit_id == "shift":
            self.mode = "lower" if self.mode == "upper" else "upper"
            self.draw_keys()
        elif hit_id == "mode":
            self.mode = "lower" if self.mode == "symbols" else "symbols"
            self.draw_keys()
        elif hit_id == "show":
            self.visible = not self.visible
            self.canvas.toggle("show", self.visible)
            self.draw_entry()
        elif hit_id == "cancel":
            self.app.show("wifi", rescan=False)
        elif hit_id == "connect":
            if len(self.entry) < MIN_PASSWORD:
                self.text("title", "At least %d characters, please"
                          % MIN_PASSWORD, RED)
                return
            password, self.entry = self.entry, ""
            self.app.screens["wifi"].connect(self.ssid, password)


SCREENS = {"wifi": Wifi, "wifi_pass": WifiPassword}
