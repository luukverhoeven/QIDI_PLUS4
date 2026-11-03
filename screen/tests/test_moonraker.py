import io
import unittest

from plus4screen.moonraker import MAX_DOWNLOAD, Moonraker, MoonrakerError


class ListFilesTest(unittest.TestCase):
    def test_skips_hidden_folders_and_non_gcode(self):
        mr = Moonraker()
        mr._request = lambda *a, **k: [
            {"path": ".cache/a.gcode", "modified": 5},
            {"path": ".plr/b.gcode", "modified": 4},
            {"path": "a.gcode", "modified": 3},
            {"path": "USB/c.gcode", "modified": 6},
            {"path": "notes.txt", "modified": 7},
        ]
        self.assertEqual([f["path"] for f in mr.list_files()],
                         ["USB/c.gcode", "a.gcode"])

    def test_metadata_returns_result(self):
        mr = Moonraker()
        mr._request = lambda *a, **k: {"estimated_time": 600}
        self.assertEqual(mr.metadata("a.gcode"), {"estimated_time": 600})


class DownloadTest(unittest.TestCase):
    class Opener:
        def __init__(self, size):
            self.size = size

        def open(self, url, timeout=None):
            return io.BytesIO(b"x" * self.size)

    def test_returns_the_file(self):
        mr = Moonraker()
        mr.opener = self.Opener(100)
        self.assertEqual(mr.download("gcodes", ".thumbs/a.png"), b"x" * 100)

    def test_refuses_a_file_larger_than_the_limit(self):
        mr = Moonraker()
        mr.opener = self.Opener(MAX_DOWNLOAD + 1)
        with self.assertRaises(MoonrakerError):
            mr.download("gcodes", ".thumbs/a.png")


if __name__ == "__main__":
    unittest.main()
