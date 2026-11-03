"""The allowlist between the Wi-Fi screen and wpa_supplicant."""

import os
import socket
import tempfile
import threading
import unittest

from plus4screen import wifi_gate
from plus4screen.wpa import Wpa, WpaError

SSID = "Office".encode().hex()


class AllowlistTest(unittest.TestCase):
    def test_commands_of_the_wifi_screen_pass(self):
        for command in ("STATUS", "SCAN", "SCAN_RESULTS", "LIST_NETWORKS",
                        "ADD_NETWORK", "SAVE_CONFIG", "ENABLE_NETWORK all",
                        "ENABLE_NETWORK 3", "SELECT_NETWORK 12",
                        "SET_NETWORK 3 ssid " + SSID,
                        "SET_NETWORK 3 ssid " + "41" * 32,
                        'SET_NETWORK 3 psk "secret123"',
                        'SET_NETWORK 3 psk "' + "a b!" * 15 + 'abc"',
                        "SET_NETWORK 3 key_mgmt NONE"):
            self.assertTrue(wifi_gate.allowed(command), command)

    def test_everything_else_is_refused(self):
        for command in (
                # Settings that make wpa_supplicant load a library as root.
                "SET pkcs11_module_path /tmp/x.so",
                "SET pkcs11_engine_path /tmp/x.so",
                "SET opensc_engine_path /tmp/x.so",
                "SET_NETWORK 3 engine 1",
                "SET_NETWORK 3 engine_id pkcs11",
                "SET_NETWORK 3 pin \"1234\"",
                # Other commands.
                "TERMINATE", "REMOVE_NETWORK all", "DRIVER x", "ATTACH",
                "status", "STATUS-VERBOSE", "STATUS ",
                # Bad arguments.
                'SET_NETWORK 3 psk "short"',
                'SET_NETWORK 3 psk "' + "a" * 64 + '"',
                'SET_NETWORK 3 psk "secret123\nnetwork={"',
                'SET_NETWORK 3 psk secret123',
                "SET_NETWORK 3 ssid 4",
                "SET_NETWORK 3 ssid " + "41" * 33,
                "SET_NETWORK 3 ssid 4G",
                "SET_NETWORK x ssid 41",
                "ENABLE_NETWORK 12345",
                "SET_NETWORK 3 key_mgmt WPA-EAP",
                ""):
            self.assertFalse(wifi_gate.allowed(command), command)

    def test_refused_requests_are_not_passed_on(self):
        passed = []
        for data in (b"SET pkcs11_module_path /tmp/x.so",
                     b"STATUS" + b" " * 300, b"SCAN\xff"):
            reply = wifi_gate.answer(data, lambda c: passed.append(c))
            self.assertEqual(reply, wifi_gate.REFUSED.encode())
        self.assertEqual(passed, [])

    def test_allowed_request_gets_the_reply_of_wpa_supplicant(self):
        reply = wifi_gate.answer(b"SCAN", lambda c: b"OK\n")
        self.assertEqual(reply, b"OK\n")


class RoundTripTest(unittest.TestCase):
    """Wpa -> gate -> wpa_supplicant over real unix sockets."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="gate", dir="/tmp")
        self.gate = os.path.join(self.dir, "gate")
        self.wpa = os.path.join(self.dir, "wpa")
        self.seen = []

    def fake_wpa_supplicant(self, replies):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.bind(self.wpa)
        self.addCleanup(sock.close)

        def serve():
            for reply in replies:
                data, client = sock.recvfrom(4096)
                self.seen.append(data.decode())
                sock.sendto(reply, client)
        threading.Thread(target=serve, daemon=True).start()

    def start_gate(self, count):
        ready = threading.Event()
        thread = threading.Thread(
            target=wifi_gate.serve, daemon=True,
            kwargs={"gate": self.gate, "group": None, "wpa": self.wpa,
                    "count": count, "ready": ready})
        thread.start()
        ready.wait(2)

    def test_status_passes_and_a_dangerous_command_does_not(self):
        self.fake_wpa_supplicant([b"wpa_state=COMPLETED\nssid=Home\n"])
        self.start_gate(count=2)
        client = Wpa(path=self.gate)
        self.assertEqual(client.status()["ssid"], "Home")
        with self.assertRaises(WpaError):
            client.request("SET pkcs11_module_path /tmp/x.so")
        self.assertEqual(self.seen, ["STATUS"])

    def test_wpa_supplicant_not_running(self):
        self.start_gate(count=1)        # nothing listens on self.wpa
        with self.assertRaises(WpaError) as caught:
            Wpa(path=self.gate).status()
        self.assertIn("not running", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
