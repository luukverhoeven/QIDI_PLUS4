"""Runs the real main loop against a pseudo-terminal and a stub Moonraker."""

import http.server
import json
import os
import select
import threading
import time
import unittest
import urllib.parse

from plus4screen import __main__ as main_mod

STATUS = {
    "webhooks": {"state": "ready", "state_message": ""},
    "extruder": {"temperature": 210.2, "target": 210.0},
    "heater_bed": {"temperature": 55.0, "target": 55.0},
    "print_stats": {"state": "standby", "filename": ""},
}


class StubMoonraker(http.server.BaseHTTPRequestHandler):
    gcodes = []

    def log_message(self, *args):
        pass

    def _reply(self, result):
        body = json.dumps({"result": result}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)
        url = urllib.parse.urlparse(self.path)
        if url.path == "/printer/objects/query":
            self._reply({"status": STATUS})
        elif url.path == "/printer/gcode/script":
            script = urllib.parse.parse_qs(url.query)["script"][0]
            self.gcodes.append(script)
            self._reply("ok")
        else:
            self._reply("ok")

    def do_GET(self):
        self._reply([])


class EndToEndTest(unittest.TestCase):
    def setUp(self):
        self.http = http.server.ThreadingHTTPServer(("127.0.0.1", 0),
                                                    StubMoonraker)
        threading.Thread(target=self.http.serve_forever, daemon=True).start()
        self.master, self.slave = os.openpty()
        args = main_mod.parse_args([
            "--ui", "qidi", "--port", os.ttyname(self.slave), "--poll", "0.1",
            "--moonraker", "http://127.0.0.1:%d" % self.http.server_port])
        threading.Thread(target=main_mod.run, args=(args,),
                         daemon=True).start()

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()

    def read_until(self, needle, timeout=3.0):
        data = b""
        end = time.monotonic() + timeout
        while needle not in data and time.monotonic() < end:
            if select.select([self.master], [], [], 0.1)[0]:
                data += os.read(self.master, 4096)
        self.assertIn(needle, data)
        return data

    def test_touch_to_gcode(self):
        data = self.read_until(b"n0.val=210\xff\xff\xff")
        self.assertTrue(data.startswith(b"page 3\xff\xff\xff"))
        os.write(self.master, b"\x65\x03\x22\xff\xff\xff")   # Control
        self.read_until(b"page 35\xff\xff\xff")
        os.write(self.master, b"\x65\x23\x0a\xff\xff\xff")   # Home
        end = time.monotonic() + 3
        while "G28" not in StubMoonraker.gcodes and time.monotonic() < end:
            time.sleep(0.05)
        self.assertIn("G28", StubMoonraker.gcodes)
        # A fan slider frame without terminator, decoded after the line
        # goes quiet.
        os.write(self.master, b"\x71\x23\x16\x32\x00")
        end = time.monotonic() + 3
        want = "SET_FAN_SPEED FAN=cooling_fan SPEED=0.50"
        while want not in StubMoonraker.gcodes and time.monotonic() < end:
            time.sleep(0.05)
        self.assertIn(want, StubMoonraker.gcodes)


if __name__ == "__main__":
    unittest.main()
