import unittest

from plus4screen import pages as P
from plus4screen import tjc
from plus4screen.app import App, GRAY, WHITE
from plus4screen.moonraker import MoonrakerError
from plus4screen.printer import PrinterState


class FakeMoonraker:
    def __init__(self):
        self.gcodes = []
        self.calls = []
        self.fail = None
        self.files = [{"path": "a.gcode", "modified": 2},
                      {"path": "sub/b.gcode", "modified": 1}]

    def gcode(self, script):
        self.gcodes.append(script)
        if self.fail:
            raise MoonrakerError(self.fail)

    def emergency_stop(self):
        self.calls.append("estop")

    def pause(self):
        self.calls.append("pause")

    def resume(self):
        self.calls.append("resume")

    def cancel(self):
        self.calls.append("cancel")

    def start_print(self, filename):
        self.calls.append("start " + filename)

    def list_files(self):
        return self.files

    def metadata(self, filename):
        return {"estimated_time": 3600}

    def last_job(self):
        return None

    def download(self, root, path):
        raise MoonrakerError("not found", True)


class ManualRunner:
    """Runs jobs only when the test says so, like a slow printer."""

    def __init__(self):
        self.pending = []

    def submit(self, fn, on_done=None):
        self.pending.append((fn, on_done))

    def spawn(self, fn, on_done=None):
        self.run(fn, on_done)

    def run(self, fn, on_done):
        try:
            result, error = fn(), None
        except Exception as exc:
            result, error = None, exc
        if on_done:
            on_done(result, error)

    def finish_all(self):
        while self.pending:
            self.run(*self.pending.pop(0))


def status(print_state="standby", extruder=(25.0, 0.0), **extra):
    s = {
        "webhooks": {"state": "ready", "state_message": "Printer is ready"},
        "extruder": {"temperature": extruder[0], "target": extruder[1]},
        "heater_bed": {"temperature": 60.4, "target": 60.0},
        "heater_generic chamber": {"temperature": 30.0, "target": 0.0},
        "fan_generic cooling_fan": {"speed": 0.5},
        "print_stats": {"state": print_state, "filename": "a.gcode",
                        "print_duration": 600.0,
                        "info": {"current_layer": 3, "total_layer": 100}},
        "virtual_sdcard": {"progress": 0.25},
        "gcode_move": {"speed_factor": 1.0, "extrude_factor": 0.95,
                       "homing_origin": [0, 0, -0.05, 0]},
        "output_pin caselight": {"value": 1.0},
    }
    s.update(extra)
    return s


class AppTest(unittest.TestCase):
    def setUp(self):
        self.out = []
        self.mr = FakeMoonraker()
        self.runner = ManualRunner()
        self.app = App(self.out.append, self.mr, self.runner)
        self.app.update(PrinterState(status()))
        self.app.start()

    def sent(self):
        cmds = [b[:-3].decode() for b in self.out]
        self.out.clear()
        return cmds

    def touch(self, page, widget):
        self.app.handle(tjc.Event(tjc.TOUCH, page=page, widget=widget))

    def run_gcode(self):
        self.runner.finish_all()
        return self.mr.gcodes

    # Start-up and navigation ---------------------------------------------

    def test_start_keeps_screen_language_and_shows_main(self):
        cmds = self.sent()
        self.assertEqual(cmds[0], "page 3")
        self.assertFalse([c for c in cmds if c.startswith("lang=")])
        self.assertIn("n0.val=25", cmds)
        self.assertIn("n1.val=60", cmds)
        self.assertIn('t3.txt="Ready"', cmds)

    def test_start_forces_language_when_given(self):
        app = App(self.out.append, self.mr, self.runner, lang=2)
        app.update(PrinterState(status()))
        self.sent()
        app.start()
        self.assertEqual(self.sent()[:2], ["lang=2", "page 3"])

    def test_unchanged_values_are_not_resent(self):
        self.sent()
        self.app.update(PrinterState(status()))
        self.assertEqual(self.sent(), [])

    def test_boot_event_reinitialises(self):
        self.sent()
        self.app.handle(tjc.Event(tjc.BOOT))
        self.assertEqual(self.sent()[0], "page 3")

    def test_nav_bar(self):
        self.touch(P.MAIN, P.NAV_CONTROL)
        self.assertEqual(self.app.page, P.CONTROL)
        self.touch(P.CONTROL, P.NAV_HOME)
        self.assertEqual(self.app.page, P.MAIN)

    def test_screen_on_unexpected_page_is_followed(self):
        self.touch(P.CONTROL, P.W_HOME)
        self.assertEqual(self.app.page, P.CONTROL)
        self.assertEqual(self.run_gcode(), ["G28"])

    def test_sleep_and_wake(self):
        self.touch(P.MAIN, P.NAV_CONTROL)
        self.touch(P.SCREEN_SLEEP, 1)
        self.assertEqual(self.app.page, P.SCREEN_SLEEP)
        self.touch(P.SCREEN_SLEEP, 0)
        self.assertEqual(self.app.page, P.CONTROL)

    def test_estop(self):
        self.touch(P.MAIN, P.W_ESTOP)
        self.assertEqual(self.mr.calls, ["estop"])

    # Control page --------------------------------------------------------

    def test_jog_uses_selected_step(self):
        self.touch(P.MAIN, P.NAV_CONTROL)
        self.sent()
        self.touch(P.CONTROL, 9)            # 100 mm
        self.assertIn("b9.picc=116", self.sent())
        self.touch(P.CONTROL, 16)           # X-
        self.touch(P.CONTROL, 18)           # Z- (xindi move_z_decrease)
        self.touch(P.CONTROL, 21)           # extrude
        self.assertEqual(self.run_gcode(), [
            "G91\nG1 X-100 F6000\nG90",
            "G91\nG1 Z-100 F600\nG90",
            "G91\nG1 E100 F300\nG90"])

    def test_no_movement_while_printing(self):
        self.app.update(PrinterState(status("printing")))
        self.touch(P.CONTROL, 14)
        self.touch(P.CONTROL, P.W_HOME)
        self.assertEqual(self.run_gcode(), [])

    def test_control_shows_temperatures_and_fans(self):
        self.touch(P.MAIN, P.NAV_CONTROL)
        cmds = self.sent()
        for cmd in ("n1.val=60", "n4.val=60", "n6.val=50", "n7.val=0"):
            self.assertIn(cmd, cmds)

    def test_keypad_sets_temperature(self):
        self.touch(P.MAIN, P.NAV_CONTROL)
        self.touch(P.CONTROL, P.W_HEATER_TARGET)
        self.assertEqual(self.app.page, P.CONTROL_KB)
        # OK sends "71 23 01 41 00": page 35, bed, 65
        self.app.handle(tjc.Event(tjc.VALUE, page=35, widget=1, value=65))
        self.assertEqual(self.app.page, P.CONTROL)
        self.assertEqual(self.run_gcode(), ["M140 S65"])

    def test_keypad_empty_input(self):
        self.touch(P.MAIN, P.NAV_CONTROL)
        self.touch(P.CONTROL, P.W_FILAMENT)
        self.touch(P.PRE_HEAT, P.W_HEATER_TARGET)
        self.touch(P.CONTROL_KB, P.W_KB_OK)
        self.assertEqual(self.app.page, P.PRE_HEAT)
        self.assertEqual(self.run_gcode(), [])

    def test_fans(self):
        self.touch(P.MAIN, P.NAV_CONTROL)
        self.touch(P.CONTROL, P.W_FANS)
        self.assertEqual(self.app.page, P.CONTROL_SETFAN)
        self.app.handle(tjc.Event(tjc.VALUE, page=35, widget=23, value=40))
        self.touch(P.CONTROL_SETFAN, 6)     # cooling fan is on -> off
        self.touch(P.CONTROL_SETFAN, P.W_FANS)
        self.assertEqual(self.app.page, P.CONTROL)
        self.assertEqual(self.run_gcode(), [
            "SET_FAN_SPEED FAN=auxiliary_cooling_fan SPEED=0.40",
            "SET_FAN_SPEED FAN=cooling_fan SPEED=0.00"])

    # Filament ------------------------------------------------------------

    def open_filament(self):
        self.touch(P.MAIN, P.NAV_CONTROL)
        self.sent()
        self.touch(P.CONTROL, P.W_FILAMENT)
        self.assertEqual(self.app.page, P.PRE_HEAT)

    def test_filament_page_relabels_buttons(self):
        self.open_filament()
        cmds = self.sent()
        self.assertIn('b10.txt="Unload"', cmds)
        self.assertIn('b9.txt="Load"', cmds)
        self.assertIn("b6.picc=124", cmds)
        self.assertIn("b7.picc=123", cmds)

    def test_unload(self):
        self.open_filament()
        self.touch(P.PRE_HEAT, 7)           # 250 C
        self.touch(P.PRE_HEAT, P.W_LEFT)
        self.assertEqual(self.app.page, P.UNLOAD)
        self.assertIn("t4.pco=%d" % GRAY, self.sent())
        self.app.update(PrinterState(status(extruder=(247.0, 250.0))))
        self.assertIn("t4.pco=%d" % WHITE, self.sent())
        self.touch(P.UNLOAD, P.W_RIGHT)     # load: blocked while running
        self.assertEqual(self.app.page, P.UNLOAD)
        self.assertEqual(self.run_gcode(), ["UNLOAD_FILAMENT TEMP=250"])
        self.assertIn("t5.pco=%d" % WHITE, self.sent())
        self.touch(P.UNLOAD, P.W_RIGHT)     # then continue with a load
        self.assertEqual(self.app.page, P.PRE_LOAD)

    def test_load(self):
        self.open_filament()
        self.touch(P.PRE_HEAT, P.W_RIGHT)
        self.assertEqual(self.app.page, P.PRE_LOAD)
        self.touch(P.PRE_LOAD, P.W_LEFT)
        self.assertEqual(self.app.page, P.LOAD)
        self.app.update(PrinterState(status(extruder=(219.0, 220.0))))
        self.assertEqual(self.app.page, P.LOAD_2)
        self.assertEqual(self.run_gcode(), ["LOAD_FILAMENT TEMP=220"])
        self.assertEqual(self.app.page, P.LOAD_FINISH)
        self.touch(P.LOAD_FINISH, P.W_LEFT)
        self.assertEqual(self.app.page, P.CONTROL)

    def test_control_button_returns_to_running_job(self):
        self.open_filament()
        self.touch(P.PRE_HEAT, P.W_LEFT)
        self.touch(P.UNLOAD, P.NAV_HOME)
        self.touch(P.MAIN, P.NAV_CONTROL)
        self.assertEqual(self.app.page, P.UNLOAD)

    def test_filament_blocked_while_printing(self):
        self.open_filament()
        self.app.update(PrinterState(status("paused")))
        self.touch(P.PRE_HEAT, P.W_LEFT)
        self.assertEqual(self.app.page, P.GCODE_ERROR)
        self.assertEqual(self.run_gcode(), [])

    def test_gcode_error_is_shown(self):
        self.mr.fail = "Extrude below minimum temp"
        self.open_filament()
        self.touch(P.PRE_HEAT, P.W_LEFT)
        self.run_gcode()
        self.assertEqual(self.app.page, P.GCODE_ERROR)
        self.assertIn('t0.txt="Extrude below minimum temp"', self.sent())
        self.touch(P.GCODE_ERROR, 0)
        self.assertEqual(self.app.page, P.UNLOAD)

    # Printing ------------------------------------------------------------

    def test_print_start_switches_to_printing_page(self):
        self.app.update(PrinterState(status("printing")))
        self.assertEqual(self.app.page, P.PRINTING)
        cmds = self.sent()
        for cmd in ('t5.txt="a.gcode"', 't7.txt="25%"', "n4.val=3",
                    't6.txt="/100"', 't0.txt="00h10m"', 't1.txt="00h50m"',
                    't2.txt="95"', 't4.txt="-0.050"', "b5.picc=69"):
            self.assertIn(cmd, cmds)

    def test_pause_resume_stop(self):
        self.app.update(PrinterState(status("printing")))
        self.touch(P.PRINTING, P.W_PRINT_PAUSE)
        self.app.update(PrinterState(status("paused")))
        self.touch(P.PRINTING, P.W_PRINT_PAUSE)
        self.touch(P.PRINTING, P.W_PRINT_STOP)
        self.assertEqual(self.app.page, P.PRINT_STOP)
        self.touch(P.PRINT_STOP, P.W_NO)
        self.touch(P.PRINTING, P.W_PRINT_STOP)
        self.touch(P.PRINT_STOP, P.W_YES)
        self.assertEqual(self.mr.calls, ["pause", "resume", "cancel"])
        self.app.update(PrinterState(status("cancelled")))
        self.assertEqual(self.app.page, P.MAIN)

    def test_flow_and_speed_keypad(self):
        self.app.update(PrinterState(status("printing")))
        self.touch(P.PRINTING, P.W_PRINT_SPEED)
        self.assertEqual(self.app.page, P.PRINT_KB)
        self.app.handle(tjc.Event(tjc.VALUE, page=17, widget=3, value=120))
        self.assertEqual(self.app.page, P.PRINTING)
        self.touch(P.PRINTING, P.W_PRINT_FLOW)
        self.touch(P.PRINT_KB, P.W_PRINT_KB_CLOSE)
        self.assertEqual(self.app.page, P.PRINTING)
        self.assertEqual(self.run_gcode(), ["M220 S120"])

    def test_value_frames_of_other_pages_are_ignored(self):
        # auto_level (page 14) sends "71 0E 04 ..."; not handled.
        self.app.handle(tjc.Event(tjc.VALUE, page=14, widget=4, value=1))
        self.assertEqual(self.run_gcode(), [])

    def test_print_finished(self):
        self.app.update(PrinterState(status("printing")))
        self.app.update(PrinterState(status("complete")))
        self.assertEqual(self.app.page, P.PRINT_FINISH)
        self.touch(P.PRINT_FINISH, 0)
        self.assertEqual(self.app.page, P.MAIN)

    def test_home_goes_to_printing_page_during_print(self):
        self.app.update(PrinterState(status("printing")))
        self.touch(P.PRINTING, P.NAV_CONTROL)
        self.touch(P.CONTROL, P.NAV_HOME)
        self.assertEqual(self.app.page, P.PRINTING)

    # Files ---------------------------------------------------------------

    def test_file_list_turns_touch_back_on(self):
        self.sent()
        self.touch(P.MAIN, P.NAV_FILES)
        cmds = self.sent()
        self.assertIn("tsw 255,1", cmds)
        self.assertGreater(cmds.index("tsw 255,1"), cmds.index("page 4"))

    def test_file_list_and_print(self):
        self.touch(P.MAIN, P.NAV_FILES)
        self.assertEqual(self.app.page, P.FILE_LIST)
        cmds = self.sent()
        self.assertIn('t0.txt="a.gcode"', cmds)
        self.assertIn('t1.txt="b.gcode"', cmds)
        self.touch(P.FILE_LIST, 5)          # empty slot
        self.assertEqual(self.app.page, P.FILE_LIST)
        self.touch(P.FILE_LIST, 1)
        self.assertEqual(self.app.page, P.PREVIEW)
        cmds = self.sent()
        self.assertIn('t1.txt="b.gcode"', cmds)
        self.assertIn("vis b4,0", cmds)
        self.touch(P.PREVIEW, P.W_PREVIEW_PRINT)
        self.assertEqual(self.mr.calls, ["start sub/b.gcode"])

    # Offline -------------------------------------------------------------

    def test_offline_status_line(self):
        self.app.update(PrinterState(online=False))
        self.assertIn('t3.txt="Moonraker not reachable"', self.sent())

    def test_klipper_error_status_line(self):
        self.mr.query = lambda objects: (_ for _ in ()).throw(
            MoonrakerError("Klippy Disconnected", reachable=True))
        self.app.poll()
        self.assertIn('t3.txt="Klipper: Klippy Disconnected"', self.sent())


if __name__ == "__main__":
    unittest.main()
