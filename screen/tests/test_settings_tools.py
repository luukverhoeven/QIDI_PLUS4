import time
import unittest
from unittest import mock

from plus4screen import pages as P
from plus4screen import settings, tjc, tools
from plus4screen.app import App
from plus4screen.printer import PrinterState

from test_app import FakeMoonraker, ManualRunner, status


class FakeMoonrakerMore(FakeMoonraker):
    def __init__(self):
        super().__init__()
        self.console = []

    def restart(self):
        self.calls.append("restart")

    def firmware_restart(self):
        self.calls.append("firmware_restart")

    def machine_reboot(self):
        self.calls.append("reboot")

    def machine_shutdown(self):
        self.calls.append("shutdown")

    def printer_info(self):
        return {"software_version": "v0.12.0-65"}

    def server_info(self):
        return {"moonraker_version": "v0.8.0-379"}

    def query(self, objects):
        return {"mcu": {"mcu_version": "v0.12.0-mcu"}}

    def system_info(self):
        return {"network": {"wlan0": {"ip_addresses": [
            {"family": "ipv6", "address": "fe80::1", "is_link_local": True},
            {"family": "ipv4", "address": "192.168.86.210",
             "is_link_local": False}]}}}

    def gcode_store(self, count=100):
        return self.console


class Base(unittest.TestCase):
    def setUp(self):
        self.out = []
        self.mr = FakeMoonrakerMore()
        self.runner = ManualRunner()
        self.app = App(self.out.append, self.mr, self.runner)
        self.app.update(PrinterState(status()))
        self.app.start()
        self.sent()

    def sent(self):
        cmds = [b[:-3].decode() for b in self.out]
        self.out.clear()
        return cmds

    def touch(self, page, widget):
        self.app.handle(tjc.Event(tjc.TOUCH, page=page, widget=widget))

    def value(self, page, widget, value):
        self.app.handle(tjc.Event(tjc.VALUE, page=page, widget=widget,
                                  value=value))

    def say(self, message):
        self.mr.console.append({"message": "// " + message,
                                "time": time.time(), "type": "response"})
        self.app.update(PrinterState(status()))


class SettingsTest(Base):
    def test_settings_tab_opens_more_with_restart_button(self):
        self.touch(P.MAIN, P.NAV_SETTINGS)
        self.assertEqual(self.app.page, P.MORE)
        self.assertIn('b8.txt="Restart printer"', self.sent())

    def test_restart_needs_confirmation(self):
        self.touch(P.MAIN, P.NAV_SETTINGS)
        self.touch(P.MORE, P.W_MORE_REBOOT)
        self.assertEqual(self.app.page, P.CONFIRM)
        self.assertIn('t0.txt="Restart the printer?"', self.sent())
        self.touch(P.CONFIRM, P.W_CONFIRM_NO)
        self.assertEqual(self.app.page, P.MORE)
        self.assertEqual(self.mr.calls, [])
        self.touch(P.MORE, P.W_MORE_REBOOT)
        self.touch(P.CONFIRM, P.W_CONFIRM_YES)
        self.assertEqual(self.app.page, P.BOOT_SPLASH)
        self.assertEqual(self.mr.calls, ["reboot"])

    def test_shutdown_from_system_page(self):
        self.touch(P.MAIN, P.NAV_SETTINGS)
        self.touch(P.MORE, P.W_SET_SYSTEM)
        self.assertEqual(self.app.page, P.SYSTEM_OK)
        self.touch(P.SYSTEM_OK, P.W_SYS_SHUTDOWN)
        self.touch(P.CONFIRM, P.W_CONFIRM_YES)
        self.assertEqual(self.app.page, P.POWER_OFF)
        self.assertEqual(self.mr.calls, ["shutdown"])

    def test_no_power_actions_while_printing(self):
        self.app.update(PrinterState(status("printing")))
        self.app.goto(P.MORE)
        self.touch(P.MORE, P.W_MORE_REBOOT)
        self.touch(P.CONFIRM, P.W_CONFIRM_YES)
        self.assertEqual(self.app.page, P.GCODE_ERROR)
        self.app.goto(P.SYSTEM_OK)
        self.touch(P.SYSTEM_OK, P.W_SYS_KLIPPER_RESTART)
        self.assertEqual(self.mr.calls, [])

    def test_system_error_page_shows_klipper_message(self):
        self.app.update(PrinterState(status(webhooks={
            "state": "shutdown", "state_message": "MCU error\nRestart"})))
        self.app.goto(P.MORE)
        self.touch(P.MORE, P.W_SET_SYSTEM)
        self.assertEqual(self.app.page, P.SYSTEM_ERR)
        self.assertIn('t6.txt="MCU error. Restart"', self.sent())
        self.touch(P.SYSTEM_ERR, P.W_SYS_FIRMWARE_RESTART)
        self.assertEqual(self.mr.calls, ["firmware_restart"])

    def test_versions_page(self):
        self.app.goto(P.MORE)
        self.sent()
        self.touch(P.MORE, 4)
        cmds = self.sent()
        self.assertIn("vis b6,0", cmds)
        text = [c for c in cmds if c.startswith('t7.txt=')][-1]
        self.assertIn("Klipper v0.12.0-65", text)
        self.assertIn("Moonraker v0.8.0-379", text)

    def test_network_page(self):
        self.app.goto(P.MORE)
        with mock.patch.object(settings, "wifi_ssid", return_value="Home"):
            self.touch(P.MORE, 1)
        cmds = self.sent()
        self.assertIn("vis b22,0", cmds)
        self.assertIn('t7.txt="192.168.86.210"', cmds)
        self.assertIn('t10.txt="Home"', cmds)
        self.assertIn("vis t11,0", cmds)

    def test_settings_tab_remembers_last_page(self):
        self.app.goto(P.MORE)
        self.touch(P.MORE, 0)
        self.assertEqual(self.app.page, P.LANGUAGE)
        self.touch(P.LANGUAGE, P.NAV_HOME)
        self.touch(P.MAIN, P.NAV_SETTINGS)
        self.assertEqual(self.app.page, P.LANGUAGE)


class ToolsTest(Base):
    def test_level_rejects_cold_bed(self):
        self.touch(P.MAIN, P.NAV_TOOLS)
        self.assertEqual(self.app.page, P.TOOL_SELECT)
        self.touch(P.TOOL_SELECT, P.W_TOOL_LEVEL)
        self.value(P.LEVEL, P.W_LEVEL_TEMP, 20)
        self.assertEqual(self.app.page, P.LEVEL_WARNING)
        self.touch(P.LEVEL_WARNING, P.W_WARNING_OK)
        self.assertEqual(self.app.page, P.LEVEL)

    def test_level_runs_qidi_macros_and_follows_progress(self):
        self.app.goto(P.LEVEL)
        self.value(P.LEVEL, P.W_LEVEL_TEMP, 200)    # clamped to 120
        self.assertEqual(self.app.page, P.LEVEL_RUNNING)
        self.sent()
        self.say("Position init complete")
        self.assertIn("q1.picc=60", self.sent())
        self.say("Nozzle cleared")
        self.say("Nozzle cooled")
        self.assertEqual(self.app.page, P.LEVEL_RUNNING)
        self.say("Bed mesh calibrate complete")
        self.assertEqual(self.app.page, P.LEVEL_DONE)
        self.runner.finish_all()          # the macro call returns last
        self.assertEqual(self.mr.gcodes, [
            "SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET=120\n"
            "M4031\nM4029\nM190 S120\nM4027"])
        self.touch(P.LEVEL_DONE, P.W_DONE_OK)
        self.assertEqual(self.app.page, P.TOOL_SELECT)
        self.assertIsNone(self.app.tool_job)

    def test_tools_tab_returns_to_running_job(self):
        self.app.goto(P.SHAPER)
        self.touch(P.SHAPER, P.W_SHAPER_START)
        self.assertEqual(self.app.page, P.SHAPER_RUNNING)
        self.touch(P.SHAPER_RUNNING, P.NAV_HOME)
        self.touch(P.MAIN, P.NAV_TOOLS)
        self.assertEqual(self.app.page, P.SHAPER_RUNNING)
        self.say("Input shaping complete")
        self.assertEqual(self.app.page, P.SHAPER_DONE)

    def test_klipper_restart_error_waits_for_marker(self):
        self.mr.fail = "Klippy Disconnected"
        self.app.goto(P.SHAPER)
        self.touch(P.SHAPER, P.W_SHAPER_START)
        self.runner.finish_all()          # M901 call fails (SAVE_CONFIG)
        self.app.update(PrinterState(status()))
        self.assertEqual(self.app.page, P.SHAPER_RUNNING)
        self.say("Input shaping complete")
        self.assertEqual(self.app.page, P.SHAPER_DONE)

    def test_error_without_marker_is_shown_after_grace(self):
        self.mr.fail = "Accelerometer not found"
        self.app.goto(P.SHAPER)
        self.touch(P.SHAPER, P.W_SHAPER_START)
        self.runner.finish_all()
        later = time.time() + tools.RESTART_GRACE + 1
        with mock.patch.object(tools.time, "time", return_value=later):
            self.app.update(PrinterState(status()))
        self.assertEqual(self.app.page, P.GCODE_ERROR)
        self.assertIsNone(self.app.tool_job)

    def test_no_calibration_while_printing(self):
        self.app.update(PrinterState(status("printing")))
        self.app.goto(P.SHAPER)
        self.touch(P.SHAPER, P.W_SHAPER_START)
        self.assertEqual(self.app.page, P.GCODE_ERROR)
        self.assertEqual(self.mr.gcodes, [])


class PrintZOffsetTest(Base):
    def test_zoffset_page(self):
        self.app.update(PrinterState(status("printing")))
        self.app.goto(P.PRINTING)
        self.touch(P.PRINTING, P.W_PRINT_ZOFFSET)
        self.assertEqual(self.app.page, P.PRINT_ZOFFSET)
        self.assertIn('t5.txt="-0.050"', self.sent())
        self.touch(P.PRINT_ZOFFSET, 8)                  # 0.1 mm
        self.assertIn("b8.picc=71", self.sent())
        self.touch(P.PRINT_ZOFFSET, P.W_ZOFFSET_DOWN)
        self.touch(P.PRINT_ZOFFSET, P.W_ZOFFSET_UP)
        self.runner.finish_all()
        self.assertEqual(self.mr.gcodes, [
            "SET_GCODE_OFFSET Z_ADJUST=-0.100 MOVE=1",
            "SET_GCODE_OFFSET Z_ADJUST=+0.100 MOVE=1"])
        self.touch(P.PRINT_ZOFFSET, P.W_ZOFFSET_BACK)
        self.assertEqual(self.app.page, P.PRINTING)


if __name__ == "__main__":
    unittest.main()
