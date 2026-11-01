"""Snapshot of the printer state, built from a Moonraker objects query."""

# Klipper objects and fields read on every refresh. Objects that do not
# exist on a printer are left out of Klipper's answer.
OBJECTS = {
    "webhooks": ["state", "state_message"],
    "extruder": ["temperature", "target"],
    "heater_bed": ["temperature", "target"],
    "heater_generic chamber": ["temperature", "target"],
    "fan_generic cooling_fan": ["speed"],
    "fan_generic auxiliary_cooling_fan": ["speed"],
    "fan_generic chamber_circulation_fan": ["speed"],
    "print_stats": ["state", "filename", "print_duration", "total_duration",
                    "info", "message"],
    "virtual_sdcard": ["progress"],
    "display_status": ["progress"],
    "gcode_move": ["speed_factor", "extrude_factor", "homing_origin"],
    "motion_report": ["live_velocity"],
    "output_pin caselight": ["value"],
    "toolhead": ["position", "homed_axes"],
}

# Fans in the order the screen shows them (n6, n7, n8 / slider 22, 23, 24).
FANS = ["cooling_fan", "auxiliary_cooling_fan", "chamber_circulation_fan"]

# Heaters in the order of the screen's ``sys0`` (0, 1, 2).
HEATERS = ["extruder", "heater_bed", "heater_generic chamber"]


class PrinterState:
    def __init__(self, status=None, online=True, error=""):
        status = status or {}
        self.online = online
        self.error = error              # why the status could not be read
        g = lambda obj, key, default=0.0: (status.get(obj) or {}).get(
            key, default)
        self.klippy_state = g("webhooks", "state", "") if online else "offline"
        self.state_message = g("webhooks", "state_message", "")
        self.temps = [(g(h, "temperature"), g(h, "target")) for h in HEATERS]
        self.fans = [round(100 * (g("fan_generic " + f, "speed") or 0))
                     for f in FANS]
        self.print_state = g("print_stats", "state", "standby")
        self.filename = g("print_stats", "filename", "") or ""
        self.print_duration = g("print_stats", "print_duration")
        self.total_duration = g("print_stats", "total_duration")
        self.message = g("print_stats", "message", "") or ""
        info = g("print_stats", "info", {}) or {}
        self.current_layer = info.get("current_layer") or 0
        self.total_layer = info.get("total_layer") or 0
        progress = g("virtual_sdcard", "progress", None)
        if progress is None:
            progress = g("display_status", "progress")
        self.progress = progress or 0.0
        self.speed_factor = g("gcode_move", "speed_factor", 1.0)
        self.extrude_factor = g("gcode_move", "extrude_factor", 1.0)
        origin = g("gcode_move", "homing_origin", [0, 0, 0, 0]) or [0] * 4
        self.z_offset = origin[2] if len(origin) > 2 else 0.0
        self.velocity = g("motion_report", "live_velocity")
        self.caselight = bool(g("output_pin caselight", "value"))
        position = g("toolhead", "position", None) or [0.0] * 4
        self.position = list(position) + [0.0] * (4 - len(position))
        self.homed_axes = g("toolhead", "homed_axes", "") or ""

    @property
    def ready(self):
        return self.klippy_state == "ready"

    @property
    def busy_printing(self):
        return self.print_state in ("printing", "paused")

    def remaining(self, estimate=None):
        """Seconds left, from the slicer estimate or from the progress."""
        if estimate:
            return max(0.0, estimate - self.print_duration)
        if self.progress > 0.001:
            return max(0.0, self.print_duration / self.progress
                       - self.print_duration)
        return 0.0


def hhmm(seconds):
    seconds = int(seconds or 0)
    return "%02dh%02dm" % (seconds // 3600, seconds // 60 % 60)
