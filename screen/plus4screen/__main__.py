"""Entry point: ``python3 -m plus4screen [options]``."""

import argparse
import logging
import select
import signal
import sys
import time

from . import __version__
from .app import App, ThreadRunner
from .moonraker import Moonraker
from .tjc import Decoder, SerialPort

QUIET_FLUSH = 0.05   # s of silence before a partial frame is decoded


def parse_args(argv):
    p = argparse.ArgumentParser(
        prog="plus4screen",
        description="Open-source touchscreen program for the QIDI Plus4.")
    p.add_argument("--port", default="/dev/ttyS1",
                   help="serial port of the screen (default: %(default)s)")
    p.add_argument("--moonraker", default="http://127.0.0.1:7125",
                   help="Moonraker URL (default: %(default)s)")
    p.add_argument("--lang", type=int, default=None,
                   help="force the screen language index (2 = English); "
                        "by default the language chosen on the screen is "
                        "kept")
    p.add_argument("--poll", type=float, default=1.0,
                   help="seconds between status updates (default: 1)")
    p.add_argument("--dry-run", action="store_true",
                   help="log G-code and print actions instead of sending "
                        "them; status is still read")
    p.add_argument("-v", "--verbose", action="store_true",
                   help="also log every command sent to the screen")
    p.add_argument("--version", action="version", version=__version__)
    return p.parse_args(argv)


def run(args):
    port = SerialPort(args.port)
    runner = ThreadRunner()
    app = App(port.write, Moonraker(args.moonraker), runner, lang=args.lang,
              dry_run=args.dry_run)
    decoder = Decoder()
    logging.getLogger("plus4screen").info(
        "started on %s, Moonraker %s%s", args.port, args.moonraker,
        " (dry run)" if args.dry_run else "")

    app.poll()
    app.start()
    next_poll = time.monotonic() + args.poll
    last_rx = 0.0
    while True:
        now = time.monotonic()
        timeout = max(0.0, min(next_poll - now,
                               QUIET_FLUSH if decoder.buf else 0.2))
        readable, _, _ = select.select([port], [], [], timeout)
        now = time.monotonic()
        events = []
        if readable:
            data = port.read()
            if data:
                last_rx = now
                events = decoder.feed(data)
        elif decoder.buf and now - last_rx >= QUIET_FLUSH:
            events = decoder.flush()
        for event in events:
            app.handle(event)
        runner.drain()
        if now >= next_poll:
            app.poll()
            next_poll = now + args.poll


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s")
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        run(args)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
