import struct
import unittest
import zlib

from plus4screen import images


def chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", zlib.crc32(kind + data)))


def png_header(width, height):
    """A PNG that declares its size but holds almost no picture data."""
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(b"")) + chunk(b"IEND", b""))


try:
    import PIL  # noqa: F401  (Pillow is on the printer)
    HAVE_PILLOW = True
except ImportError:
    HAVE_PILLOW = False


class SizeTest(unittest.TestCase):
    def test_thumbnail_sizes_pass(self):
        images.check_size(380, 380)
        images.check_size(images.MAX_SIDE, images.MAX_SIDE)

    def test_huge_pictures_are_refused(self):
        for size in ((images.MAX_SIDE + 1, 10), (10, 30000)):
            with self.assertRaises(ValueError):
                images.check_size(*size)

    @unittest.skipUnless(HAVE_PILLOW, "needs Pillow")
    def test_size_is_read_from_the_header_only(self):
        # Pillow's own limit lets 5000 x 5000 through: 100 MB as RGBA.
        with self.assertRaises(ValueError):
            images.open_checked(png_header(5000, 5000))
        with self.assertRaises(Exception):       # Pillow's own refusal
            images.open_checked(png_header(30000, 30000))
        self.assertEqual(images.open_checked(png_header(96, 96)).size,
                         (96, 96))


if __name__ == "__main__":
    unittest.main()
