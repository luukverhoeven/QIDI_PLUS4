"""Home, the print screen, the file list and the file preview."""

import os
import time

from .base import Screen
from .text import (ACC, AMBER, BG, MUTE, RED, SUB, TEXT, clock, duration,
                   file_title, filament, target, temp)

HEATERS = ("nozzle", "bed", "chamber")
HEAT_CMD = ("M104 S%d", "M140 S%d", "M141 S%d")
HEAT_MAX = (300, 110, 65)
HEAT_NAME = ("Nozzle", "Bed", "Chamber")
HEATING_MARGIN = 2.0
FILES_PER_PAGE = 6


def state_label(s):
    """(text, colour) of the printer state chip."""
    if not s.online:
        return "Offline", RED
    if s.klippy_state in ("shutdown", "error"):
        return "Error", RED
    if not s.ready:
        return "Starting", SUB
    if s.print_state == "paused":
        return "Paused", AMBER
    if s.print_state == "printing":
        return "Printing", AMBER
    return "Ready", ACC


def status_line(s):
    if not s.online:
        return s.error.splitlines()[0] if s.error else \
            "Moonraker is not reachable"
    if not s.ready:
        return (s.state_message or s.klippy_state).splitlines()[0]
    heating = [HEAT_NAME[i].lower() for i, (cur, tgt) in enumerate(s.temps)
               if tgt >= 1 and cur < tgt - HEATING_MARGIN]
    if heating:
        return "Heating the %s" % " and ".join(heating)
    return "Ready to print"


def heater_look(current, goal):
    """(target text colour, bar fraction, bar colour) of a heater."""
    if goal < 1:
        return MUTE, 0.0, ACC
    if current < goal - HEATING_MARGIN:
        return AMBER, current / goal, AMBER
    return ACC, 1.0, ACC


def set_heater(app, index):
    current = app.state.temps[index][1]
    app.keypad("%s temperature" % HEAT_NAME[index],
               "0 to %d °C, 0 turns it off" % HEAT_MAX[index],
               int(current), 0, HEAT_MAX[index],
               lambda v: app.gcode(HEAT_CMD[index] % v))


def start_print(app, filename):
    reason = app.busy_reason()
    if reason:
        app.message("Cannot start the print", reason)
        return
    app.action("start %s" % filename, lambda: app.mr.start_print(filename))
    app.show("printing")


class Home(Screen):
    name = "home"

    def __init__(self, app):
        super().__init__(app)
        self.last = None          # last job from Moonraker's history
        self.asked = False

    def follow(self, old, new):
        if not self.asked or (old.print_state != new.print_state and
                              new.print_state in ("complete", "cancelled",
                                                  "error")):
            self.asked = True
            self.app.runner.spawn(self.app.mr.last_job, self._got_last)

    def _got_last(self, job, error):
        if error is None:
            self.last = job
            if self.app.current == self.name:
                self.draw_last()

    def enter(self, **options):
        self.draw_last()

    def refresh(self, s):
        text, color = state_label(s)
        self.text("state", text, color)
        self.canvas.dot("state_dot", color)
        self.text("status", status_line(s))
        self.text("ip", self.app.net.get("ip") or "No network")
        self.text("clock", clock(self.app.clock()))
        for i, name in enumerate(HEATERS):
            current, goal = s.temps[i]
            color, fraction, bar = heater_look(current, goal)
            self.text(name, temp(current))
            self.text(name + "_target", target(goal), color)
            self.canvas.bar(name + "_bar", fraction, bar)
        for i in range(3):
            self.text("fan%d" % i, "%d%%" % s.fans[i])
        self.canvas.toggle("light", s.caselight)

    def draw_last(self):
        job = self.last
        if not job:
            self.text("last_name1", "No prints yet")
            for key in ("last_name2", "last_time", "last_filament",
                        "last_result"):
                self.text(key, "")
            return
        self.wrap(("last_name1", "last_name2"),
                  file_title(job.get("filename")))
        meta = job.get("metadata") or self.app.metadata(
            job.get("filename")) or {}
        self.text("last_time", duration(job.get("print_duration")
                                        or meta.get("estimated_time")))
        self.text("last_filament", filament(meta))
        self.text("last_result", result_text(job))

    def touch(self, hit_id):
        app = self.app
        if hit_id.startswith("temp_"):
            set_heater(app, HEATERS.index(hit_id[5:]))
        elif hit_id == "fans":
            app.show("temps")
        elif hit_id == "light":
            app.gcode("SET_PIN PIN=caselight VALUE=%d"
                      % (0 if self.state.caselight else 1))
        elif hit_id == "filament":
            app.show("filament")
        elif hit_id == "home_all":
            app.gcode("G28")
        elif hit_id == "preheat":
            app.gcode("M104 S220\nM140 S60")
        elif hit_id in ("open_last", "reprint") and self.last:
            filename = self.last.get("filename")
            if hit_id == "open_last":
                app.show("preview", filename=filename)
            else:
                app.confirm("Print it again?", file_title(filename),
                            "Print", lambda: start_print(app, filename))


def result_text(job):
    status = job.get("status")
    if status != "completed":
        return {"cancelled": "Cancelled", "error": "Failed",
                "klippy_shutdown": "Stopped by Klipper",
                "interrupted": "Interrupted",
                "in_progress": "Printing"}.get(status, status or "")
    end = job.get("end_time")
    if not end:
        return "Finished"
    day = time.localtime(end)
    today = time.localtime()
    if day[:3] == today[:3]:
        return "Finished today %s" % time.strftime("%H:%M", day)
    return "Finished %s" % time.strftime("%d %b", day)


class Printing(Screen):
    name = "printing"

    def refresh(self, s):
        app = self.app
        label, color = state_label(s)
        self.text("state", label, color)
        self.canvas.dot("state_dot", color)
        self.text("clock", clock(app.clock()))
        self.text("file", os.path.basename(s.filename))
        self.text("percent", "%d%%" % int(s.progress * 100))
        self.canvas.bar("progress", s.progress)
        if s.total_layer:
            self.text("layer", "Layer %d / %d" % (s.current_layer,
                                                  s.total_layer))
        else:
            self.text("layer", "Z %.2f" % s.position[2])
        meta = app.metadata(s.filename) or {}
        left = s.remaining(meta.get("estimated_time"))
        self.text("left", duration(left))
        self.text("elapsed", duration(s.print_duration))
        self.text("finish", clock(app.clock() + left) if left else "-")
        for i, name in enumerate(("nozzle", "bed")):
            current, goal = s.temps[i]
            self.text(name, temp(current))
            self.text(name + "_target", "/ %d" % round(goal))
        self.text("speed", "%d%%" % round(s.speed_factor * 100))
        self.text("flow", "%d%%" % round(s.extrude_factor * 100))
        self.text("zoffset", "%+.3f" % s.z_offset)
        self.canvas.toggle("paused", s.print_state == "paused")
        self.canvas.toggle("light", s.caselight)

    def touch(self, hit_id):
        app, s = self.app, self.state
        if hit_id == "pause":
            if s.print_state == "paused":
                app.action("resume", app.mr.resume)
            elif s.print_state == "printing":
                app.action("pause", app.mr.pause)
        elif hit_id == "stop":
            app.confirm("Stop the print?", "The print is cancelled and "
                        "cannot be resumed.", "Stop print",
                        lambda: app.action("cancel", app.mr.cancel))
        elif hit_id == "light":
            app.gcode("SET_PIN PIN=caselight VALUE=%d"
                      % (0 if s.caselight else 1))
        elif hit_id == "set_nozzle":
            set_heater(app, 0)
        elif hit_id == "set_bed":
            set_heater(app, 1)
        elif hit_id == "set_speed":
            app.keypad("Print speed", "10 to 300 %",
                       round(s.speed_factor * 100), 10, 300,
                       lambda v: app.gcode("M220 S%d" % v))
        elif hit_id == "set_flow":
            app.keypad("Flow", "50 to 150 %",
                       round(s.extrude_factor * 100), 50, 150,
                       lambda v: app.gcode("M221 S%d" % v))
        elif hit_id == "set_zoffset":
            app.keypad("Z offset", "-2.000 to 2.000 mm, + is further from "
                       "the bed", s.z_offset, -2, 2,
                       lambda v: app.gcode("SET_GCODE_OFFSET Z=%.3f MOVE=1"
                                           % v),
                       decimals=3, negative=True)


class Files(Screen):
    name = "files"

    def __init__(self, app):
        super().__init__(app)
        self.usb = False
        self.page = 0
        self.files = None         # all files, newest first
        self.error = None

    def enter(self, **options):
        self.canvas.toggle("tab_local", not self.usb)
        self.canvas.toggle("tab_usb", self.usb)
        self.app.runner.spawn(self.app.mr.list_files, self._got_files)
        self.draw()

    def _got_files(self, files, error):
        self.files = files or []
        self.error = str(error) if error else None
        if self.app.current == self.name:
            self.draw()

    def shown(self):
        files = self.files or []
        return [f for f in files
                if f["path"].startswith("USB/") == self.usb]

    def draw(self):
        files = self.shown()
        pages = max(1, (len(files) + FILES_PER_PAGE - 1) // FILES_PER_PAGE)
        self.page = min(self.page, pages - 1)
        if self.files is None:
            summary = "Reading files…"
        elif self.error:
            summary = self.error
        elif not files:
            summary = "No USB stick, or no files on it" if self.usb \
                else "No files yet"
        else:
            summary = "%d files · newest first" % len(files)
        self.text("summary", summary)
        self.text("page", "Page %d of %d" % (self.page + 1, pages))
        start = self.page * FILES_PER_PAGE
        for i in range(FILES_PER_PAGE):
            index = start + i
            if index < len(files):
                self.draw_card(i, files[index])
            else:
                self.canvas.fill(self.canvas.screen.hit("file%d" % i).rect,
                                 BG)

    def draw_card(self, i, entry):
        self.text("name%d" % i, file_title(entry["path"]))
        meta = self.app.metadata(entry["path"])
        if meta is None:
            self.text("meta%d" % i, "")
        else:
            self.text("meta%d" % i, "%s · %s" % (
                duration(meta.get("estimated_time")), filament(meta)))

    def refresh(self, s):
        files = self.shown()
        start = self.page * FILES_PER_PAGE
        for i, entry in enumerate(files[start:start + FILES_PER_PAGE]):
            if self.app.metadata(entry["path"]) is not None:
                self.draw_card(i, entry)

    def touch(self, hit_id):
        files = self.shown()
        pages = max(1, (len(files) + FILES_PER_PAGE - 1) // FILES_PER_PAGE)
        if hit_id in ("tab_local", "tab_usb"):
            usb = hit_id == "tab_usb"
            if usb != self.usb:
                self.usb, self.page = usb, 0
                self.app.show(self.name)
        elif hit_id in ("prev", "next"):
            page = self.page + (1 if hit_id == "next" else -1)
            if 0 <= page < pages:
                self.page = page
                self.app.show(self.name)
        elif hit_id.startswith("file"):
            index = self.page * FILES_PER_PAGE + int(hit_id[4:])
            if index < len(files):
                self.app.show("preview", filename=files[index]["path"])


class Preview(Screen):
    name = "preview"

    def __init__(self, app):
        super().__init__(app)
        self.filename = None

    def enter(self, filename=None, **options):
        if filename:
            self.filename = filename
        self.wrap(("name1", "name2"), file_title(self.filename))
        self.text("where", "USB stick" if (self.filename or "").startswith(
            "USB/") else "Local storage")

    def refresh(self, s):
        meta = self.app.metadata(self.filename)
        if meta is None:
            self.text("time", "Reading…", SUB)
            return
        self.text("time", duration(meta.get("estimated_time")), TEXT)
        self.text("filament", filament(meta))
        height, layer = meta.get("object_height"), meta.get("layer_height")
        if height and layer:
            self.text("layers", "%.2f mm · %d layers"
                      % (layer, round(height / layer)))
        elif layer:
            self.text("layers", "%.2f mm" % layer)
        else:
            self.text("layers", "-")

    def touch(self, hit_id):
        if hit_id == "back":
            self.app.show("files")
        elif hit_id == "print" and self.filename:
            start_print(self.app, self.filename)


SCREENS = {"home": Home, "printing": Printing, "files": Files,
           "preview": Preview}
