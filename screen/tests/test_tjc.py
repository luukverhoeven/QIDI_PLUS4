import os
import select
import unittest

from plus4screen import tjc
from plus4screen.tjc import Decoder, SerialPort


class EncodeTest(unittest.TestCase):
    def test_terminator(self):
        self.assertEqual(tjc.encode("page 3"), b"page 3\xff\xff\xff")

    def test_utf8(self):
        self.assertEqual(tjc.encode('t0.txt="\u2103"'),
                         b't0.txt="\xe2\x84\x83"\xff\xff\xff')

    def test_quote(self):
        self.assertEqual(tjc.quote('a "b"\nc\\d'), "a 'b'\\rc/d")


class DecoderTest(unittest.TestCase):
    def test_button(self):
        ev, = Decoder().feed(b"\x65\x23\x0d\xff\xff\xff")
        self.assertEqual((ev.kind, ev.page, ev.widget), (tjc.TOUCH, 35, 13))

    def test_standard_touch_with_type_byte(self):
        ev, = Decoder().feed(b"\x65\x03\x22\x01\xff\xff\xff")
        self.assertEqual((ev.kind, ev.page, ev.widget), (tjc.TOUCH, 3, 34))

    def test_split_frames(self):
        d = Decoder()
        self.assertEqual(d.feed(b"\x65\x23"), [])
        self.assertEqual(d.feed(b"\x0d\xff"), [])
        ev, = d.feed(b"\xff\xff")
        self.assertEqual(ev.widget, 13)

    def test_several_frames(self):
        evs = Decoder().feed(b"\x65\x03\x22\xff\xff\xff\x91"
                             b"\x65\x23\x06\xff\xff\xff")
        self.assertEqual([e.kind for e in evs],
                         [tjc.TOUCH, tjc.BOOT, tjc.TOUCH])

    def test_fan_value_frame_has_no_terminator(self):
        evs = Decoder().feed(b"\x71\x23\x16\x50\x00\x65\x23\x16\xff\xff\xff")
        self.assertEqual(evs[0][:4], (tjc.VALUE, 35, 22, 80))
        self.assertEqual(evs[1].kind, tjc.TOUCH)

    def test_fan_value_frame_alone_needs_flush(self):
        d = Decoder()
        self.assertEqual(d.feed(b"\x71\x23\x17\x64\x00"), [])
        ev, = d.flush()
        self.assertEqual(ev[:4], (tjc.VALUE, 35, 23, 100))

    def test_get_number_reply(self):
        ev, = Decoder().feed(b"\x71\x02\x00\x00\x00\xff\xff\xff")
        self.assertEqual((ev.kind, ev.value), (tjc.NUMBER, 2))

    def test_get_number_reply_split(self):
        d = Decoder()
        self.assertEqual(d.feed(b"\x71\x01\x00\x00\x00\xff"), [])
        ev, = d.feed(b"\xff\xff")
        self.assertEqual((ev.kind, ev.value), (tjc.NUMBER, 1))

    def test_get_string_reply(self):
        ev, = Decoder().feed(b"\x70215\xff\xff\xff")
        self.assertEqual((ev.kind, ev.text), (tjc.STRING, "215"))

    def test_status_and_stray_bytes(self):
        evs = Decoder().feed(b"\xff\x1a\xff\xff\xff\x92\x93")
        self.assertEqual([(e.kind, e.value) for e in evs],
                         [(tjc.STATUS, 0x1A), (tjc.NETTEST, True),
                          (tjc.NETTEST, False)])

    def test_garbage_is_dropped(self):
        d = Decoder()
        d.feed(b"\x20" * 300)
        ev, = d.feed(b"\x65\x03\x01\xff\xff\xff")
        self.assertEqual(ev.widget, 1)


class SerialPortTest(unittest.TestCase):
    def test_pty_round_trip(self):
        master, slave = os.openpty()
        port = SerialPort(os.ttyname(slave))
        try:
            port.write(tjc.encode("page 35"))
            select.select([master], [], [], 1)
            self.assertEqual(os.read(master, 100), b"page 35\xff\xff\xff")
            os.write(master, b"\x65\x23\x0d\xff\xff\xff")
            select.select([port], [], [], 1)
            ev, = Decoder().feed(port.read())
            self.assertEqual(ev.widget, 13)
            self.assertEqual(port.read(), b"")      # non-blocking
        finally:
            port.close()
            os.close(master)
            os.close(slave)


if __name__ == "__main__":
    unittest.main()
