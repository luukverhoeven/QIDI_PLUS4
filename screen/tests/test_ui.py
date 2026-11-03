"""plus4screen's own interface (plus4screen/ui) against a fake printer."""

import os
import tempfile
import unittest
from unittest import mock

from plus4screen import tjc
from plus4screen.ui.app import UIApp
from plus4screen.ui.layout import Layout
from plus4screen.ui.text import BG, RED, fit, lines

LAYOUT = Layout.load()


def status(**over):
    st = {
        "webhooks": {"state": "ready", "state_message": ""},
        "extruder": {"temperature": 25.0, "target": 0.0},
        "heater_bed": {"temperature": 24.0, "target": 0.0},
        "heater_generic chamber": {"temperature": 23.0, "target": 0.0},
        "print_stats": {"state": "standby", "filename": ""},
        "output_pin caselight": {"value": 0.0},
        "toolhead": {"position": [10.0, 20.0, 30.0, 0.0],
                     "homed_axes": "xyz"},
    }
    st.update(over)
    return st


class FakeMoonraker:
    def __init__(self):
        self.status = status()
        self.scripts = []
        self.calls = []
        self.files = [{"path": "a.gcode", "modified": 3},
                      {"path": "USB/b.gcode", "modified": 2}]

    def query(self, objects):
        return self.status

    def gcode(self, script):
        self.scripts.append(script)

    def list_files(self):
        return self.files

    def metadata(self, filename):
        return {"estimated_time": 3600, "filament_weight_total": 12}

    def last_job(self):
        return None

    def system_info(self):
        return {"network": {}}

    def __getattr__(self, name):
        def call(*args):
            self.calls.append(name)
        return call


class SyncRunner:
    def submit(self, fn, on_done=None):
        self.spawn(fn, on_done)

    def spawn(self, fn, on_done=None):
        try:
            result, error = fn(), None
        except Exception as exc:     # mirrors ThreadRunner
            result, error = None, exc
        if on_done:
            on_done(result, error)


class LastJobRetryTest(unittest.TestCase):
    def test_last_print_is_asked_again_after_an_error(self):
        mr = FakeMoonraker()
        calls = []

        def last_job():
            calls.append(1)
            if len(calls) == 1:
                raise OSError("Connection refused")
            return {"filename": "a.gcode", "status": "completed"}
        mr.last_job = last_job
        app = UIApp(lambda d: None, mr, SyncRunner(), LAYOUT,
                    prefs_path=os.path.join(tempfile.mkdtemp(), "p.json"))
        app.poll()
        app.poll()
        self.assertEqual(len(calls), 2)
        self.assertEqual(app.screens["home"].last["filename"], "a.gcode")


class DeferredRunner(SyncRunner):
    """Keeps calls until run_all(), like the threads on the printer."""

    def __init__(self):
        self.pending = []

    def spawn(self, fn, on_done=None):
        self.pending.append((fn, on_done))

    def run_all(self):
        while self.pending:
            fn, on_done = self.pending.pop(0)
            SyncRunner.spawn(self, fn, on_done)


class UITest(unittest.TestCase):
    def setUp(self):
        self.sent = []
        self.mr = FakeMoonraker()
        self.now = [1000.0]
        prefs = os.path.join(tempfile.mkdtemp(), "prefs.json")
        self.app = UIApp(self.write, self.mr, SyncRunner(), LAYOUT,
                         prefs_path=prefs, clock=lambda: self.now[0])
        self.app.poll()
        self.app.start()
        # The screen answers "get sys2" with the id of its screen file.
        self.app.handle(tjc.Event(tjc.NUMBER, value=LAYOUT.screen_id))
        self.sent.clear()

    def write(self, data):
        self.sent.extend(p.decode("utf-8") for p in data.split(tjc.TERM)
                         if p)

    def tap(self, hit_id, release_on=None):
        x, y, w, h = self.app.canvas.screen.hit(hit_id).rect
        self.app.on_touch(x + w // 2, y + h // 2, True)
        if release_on:
            x, y, w, h = self.app.canvas.screen.hit(release_on).rect
        self.app.on_touch(x + w // 2, y + h // 2, False)

    # Layout -----------------------------------------------------------------

    def test_layout_has_every_screen(self):
        for name in self.app.screens:
            screen = LAYOUT[name]
            self.assertIsNotNone(screen.bg)
            ids = [h.id for h in screen.hits]
            self.assertEqual(len(ids), len(set(ids)), name)

    def test_start_turns_on_touch_positions_and_draws_home(self):
        self.app.start()
        bg = LAYOUT["home"].bg
        self.assertEqual(self.sent[:8], [
            "bkcmd=2", "sendxy=1", "dim=80", "get sys2", "page 1",
            "vis 255,0", "page1.pic=%d" % bg, "pic 0,0,%d" % bg])
        self.assertEqual(self.app.current, "home")

    # Touch ------------------------------------------------------------------

    def test_tap_presses_then_runs_the_action(self):
        self.tap("home_all")
        pressed = LAYOUT["home"].pressed
        crops = [c for c in self.sent if c.startswith("xpic")]
        self.assertTrue(crops[0].endswith(",%d" % pressed))
        self.assertTrue(crops[-1].endswith(",%d" % LAYOUT["home"].bg))
        self.assertEqual(self.mr.scripts, ["G28"])

    def test_sliding_off_a_button_cancels_it(self):
        self.tap("home_all", release_on="preheat")
        self.assertEqual(self.mr.scripts, [])

    def test_navigation_rail(self):
        self.tap("nav_files")
        self.assertEqual(self.app.current, "files")
        self.assertIn("pic 0,0,%d" % LAYOUT["files"].bg, self.sent)

    def test_refresh_only_sends_changes(self):
        self.app.poll()
        self.sent.clear()
        self.app.poll()
        self.assertEqual(self.sent, [])

    # Keypad -----------------------------------------------------------------

    def test_keypad_sets_a_heater(self):
        self.tap("temp_nozzle")
        self.assertEqual(self.app.current, "keypad")
        for key in ("k2", "k1", "k0", "ok"):
            self.tap(key)
        self.assertEqual(self.mr.scripts, ["M104 S210"])
        self.assertEqual(self.app.current, "home")

    def test_keypad_refuses_values_out_of_range(self):
        self.tap("temp_bed")
        for key in ("k5", "k0", "k0", "ok"):
            self.tap(key)
        self.assertEqual(self.mr.scripts, [])
        self.assertEqual(self.app.current, "keypad")
        self.assertTrue(any(",%d," % RED in c for c in self.sent
                            if c.startswith("xstr")))

    def test_keypad_decimals_and_sign(self):
        self.app.show("printing")
        self.tap("set_zoffset")
        for key in ("k0", "kdot", "k0", "k5", "ksign", "ok"):
            self.tap(key)
        self.assertEqual(self.mr.scripts,
                         ["SET_GCODE_OFFSET Z=-0.050 MOVE=1"])

    # Screens ----------------------------------------------------------------

    def test_jog_uses_the_selected_step(self):
        self.app.show("move")
        self.tap("step50")
        self.tap("y_plus")
        self.assertEqual(self.mr.scripts, ["G91\nG1 Y50 F6000\nG90"])

    def test_extrude_needs_a_hot_nozzle(self):
        self.app.show("move")
        self.tap("extrude")
        self.assertEqual(self.mr.scripts, [])
        self.assertEqual(self.app.current, "message")

    def test_filament_load_uses_the_chosen_material(self):
        self.app.show("filament")
        self.tap("mat_pla")
        self.tap("load")
        self.assertEqual(self.mr.scripts, ["LOAD_FILAMENT TEMP=220"])

    def test_files_split_local_and_usb(self):
        self.app.show("files")
        texts = " ".join(self.sent)
        self.assertIn('"a"', texts)
        self.assertNotIn('"b"', texts)
        # Unused cards are painted over.
        self.assertIn("fill %d,%d,%d,%d,%d" % (
            tuple(LAYOUT["files"].hit("file1").rect) + (BG,)), self.sent)
        self.tap("tab_usb")
        self.assertIn('"b"', " ".join(self.sent))

    def test_print_start_switches_to_the_print_screen(self):
        self.mr.status = status(print_stats={"state": "printing",
                                             "filename": "a.gcode"})
        self.app.poll()
        self.assertEqual(self.app.current, "printing")

    def test_emergency_stop_asks_first(self):
        self.tap("estop")
        self.assertEqual(self.app.current, "confirm")
        self.assertEqual(self.mr.calls, [])
        self.tap("yes")
        self.assertEqual(self.mr.calls, ["emergency_stop"])

    def test_klipper_error_is_shown(self):
        def fail(script):
            raise RuntimeError("Must home axis first")
        self.mr.gcode = fail
        self.tap("home_all")
        self.assertEqual(self.app.current, "message")
        self.assertIn("Must home axis first", " ".join(self.sent))

    # Sleep ------------------------------------------------------------------

    def test_screen_sleeps_and_the_waking_touch_does_nothing(self):
        self.now[0] += 5 * 60 + 1
        self.app.poll()
        self.assertIn("dim=0", self.sent)
        self.tap("home_all")
        self.assertIn("dim=80", self.sent)
        self.assertEqual(self.mr.scripts, [])
        self.tap("home_all")
        self.assertEqual(self.mr.scripts, ["G28"])


    # Review findings ------------------------------------------------------

    def printing(self):
        self.mr.status = status(print_stats={"state": "printing",
                                             "filename": "a.gcode"})
        self.app.poll()

    def test_dot_first_starts_a_new_number(self):
        self.mr.status = status(gcode_move={"homing_origin": [0, 0, -0.05,
                                                              0]})
        self.app.poll()
        self.app.show("printing")
        self.tap("set_zoffset")
        for key in ("kdot", "k1", "ok"):
            self.tap(key)
        self.assertEqual(self.app.current, "printing")
        self.assertEqual(self.mr.scripts,
                         ["SET_GCODE_OFFSET Z=0.100 MOVE=1"])

    def test_first_digit_drops_the_old_sign(self):
        self.mr.status = status(gcode_move={"homing_origin": [0, 0, -0.05,
                                                              0]})
        self.app.poll()
        self.app.show("printing")
        self.tap("set_zoffset")
        for key in ("k0", "kdot", "k1", "ok"):
            self.tap(key)
        self.assertEqual(self.mr.scripts,
                         ["SET_GCODE_OFFSET Z=0.100 MOVE=1"])

    def test_big_z_offset_change_asks_first(self):
        self.app.show("printing")
        self.tap("set_zoffset")
        for key in ("k1", "ok"):
            self.tap(key)
        self.assertEqual(self.app.current, "confirm")
        self.assertEqual(self.mr.scripts, [])
        self.tap("yes")
        self.assertEqual(self.mr.scripts,
                         ["SET_GCODE_OFFSET Z=1.000 MOVE=1"])

    def test_no_motion_while_printing(self):
        self.printing()
        self.app.show("move")
        for hit in ("home_all", "home_xy", "motors_off", "y_plus",
                    "extrude"):
            self.tap(hit)
            self.assertEqual(self.app.current, "message", hit)
            self.app.close_modal()
        self.app.show("home")
        for hit in ("home_all", "preheat"):
            self.tap(hit)
            self.app.close_modal()
        self.assertEqual(self.mr.scripts, [])

    def test_no_motion_during_a_filament_job(self):
        self.app.runner = DeferredRunner()     # the load keeps running
        self.app.screens["filament"].start("load")
        self.mr.scripts.clear()
        self.app.show("move")
        self.tap("home_all")
        self.assertEqual(self.mr.scripts, [])

    def test_cooldown_during_a_print_asks_first(self):
        self.printing()
        self.app.show("temps")
        self.tap("cooldown")
        self.assertEqual(self.app.current, "confirm")
        self.assertEqual(self.mr.scripts, [])

    def test_restart_is_refused_if_a_print_started_meanwhile(self):
        self.app.show("settings")
        self.tap("restart_klipper")
        self.assertEqual(self.app.current, "confirm")
        self.mr.status = status(print_stats={"state": "printing",
                                             "filename": "a.gcode"})
        self.app.poll()
        self.tap("yes")
        self.assertNotIn("restart", self.mr.calls)

    def test_files_arriving_later_restore_the_cards(self):
        runner = DeferredRunner()
        self.app.runner = runner
        self.app.show("files")
        rect = LAYOUT["files"].hit("file0").rect
        self.assertIn("fill %d,%d,%d,%d,%d" % (tuple(rect) + (BG,)),
                      self.sent)
        self.sent.clear()
        runner.run_all()
        bg = LAYOUT["files"].bg
        self.assertIn("xpic %d,%d,%d,%d,%d,%d,%d"
                      % (tuple(rect) + rect[:2] + (bg,)), self.sent)
        self.assertIn('"a"', " ".join(self.sent))

    def test_empty_klipper_message_does_not_crash(self):
        self.mr.status = status(webhooks={"state": "", "state_message": ""})
        self.app.poll()
        self.app.show("settings")
        self.app.poll()

    def test_release_on_another_screen_does_nothing(self):
        x, y, w, h = self.app.canvas.screen.hit("home_all").rect
        self.app.on_touch(x + 1, y + 1, True)
        self.app.show("move")       # e.g. a message popped up
        self.app.on_touch(x + 1, y + 1, False)
        self.assertEqual(self.mr.scripts, [])


    # Thumbnails --------------------------------------------------------------

    def with_thumbnails(self):
        from plus4screen.ui import thumbs
        self.uploads = []
        self.app.upload = lambda name, data: self.uploads.append(
            (name, data)) or True
        self.mr.metadata = lambda path: {"estimated_time": 60, "thumbnails": [
            {"width": 32, "relative_path": ".thumbs/x-32.png"},
            {"width": 300, "relative_path": ".thumbs/x-300.png"}]}
        self.mr.download = lambda root, path: b"PNG " + path.encode()
        original = thumbs.make_jpeg
        thumbs.make_jpeg = lambda data, size: b"JPEG %d " % size + data
        self.addCleanup(setattr, thumbs, "make_jpeg", original)

    def test_file_thumbnails_are_uploaded_and_shown(self):
        self.with_thumbnails()
        self.app.show("files")
        while self.app.thumbs.pump():
            pass
        self.assertEqual(self.uploads, [
            ("ram/t3.jpg", b"JPEG 96 PNG .thumbs/x-300.png")])
        x, y, _, _ = LAYOUT["files"].thumbs["file0"].rect
        for command in ('exp3.path="ram/t3.jpg"', "exp3.x=%d" % x,
                        "exp3.y=%d" % y, "vis exp3,1"):
            self.assertIn(command, self.sent)
        # Shown already: nothing is sent again.
        self.sent.clear()
        self.app.poll()
        while self.app.thumbs.pump():
            pass
        self.assertNotIn("vis exp3,1", self.sent)
        # Another screen hides it before its picture is drawn.
        self.sent.clear()
        self.app.show("move")
        self.assertLess(self.sent.index("vis exp3,0"),
                        self.sent.index("pic 0,0,%d" % LAYOUT["move"].bg))

    def test_thumbnail_is_not_uploaded_twice(self):
        self.with_thumbnails()
        self.app.show("files")
        while self.app.thumbs.pump():
            pass
        self.app.show("move")
        self.app.show("files")
        while self.app.thumbs.pump():
            pass
        self.assertEqual(len(self.uploads), 1)
        self.assertIn("vis exp3,1", self.sent)

    def test_screen_picture_is_also_the_page_background(self):
        self.app.show("files")
        bg = LAYOUT["files"].bg
        self.assertLess(self.sent.index("page1.pic=%d" % bg),
                        self.sent.index("pic 0,0,%d" % bg))

    def test_screen_redraws_the_page_before_anything_is_drawn_on_it(self):
        # Changing page1.pic makes the screen redraw the page once its
        # input is empty; drawing sent before that would be wiped.
        self.app.canvas.settle = lambda: self.sent.append("<settle>")
        self.app.show("files")
        bg = LAYOUT["files"].bg
        at = self.sent.index("page1.pic=%d" % bg)
        self.assertEqual(self.sent[at + 1], "<settle>")
        self.assertLess(at + 1, self.sent.index("pic 0,0,%d" % bg))

    def test_screen_redraws_the_page_before_the_upload_repaint(self):
        self.with_thumbnails()
        self.app.show("files")
        self.app.canvas.settle = lambda: self.sent.append("<settle>")
        self.sent.clear()
        while self.app.thumbs.pump():
            pass
        empty = LAYOUT["files"].hit("file1").rect
        fill = "fill %d,%d,%d,%d,%d" % (tuple(empty) + (BG,))
        self.assertLess(self.sent.index("<settle>"), self.sent.index(fill))

    def test_hidden_thumbnail_area_is_redrawn_before_it_is_painted(self):
        self.with_thumbnails()
        self.app.show("files")
        while self.app.thumbs.pump():
            pass
        canvas = self.app.canvas
        canvas.settle = lambda: self.sent.append("<settle>")
        card = LAYOUT["files"].hit("file0").rect
        self.sent.clear()
        canvas.blank(card, BG)
        self.assertEqual(self.sent[:3], [
            "vis exp3,0", "<settle>",
            "fill %d,%d,%d,%d,%d" % (tuple(card) + (BG,))])
        canvas.thumb(3, LAYOUT["files"].thumbs["file0"].rect, "ram/t3.jpg")
        self.sent.clear()
        canvas.hide_thumb(3)
        self.assertEqual(self.sent[:2], ["vis exp3,0", "<settle>"])

    def test_live_content_is_drawn_again_after_an_upload(self):
        # Writing a file makes the screen repaint the page from its
        # background picture, which wipes texts and blanked cards.
        self.with_thumbnails()
        self.app.show("files")
        self.sent.clear()
        while self.app.thumbs.pump():
            pass
        empty = LAYOUT["files"].hit("file1").rect
        fill = "fill %d,%d,%d,%d,%d" % (tuple(empty) + (BG,))
        self.assertIn(fill, self.sent)
        name = [c for c in self.sent if c.endswith(',"a"')]
        self.assertTrue(name)
        self.assertLess(self.sent.index(fill), self.sent.index("vis exp3,1"))

    def test_restored_card_is_not_blanked_again_after_an_upload(self):
        self.with_thumbnails()
        runner = DeferredRunner()
        self.app.runner = runner
        self.app.show("files")      # no files yet: every card blanked
        runner.run_all()            # one file arrives: card 0 restored
        while runner.pending or self.app.thumbs.queue:
            runner.run_all()
            self.app.thumbs.pump()
        card = LAYOUT["files"].hit("file0").rect
        self.sent.clear()
        self.app.canvas.repaint()
        self.assertNotIn("fill %d,%d,%d,%d,%d" % (tuple(card) + (BG,)),
                         self.sent)

    def test_new_picture_in_a_shown_slot_is_drawn_again(self):
        self.with_thumbnails()
        self.app.show("files")
        while self.app.thumbs.pump():
            pass
        self.sent.clear()
        for _ in range(2):          # the first call makes the picture
            self.app.thumbs.show("files", "file0", "b.gcode")
        while self.app.thumbs.pump():
            pass
        self.assertEqual([name for name, _ in self.uploads],
                         ["ram/t3.jpg", "ram/t3.jpg"])
        self.assertIn('exp3.path="ram/t3.jpg"', self.sent)
        self.assertIn("ref exp3", self.sent)

    def test_pressing_a_card_redraws_its_thumbnail(self):
        self.with_thumbnails()
        self.app.show("files")
        while self.app.thumbs.pump():
            pass
        self.sent.clear()
        self.tap("tab_local")   # a press elsewhere does not touch it
        self.assertNotIn("ref exp3", self.sent)
        x, y, w, h = LAYOUT["files"].hit("file0").rect
        self.app.on_touch(x + 2, y + 2, True)
        self.assertIn("ref exp3", self.sent)


class TwfileTest(unittest.TestCase):
    class Port:
        def write(self, data):
            self.written.append(bytes(data))

        def fileno(self):
            return os.open(os.devnull, os.O_RDONLY)

        def __init__(self):
            self.written = []
            self.fd = None
            self.replies = [b"\xfe\xff\xff\xff"]

        def read(self):
            return self.replies.pop(0) if self.replies else b"\x05"

    def test_packets_and_acks(self):
        import select as select_mod
        import termios as termios_mod
        port = self.Port()
        originals = (tjc.select.select, tjc.termios.tcdrain, tjc.time.sleep)
        tjc.select.select = lambda r, w, x, t: (r, [], [])
        tjc.termios.tcdrain = lambda fd: None
        tjc.time.sleep = lambda s: None
        try:
            self.assertTrue(tjc.twfile(port, "ram/t0.jpg", bytes(3000)))
        finally:
            (tjc.select.select, tjc.termios.tcdrain,
             tjc.time.sleep) = originals
        self.assertEqual(port.written[0], b'twfile "ram/t0.jpg",3000'
                         + tjc.TERM)
        self.assertEqual([len(p) for p in port.written[1:]],
                         [12 + 2034 + 2, 12 + 966 + 2])
        self.assertIs(select_mod.select, tjc.select.select)
        self.assertIs(termios_mod.tcdrain, tjc.termios.tcdrain)

    def test_crc(self):
        self.assertEqual(tjc.crc16_modbus(b"123456789"), 0x4B37)


class ScriptedPort:
    """Answers like the screen: in order, after each write."""

    def __init__(self, answer):
        self.answer = answer        # written bytes -> reply, or replies
        self.written = []
        self.pending = []           # one reply per read
        self.fd = None

    def write(self, data):
        self.written.append(bytes(data))
        reply = self.answer(bytes(data))
        self.pending.extend(reply if isinstance(reply, tuple) else
                            [reply] if reply else [])

    def read(self):
        return self.pending.pop(0) if self.pending else b""


def screen_answers(twfile=b"\xfe\xff\xff\xff", packet=b"\x05",
                   sendme=b"\x66\x01\xff\xff\xff", abort=b""):
    def answer(data):
        if data.startswith(tjc.TWFILE_ABORT):
            return abort
        if data.startswith(tjc.TWFILE_MAGIC):
            return packet
        if data.startswith(b"twfile"):
            return twfile
        if data.startswith(b"sendme"):
            return sendme
        return b""
    return answer


class WriteFileTest(unittest.TestCase):
    def setUp(self):
        clock = [0.0]

        def monotonic():
            clock[0] += 0.05
            return clock[0]
        for target, name, value in (
                (tjc.select, "select", lambda r, w, x, t: (r, [], [])),
                (tjc.termios, "tcdrain", lambda fd: None),
                (tjc.termios, "tcflush", lambda fd, q: None),
                (tjc.time, "sleep", lambda s: None),
                (tjc.time, "monotonic", monotonic)):
            patcher = mock.patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def commands(self, port):
        return [w for w in port.written if w.endswith(tjc.TERM)]

    def test_late_reply_of_an_earlier_command_is_not_taken_for_twfile(self):
        # delfile of a missing file fails (0x06); while the screen is busy
        # drawing, that reply comes late, just before sendme's answer.
        port = ScriptedPort(screen_answers(
            sendme=(b"\x06\xff\xff\xff", b"\x66\x01\xff\xff\xff")))
        self.assertTrue(tjc.write_file(port, "ram/t5.jpg", bytes(10)))
        sent = self.commands(port)
        self.assertEqual(sent[:4], [tjc.encode(c) for c in (
            "sendxy=0", 'delfile "ram/t5.jpg"', "sendme",
            'twfile "ram/t5.jpg",10')])
        self.assertEqual(sent[-1], tjc.encode("sendxy=1"))

    def test_other_replies_before_the_ready_answer_are_skipped(self):
        # While the file is made the screen may send 0x06 frames first.
        port = ScriptedPort(screen_answers(
            twfile=(b"\x06\xff\xff\xff", b"\x06\xff\xff\xff",
                    b"\xfe\xff\xff\xff")))
        self.assertTrue(tjc.write_file(port, "ram/t6.jpg", bytes(10)))
        self.assertNotIn(tjc.TWFILE_ABORT, port.written)

    def test_transfer_is_ended_when_a_packet_gets_no_answer(self):
        port = ScriptedPort(screen_answers(packet=b"",
                                           abort=b"\xfd\xff\xff\xff"))
        self.assertFalse(tjc.write_file(port, "ram/t5.jpg", bytes(10)))
        self.assertIn(tjc.TWFILE_ABORT, port.written)
        self.assertEqual(port.written[-1], tjc.encode("sendxy=1"))

    def test_transfer_is_ended_when_twfile_gets_no_answer(self):
        # The screen may still start the transfer after we gave up.
        port = ScriptedPort(screen_answers(twfile=b""))
        self.assertFalse(tjc.write_file(port, "ram/t5.jpg", bytes(10)))
        abort = port.written.index(tjc.TWFILE_ABORT)
        # No transfer ran: TERM closes the abort bytes as one bad command,
        # so they do not spoil sendxy=1.
        self.assertEqual(port.written[abort + 1], tjc.TERM)
        self.assertFalse(any(w.startswith(tjc.TWFILE_MAGIC + b"\x01")
                             for w in port.written))

    def test_ready_answer_during_the_abort_is_aborted_again(self):
        aborts = []

        def answer(data):
            if data.startswith(tjc.TWFILE_ABORT):
                aborts.append(data)
                # The first abort crosses the late 0xFE of the transfer.
                return b"\xfe\xff\xff\xff" if len(aborts) == 1 \
                    else b"\xfd\xff\xff\xff"
            return screen_answers(twfile=b"")(data)
        port = ScriptedPort(answer)
        self.assertFalse(tjc.write_file(port, "ram/t5.jpg", bytes(10)))
        self.assertEqual(len(aborts), 2)
        self.assertNotIn(tjc.TERM, port.written)

    def test_no_answer_to_sendme_ends_a_stuck_transfer(self):
        port = ScriptedPort(screen_answers(sendme=b""))
        self.assertFalse(tjc.write_file(port, "ram/t5.jpg", bytes(10)))
        self.assertIn(tjc.TWFILE_ABORT, port.written)
        self.assertFalse(any(w.startswith(b"twfile") for w in port.written))

    def test_no_room_on_the_screen(self):
        port = ScriptedPort(screen_answers(twfile=b"\x06\xff\xff\xff"))
        self.assertFalse(tjc.write_file(port, "ram/t0.jpg", bytes(10)))
        self.assertFalse(any(w.startswith(tjc.TWFILE_MAGIC + b"\x01")
                             for w in port.written))    # no data was sent

    def test_start_ends_a_transfer_left_running(self):
        def answer(data):
            if data.startswith(tjc.TWFILE_ABORT):
                return b"\xfd\xff\xff\xff"
            return b"comok 2,1281-0" if b"connect" in data else b""
        port = ScriptedPort(answer)
        with mock.patch.object(tjc, "SerialPort", lambda path, baud: port):
            self.assertIs(tjc.open_screen("/dev/ttyS1"), port)
        self.assertEqual(port.written[0], tjc.TWFILE_ABORT)



class ScreenIdTest(unittest.TestCase):
    def make(self, screen_id):
        data = {"size": [800, 480], "screen_id": screen_id,
                "screens": {}}
        layout = Layout(data)
        layout.screens = LAYOUT.screens
        self.sent = []
        app = UIApp(lambda d: self.sent.append(d), FakeMoonraker(),
                    SyncRunner(), layout,
                    prefs_path=os.path.join(tempfile.mkdtemp(), "p.json"))
        app.poll()
        app.start()
        return app

    def tap_home_all(self, app):
        x, y, w, h = app.canvas.screen.hit("home_all").rect
        app.on_touch(x + 1, y + 1, True)
        app.on_touch(x + 1, y + 1, False)

    def test_touches_wait_for_the_screen_id(self):
        app = self.make(1234)
        self.assertIn(b"get sys2" + tjc.TERM, self.sent)
        self.tap_home_all(app)
        self.assertEqual(app.mr.scripts, [])
        app.handle(tjc.Event(tjc.NUMBER, value=1234))
        self.tap_home_all(app)
        self.assertEqual(app.mr.scripts, ["G28"])

    def test_wrong_screen_file_ignores_touches(self):
        app = self.make(1234)
        app.handle(tjc.Event(tjc.NUMBER, value=0))
        self.tap_home_all(app)
        self.assertEqual(app.mr.scripts, [])


class PrefsTest(unittest.TestCase):
    def test_bad_values_fall_back_to_defaults(self):
        path = os.path.join(tempfile.mkdtemp(), "p.json")
        with open(path, "w") as f:
            f.write('{"brightness": "high", "sleep_minutes": 999}')
        from plus4screen.ui.app import Prefs
        prefs = Prefs(path)
        self.assertEqual(prefs["brightness"], 80)
        self.assertEqual(prefs["sleep_minutes"], 240)


class TextTest(unittest.TestCase):
    def test_fit_shortens_with_an_ellipsis(self):
        self.assertEqual(fit("short", 200, 1), "short")
        self.assertTrue(fit("x" * 50, 90, 1).endswith("…"))
        self.assertLessEqual(len(fit("x" * 50, 90, 1)), 10)

    def test_lines_wrap_and_cut(self):
        self.assertEqual(lines("one two three", 7, 2), ["one two", "three"])
        out = lines("aaa bbb ccc ddd eee", 7, 2)
        self.assertEqual(out[0], "aaa bbb")
        self.assertTrue(out[1].endswith("…"))


class DecoderTest(unittest.TestCase):
    def test_touch_positions(self):
        events = tjc.Decoder().feed(bytes.fromhex(
            "6701b000f501ffffff" "6800100020 00ffffff".replace(" ", "")))
        self.assertEqual([e.value for e in events],
                         [(432, 245, True), (16, 32, False)])
        self.assertTrue(all(e.kind == tjc.XY for e in events))


if __name__ == "__main__":
    unittest.main()
