import unittest
from unittest import mock

from plus4screen import pages as P
from plus4screen import pictures, tjc
from plus4screen.app import App
from plus4screen.printer import PrinterState

from test_app import FakeMoonraker, ManualRunner, status

PICTURE = "0`0" * 500          # 1500 characters: two write commands


class PictureMoonraker(FakeMoonraker):
    def __init__(self):
        super().__init__()
        self.job = {"filename": "sub/b.gcode", "exists": True}
        self.downloads = []

    def last_job(self):
        return self.job

    def metadata(self, filename):
        return {"estimated_time": 3600, "thumbnails": [
            {"width": 96, "relative_path": ".thumbs/b-96x96.png"},
            {"width": 272, "relative_path": ".thumbs/b-272x272.png"}]}

    def download(self, root, path):
        self.downloads.append((root, path))
        return b"png"


class PicturesTest(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(pictures, "make_colpic",
                                    return_value=PICTURE)
        self.make = patcher.start()
        self.addCleanup(patcher.stop)
        self.out = []
        self.mr = PictureMoonraker()
        self.runner = ManualRunner()
        self.app = App(self.out.append, self.mr, self.runner)
        self.app.update(PrinterState(status()))

    def sent(self):
        cmds = [b[:-3].decode() for b in self.out]
        self.out.clear()
        return cmds

    def touch(self, page, widget):
        self.app.handle(tjc.Event(tjc.TOUCH, page=page, widget=widget))

    def test_main_shows_last_print_once(self):
        self.app.start()
        cmds = self.sent()
        self.assertIn("cp0.close()", cmds)
        self.assertEqual(len([c for c in cmds if c.startswith("cp0.write")]),
                         2)
        self.assertIn("vis q0,1", cmds)
        self.assertEqual(self.mr.downloads,
                         [("gcodes", "sub/.thumbs/b-272x272.png")])
        self.app.goto(P.CONTROL)
        self.app.goto(P.MAIN)
        self.assertFalse([c for c in self.sent() if c.startswith("cp0.")])
        self.make.assert_called_once()

    def test_tap_on_last_print_opens_preview(self):
        self.app.start()
        self.touch(P.MAIN, P.W_LAST_PRINT)
        self.assertEqual(self.app.page, P.PREVIEW)
        self.assertEqual(self.app.selected, "sub/b.gcode")

    def test_main_clears_stale_picture_without_history(self):
        self.mr.job = None
        self.app.start()
        cmds = self.sent()
        self.assertIn("cp0.close()", cmds)
        self.assertIn("vis q0,0", cmds)
        self.app.goto(P.CONTROL)
        self.app.goto(P.MAIN)
        self.assertNotIn("cp0.close()", self.sent())

    def test_preview_fills_cp0_text_and_draws(self):
        self.app.selected = "sub/b.gcode"
        self.app.goto(P.PREVIEW)
        cmds = self.sent()
        first_close = cmds.index("cp0.close()")
        self.assertLess(first_close, cmds.index('add.txt="%s"'
                                                 % PICTURE[:1024]))
        self.assertIn("cp0_text.txt=cp0_text.txt+add.txt", cmds)
        self.assertIn("cp0.write(cp0_text.txt)", cmds)
        self.assertEqual(cmds[-1], "vis cp0,1")
        self.assertEqual(self.app.cp0_text_file, "sub/b.gcode")

    def test_printing_redraws_when_preview_text_is_other_file(self):
        self.app.update(PrinterState(status("printing")))
        self.app.goto(P.PRINTING)
        cmds = self.sent()
        self.assertIn('preview.cp0_text.txt=""', cmds)
        self.assertIn("cp0.write(preview.cp0_text.txt)", cmds)
        self.app.goto(P.MAIN)
        self.app.goto(P.PRINTING)
        self.assertNotIn("cp0.write(preview.cp0_text.txt)", self.sent())

    def test_pick_thumbnail_prefers_272(self):
        self.assertEqual(pictures.pick_thumbnail(self.mr.metadata("x")),
                         ".thumbs/b-272x272.png")
        self.assertIsNone(pictures.pick_thumbnail({}))


if __name__ == "__main__":
    unittest.main()
