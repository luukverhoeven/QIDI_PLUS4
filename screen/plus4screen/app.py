"""Screen logic: reacts to touch events and keeps the pages up to date.

All methods of ``App`` run on the main thread. Slow work (G-code, HTTP
calls that may block) goes through a runner, whose completion callbacks
are handed back to the main thread.
"""

import logging
import os
import queue
import threading

from . import pages as P
from . import tjc
from .moonraker import MoonrakerError
from .pictures import PicturesMixin
from .printer import FANS, OBJECTS, PrinterState, hhmm
from .settings import SettingsMixin
from .tools import ToolsMixin

log = logging.getLogger("plus4screen")

# Language index of the screen's ``lang`` variable, as used by the page
# code in QIDI's layout: 0 Chinese, 1 Russian, 2 English, 3 Japanese,
# 4 French, 5 German, 6 Italian, 7 Spanish, 9 Portuguese.
ENGLISH = 2

GRAY = P.GRAY
WHITE = P.WHITE

JOG_FEED = {"X": 6000, "Y": 6000, "Z": 600}
EXTRUDE_FEED = 300
TEMP_REACHED_MARGIN = 5.0


class Job:
    """A running filament load or unload."""

    def __init__(self, kind, temp):
        self.kind = kind          # "load" or "unload"
        self.temp = temp
        self.stage = "heating"    # heating -> working -> done / failed
        self.error = None

    @property
    def running(self):
        return self.stage in ("heating", "working")


class ThreadRunner:
    """Runs blocking calls off the main thread.

    ``submit`` jobs run one after another on a worker thread, so G-code is
    sent in order. ``spawn`` jobs get their own thread; use it for calls
    that must not wait behind a long G-code (pause, cancel, file lists).
    """

    def __init__(self):
        self.done = queue.Queue()
        self.jobs = queue.Queue()
        threading.Thread(target=self._worker, daemon=True).start()

    def submit(self, fn, on_done=None):
        self.jobs.put((fn, on_done))

    def spawn(self, fn, on_done=None):
        threading.Thread(target=self._call, args=(fn, on_done),
                         daemon=True).start()

    def _worker(self):
        while True:
            self._call(*self.jobs.get())

    def _call(self, fn, on_done):
        try:
            result, error = fn(), None
        except Exception as exc:     # reported to the screen, not raised
            result, error = None, exc
        self.done.put((on_done, result, error))

    def drain(self):
        while True:
            try:
                on_done, result, error = self.done.get_nowait()
            except queue.Empty:
                return
            if error is not None:
                log.warning("command failed: %s", error)
            if on_done:
                on_done(result, error)


class App(SettingsMixin, ToolsMixin, PicturesMixin):
    def __init__(self, write, moonraker, runner, lang=None,
                 dry_run=False):
        self.write = write
        self.mr = moonraker
        self.runner = runner
        self.lang = lang
        self.dry_run = dry_run

        self.page = None
        self.shown = {}                 # (object, attr) -> last value sent
        self.state = PrinterState(online=False)

        self.step = 10                  # jog distance in mm
        self.temp = P.W_TEMP[6]         # filament temperature
        self.job = None
        self.kb_return = P.CONTROL
        self.fan_return = P.CONTROL
        self.sleep_return = P.MAIN
        self.error_return = P.MAIN
        self.files = []
        self.file_page = 0
        self.selected = None
        self.estimate = {}              # filename -> slicer estimate (s)

        self.set_page = P.MORE          # last settings page
        self.confirm_return = P.MORE
        self.confirm_action = None
        self.tool_job = None
        self.zstep = 0.01

        self.pictures = {}              # filename -> ColPic text or None
        self.pictures_pending = {}      # filename -> callbacks
        self.last_print = None
        self.reset_pictures()

    # Screen output --------------------------------------------------------

    def send(self, command):
        log.debug("-> %s", command)
        self.write(tjc.encode(command))

    def set_attr(self, obj, attr, value):
        key = (obj, attr)
        if self.shown.get(key) == value:
            return
        self.shown[key] = value
        if attr == "txt":
            self.send('%s.txt="%s"' % (obj, tjc.quote(value)))
        else:
            self.send("%s.%s=%d" % (obj, attr, int(value)))

    def set_val(self, obj, value):
        self.set_attr(obj, "val", int(round(value)))

    def set_vis(self, obj, visible):
        key = (obj, "vis")
        if self.shown.get(key) == bool(visible):
            return
        self.shown[key] = bool(visible)
        self.send("vis %s,%d" % (obj, 1 if visible else 0))

    def set_txt(self, obj, text):
        self.set_attr(obj, "txt", text)

    def goto(self, page):
        if page != self.page:
            log.info("page %s -> %s", self.page, page)
        self.page = page
        self.shown.clear()
        self.send("page %d" % page)
        enter = self.ENTER.get(page)
        if enter:
            enter(self)
        self.refresh()

    def start(self):
        """(Re)initialise the screen, e.g. after it booted.

        The screen keeps its own language (set on its language page and
        stored with ``wepo``); only override it when ``--lang`` was given.
        """
        if self.lang is not None:
            self.send("lang=%d" % self.lang)
        self.goto(P.PRINTING if self.state.busy_printing else P.MAIN)

    # Printer interaction --------------------------------------------------

    def gcode(self, script, on_done=None):
        log.info("gcode: %s", script.replace("\n", " | "))
        if self.dry_run:
            if on_done:
                on_done(None, None)
            return
        self.runner.submit(lambda: self.mr.gcode(script),
                           on_done or self._report_error)

    def action(self, name, fn):
        """Print control that must not wait behind G-code."""
        log.info("action: %s", name)
        if self.dry_run:
            return
        self.runner.spawn(fn, self._report_error)

    def _report_error(self, _result, error):
        if error is not None:
            self.show_error(str(error))

    def show_error(self, message):
        if self.page != P.GCODE_ERROR:
            self.error_return = self.page or P.MAIN
        self.goto(P.GCODE_ERROR)
        self.set_txt("t0", message)

    def poll(self):
        try:
            state = PrinterState(self.mr.query(OBJECTS))
        except MoonrakerError as exc:
            if self.state.online:
                log.warning("printer status not available: %s", exc)
            state = PrinterState(online=False, error=str(exc)
                                 if exc.reachable else "")
        self.update(state)

    def update(self, state):
        old, self.state = self.state, state
        self._follow_print(old, state)
        self._follow_job(state)
        self.refresh()
        self.follow_tool_job()

    def _follow_print(self, old, new):
        if new.filename and new.filename not in self.estimate:
            self.estimate[new.filename] = None
            self._fetch_estimate(new.filename)
        was, now = old.print_state, new.print_state
        if was == now:
            return
        log.info("print state %s -> %s", was, now)
        print_pages = (P.PRINTING, P.PRINT_KB, P.PRINT_STOP, P.PRINT_ZOFFSET)
        if now == "printing" and self.page in (P.MAIN, P.FILE_LIST,
                                               P.PREVIEW):
            self.goto(P.PRINTING)
        elif now == "complete" and self.page in print_pages:
            self.goto(P.PRINT_FINISH)
            self.set_txt("t1", hhmm(new.print_duration))
        elif now in ("cancelled", "error", "standby") and (
                self.page in print_pages):
            self.goto(P.MAIN)

    def _fetch_estimate(self, filename):
        def done(meta, error):
            if meta:
                self.estimate[filename] = meta.get("estimated_time")
                if self.page == P.PREVIEW and self.selected == filename:
                    self.set_txt("t2", hhmm(self.estimate[filename]))
        self.runner.spawn(lambda: self.mr.metadata(filename), done)

    # Event dispatch -------------------------------------------------------

    def handle(self, event):
        if event.kind == tjc.TOUCH:
            log.info("touch page=%d widget=%d", event.page, event.widget)
            self.touch(event.page, event.widget)
        elif event.kind == tjc.VALUE:
            log.info("value page=%d widget=%d value=%d", event.page,
                     event.widget, event.value)
            self.value(event.page, event.widget, event.value)
        elif event.kind == tjc.BOOT:
            log.info("screen booted")
            self.reset_pictures()
            self.start()
        elif event.kind == tjc.STATUS:
            log.debug("screen status 0x%02x", event.value)

    def touch(self, page, widget):
        if (page, widget) == P.SLEEP_EVENT:
            if self.page != P.SCREEN_SLEEP:
                self.sleep_return = self.page or P.MAIN
                self.goto(P.SCREEN_SLEEP)
            return
        if page != self.page:
            # The screen is showing another page than we think, e.g. after
            # it switched pages by itself. Follow the screen.
            log.info("screen is on page %d, expected %s", page, self.page)
            self.page = page
            self.shown.clear()
        handler = self.TOUCH.get(page)
        if handler and handler(self, widget) is not False:
            return
        if page not in self.NO_NAV and self.nav(widget):
            return
        log.info("no action for page=%d widget=%d", page, widget)

    def nav(self, widget):
        if widget in (P.NAV_HOME, P.NAV_HOME_ALT):
            self.goto(P.PRINTING if self.state.busy_printing else P.MAIN)
        elif widget == P.NAV_CONTROL:
            self.go_control()
        elif widget == P.NAV_FILES:
            self.goto(P.FILE_LIST)
        elif widget == P.NAV_TOOLS:
            self.go_tools()
        elif widget == P.NAV_SETTINGS:
            self.go_settings()
        else:
            return False
        return True

    def go_control(self):
        job = self.job
        if job and job.running:
            if job.kind == "unload":
                self.goto(P.UNLOAD)
            else:
                self.goto(P.LOAD if job.stage == "heating" else P.LOAD_2)
        else:
            self.goto(P.CONTROL)

    def value(self, page, widget, value):
        if page == P.CONTROL:
            if widget in P.HEATER_VALUE_WIDGETS:
                self.set_heater(P.HEATER_VALUE_WIDGETS.index(widget), value)
            elif widget in P.FAN_VALUE_WIDGETS:
                self.set_fan(P.FAN_VALUE_WIDGETS.index(widget), value)
            if self.page == P.CONTROL_KB:
                self.goto(self.kb_return)
        elif page == P.PRINTING:
            if widget == P.W_PRINT_FLOW:
                self.gcode("M221 S%d" % value)
            elif widget == P.W_PRINT_SPEED:
                self.gcode("M220 S%d" % value)
            if self.page == P.PRINT_KB:
                self.goto(P.PRINTING)
        elif page == P.LEVEL and widget == P.W_LEVEL_TEMP:
            self.level_value(value)

    # Shared control column -----------------------------------------------

    def control_column(self, widget):
        if widget == P.W_HEATER_TARGET:
            if self.page != P.CONTROL_KB:
                self.kb_return = self.page
            self.goto(P.CONTROL_KB)     # the screen already set sys0
        elif widget == P.W_FANS:
            if self.page == P.CONTROL_SETFAN:
                self.goto(self.fan_return)
            else:
                self.fan_return = self.page
                self.goto(P.CONTROL_SETFAN)
        else:
            return False
        return True

    def set_fan(self, index, percent):
        percent = max(0, min(100, int(percent)))
        self.gcode("SET_FAN_SPEED FAN=%s SPEED=%.2f"
                   % (FANS[index], percent / 100.0))

    # Page: MAIN -----------------------------------------------------------

    def enter_main(self):
        self.show_last_print()

    def touch_main(self, widget):
        if widget == P.W_LAST_PRINT:
            if self.last_print:
                self.selected = self.last_print
                self.goto(P.PREVIEW)
        elif widget == P.W_ESTOP:
            log.warning("emergency stop from the screen")
            self.action("emergency stop", self.mr.emergency_stop)
        elif widget == P.W_LIGHT:
            self.gcode("SET_PIN PIN=caselight VALUE=%d"
                       % (0 if self.state.caselight else 1))
        elif widget == P.W_WIFI:
            self.set_page = P.NETWORK
            self.goto(P.NETWORK)
        else:
            return False

    # Page: CONTROL --------------------------------------------------------

    def enter_control(self):
        self.show_step()

    def show_step(self):
        for widget, mm in P.W_STEP.items():
            self.set_attr("b%d" % widget, "picc",
                          P.STEP_PICC[1 if mm == self.step else 0])

    def touch_control(self, widget):
        if self.control_column(widget):
            return
        if widget in P.W_STEP:
            self.step = P.W_STEP[widget]
            self.show_step()
        elif widget in P.W_JOG or widget in P.W_EXTRUDER or widget in (
                P.W_HOME, P.W_MOTORS_OFF):
            if self.state.busy_printing or self.tool_running:
                log.info("movement blocked while printing or calibrating")
                return
            if widget in P.W_JOG:
                axis, sign = P.W_JOG[widget]
                self.gcode("G91\nG1 %s%g F%d\nG90"
                           % (axis, sign * self.step, JOG_FEED[axis]))
            elif widget in P.W_EXTRUDER:
                self.gcode("G91\nG1 E%g F%d\nG90"
                           % (P.W_EXTRUDER[widget] * self.step,
                              EXTRUDE_FEED))
            elif widget == P.W_HOME:
                self.gcode("G28")
            else:
                self.gcode("M84")
        elif widget == P.W_FILAMENT:
            self.goto(P.PRE_HEAT)
        else:
            return False

    # Page: CONTROL_KB (temperature keypad) -------------------------------

    def touch_control_kb(self, widget):
        if widget == P.W_HEATER_TARGET:
            self.goto(P.CONTROL_KB)     # other heater picked: reload page
        elif widget == P.W_KB_OK:
            self.goto(self.kb_return)   # OK with empty input, or close
        elif self.control_column(widget):
            return
        else:
            return False

    def set_heater(self, index, temp):
        commands = {0: "M104 S%d", 1: "M140 S%d", 2: "M141 S%d"}
        self.gcode(commands[index] % temp)

    # Page: CONTROL_SETFAN -------------------------------------------------

    def touch_setfan(self, widget):
        if widget in P.W_FAN_TOGGLE:
            index = P.W_FAN_TOGGLE[widget]
            self.set_fan(index, 0 if self.state.fans[index] else 100)
        elif self.control_column(widget):
            return
        else:
            return False

    # Filament: PRE_HEAT -> UNLOAD, or PRE_HEAT -> PRE_LOAD -> LOAD ... ----

    def enter_pre_heat(self):
        self.show_temp_choice()
        self.set_txt("b%d" % P.W_LEFT, "Unload")
        self.set_txt("b%d" % P.W_RIGHT, "Load")

    def show_temp_choice(self):
        for widget, temp in P.W_TEMP.items():
            self.set_attr("b%d" % widget, "picc",
                          P.TEMP_PICC[1 if temp == self.temp else 0])

    def touch_pre_heat(self, widget):
        if self.control_column(widget):
            return
        if widget in P.W_TEMP:
            self.temp = P.W_TEMP[widget]
            self.show_temp_choice()
        elif widget == P.W_LEFT:
            self.start_job("unload")
        elif widget == P.W_RIGHT:
            self.goto(P.PRE_LOAD)
        else:
            return False

    def touch_pre_load(self, widget):
        if self.control_column(widget):
            return
        if widget == P.W_LEFT:          # Next
            self.start_job("load")
        elif widget == P.W_RIGHT:       # Back
            self.goto(P.PRE_HEAT)
        else:
            return False

    def start_job(self, kind):
        if self.job and self.job.running:
            log.info("a filament %s is still running", self.job.kind)
            return
        if self.state.busy_printing:
            self.show_error("Pause or finish the print first.")
            return
        if self.tool_running:
            self.show_error("Wait for the calibration to finish.")
            return
        job = self.job = Job(kind, self.temp)
        self.goto(P.UNLOAD if kind == "unload" else P.LOAD)
        macro = "UNLOAD_FILAMENT" if kind == "unload" else "LOAD_FILAMENT"
        self.gcode("%s TEMP=%d" % (macro, job.temp),
                   lambda _r, error: self._job_done(job, error))

    def _follow_job(self, state):
        job = self.job
        if job and job.stage == "heating" and (
                state.temps[0][0] >= job.temp - TEMP_REACHED_MARGIN):
            job.stage = "working"
            if job.kind == "load" and self.page == P.LOAD:
                self.goto(P.LOAD_2)
            elif self.page == P.UNLOAD:
                self.show_unload_stage()

    def _job_done(self, job, error):
        job.stage = "failed" if error is not None else "done"
        if error is not None:
            job.error = str(error)
            self.show_error(job.error)
            return
        if job.kind == "load":
            if self.page in (P.LOAD, P.LOAD_2):
                self.goto(P.LOAD_FINISH)
        elif self.page == P.UNLOAD:
            self.show_unload_stage()

    def enter_unload(self):
        self.show_unload_stage()

    def show_unload_stage(self):
        stage = self.job.stage if self.job else "done"
        active = {"heating": 1, "working": 2}.get(stage, 3)
        for n, obj in enumerate(("t3", "t4", "t5"), 1):
            self.set_attr(obj, "pco", WHITE if n <= active else GRAY)

    def touch_unload(self, widget):
        if self.control_column(widget):
            return
        running = self.job and self.job.running
        if widget == P.W_RIGHT:         # "Load filament"
            if not running:
                self.goto(P.PRE_LOAD)
        elif widget == P.W_LEFT:        # "Done"
            self.goto(P.CONTROL)
        else:
            return False

    def touch_load_progress(self, widget):
        if self.control_column(widget):
            return
        return False

    def touch_load_finish(self, widget):
        if self.control_column(widget):
            return
        if widget == P.W_RIGHT:         # Retry
            self.start_job("load")
        elif widget == P.W_LEFT:        # Done
            self.goto(P.CONTROL)
        else:
            return False

    # Page: PRINTING -------------------------------------------------------

    def enter_printing(self):
        self.set_txt("t5", os.path.basename(self.state.filename))
        self.set_txt("t11", "mm/s")
        self.show_printing_picture()

    def touch_printing(self, widget):
        state = self.state
        if widget == P.W_PRINT_STOP:
            self.goto(P.PRINT_STOP)
        elif widget == P.W_PRINT_PAUSE:
            if state.print_state == "paused":
                self.action("resume", self.mr.resume)
            elif state.print_state == "printing":
                self.action("pause", self.mr.pause)
        elif widget == P.W_PRINT_LIGHT:
            self.gcode("SET_PIN PIN=caselight VALUE=%d"
                       % (0 if state.caselight else 1))
        elif widget in (P.W_PRINT_FLOW, P.W_PRINT_SPEED):
            self.goto(P.PRINT_KB)       # the screen already set sys0
        elif widget == P.W_PRINT_ZOFFSET:
            self.goto(P.PRINT_ZOFFSET)
        else:
            return False

    def touch_print_kb(self, widget):
        if widget == P.W_PRINT_KB_CLOSE:
            self.goto(P.PRINTING)
        else:
            return self.touch_printing(widget)

    def touch_print_stop(self, widget):
        if widget == P.W_YES:
            self.action("cancel", self.mr.cancel)
            self.goto(P.PRINTING)
        elif widget == P.W_NO:
            self.goto(P.PRINTING)
        else:
            return False

    def touch_print_finish(self, widget):
        self.goto(P.MAIN)

    # Page: FILE_LIST and PREVIEW -----------------------------------------

    def enter_file_list(self):
        self.render_files()
        # The page's load event runs "tsw 255,0" (all touch off); its
        # timer tm0 only turns touch back on after 30 s. xindi sends
        # "tsw 255,1" itself once the list is filled.
        self.send("tsw 255,1")

        def done(files, error):
            if error is None:
                self.files = files or []
                if self.page == P.FILE_LIST:
                    self.render_files()
        self.runner.spawn(self.mr.list_files, done)

    def render_files(self):
        start = self.file_page * P.FILES_PER_PAGE
        for i in range(P.FILES_PER_PAGE):
            index = start + i
            name = ""
            if index < len(self.files):
                name = os.path.basename(self.files[index]["path"])
            self.set_txt("t%d" % i, name)

    def touch_file_list(self, widget):
        pages = max(1, -(-len(self.files) // P.FILES_PER_PAGE))
        if widget < P.FILES_PER_PAGE:
            index = self.file_page * P.FILES_PER_PAGE + widget
            if index < len(self.files):
                self.selected = self.files[index]["path"]
                self.goto(P.PREVIEW)
        elif widget == P.W_FILE_PREV:
            self.file_page = max(0, self.file_page - 1)
            self.render_files()
        elif widget == P.W_FILE_NEXT:
            self.file_page = min(pages - 1, self.file_page + 1)
            self.render_files()
        else:
            return False

    def enter_preview(self):
        # The three QIDI print options (Box, time-lapse, bed levelling)
        # are not used in single-spool mode.
        for obj in ("b2", "b3", "b4", "t0", "t6", "t7"):
            self.send("vis %s,0" % obj)
        self.set_txt("t1", os.path.basename(self.selected or ""))
        estimate = self.estimate.get(self.selected)
        self.set_txt("t2", hhmm(estimate) if estimate else "")
        if self.selected and self.selected not in self.estimate:
            self.estimate[self.selected] = None
            self._fetch_estimate(self.selected)
        if self.selected:
            self.show_preview_picture(self.selected)

    def touch_preview(self, widget):
        if widget == P.W_PREVIEW_BACK:
            self.goto(P.FILE_LIST)
        elif widget == P.W_PREVIEW_PRINT and self.selected:
            if self.state.busy_printing or not self.state.ready:
                self.show_error("The printer is busy or not ready.")
                return
            filename = self.selected
            self.action("start %s" % filename,
                        lambda: self.mr.start_print(filename))
        else:
            return False

    # Small pages ----------------------------------------------------------

    def touch_sleep(self, widget):
        self.goto(self.sleep_return)

    def touch_error(self, widget):
        self.goto(self.error_return)

    # Refresh --------------------------------------------------------------

    def refresh(self):
        s = self.state
        page = self.page
        if page == P.MAIN:
            for i in range(3):
                self.set_val("n%d" % i, s.temps[i][0])
                self.set_attr("n%d" % i, "pco",
                              P.RED if s.temps[i][1] >= 1 else P.WHITE)
            picc, picc2 = P.LIGHT_PICC[1 if s.caselight else 0]
            self.set_attr("b0", "picc", picc)
            self.set_attr("b0", "picc2", picc2)
            self.set_txt("t3", self.status_line())
        elif page in P.CONTROL_FAMILY:
            if page == P.CONTROL_KB:
                return
            for i in range(3):
                self.set_val("n%d" % i, s.temps[i][0])
                self.set_val("n%d" % (i + 3), s.temps[i][1])
                self.set_val("n%d" % (i + 6), s.fans[i])
                if page == P.CONTROL_SETFAN:
                    self.set_val("h%d" % i, s.fans[i])
        elif page == P.PRINTING:
            self.refresh_printing(s)
        elif page == P.PRINT_KB:
            self.refresh_print_common(s)
        elif page == P.PRINT_ZOFFSET:
            self.refresh_print_zoffset()
        elif page == P.LEVEL_RUNNING:
            self.refresh_level()
        elif page in (P.SYSTEM_OK, P.SYSTEM_ERR):
            self.refresh_system()

    def refresh_printing(self, s):
        for i in range(3):
            self.set_val("n%d" % i, s.temps[i][0])
            self.set_txt("t%d" % (i + 8), "/%d℃" % round(s.temps[i][1]))
        self.set_val("n3", s.velocity)
        self.set_val("n4", s.current_layer)
        self.set_txt("t6", "/%d" % s.total_layer)
        self.set_txt("t5", os.path.basename(s.filename))
        self.set_attr("b1", "picc",
                      P.TOGGLE_PICC[1 if s.print_state == "paused" else 0])
        self.set_attr("b5", "picc", P.TOGGLE_PICC[1 if s.caselight else 0])
        self.refresh_print_common(s)

    def refresh_print_common(self, s):
        """Widgets shared by PRINTING and PRINT_KB."""
        self.set_txt("t7", "%d%%" % int(s.progress * 100))
        self.set_txt("t0", hhmm(s.print_duration))
        self.set_txt("t1", hhmm(s.remaining(self.estimate.get(s.filename))))
        self.set_txt("t4", "%.3f" % s.z_offset)
        self.set_txt("t2", "%d" % round(s.extrude_factor * 100))
        self.set_txt("t3", "%d" % round(s.speed_factor * 100))

    def status_line(self):
        s = self.state
        if not s.online:
            if s.error:
                return "Klipper: %s" % s.error.splitlines()[0]
            return "Moonraker not reachable"
        if not s.ready:
            return (s.state_message or s.klippy_state).splitlines()[0]
        if s.busy_printing:
            return os.path.basename(s.filename)
        return "Ready"

    ENTER = {
        P.MAIN: enter_main,
        P.CONTROL: enter_control,
        P.PRE_HEAT: enter_pre_heat,
        P.UNLOAD: enter_unload,
        P.PRINTING: enter_printing,
        P.FILE_LIST: enter_file_list,
        P.PREVIEW: enter_preview,
        **SettingsMixin.SETTINGS_ENTER,
        **ToolsMixin.TOOLS_ENTER,
    }
    TOUCH = {
        P.MAIN: touch_main,
        P.CONTROL: touch_control,
        P.CONTROL_KB: touch_control_kb,
        P.CONTROL_SETFAN: touch_setfan,
        P.PRE_HEAT: touch_pre_heat,
        P.PRE_LOAD: touch_pre_load,
        P.UNLOAD: touch_unload,
        P.LOAD: touch_load_progress,
        P.LOAD_2: touch_load_progress,
        P.LOAD_FINISH: touch_load_finish,
        P.PRINTING: touch_printing,
        P.PRINT_KB: touch_print_kb,
        P.PRINT_STOP: touch_print_stop,
        P.PRINT_FINISH: touch_print_finish,
        P.FILE_LIST: touch_file_list,
        P.PREVIEW: touch_preview,
        P.SCREEN_SLEEP: touch_sleep,
        P.GCODE_ERROR: touch_error,
        **SettingsMixin.SETTINGS_TOUCH,
        **ToolsMixin.TOOLS_TOUCH,
    }
    # Pages without the navigation bar: widget numbers 33-37 mean
    # something else there (or nothing).
    NO_NAV = (P.SCREEN_SLEEP, P.GCODE_ERROR, P.PRINT_STOP, P.PRINT_FINISH,
              P.LOGO, P.BOOT_SPLASH, P.POWER_OFF, P.CONFIRM, P.LEVEL_WARNING,
              P.LEVEL_DONE, P.SHAPER_DONE)
