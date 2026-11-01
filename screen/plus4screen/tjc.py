"""Serial protocol of the TJC (Nextion-compatible) touchscreen.

Commands to the screen are ASCII instructions terminated by ``FF FF FF``.
What the screen sends back is decided by the event code in QIDI's layout
(``UI/xindi_800_480.HMI``, see ``tools/hmi_dump.py``):

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
import os
import select
import termios

TERM = b"\xff\xff\xff"

Event = collections.namedtuple("Event", "kind page widget value text raw")
Event.__new__.__defaults__ = (None, None, None, None, b"")

TOUCH = "touch"      # page, widget
VALUE = "value"      # page, widget, value (custom 0x71 frame)
NUMBER = "number"    # value (reply to get)
STRING = "string"    # text (reply to get)
BOOT = "boot"        # screen (re)started
NETTEST = "nettest"  # value: True entered, False left
STATUS = "status"    # value: status/error code

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
        if code == 0x70:
            return Event(STRING, text=frame[1:].decode("utf-8", "replace"),
                         raw=frame)
        return Event(STATUS, value=code, raw=frame)


BAUD = {115200: termios.B115200, 9600: termios.B9600}


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
