"""Tools tab (auto bed levelling, input shaping) and the print Z offset.

The calibrations run QIDI's own macros, like the stock program:

* auto levelling: ``M4031``, ``M4029``, ``M190``, ``M4027``
* input shaping: ``M901``

Both macros end with ``SAVE_CONFIG``, which restarts Klipper, so their
G-code call may fail even when the calibration worked. Progress and the
result are read from the ``M118`` lines the macros print, through
Moonraker's G-code store.
"""

import logging
import time

from . import pages as P

log = logging.getLogger("plus4screen")

# M118 lines printed by QIDI's macros, in order.
LEVEL_MARKS = ("Position init complete", "Nozzle cleared", "Nozzle cooled",
               "Bed mesh calibrate complete")
SHAPER_MARKS = ("Input shaping complete",)

# How long to wait for the closing M118 line after the G-code call ended
# with an error (Klipper restarting after SAVE_CONFIG).
RESTART_GRACE = 90.0

# LEVEL_RUNNING display per step 1-4: q1 picture, visible gm, white
# labels among t0-t3 (the others gray).
LEVEL_PICC = {1: 59, 2: 60, 3: 61, 4: 62}
RED = 63488


class ToolJob:
    """A running calibration."""

    def __init__(self, kind, marks):
        self.kind = kind            # "level" or "shaper"
        self.marks = marks
        self.started = time.time()
        self.seen = 0               # number of marks seen
        self.call_done_at = None    # when the G-code call returned
        self.error = None
        self.finished = False
        self.fetching = False

    @property
    def running(self):
        return not self.finished


class ToolsMixin:
    """Methods ``App`` uses for the tools pages and the print Z offset."""

    # Navigation ---------------------------------------------------------

    def go_tools(self):
        job = self.tool_job
        if job and job.kind == "level":
            self.goto(P.LEVEL_DONE if job.finished else P.LEVEL_RUNNING)
        elif job and job.kind == "shaper":
            self.goto(P.SHAPER_DONE if job.finished else P.SHAPER_RUNNING)
        else:
            self.goto(P.TOOL_SELECT)

    @property
    def tool_running(self):
        return bool(self.tool_job and self.tool_job.running)

    def busy_reason(self):
        s = self.state
        if not s.ready:
            return "Klipper is not ready."
        if s.busy_printing:
            return "Stop the print first."
        if self.tool_running or (self.job and self.job.running):
            return "Wait for the running job to finish."
        return None

    def touch_tool_select(self, widget):
        if widget == P.W_TOOL_LEVEL:
            self.goto(P.LEVEL)
        elif widget == P.W_TOOL_SHAPER:
            self.goto(P.SHAPER)
        elif widget in (P.W_TOOL_SCREWS, 3, 4):
            log.info("tool %d is not implemented, use Fluidd", widget)
        else:
            return False

    # Auto bed levelling -------------------------------------------------

    def touch_level(self, widget):
        if widget == P.W_LEVEL_BACK:
            self.goto(P.TOOL_SELECT)
        else:
            return False

    def level_value(self, value):
        """Bed temperature typed on LEVEL's keypad."""
        temp = min(int(value), P.LEVEL_BED_MAX)
        if temp < P.LEVEL_BED_MIN:
            self.goto(P.LEVEL_WARNING)
            return
        reason = self.busy_reason()
        if reason:
            self.show_error(reason)
            return
        self.start_tool("level", LEVEL_MARKS, P.LEVEL_RUNNING,
                        "SET_HEATER_TEMPERATURE HEATER=heater_bed "
                        "TARGET=%d\nM4031\nM4029\nM190 S%d\nM4027"
                        % (temp, temp))

    def touch_level_warning(self, widget):
        self.goto(P.LEVEL)

    def refresh_level(self):
        s = self.state
        self.set_txt("t6", "%d" % round(s.temps[0][0]))
        self.set_txt("t7", "%d" % round(s.temps[0][1]))
        step = min(4, 1 + (self.tool_job.seen if self.tool_job else 0))
        self.set_attr("q1", "picc", LEVEL_PICC[step])
        for n in range(4):
            self.set_vis("gm%d" % n, n == step - 1)
            self.set_attr("t%d" % n, "pco",
                          P.WHITE if n < step else P.GRAY)
        if step >= 2:
            for n in (5, 7, 8, 9):
                self.set_attr("t%d" % n, "pco", P.WHITE)
            self.set_attr("t6", "pco", RED if step == 2 else P.WHITE)

    # Input shaping -------------------------------------------------------

    def touch_shaper(self, widget):
        if widget == P.W_SHAPER_START:
            reason = self.busy_reason()
            if reason:
                self.show_error(reason)
                return
            self.start_tool("shaper", SHAPER_MARKS, P.SHAPER_RUNNING,
                            "M901")
        elif widget == P.W_SHAPER_BACK:
            self.goto(P.TOOL_SELECT)
        else:
            return False

    def touch_tool_done(self, widget):
        if widget == P.W_DONE_OK:
            self.tool_job = None
            self.goto(P.TOOL_SELECT)
        else:
            return False

    # Shared job handling ---------------------------------------------------

    def start_tool(self, kind, marks, page, script):
        job = self.tool_job = ToolJob(kind, marks)
        self.goto(page)

        def done(_result, error):
            job.call_done_at = time.time()
            job.error = error
        self.gcode(script, done)

    def follow_tool_job(self):
        """Called after every status poll."""
        job = self.tool_job
        if not job or job.finished or job.fetching:
            return
        if self.dry_run:
            return
        job.fetching = True

        def done(lines, error):
            job.fetching = False
            if error is None:
                self._tool_progress(job, lines or [])
            self._tool_check_end(job)
        self.runner.spawn(lambda: self.mr.gcode_store(200), done)

    def _tool_progress(self, job, lines):
        texts = [line.get("message", "") for line in lines
                 if line.get("time", 0) >= job.started - 1]
        seen = job.seen
        while seen < len(job.marks) and any(job.marks[seen] in t
                                            for t in texts):
            seen += 1
        if seen != job.seen:
            log.info("%s: %s", job.kind, job.marks[seen - 1])
            job.seen = seen
            self.refresh()

    def _tool_check_end(self, job):
        if job is not self.tool_job or job.finished:
            return
        if job.seen == len(job.marks):
            self._tool_finish(job)
        elif job.call_done_at is not None:
            if job.error is None:
                self._tool_finish(job)
            elif time.time() - job.call_done_at > RESTART_GRACE:
                job.finished = True
                self.tool_job = None
                self.show_error(str(job.error))

    def _tool_finish(self, job):
        job.finished = True
        log.info("%s finished", job.kind)
        if self.page in (P.LEVEL_RUNNING, P.SHAPER_RUNNING):
            self.goto(P.LEVEL_DONE if job.kind == "level"
                      else P.SHAPER_DONE)

    # Print Z offset ----------------------------------------------------------

    def enter_print_zoffset(self):
        self.show_zoffset_step()

    def show_zoffset_step(self):
        for widget, step in P.W_ZOFFSET_STEP.items():
            picc, picc2 = P.ZOFFSET_STEP_PICC[1 if step == self.zstep else 0]
            self.set_attr("b%d" % widget, "picc", picc)
            self.set_attr("b%d" % widget, "picc2", picc2)

    def touch_print_zoffset(self, widget):
        if widget in P.W_ZOFFSET_STEP:
            self.zstep = P.W_ZOFFSET_STEP[widget]
            self.show_zoffset_step()
        elif widget in (P.W_ZOFFSET_DOWN, P.W_ZOFFSET_UP):
            if not self.state.busy_printing:
                return
            sign = -1 if widget == P.W_ZOFFSET_DOWN else 1
            self.gcode("SET_GCODE_OFFSET Z_ADJUST=%+.3f MOVE=1"
                       % (sign * self.zstep))
        elif widget == P.W_ZOFFSET_BACK:
            self.goto(P.PRINTING)
        else:
            return self.touch_printing(widget)

    def refresh_print_zoffset(self):
        self.refresh_print_common(self.state)
        self.set_txt("t5", "%.3f" % self.state.z_offset)

    TOOLS_ENTER = {
        P.PRINT_ZOFFSET: enter_print_zoffset,
    }
    TOOLS_TOUCH = {
        P.TOOL_SELECT: touch_tool_select,
        P.LEVEL: touch_level,
        P.LEVEL_WARNING: touch_level_warning,
        P.LEVEL_DONE: touch_tool_done,
        P.SHAPER: touch_shaper,
        P.SHAPER_DONE: touch_tool_done,
        P.PRINT_ZOFFSET: touch_print_zoffset,
    }
