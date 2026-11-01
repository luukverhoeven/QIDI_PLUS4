"""Moving the axes, loading filament, heaters and fans."""

import logging

from .base import Screen
from .home import HEAT_CMD, HEATERS, heater_look, set_heater
from .text import ACC, AMBER, RED, SUB, TEXT, target, temp

log = logging.getLogger("plus4screen")

STEPS = {"step1": 1, "step10": 10, "step50": 50, "step100": 100}
JOG = {"x_minus": ("X", -1), "x_plus": ("X", 1), "y_minus": ("Y", -1),
       "y_plus": ("Y", 1), "z_up": ("Z", 1), "z_down": ("Z", -1)}
JOG_FEED = {"X": 6000, "Y": 6000, "Z": 600}
EXTRUDE_MM = 10
EXTRUDE_FEED = 300
MIN_EXTRUDE_TEMP = 170
MATERIALS = {"mat_pla": 220, "mat_petg": 250, "mat_abs": 260, "mat_pa": 300}
FAN_NAMES = ("cooling_fan", "auxiliary_cooling_fan", "chamber_circulation_fan")
FAN_STEP = 10
PRESETS = {"pre_pla": (220, 60), "pre_petg": (250, 70),
           "pre_abs": (260, 100)}


class Move(Screen):
    name = "move"

    def __init__(self, app):
        super().__init__(app)
        self.step = 10

    def enter(self, **options):
        for hit, mm in STEPS.items():
            self.canvas.toggle(hit, mm == self.step)

    def refresh(self, s):
        x, y, z = s.position[:3]
        homed = s.homed_axes.upper()
        note = "homed" if homed == "XYZ" else (
            "homed %s" % homed if homed else "not homed")
        self.text("position", "X %.1f · Y %.1f · Z %.1f · %s"
                  % (x, y, z, note))
        self.text("z", "%.1f" % z)
        self.text("extruder", "%d mm · nozzle %s"
                  % (EXTRUDE_MM, temp(s.temps[0][0])))

    def touch(self, hit_id):
        app, s = self.app, self.state
        if hit_id in STEPS:
            self.step = STEPS[hit_id]
            self.enter()
        elif hit_id in JOG:
            if s.busy_printing:
                app.message("Not while printing", "Pause or stop the print "
                            "before moving the axes.")
                return
            axis, sign = JOG[hit_id]
            app.gcode("G91\nG1 %s%g F%d\nG90"
                      % (axis, sign * self.step, JOG_FEED[axis]))
        elif hit_id == "home_xy":
            app.gcode("G28 X Y")
        elif hit_id == "home_all":
            app.gcode("G28")
        elif hit_id in ("retract", "extrude"):
            if s.temps[0][0] < MIN_EXTRUDE_TEMP:
                app.message("Nozzle too cold", "Heat the nozzle to at least "
                            "%d °C first." % MIN_EXTRUDE_TEMP)
                return
            sign = -1 if hit_id == "retract" else 1
            app.gcode("G91\nG1 E%d F%d\nG90"
                      % (sign * EXTRUDE_MM, EXTRUDE_FEED))
        elif hit_id == "motors_off":
            app.gcode("M84")
        elif hit_id == "filament":
            app.show("filament")
        elif hit_id == "temps":
            app.show("temps")


class Job:
    """A filament load or unload run by the LOAD_/UNLOAD_FILAMENT macros."""

    def __init__(self, kind, temp_c):
        self.kind = kind          # "load" or "unload"
        self.temp = temp_c
        self.stage = "heating"    # heating -> working -> done / failed
        self.error = None

    @property
    def running(self):
        return self.stage in ("heating", "working")


class Filament(Screen):
    name = "filament"

    def __init__(self, app):
        super().__init__(app)
        self.material = "mat_petg"
        self.custom = 230
        self.job = None

    @property
    def running(self):
        return bool(self.job and self.job.running)

    @property
    def temp(self):
        return MATERIALS.get(self.material, self.custom)

    def enter(self, **options):
        for hit in list(MATERIALS) + ["mat_custom"]:
            self.canvas.toggle(hit, hit == self.material)
        self.text("custom", "%d°" % self.custom)

    def follow(self, old, new):
        job = self.job
        if job and job.stage == "heating" and \
                new.temps[0][0] >= job.temp - 5:
            job.stage = "working"

    def refresh(self, s):
        current, goal = s.temps[0]
        job = self.job
        aim = job.temp if job and job.running else self.temp
        self.text("temp", temp(current))
        self.text("target", "of %d°" % aim)
        color, fraction, bar = heater_look(current, goal or aim)
        self.canvas.bar("heat", min(1.0, current / aim) if aim else 0, bar)
        stage = self.stage()
        self.canvas.toggle("stage1", stage >= 1)
        self.canvas.toggle("stage2", stage >= 2)
        self.canvas.toggle("stage3", stage >= 3)
        title, detail, color = self.status()
        self.text("status", title, color)
        self.text("detail1", detail[0])
        self.text("detail2", detail[1])
        self.text("hint", "Pick a material, then unload or load")

    def stage(self):
        job = self.job
        if not job:
            return 1
        if job.kind == "unload":
            return 2 if job.stage != "done" else 3
        return 3

    def status(self):
        job = self.job
        if not job:
            return ("Ready", ["Unload cuts the filament and pulls it back.",
                              "Load pushes filament until it leaves the "
                              "nozzle."], TEXT)
        verb = "Loading" if job.kind == "load" else "Unloading"
        if job.stage == "heating":
            return ("Heating to %d°" % job.temp,
                    ["%s starts when the nozzle is hot." % verb, ""], AMBER)
        if job.stage == "working":
            return ("%s…" % verb, ["Keep the filament path clear.",
                                         ""], AMBER)
        if job.stage == "failed":
            return ("Failed", [job.error or "", ""], RED)
        if job.kind == "unload":
            return ("Unloaded", ["Pull the filament out of the extruder,",
                                 "then insert the new filament and Load."],
                    ACC)
        return ("Loaded", ["Clean the nozzle before printing.", ""], ACC)

    def touch(self, hit_id):
        app = self.app
        if hit_id in MATERIALS:
            self.material = hit_id
            self.enter()
        elif hit_id == "mat_custom":
            def chosen(value):
                self.custom = value
                self.material = "mat_custom"
            app.keypad("Filament temperature", "180 to 300 °C",
                       self.custom, 180, 300, chosen)
        elif hit_id in ("load", "unload"):
            self.start(hit_id)
        elif hit_id == "close":
            app.show("move")

    def start(self, kind):
        app = self.app
        if self.running:
            return
        reason = app.busy_reason()
        if reason:
            app.message("Cannot %s now" % kind, reason)
            return
        job = self.job = Job(kind, self.temp)
        macro = "UNLOAD_FILAMENT" if kind == "unload" else "LOAD_FILAMENT"

        def done(_result, error):
            job.stage = "failed" if error is not None else "done"
            job.error = str(error) if error is not None else None
            if app.current == self.name:
                self.refresh(app.state)
        app.gcode("%s TEMP=%d" % (macro, job.temp), done)
        self.refresh(app.state)


class Temps(Screen):
    name = "temps"

    def refresh(self, s):
        for i, name in enumerate(HEATERS):
            current, goal = s.temps[i]
            color, _, _ = heater_look(current, goal)
            self.text(name, temp(current), SUB)
            self.text(name + "_target", target(goal),
                      TEXT if goal >= 1 else SUB)
        for i in range(3):
            self.text("fan%d" % i, "%d%%" % s.fans[i])

    def touch(self, hit_id):
        app, s = self.app, self.state
        if hit_id.startswith("set_"):
            set_heater(app, HEATERS.index(hit_id[4:]))
        elif hit_id.startswith("off_"):
            app.gcode(HEAT_CMD[HEATERS.index(hit_id[4:])] % 0)
        elif hit_id.startswith("fan"):
            index = int(hit_id[3])
            step = FAN_STEP if hit_id.endswith("_up") else -FAN_STEP
            value = max(0, min(100, s.fans[index] + step))
            app.gcode("SET_FAN_SPEED FAN=%s SPEED=%.2f"
                      % (FAN_NAMES[index], value / 100.0))
        elif hit_id in PRESETS:
            nozzle, bed = PRESETS[hit_id]
            app.gcode("M104 S%d\nM140 S%d" % (nozzle, bed))
        elif hit_id == "cooldown":
            app.gcode("M104 S0\nM140 S0\nM141 S0")
        elif hit_id == "close":
            app.show("move")


SCREENS = {"move": Move, "filament": Filament, "temps": Temps}
