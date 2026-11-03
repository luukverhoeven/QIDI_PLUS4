"""Wi-Fi through wpa_supplicant's control protocol, as QIDI's xindi does it.

The Plus4 runs ``wpa_supplicant -c /etc/wpa_supplicant/wpa_supplicant-wlan0
.conf -i wlan0`` with a control socket only root may use: it also takes
commands that make wpa_supplicant load a library as root. plus4screen talks
to plus4-wifi-gate instead (see wifi_gate.py), which passes on only the
commands used here.

Passwords are only sent to wpa_supplicant, never logged.
"""

import codecs
import os
import socket
import tempfile

CTRL = "/run/plus4-wifi/wlan0"       # plus4-wifi-gate
GATE_REFUSED = "FAIL-GATE-REFUSED"
GATE_NO_WIFI = "FAIL-GATE-NO-WIFI"
STRONG = -55             # dBm
GOOD = -70


class WpaError(Exception):
    pass


def unescape(text):
    """wpa_supplicant prints SSIDs with C escapes (\\xNN, \\\\, \\")."""
    try:
        raw = codecs.escape_decode(text.encode("latin-1"))[0]
        return raw.decode("utf-8", "replace")
    except (ValueError, UnicodeError):
        return text


def signal_words(level):
    if level >= STRONG:
        return "strong signal"
    if level >= GOOD:
        return "good signal"
    return "weak signal"


class Wpa:
    def __init__(self, path=CTRL, timeout=4.0):
        self.path = path
        self.timeout = timeout

    def request(self, command):
        local = os.path.join(tempfile.gettempdir(),
                             "plus4screen-wpa-%d" % os.getpid())
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            if os.path.exists(local):
                os.unlink(local)
            sock.bind(local)
            sock.settimeout(self.timeout)
            sock.connect(self.path)
            sock.send(command.encode("utf-8"))
            reply = sock.recv(16384).decode("utf-8", "replace")
        except (PermissionError, FileNotFoundError, ConnectionRefusedError):
            raise WpaError("No access to Wi-Fi control. Run install.sh "
                           "again to set it up.") from None
        except OSError as exc:
            raise WpaError("Wi-Fi control: %s" % exc) from None
        finally:
            sock.close()
            if os.path.exists(local):
                os.unlink(local)
        if reply.startswith(GATE_NO_WIFI):
            raise WpaError("Wi-Fi is not running (wpa_supplicant).")
        if reply.startswith(GATE_REFUSED):
            raise WpaError("Wi-Fi control refused %s."
                           % (command.split(" ", 1)[0] or "the request"))
        return reply

    def ok(self, command):
        reply = self.request(command).strip()
        if reply != "OK":
            raise WpaError("Wi-Fi refused %s: %s"
                           % (command.split()[0], reply))

    def status(self):
        lines = self.request("STATUS").splitlines()
        return dict(line.split("=", 1) for line in lines if "=" in line)

    def scan(self):
        self.request("SCAN")          # FAIL-BUSY: a scan is already running

    def results(self):
        """Networks in range, strongest first, one entry per name."""
        best = {}
        for line in self.request("SCAN_RESULTS").splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) < 5:
                continue
            ssid = unescape(parts[4])
            if not ssid or "\x00" in ssid:
                continue
            level = int(parts[2]) if parts[2].lstrip("-").isdigit() else -100
            flags = parts[3]
            entry = {"ssid": ssid, "signal": level,
                     "secured": any(k in flags for k in ("WPA", "WEP",
                                                          "SAE"))}
            if ssid not in best or level > best[ssid]["signal"]:
                best[ssid] = entry
        return sorted(best.values(), key=lambda n: -n["signal"])

    def known(self):
        """Saved networks: ssid -> network id."""
        known = {}
        for line in self.request("LIST_NETWORKS").splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) >= 2:
                known[unescape(parts[1])] = parts[0]
        return known

    def connect(self, ssid, password=None):
        """Add or update the network and switch to it; saves the config."""
        known = self.known()
        if ssid in known:
            net = known[ssid]
        else:
            net = self.request("ADD_NETWORK").strip()
            if not net.isdigit():
                raise WpaError("Wi-Fi could not add the network: %s" % net)
        self.ok("SET_NETWORK %s ssid %s" % (net,
                                             ssid.encode("utf-8").hex()))
        if password is not None:
            if password:
                self.ok('SET_NETWORK %s psk "%s"' % (net, password))
            else:
                self.ok("SET_NETWORK %s key_mgmt NONE" % net)
        self.ok("ENABLE_NETWORK %s" % net)
        self.ok("SELECT_NETWORK %s" % net)
        return net

    def keep_all(self):
        """After a switch: let wpa_supplicant use every saved network again
        and store the configuration."""
        self.ok("ENABLE_NETWORK all")
        self.ok("SAVE_CONFIG")
