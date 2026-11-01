import unittest

from plus4screen.moonraker import Moonraker


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


if __name__ == "__main__":
    unittest.main()
