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
import re
import select
import struct
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
    end_transfer(port)          # a restart may have left one running
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


# twfile: writes a file to the screen's file system (here: JPEG thumbnails
# into ram/), as QIDI's xindi does. Each packet is a 12-byte header (magic,
# packet number, length + 2), up to 2034 data bytes and their CRC-16/MODBUS,
# low byte first. The screen answers 0x05 per packet and 0xFD at the end.
TWFILE_MAGIC = bytes.fromhex("3aa1bb447ffffe")
TWFILE_CHUNK = 2034
TWFILE_ABORT = TWFILE_MAGIC + bytes.fromhex("00ffff0000")
SENDME_REPLY = re.compile(rb"\x66.\xff\xff\xff", re.S)


def crc16_modbus(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def twfile_packets(data):
    for number, start in enumerate(range(0, len(data), TWFILE_CHUNK)):
        chunk = data[start:start + TWFILE_CHUNK]
        yield (TWFILE_MAGIC + b"\x01"
               + struct.pack("<HH", number, len(chunk) + 2) + chunk
               + struct.pack("<H", crc16_modbus(chunk)))


def _wait_for(port, codes, timeout, seen):
    """Read until one of ``codes`` arrives; return it, or None."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        readable, _, _ = select.select([port], [], [], 0.05)
        if readable:
            data = port.read()
            seen.extend(data)
            for code in codes:
                if code in data:
                    return code
    return None


def sync(port, timeout=3.0):
    """Wait until the screen has carried out every command sent so far.

    The screen answers in order, so whatever arrives before the answer to
    ``sendme`` (for example a late 0x06 from ``delfile`` while the screen
    is still drawing) is dropped. Returns False if no answer came.
    """
    port.write(encode("sendme"))
    termios.tcdrain(port.fd)
    got = bytearray()
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        readable, _, _ = select.select([port], [], [], 0.05)
        if readable:
            got.extend(port.read())
            if SENDME_REPLY.search(got):
                return True
    log.warning("screen did not answer sendme (got %s)",
                bytes(got).hex() or "nothing")
    return False


def end_transfer(port):
    """End a file transfer the screen may be in.

    While a transfer runs, the screen takes everything as file data and
    draws nothing. A pause of 20 ms marks a packet boundary; the abort
    packet then ends the transfer (0xFD). Without a transfer the abort
    bytes are a bad command, closed by TERM so the next command is clean.
    A late 0xFE means the transfer only started now: abort once more.
    """
    for _ in range(2):
        time.sleep(0.03)
        port.write(TWFILE_ABORT)
        termios.tcdrain(port.fd)
        answer = _wait_for(port, (0xFD, 0xFE), 0.3, bytearray())
        if answer == 0xFD:
            break
        if answer is None:
            port.write(TERM)
            time.sleep(0.05)
            break
    termios.tcflush(port.fd, termios.TCIFLUSH)


def write_file(port, name, data):
    """Replace ``name`` on the screen with ``data``; True when written."""
    # Touch reports would mix with the acknowledgements.
    port.write(encode("sendxy=0"))
    port.write(encode('delfile "%s"' % name))    # 0x06 if it is missing
    try:
        if not sync(port):
            end_transfer(port)
            return False
        return twfile(port, name, data)
    finally:
        port.write(encode("sendxy=1"))


def twfile(port, name, data, timeout=2.0):
    """Write ``data`` to the screen as ``name`` (e.g. "ram/t0.jpg").

    Touch reports must be off (``sendxy=0``): their bytes could look like
    acknowledgements. Returns False if the screen stopped answering.
    """
    port.write(encode('twfile "%s",%d' % (name, len(data))))
    termios.tcdrain(port.fd)
    seen = bytearray()
    # 0xFE: file created, send the data. 0x06 frames may come first (seen
    # while the screen repaints the page), so only a missing 0xFE means the
    # file was refused, e.g. no room: the screen file needs a RAM file
    # system, a project setting of the TJC editor.
    ready = _wait_for(port, (0xFE,), 1.0, seen)
    if ready is None:
        log.warning("twfile %s: screen did not accept the file (got %s)",
                    name, bytes(seen).hex() or "nothing")
        end_transfer(port)      # in case the 0xFE comes after all
        return False
    for number, packet in enumerate(twfile_packets(data)):
        seen = bytearray()
        port.write(packet)
        if _wait_for(port, (0x05, 0xFD), timeout, seen) is None:
            log.warning("twfile %s: no answer to packet %d (got %s)",
                        name, number, bytes(seen).hex() or "nothing")
            end_transfer(port)
            return False
    return True
