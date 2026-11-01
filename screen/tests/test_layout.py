"""Checks pages.py against QIDI's screen layout in UI/xindi_800_480.HMI."""

import importlib.util
import os
import unittest

from plus4screen import pages as P

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HMI = os.path.join(ROOT, "UI", "xindi_800_480.HMI")
TOOL = os.path.join(ROOT, "tools", "hmi_dump.py")

PAGE_NAMES = {
    P.LOGO: "logo", P.MAIN: "main", P.FILE_LIST: "file_list",
    P.PREVIEW: "preview", P.PRINTING: "printing", P.PRINT_KB: "print_kb",
    P.PRINT_FINISH: "print_finish", P.CONTROL: "control",
    P.CONTROL_KB: "control_kb", P.PRE_LOAD: "pre_load",
    P.PRE_HEAT: "pre_heat", P.UNLOAD: "unload", P.LOAD: "load",
    P.SCREEN_SLEEP: "screen_sleep", P.GCODE_ERROR: "gcode_error",
    P.PRINT_STOP: "print_stop", P.CONTROL_SETFAN: "control_setfan",
    P.LOAD_2: "load_2", P.LOAD_FINISH: "load_finish",
}


@unittest.skipUnless(os.path.exists(HMI), "screen layout not available")
class LayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("hmi_dump", TOOL)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        cls.pages = mod.dump(HMI)["pages"]

    def reports(self, page):
        return {n for o in self.pages[page]["objects"]
                for nums in o.get("reports", {}).values() for n in nums}

    def objects(self, page):
        return {o["name"]: o for o in self.pages[page]["objects"]}

    def test_page_numbers(self):
        for number, name in PAGE_NAMES.items():
            self.assertEqual(self.pages[number]["name"], name)

    def test_widget_numbers(self):
        cases = {
            P.MAIN: [P.W_WIFI, P.W_ESTOP, P.NAV_HOME_ALT, P.NAV_CONTROL,
                     P.NAV_FILES],
            P.CONTROL: list(P.W_STEP) + list(P.W_JOG) + list(P.W_EXTRUDER)
            + [P.W_HOME, P.W_MOTORS_OFF, P.W_FILAMENT, P.W_HEATER_TARGET,
               P.W_FANS, P.NAV_HOME],
            P.CONTROL_KB: [P.W_FANS, P.NAV_HOME],
            P.CONTROL_SETFAN: list(P.W_FAN_TOGGLE) + [P.W_FANS],
            P.PRE_HEAT: list(P.W_TEMP) + [P.W_LEFT, P.W_RIGHT],
            P.PRE_LOAD: [P.W_LEFT, P.W_RIGHT],
            P.UNLOAD: [P.W_LEFT, P.W_RIGHT],
            P.LOAD_FINISH: [P.W_LEFT, P.W_RIGHT],
            P.PRINTING: [P.W_PRINT_STOP, P.W_PRINT_PAUSE, P.W_PRINT_LIGHT,
                         P.W_PRINT_FLOW, P.W_PRINT_SPEED],
            P.PRINT_KB: [P.W_PRINT_STOP, P.W_PRINT_PAUSE, P.W_PRINT_LIGHT,
                         P.W_PRINT_KB_CLOSE],
            P.FILE_LIST: list(range(P.FILES_PER_PAGE))
            + [P.W_FILE_PREV, P.W_FILE_NEXT],
            P.PREVIEW: [P.W_PREVIEW_BACK, P.W_PREVIEW_PRINT],
            P.PRINT_STOP: [P.W_YES, P.W_NO],
            P.GCODE_ERROR: [0],
            P.PRINT_FINISH: [0],
        }
        for page, widgets in cases.items():
            missing = set(widgets) - self.reports(page)
            self.assertFalse(missing, "page %d lacks %s" % (page, missing))

    def test_keypad_ok_and_sleep_event(self):
        ok = self.objects(P.CONTROL_KB)["b6"]["events"]["up"]
        self.assertIn("  prints %d,1" % P.W_KB_OK, ok)
        for widget in P.HEATER_VALUE_WIDGETS + P.FAN_VALUE_WIDGETS:
            self.assertIn("  prints %d,1" % widget, ok)
        timer = self.objects(P.CONTROL)["sleep_mode"]["events"]["timer"]
        self.assertIn("  prints %d,1" % P.SLEEP_EVENT[0], timer)
        self.assertIn("  prints %d,1" % P.SLEEP_EVENT[1], timer)

    def test_fan_value_frames(self):
        sliders = self.objects(P.CONTROL_SETFAN)
        for name, widget in zip(("h0", "h1", "h2"), P.FAN_VALUE_WIDGETS):
            code = sliders[name]["events"]["up"]
            self.assertIn("prints 113,1", code)     # 0x71
            self.assertIn("prints %d,1" % P.CONTROL, code)
            self.assertIn("prints %d,1" % widget, code)

    def test_selection_pictures(self):
        control = self.objects(P.CONTROL)
        # The layout default is the unselected look; picc2 is the
        # pressed picture, not the selected one.
        self.assertEqual((control["b6"]["picc"], control["b6"]["picc2"]),
                         P.STEP_PICC[0])
        heat = self.objects(P.PRE_HEAT)
        self.assertEqual(heat["b7"]["picc"], P.TEMP_PICC[0])
        self.assertEqual(heat["b6"]["picc"], P.TEMP_PICC[1])

    def test_widgets_written_by_the_app_exist(self):
        cases = {
            P.MAIN: ["n0", "n1", "n2", "t3"],
            P.CONTROL: ["n%d" % i for i in range(9)],
            P.CONTROL_SETFAN: ["h0", "h1", "h2", "n6", "n7", "n8"],
            P.PRE_HEAT: ["b6", "b7", "b8", "b9", "b10"],
            P.UNLOAD: ["t3", "t4", "t5"],
            P.PRINTING: ["n0", "n1", "n2", "n3", "n4", "t0", "t1", "t2",
                         "t3", "t4", "t5", "t6", "t7", "t8", "t9", "t10",
                         "t11", "b1", "b5"],
            P.FILE_LIST: ["t%d" % i for i in range(6)],
            P.PREVIEW: ["t1", "t2", "b2", "b3", "b4", "t0", "t6", "t7"],
            P.PRINT_KB: ["t0", "t1", "t2", "t3", "t4", "t7"],
            P.PRINT_FINISH: ["t1"],
            P.GCODE_ERROR: ["t0"],
        }
        for page, names in cases.items():
            missing = set(names) - set(self.objects(page))
            self.assertFalse(missing, "page %d lacks %s" % (page, missing))


if __name__ == "__main__":
    unittest.main()
