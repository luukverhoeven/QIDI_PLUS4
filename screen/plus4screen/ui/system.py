"""Calibrations, settings and versions."""

import logging
import platform

from .. import __version__
from ..settings import ipv4, wifi_ssid
from ..tools import LEVEL_MARKS, RESTART_GRACE, SHAPER_MARKS
from .base import Screen
from .text import ACC, AMBER, RED, SUB, TEXT, clock, duration, first_line

log = logging.getLogger("plus4screen")

LEVEL_STEPS = ("Homing and heating", "Cleaning the nozzle",
               "Cooling the nozzle", "Probing the bed mesh")
SHAPER_STEPS = ("Measuring resonances on X and Y", "", "", "")
SLEEP_CHOICES = (1, 2, 5, 10, 30, 0)          # minutes, 0 = never
BRIGHT_STEP = 10
BRIGHT_MIN = 10


class Tools(Screen):
    name = "tools"

    def touch(self, hit_id):
        app = self.app
        run = app.screens["tool_run"]
        if hit_id == "level":
            reason = app.busy_reason()
            if reason:
                app.message("Cannot start now", reason)
                return
            app.keypad("Bed temperature for levelling", "35 to 120 °C",
                       60, 35, 120, run.start_level)
        elif hit_id == "shaper":
            reason = app.busy_reason()
            if reason:
                app.message("Cannot start now", reason)
                return
            app.confirm("Start input shaping?", "The toolhead shakes for a "
                        "few minutes. Klipper restarts at the end.",
                        "Start", run.start_shaper)


class ToolJob:
    def __init__(self, kind, marks, title, steps, subtitle, now):
        self.kind = kind
        self.marks = marks
        self.title = title
        self.steps = steps
        self.subtitle = subtitle
        self.started = now
        self.seen = 0
        self.call_done_at = None
        self.error = None
        self.finished = False
        self.fetching = False


class ToolRun(Screen):
    """Progress of a calibration, followed through the M118 lines QIDI's
    macros print (see plus4screen/tools.py)."""

    name = "tool_run"

    def __init__(self, app):
        super().__init__(app)
        self.job = None

    @property
    def running(self):
        return bool(self.job and not self.job.finished)

    def start_level(self, bed):
        self._start(ToolJob("level", LEVEL_MARKS, "Auto bed levelling",
                            LEVEL_STEPS, "Bed target %d°" % bed,
                            self.app.clock()),
                    "SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET=%d\n"
                    "M4031\nM4029\nM190 S%d\nM4027" % (bed, bed))

    def start_shaper(self):
        self._start(ToolJob("shaper", SHAPER_MARKS, "Input shaping",
                            SHAPER_STEPS, "X and Y axes", self.app.clock()),
                    "M901")

    def _start(self, job, script):
        app = self.app
        if self.running:
            return
        reason = app.busy_reason()    # things may have changed since asked
        if reason:
            app.message("Cannot start now", reason)
            return
        self.job = job
        app.show(self.name)

        def done(_result, error):
            job.call_done_at = app.clock()
            job.error = error
        app.gcode(script, done)

    def follow(self, old, new):
        job = self.job
        if not job or job.finished or job.fetching:
            return
        if self.app.dry_run:
            if job.call_done_at is not None:
                job.finished = True     # nothing ran; do not block forever
                job.seen = len(job.marks)
            return
        job.fetching = True

        def done(lines, error):
            job.fetching = False
            if error is None:
                self._progress(job, lines or [])
            self._check_end(job)
        self.app.runner.spawn(lambda: self.app.mr.gcode_store(200), done)

    def _progress(self, job, lines):
        texts = [line.get("message", "") for line in lines
                 if line.get("time", 0) >= job.started - 1]
        seen = job.seen
        while seen < len(job.marks) and any(job.marks[seen] in t
                                            for t in texts):
            seen += 1
        if seen != job.seen:
            log.info("%s: %s", job.kind, job.marks[seen - 1])
            job.seen = seen

    def _check_end(self, job):
        if job.finished:
            return
        if job.seen == len(job.marks):
            job.finished = True
        elif job.call_done_at is not None:
            if job.error is None:
                job.finished = True
                job.seen = len(job.marks)
            elif self.app.clock() - job.call_done_at > RESTART_GRACE:
                job.finished = True
        if job.finished and self.app.current == self.name:
            self.refresh(self.app.state)

    def enter(self, **options):
        job = self.job
        if not job:
            return
        self.text("title", job.title)
        self.text("subtitle", job.subtitle)
        for i, step in enumerate(job.steps):
            self.text("step%d" % (i + 1), step)

    def refresh(self, s):
        job = self.job
        if not job:
            return
        steps = len([x for x in job.steps if x])
        done = min(job.seen, steps)
        for i in range(4):
            self.canvas.toggle("done%d" % (i + 1), i < done and job.steps[i])
        elapsed = duration(self.app.clock() - job.started)
        if not job.finished:
            current = job.steps[min(done, steps - 1)]
            self.text("status", current or "Running", AMBER)
            self.text("detail", "Started %s · %s"
                      % (clock(job.started), elapsed))
        elif job.seen == len(job.marks):
            self.text("status", "Done", ACC)
            self.text("detail", "Saved. Klipper restarted with the new "
                      "values.")
        else:
            self.text("status", "Failed", RED)
            self.text("detail", str(job.error or "No result from Klipper."))

    def touch(self, hit_id):
        if hit_id == "back":
            if self.job and self.job.finished:
                self.job = None
            self.app.show("tools")


class Settings(Screen):
    name = "settings"

    def read_network(self):
        net = self.app.mr.system_info().get("network", {})
        wifi = ipv4(net.get("wlan0"))
        ethernet = ipv4(net.get("eth0"))
        return {"ip": wifi or ethernet,
                "ssid": wifi_ssid() if wifi else ("Ethernet" if ethernet
                                                  else "")}

    def refresh(self, s):
        app = self.app
        net = app.net
        if net.get("ip"):
            self.text("wifi", "%s · %s" % (net.get("ssid") or "Wi-Fi",
                                                net["ip"]))
            self.text("url", "http://%s" % net["ip"])
        else:
            self.text("wifi", "Not connected", SUB)
            self.text("url", "-")
        self.text("brightness", "%d%%" % app.prefs["brightness"])
        minutes = app.prefs["sleep_minutes"]
        self.text("sleep", "Never" if not minutes else
                  "%d minute%s" % (minutes, "" if minutes == 1 else "s"))
        if not s.online:
            self.text("klipper", "Moonraker not reachable", RED)
            self.canvas.dot("klipper_dot", RED)
        elif s.ready:
            self.text("klipper", "Ready", TEXT)
            self.canvas.dot("klipper_dot", ACC)
        else:
            message = first_line(s.state_message, s.klippy_state, "Starting")
            self.text("klipper", message, AMBER)
            self.canvas.dot("klipper_dot", AMBER)
        self.text("versions", "plus4screen %s" % __version__)

    def touch(self, hit_id):
        app, prefs = self.app, self.app.prefs
        if hit_id in ("bright_up", "bright_down"):
            step = BRIGHT_STEP if hit_id == "bright_up" else -BRIGHT_STEP
            prefs["brightness"] = max(BRIGHT_MIN,
                                      min(100, prefs["brightness"] + step))
            prefs.save()
            app.send("dim=%d" % prefs["brightness"])
            self.refresh(self.state)
        elif hit_id == "sleep":
            index = SLEEP_CHOICES.index(prefs["sleep_minutes"]) \
                if prefs["sleep_minutes"] in SLEEP_CHOICES else 0
            prefs["sleep_minutes"] = SLEEP_CHOICES[(index + 1)
                                                   % len(SLEEP_CHOICES)]
            prefs.save()
            self.refresh(self.state)
        elif hit_id == "wifi":
            app.message("Wi-Fi", "Change the Wi-Fi network in Fluidd or with "
                        "nmtui over SSH.")
        elif hit_id == "restart_klipper":
            self.klipper_action("Restart Klipper?", "Restart",
                                "restart", app.mr.restart)
        elif hit_id == "restart_firmware":
            self.klipper_action("Restart the firmware?", "Restart",
                                "firmware restart", app.mr.firmware_restart)
        elif hit_id == "about":
            app.show("about")
        elif hit_id == "reboot":
            self.power("Restart the printer?", "Restart",
                       app.mr.machine_reboot)
        elif hit_id == "shutdown":
            self.power("Shut the printer down?", "Shut down",
                       app.mr.machine_shutdown)

    def klipper_action(self, question, yes, name, fn):
        app = self.app
        if self.state.busy_printing:
            app.message("Not while printing", "Stop the print first.")
            return
        app.confirm(question, "The printer is unavailable for a few "
                    "seconds.", yes, lambda: self.unless_printing(name, fn))

    def power(self, question, yes, fn):
        app = self.app
        if self.state.busy_printing:
            app.message("Not while printing", "Stop the print first.")
            return
        app.confirm(question, "Klipper, Moonraker and this screen stop.",
                    yes, lambda: self.unless_printing(question, fn))

    def unless_printing(self, name, fn):
        """Run a restart or power action, unless a print started since the
        question was asked."""
        if self.state.busy_printing:
            self.app.message("Not while printing", "A print started. Stop "
                             "it first.")
            return
        self.app.action(name, fn)


class About(Screen):
    name = "about"

    def __init__(self, app):
        super().__init__(app)
        self.versions = {}

    def enter(self, **options):
        self.app.runner.spawn(self._read, self._got)
        self.draw()

    def _read(self):
        mr = self.app.mr
        versions = {"v_screen": __version__}
        versions["v_klipper"] = mr.printer_info().get("software_version", "?")
        versions["v_moonraker"] = mr.server_info().get(
            "moonraker_version", "?")
        status = mr.query({"mcu": ["mcu_version"],
                           "mcu U_1": ["mcu_version"]})
        versions["v_mcu"] = (status.get("mcu") or {}).get("mcu_version", "-")
        versions["v_mcu_th"] = (status.get("mcu U_1") or {}).get(
            "mcu_version", "-")
        return versions

    def _got(self, versions, error):
        if error is None:
            self.versions.update(versions)
        if self.app.current == self.name:
            self.draw()

    def draw(self):
        self.versions.setdefault("v_screen", __version__)
        self.versions["v_host"] = "%s · Python %s" % (
            platform.system(), platform.python_version())
        for key in ("v_screen", "v_klipper", "v_moonraker", "v_mcu",
                    "v_mcu_th", "v_host"):
            self.text(key, self.versions.get(key, "…"))

    def touch(self, hit_id):
        if hit_id == "close":
            self.app.show("settings")


SCREENS = {"tools": Tools, "tool_run": ToolRun, "settings": Settings,
           "about": About}
