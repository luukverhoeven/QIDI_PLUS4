"""Allowlist between plus4screen's Wi-Fi screen and wpa_supplicant.

wpa_supplicant's control socket takes any command, including settings that
make it load a library as root (``SET pkcs11_module_path`` and the like),
so only root may use it. This small service runs as root and passes on
just the commands the Wi-Fi screen sends, with checked arguments; anything
else is answered with FAIL-GATE-REFUSED and never reaches wpa_supplicant.

install.sh copies this file to /usr/local/lib/plus4screen (owned by root,
so the user running plus4screen cannot change it) and starts it with
plus4-wifi-gate.service. Standard library only: it imports nothing from
plus4screen. Passwords are passed on, never logged.
"""

import grp
import logging
import os
import re
import socket
import sys
import time

WPA = "/var/run/wpa_supplicant/wlan0"
GATE = "/run/plus4-wifi/wlan0"
GROUP = "netdev"             # may use the gate; mks is a member
TIMEOUT = 4.0                # s to wait for wpa_supplicant
CLIENT_TIMEOUT = 2.0         # s a client may take for its whole request
MAX_REQUEST = 256            # bytes
REFUSED = "FAIL-GATE-REFUSED"
NO_WIFI = "FAIL-GATE-NO-WIFI"

NET = r"[0-9]{1,4}"
ALLOWED = [re.compile(pattern) for pattern in (
    r"STATUS",
    r"SCAN",
    r"SCAN_RESULTS",
    r"LIST_NETWORKS",
    r"ADD_NETWORK",
    r"SAVE_CONFIG",
    r"ENABLE_NETWORK (?:all|%s)" % NET,
    r"SELECT_NETWORK %s" % NET,
    r"SET_NETWORK %s ssid (?:[0-9a-f]{2}){1,32}" % NET,     # hex, 1-32 bytes
    r'SET_NETWORK %s psk "[ -~]{8,63}"' % NET,              # WPA passphrase
    r"SET_NETWORK %s key_mgmt NONE" % NET,                  # open network
)]

log = logging.getLogger("plus4-wifi-gate")


def allowed(command):
    return any(pattern.fullmatch(command) for pattern in ALLOWED)


def forward(command, wpa=WPA, local_dir=os.path.dirname(GATE)):
    """Send one command to wpa_supplicant and return its reply."""
    local = os.path.join(local_dir, "client-%d" % os.getpid())
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        if os.path.exists(local):
            os.unlink(local)
        sock.bind(local)
        sock.settimeout(TIMEOUT)
        sock.connect(wpa)
        sock.send(command.encode("ascii"))
        return sock.recv(16384)
    except OSError as exc:
        log.warning("wpa_supplicant: %s", exc)
        return NO_WIFI.encode()
    finally:
        sock.close()
        if os.path.exists(local):
            os.unlink(local)


def answer(data, forward=forward):
    """The reply to one request."""
    command = None
    if len(data) <= MAX_REQUEST:
        try:
            command = data.decode("ascii")
        except UnicodeDecodeError:
            pass
    if command is None or not allowed(command):
        word = data.split(b" ", 1)[0][:32].decode("ascii", "replace")
        log.warning("refused: %s", word)
        return REFUSED.encode()
    return forward(command)


def read_request(conn, timeout=CLIENT_TIMEOUT, clock=time.monotonic):
    """Up to MAX_REQUEST + 1 bytes, until the client shuts its side. The
    whole request must arrive within ``timeout``, so a client sending a
    byte now and then cannot hold the gate."""
    end = clock() + timeout
    data = b""
    while len(data) <= MAX_REQUEST:
        left = end - clock()
        if left <= 0:
            raise socket.timeout("request took too long")
        conn.settimeout(left)
        chunk = conn.recv(MAX_REQUEST + 1 - len(data))
        if not chunk:
            break
        data += chunk
    return data


def serve(gate=GATE, group=GROUP, wpa=WPA, count=None, ready=None):
    """Answer requests on the ``gate`` socket, one per connection.

    The client sends a command and shuts its side; the reply goes back on
    the same connection, so root never sends anything to a path a client
    chose. ``count`` ends the loop after that many connections (tests).
    """
    os.umask(0o077)
    if os.path.exists(gate):
        os.unlink(gate)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(gate)
    if group is not None:
        os.chown(gate, 0, grp.getgrnam(group).gr_gid)
    os.chmod(gate, 0o660 if group is not None else 0o600)
    sock.listen(4)
    if ready is not None:
        ready.set()
    local_dir = os.path.dirname(gate)
    try:
        while count is None or count > 0:
            conn, _ = sock.accept()
            if count is not None:
                count -= 1
            with conn:
                try:
                    reply = answer(read_request(conn),
                                   lambda c: forward(c, wpa, local_dir))
                    conn.settimeout(CLIENT_TIMEOUT)
                    conn.sendall(reply)
                except OSError as exc:
                    log.warning("request failed: %s", exc)
    finally:
        sock.close()


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(levelname)s %(message)s")
    log.info("passing allowed commands from %s to %s", GATE, WPA)
    serve()


if __name__ == "__main__":
    main()
