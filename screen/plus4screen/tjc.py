"""Serial protocol of the TJC (Nextion-compatible) touchscreen.

Commands to the screen are ASCII instructions terminated by ``FF FF FF``.
What the screen sends back is decided by the event code in QIDI's layout
(``UI/xindi_800_480.HMI``, see ``tools/hmi_dump.py``):

* ``67 <x hi> <x lo> <y hi> <y lo> <1|0> FF FF FF`` - raw touch position
  (press or release), sent after ``sendxy=1``; ``68`` is the same for the
  touch that woke the screen.
* ``65 <page> <widget> FF FF FF`` - a button was released. Buttons print
  this themselves (``prints 0x65,1`` ...), so there is no touch-type byte.
  The standard TJC form with a type byte is accepted as well.
* ``71 <page> <widget> <lo> <hi>`` - a value was set, e.g. a fan slider.
  Five bytes, **no** terminator.
* ``71 <4 bytes LE> FF FF FF`` - standard reply to ``get <number>``.
* ``70 <text> FF FF FF`` - reply to ``get <obj>.txt``.
* ``91`` - one byte, sent by the boot page (``printh 91``).
* ``92`` / ``93`` - one byte, network-test page entered/left.
* Any other ``<code> ... FF FF FF`` - status or error code of the screen.
"""

import collections
import errno
import logging
import os
import select
import termios
import time

TERM = b"\xff\xff\xff"

log = logging.getLogger("plus4screen")

Event = collections.namedtuple("Event", "kind page widget value text raw")
Event.__new__.__defaults__ = (None, None, None, None, b"")

TOUCH = "touch"      # page, widget
VALUE = "value"      # page, widget, value (custom 0x71 frame)
NUMBER = "number"    # value (reply to get)
STRING = "string"    # text (reply to get)
BOOT = "boot"        # screen (re)started
NETTEST = "nettest"  # value: True entered, False left
STATUS = "status"    # value: status/error code
XY = "xy"            # value: (x, y, pressed)

SINGLE_BYTE = {0x91: (BOOT, None), 0x92: (NETTEST, True),
               0x93: (NETTEST, False)}


# First bytes the screen can send: the codes above plus the standard TJC
# status/error codes (0x00-0x24) and reply codes.
KNOWN_CODES = (set(range(0x00, 0x25)) | set(SINGLE_BYTE)
               | {0x65, 0x66, 0x67, 0x68, 0x70, 0x71, 0x86, 0x87, 0x88,
                  0x89, 0xFD, 0xFE})


# Longest frame (without terminator) for codes with a fixed size. Status
# codes are one byte; 0x70 strings may be any length.
FRAME_LEN = {0x65: 4, 0x66: 2, 0x67: 6, 0x68: 6}


def quote(text):
    """Make ``text`` safe inside a TJC string literal."""
    text = str(text).replace("\\", "/").replace('"', "'")
    return text.replace("\r", "").replace("\n", "\\r")


def encode(command):
    return command.encode("utf-8") + TERM


class Decoder:
    """Turns the byte stream from the screen into ``Event`` objects."""

    MAX_FRAME = 256

    def __init__(self):
        self.buf = bytearray()

    def feed(self, data):
        self.buf.extend(data)
        return self._decode(force=False)

    def flush(self):
        """Decode what is left after the line went quiet."""
        return self._decode(force=True)

    def _decode(self, force):
        events = []
        buf = self.buf
        while buf:
            code = buf[0]
            if code not in KNOWN_CODES:
                del buf[0]          # stray terminator byte or garbage
                continue
            if code in SINGLE_BYTE:
                kind, value = SINGLE_BYTE[code]
                events.append(Event(kind, value=value, raw=bytes(buf[:1])))
                del buf[0]
                continue
            if code == 0x71:
                event, used = self._value_frame(force)
                if used == 0:
                    break
                events.append(event)
                del buf[:used]
                continue
            end = buf.find(TERM)
            if end < 0:
                if len(buf) > self.MAX_FRAME:
                    del buf[0]      # garbage, resynchronise
                    continue
                break
            if code != 0x70 and end > FRAME_LEN.get(code, 1):
                del buf[0]          # longer than this code allows: garbage
                continue
            frame = bytes(buf[:end])
            del buf[:end + 3]
            events.append(self._frame(frame))
        return events

    def _value_frame(self, force):
        buf = self.buf
        if len(buf) >= 8 and buf[5:8] == TERM:
            value = int.from_bytes(bytes(buf[1:5]), "little", signed=True)
            return Event(NUMBER, value=value, raw=bytes(buf[:8])), 8
        if len(buf) < 5:
            return None, 0
        tail = bytes(buf[5:8])
        if not force and len(buf) < 8 and TERM.startswith(tail):
            return None, 0          # could still become a get-reply
        return Event(VALUE, page=buf[1], widget=buf[2],
                     value=buf[3] | (buf[4] << 8), raw=bytes(buf[:5])), 5

    @staticmethod
    def _frame(frame):
        code = frame[0]
        if code == 0x65 and len(frame) >= 3:
            return Event(TOUCH, page=frame[1], widget=frame[2], raw=frame)
        if code in (0x67, 0x68) and len(frame) == 6:
            x = frame[1] << 8 | frame[2]
            y = frame[3] << 8 | frame[4]
            return Event(XY, value=(x, y, bool(frame[5])), raw=frame)
        if code == 0x70:
            return Event(STRING, text=frame[1:].decode("utf-8", "replace"),
                         raw=frame)
        return Event(STATUS, value=code, raw=frame)


BAUD = {115200: termios.B115200, 9600: termios.B9600}
if hasattr(termios, "B921600"):         # Linux; used to write screen files
    BAUD[921600] = termios.B921600


class SerialPort:
    """Raw, non-blocking serial port using only the standard library.

    The port is opened with ``O_NOCTTY | O_NONBLOCK`` and ``CLOCAL`` set:
    ``/dev/ttyS1`` on the Plus4 has ``-clocal``, and a plain open blocks
    forever waiting for a carrier signal.
    """

    def __init__(self, path, baud=115200):
        self.fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        attrs = termios.tcgetattr(self.fd)
        iflag, oflag, cflag, lflag, _, _, cc = attrs
        iflag = 0
        oflag = 0
        lflag = 0
        cflag = (cflag & ~(termios.CSIZE | termios.PARENB | termios.CSTOPB
                           | getattr(termios, "CRTSCTS", 0)))
        cflag |= termios.CS8 | termios.CLOCAL | termios.CREAD
        cc[termios.VMIN] = 0
        cc[termios.VTIME] = 0
        speed = BAUD[baud]
        termios.tcsetattr(self.fd, termios.TCSANOW,
                          [iflag, oflag, cflag, lflag, speed, speed, cc])
        termios.tcflush(self.fd, termios.TCIOFLUSH)

    def fileno(self):
        return self.fd

    def write(self, data):
        view = memoryview(data)
        while view:
            try:
                n = os.write(self.fd, view)
                view = view[n:]
            except OSError as exc:
                if exc.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                    raise
                select.select([], [self.fd], [], 1.0)

    def read(self):
        try:
            return os.read(self.fd, 4096)
        except OSError as exc:
            if exc.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                return b""
            raise

    def close(self):
        os.close(self.fd)


def answers(port, timeout=1.0):
    """True if the screen answers ``connect`` at the port's speed."""
    port.write(TERM + b"connect" + TERM)
    termios.tcdrain(port.fd)
    got = bytearray()
    end = time.monotonic() + timeout
    while time.monotonic() < end and b"comok" not in got:
        readable, _, _ = select.select([port], [], [], 0.1)
        if readable:
            got.extend(port.read())
    return b"comok" in got


def open_screen(path, baud=115200, fallback=9600):
    """Open the screen's port at ``baud``.

    A screen file that leaves its speed at the TJC default (9600) is
    switched to ``baud`` for this power cycle with ``baud=``.
    """
    port = SerialPort(path, baud)
    if answers(port):
        return port
    port.close()
    slow = SerialPort(path, fallback)
    if answers(slow):
        log.info("screen answered at %d baud; switching it to %d",
                 fallback, baud)
        slow.write(encode("baud=%d" % baud))
        termios.tcdrain(slow.fd)
        time.sleep(0.2)
    else:
        log.warning("screen does not answer at %d or %d baud", baud,
                    fallback)
    slow.close()
    return SerialPort(path, baud)
