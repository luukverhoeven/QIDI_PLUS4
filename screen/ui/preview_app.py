"""Run plus4screen's interface against a made-up printer and save what the
screen would show, one PNG per step, in build/app-preview/.

    python3 screen/ui/preview_app.py     (needs Pillow)
"""

import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from emulator import Emulator  # noqa: E402
from plus4screen import tjc  # noqa: E402
from plus4screen.ui.app import UIApp  # noqa: E402
from plus4screen.ui.layout import Layout  # noqa: E402

OUT = os.path.join(HERE, "build", "app-preview")
NOW = time.time()


def status(printing=False):
    return {
        "webhooks": {"state": "ready", "state_message": "Printer is ready"},
        "extruder": {"temperature": 186.4, "target": 220.0},
        "heater_bed": {"temperature": 60.1, "target": 60.0},
        "heater_generic chamber": {"temperature": 31.0, "target": 0.0},
        "fan_generic cooling_fan": {"speed": 0.0},
        "fan_generic auxiliary_cooling_fan": {"speed": 0.0},
        "fan_generic chamber_circulation_fan": {"speed": 0.3},
        "print_stats": {"state": "printing" if printing else "standby",
                        "filename": "Macbook_14__Riser.gcode"
                        if printing else "",
                        "print_duration": 4380.0, "total_duration": 4500.0,
                        "info": {"current_layer": 112, "total_layer": 240},
                        "message": ""},
        "virtual_sdcard": {"progress": 0.47 if printing else 0.0},
        "gcode_move": {"speed_factor": 1.0, "extrude_factor": 1.0,
                       "homing_origin": [0, 0, 0.02, 0]},
        "output_pin caselight": {"value": 1.0},
        "toolhead": {"position": [120.0, 120.0, 10.0, 0.0],
                     "homed_axes": "xyz"},
    }


FILES = ["gabbys_cookie_cutter.gcode", "Pom Hedgehog No Ears_fixed.gcode",
         "Body1.gcode", "OutletSocket.gcode", "Macbook_14__Riser.gcode",
         "Gira+Standard+55_compatibility2_Single Frame.gcode",
         "Gira_Rahmen_123fach_plate_1.gcode", "USB/benchy.gcode"]


class FakeMoonraker:
    printing = False

    def query(self, objects):
        if "mcu" in objects:
            return {"mcu": {"mcu_version": "v0.12.0-65"},
                    "mcu U_1": {"mcu_version": "v0.12.0-65"}}
        return status(self.printing)

    def gcode(self, script):
        return None

    def list_files(self):
        return [{"path": p, "modified": NOW - i} for i, p in enumerate(FILES)]

    def metadata(self, filename):
        return {"estimated_time": 9267, "filament_weight_total": 97.1,
                "filament_type": "PLA", "layer_height": 0.2,
                "object_height": 48.0}

    def last_job(self):
        return {"filename": "Macbook_14__Riser.gcode", "status": "completed",
                "end_time": NOW - 3600, "print_duration": 9240,
                "metadata": self.metadata("")}

    def system_info(self):
        return {"network": {"wlan0": {"ip_addresses": [
            {"family": "ipv4", "address": "192.168.86.210"}]}}}

    def printer_info(self):
        return {"software_version": "v0.12.0-65"}

    def server_info(self):
        return {"moonraker_version": "v0.8.0-379"}

    def gcode_store(self, count=100):
        return []

    def __getattr__(self, name):
        # pause, resume, cancel, start_print, restarts: nothing to show.
        return lambda *args: None


class SyncRunner:
    def submit(self, fn, on_done=None):
        self.spawn(fn, on_done)

    def spawn(self, fn, on_done=None):
        try:
            result, error = fn(), None
        except Exception as exc:
            result, error = None, exc
        if on_done:
            on_done(result, error)

    def drain(self):
        pass


def main():
    os.makedirs(OUT, exist_ok=True)
    emu = Emulator()
    sent = []

    def write(data):
        for part in data.split(tjc.TERM):
            if part:
                command = part.decode("utf-8")
                sent.append(command)
                emu.command(command)

    mr = FakeMoonraker()
    prefs = os.path.join(tempfile.mkdtemp(), "prefs.json")
    app = UIApp(write, mr, SyncRunner(), Layout.load(
        os.path.join(HERE, "build", "layout.json")), prefs_path=prefs)
    app.poll()
    app.start()
    app.poll()

    def save(name):
        emu.image.save(os.path.join(OUT, name + ".png"))

    def tap(screen, hit_id, pressed_name=None):
        x, y, w, h = app.canvas.screen.hit(hit_id).rect
        app.on_touch(x + w // 2, y + h // 2, True)
        if pressed_name:
            save(pressed_name)
        app.on_touch(x + w // 2, y + h // 2, False)

    save("01_home")
    tap("home", "home_all", "02_home_pressed")
    app.show("files")
    save("03_files")
    tap("files", "file4")
    save("04_preview")
    app.show("move")
    save("05_move")
    tap("move", "step50")
    save("06_move_step50")
    app.show("filament")
    save("07_filament")
    app.show("temps")
    save("08_temps")
    app.show("tools")
    save("09_tools")
    tap("tools", "level")
    save("10_keypad")
    for key in ("k7", "k5"):
        tap("keypad", key)
    save("11_keypad_75")
    tap("keypad", "ok")
    save("12_tool_run")
    app.show("settings")
    save("13_settings")
    tap("settings", "about")
    save("14_about")
    tap("about", "nav_settings")
    tap("settings", "reboot")
    save("15_confirm")
    tap("confirm", "no")
    mr.printing = True
    app.show("home")
    app.poll()
    save("16_printing")
    tap("printing", "stop")
    save("17_confirm_stop")
    tap("confirm", "no")
    app.message("Klipper said no", "Must home axis first: 120.000 120.000 "
                "10.000 [0.000]")
    save("18_message")
    if emu.unknown:
        print("unknown commands:", sorted(set(c.split()[0]
                                              for c in emu.unknown)))
    print("%d commands, pictures in %s" % (len(sent), OUT))


if __name__ == "__main__":
    main()
