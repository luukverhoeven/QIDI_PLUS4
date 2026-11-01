"""Wi-Fi: the wpa_supplicant client and the network and password screens."""

import os
import tempfile
import unittest

from plus4screen import tjc
from plus4screen.ui.app import UIApp
from plus4screen.ui.layout import Layout
from plus4screen.wpa import Wpa, unescape
from test_ui import FakeMoonraker, SyncRunner

LAYOUT = Layout.load()

SCAN = ("bssid / frequency / signal level / flags / ssid\n"
        "aa:bb:cc:00:00:01\t2412\t-48\t[WPA2-PSK-CCMP][ESS]\tHome\n"
        "aa:bb:cc:00:00:02\t5180\t-60\t[WPA2-PSK-CCMP][ESS]\tHome\n"
        "aa:bb:cc:00:00:03\t2437\t-75\t[ESS]\tCaf\\xc3\\xa9 guest\n"
        "aa:bb:cc:00:00:04\t2462\t-66\t[WPA2-PSK-CCMP][ESS]\tOffice\n"
        "aa:bb:cc:00:00:05\t2462\t-80\t[WPA2-PSK-CCMP][ESS]\t\n")


class FakeWpa(Wpa):
    def __init__(self):
        super().__init__(path="/nonexistent")
        self.sent = []
        self.state = {"wpa_state": "COMPLETED", "ssid": "Home",
                      "ip_address": "192.168.86.210"}

    def request(self, command):
        self.sent.append(command)
        if command == "SCAN_RESULTS":
            return SCAN
        if command == "STATUS":
            return "".join("%s=%s\n" % kv for kv in self.state.items())
        if command == "LIST_NETWORKS":
            return "network id / ssid / bssid / flags\n0\tHome\tany\t[CURRENT]\n"
        if command == "ADD_NETWORK":
            return "1\n"
        if command == "SCAN":
            return "OK\n"
        return "OK\n"


class WpaTest(unittest.TestCase):
    def test_results_are_unique_and_strongest_first(self):
        nets = FakeWpa().results()
        self.assertEqual([n["ssid"] for n in nets],
                         ["Home", "Office", "Café guest"])
        self.assertEqual(nets[0]["signal"], -48)
        self.assertFalse(nets[2]["secured"])

    def test_connect_new_network(self):
        wpa = FakeWpa()
        wpa.connect("Office", "secret123")
        self.assertIn("SET_NETWORK 1 ssid %s" % "Office".encode().hex(),
                      wpa.sent)
        self.assertIn('SET_NETWORK 1 psk "secret123"', wpa.sent)
        self.assertEqual(wpa.sent[-1], "SELECT_NETWORK 1")

    def test_connect_open_and_saved(self):
        wpa = FakeWpa()
        wpa.connect("Home")
        self.assertNotIn("ADD_NETWORK", wpa.sent)
        self.assertFalse(any("psk" in c for c in wpa.sent))
        wpa.connect("Cafe", "")
        self.assertIn("SET_NETWORK 1 key_mgmt NONE", wpa.sent)

    def test_unescape(self):
        self.assertEqual(unescape("Caf\\xc3\\xa9"), "Café")
        self.assertEqual(unescape('a\\"b'), 'a"b')


class WifiScreenTest(unittest.TestCase):
    def setUp(self):
        self.sent = []
        self.now = [1000.0]
        self.app = UIApp(self.write, FakeMoonraker(), SyncRunner(), LAYOUT,
                         prefs_path=os.path.join(tempfile.mkdtemp(), "p"),
                         clock=lambda: self.now[0])
        self.app.poll()
        self.app.start()
        self.app.handle(tjc.Event(tjc.NUMBER, value=LAYOUT.screen_id))
        self.wpa = FakeWpa()
        self.app.screens["wifi"].wpa = self.wpa
        import plus4screen.ui.wifi as wifi
        self.addCleanup(setattr, wifi, "SCAN_WAIT", wifi.SCAN_WAIT)
        wifi.SCAN_WAIT = 0

    def write(self, data):
        self.sent.extend(p.decode("utf-8") for p in data.split(tjc.TERM)
                         if p)

    def tap(self, hit_id):
        x, y, w, h = self.app.canvas.screen.hit(hit_id).rect
        self.app.on_touch(x + w // 2, y + h // 2, True)
        self.app.on_touch(x + w // 2, y + h // 2, False)

    def test_settings_opens_the_network_list(self):
        self.app.show("settings")
        self.tap("wifi")
        self.assertEqual(self.app.current, "wifi")
        texts = " ".join(self.sent)
        self.assertIn('"Connected to Home', texts)
        self.assertIn('"Café guest"', texts)
        self.assertIn('"Connected · strong signal"', texts)
        # Three networks: rows 4-6 are painted over.
        self.assertEqual(sum(c.startswith("fill") for c in self.sent), 3)

    def test_password_then_connect(self):
        self.app.show("wifi")
        self.tap("net1")                       # Office, secured
        self.assertEqual(self.app.current, "wifi_pass")
        for key in ("key9", "key2", "key0"):   # p e q
            self.tap(key)
        self.tap("connect")                    # too short
        self.assertEqual(self.app.current, "wifi_pass")
        for key in ("key3", "key4", "key5", "key6", "key7"):
            self.tap(key)
        self.tap("connect")
        self.assertIn('SET_NETWORK 1 psk "peqrtyui"', self.wpa.sent)
        self.assertEqual(self.app.current, "wifi")
        self.assertNotIn("peqrtyui", " ".join(self.sent))

    def test_password_is_hidden_until_shown(self):
        self.app.show("wifi_pass", ssid="Office")
        self.tap("key0")
        self.assertIn('"*"', " ".join(self.sent))
        self.tap("show")
        self.assertIn('"q"', " ".join(self.sent))

    def test_symbols_and_shift(self):
        self.app.show("wifi_pass", ssid="Office")
        self.tap("shift")
        self.tap("key0")
        self.tap("mode")
        self.tap("key0")
        self.tap("show")
        self.assertIn('"Q1"', " ".join(self.sent))

    def test_connection_result_is_shown(self):
        self.app.show("wifi")
        self.wpa.state = {"wpa_state": "SCANNING"}
        self.app.screens["wifi"].connect("Office", "secret123")
        self.app.poll()
        self.assertEqual(self.app.current, "wifi")
        self.wpa.state = {"wpa_state": "COMPLETED", "ssid": "Office",
                          "ip_address": "192.168.86.77"}
        self.app.poll()
        self.assertEqual(self.app.current, "message")
        self.assertIn("SAVE_CONFIG", self.wpa.sent)
        self.assertIn("192.168.86.77", " ".join(self.sent))

    def test_open_network_asks_first(self):
        self.app.show("wifi")
        self.tap("net2")                       # Cafe guest, open
        self.assertEqual(self.app.current, "confirm")


if __name__ == "__main__":
    unittest.main()
