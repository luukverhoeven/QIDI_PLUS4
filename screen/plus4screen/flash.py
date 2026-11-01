"""Write a screen file (.tft) to the touchscreen over its serial port.

    python3 -m plus4screen.flash plus4ui.tft
    python3 -m plus4screen.flash /path/to/QIDI.tft      (back to stock)

Stop the program that uses the port first (makerbase-client or
plus4screen). The upload is the one QIDI's xindi uses: ``whmi-wri
<size>,<baud>,0``, then the file in 4096-byte blocks, each acknowledged by
the screen with 0x05. A failed upload leaves the screen waiting for a new
one; run this again.
"""

import argparse
import os
import select
import sys
import time

from .tjc import TERM, SerialPort

BLOCK = 4096
ACK = 0x05
ACK_TIMEOUT = 5.0            # s per block
START_TIMEOUT = 10.0         # s for the screen to accept the upload


def wait_for(port, byte, timeout):
    """Wait for ``byte``; return what else arrived, or None on timeout."""
    end = time.monotonic() + timeout
    seen = bytearray()
    while time.monotonic() < end:
        readable, _, _ = select.select([port], [], [],
                                       max(0.0, end - time.monotonic()))
        if not readable:
            continue
        data = port.read()
        if byte in data:
            return bytes(seen + data[:data.index(byte)])
        seen.extend(data)
    return None


def connect(port):
    """Ask the screen who it is; returns its answer or ''."""
    port.write(TERM + b"connect" + TERM)
    time.sleep(0.3)
    answer = bytearray()
    end = time.monotonic() + 1.0
    while time.monotonic() < end:
        readable, _, _ = select.select([port], [], [], 0.1)
        if readable:
            answer.extend(port.read())
    text = answer.decode("latin-1")
    return text[text.find("comok"):].split("\xff")[0] if "comok" in text \
        else ""


def flash(path, port_path="/dev/ttyS1", baud=115200, out=sys.stdout):
    data = open(path, "rb").read()
    port = SerialPort(port_path, 115200)
    who = connect(port)
    out.write("screen: %s\n" % (who or "no answer to connect"))
    port.write(b"whmi-wri %d,%d,0" % (len(data), baud) + TERM)
    if baud != 115200:
        time.sleep(0.1)
        port.close()
        port = SerialPort(port_path, baud)
    if wait_for(port, bytes([ACK]), START_TIMEOUT) is None:
        raise SystemExit("the screen did not accept the upload")
    blocks = (len(data) + BLOCK - 1) // BLOCK
    started = time.monotonic()
    for index in range(blocks):
        port.write(data[index * BLOCK:(index + 1) * BLOCK])
        if wait_for(port, bytes([ACK]), ACK_TIMEOUT) is None:
            raise SystemExit("no answer after block %d of %d"
                             % (index + 1, blocks))
        if index % 32 == 0 or index == blocks - 1:
            out.write("\r%3d%%  %d of %d KiB  %ds" % (
                100 * (index + 1) // blocks, (index + 1) * BLOCK // 1024,
                len(data) // 1024, time.monotonic() - started))
            out.flush()
    out.write("\ndone in %ds; the screen restarts with the new file\n"
              % (time.monotonic() - started))
    port.close()


def main(argv=None):
    p = argparse.ArgumentParser(prog="plus4screen.flash",
                                description=__doc__.splitlines()[0])
    p.add_argument("tft", help="screen file to write")
    p.add_argument("--port", default="/dev/ttyS1")
    p.add_argument("--baud", type=int, default=115200,
                   choices=(115200, 921600),
                   help="transfer speed (default: %(default)s, as xindi)")
    args = p.parse_args(argv)
    if not os.path.isfile(args.tft):
        p.error("%s does not exist" % args.tft)
    flash(args.tft, args.port, args.baud)
    return 0


if __name__ == "__main__":
    sys.exit(main())
