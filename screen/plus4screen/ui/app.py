"""plus4screen with its own screen file (``plus4ui.tft``).

The screen only shows pictures and reports where it is touched
(``sendxy=1``). This module decides what is on screen: it keeps the
current screen, turns touches into actions, opens the keypad and the
dialogs, and dims the backlight when the screen is not used.
"""

import json
import logging
import os
import time

from .. import tjc
from ..moonraker import MoonrakerError
from ..printer import OBJECTS, PrinterState
from .canvas import Canvas
from .layout import Layout
from .thumbs import Thumbs
from . import control, dialogs, home, system, wifi

log = logging.getLogger("plus4screen")

PREFS_PATH = os.path.expanduser("~/.config/plus4screen.json")
DEFAULT_PREFS = {"brightness": 80, "sleep_minutes": 5}
PREF_RANGE = {"brightness": (10, 100), "sleep_minutes": (0, 240)}
NET_REFRESH = 30.0           # s between network look-ups
NAV = {"nav_home": "home", "nav_files": "files", "nav_move": "move",
       "nav_tools": "tools", "nav_settings": "settings"}
MODALS = ("keypad", "confirm", "message")


class Prefs(dict):
    def __init__(self, path):
        super().__init__(DEFAULT_PREFS)
        self.path = path
        try:
            with open(path, encoding="utf-8") as f:
                saved = json.load(f)
        except (OSError, ValueError):
            saved = {}
        for key, (low, high) in PREF_RANGE.items():
            value = saved.get(key) if isinstance(saved, dict) else None
            if isinstance(value, int) and not isinstance(value, bool):
                self[key] = max(low, min(high, value))

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(dict(self), f)
        except OSError as exc:
            log.warning("preferences not saved: %s", exc)


class UIApp:
    def __init__(self, write, moonraker, runner, layout=None, dry_run=False,
                 prefs_path=PREFS_PATH, clock=time.time, upload=None):
        self.write = write
        self.upload = upload          # (name, bytes) -> ok; see thumbs.py
        self.mr = moonraker
        self.runner = runner
        self.dry_run = dry_run
        self.clock = clock
        self.canvas = Canvas(self.send, layout or Layout.load())
        self.prefs = Prefs(prefs_path)
        self.state = PrinterState(online=False)
        self.screens = {}
        for module in (home, control, system, dialogs, wifi):
            for name, cls in module.SCREENS.items():
                self.screens[name] = cls(self)
        self.current = None
        self.modal_return = None
        self.touch_hit = None
        # Does the screen have the screen file ui_layout.json describes?
        # None until it answered "get sys2"; no id in the layout: no check.
        self.screen_ok = None if self.canvas.layout.screen_id else True
        self.last_touch = clock()
        self.asleep = False
        self.swallow = False
        self.net = {"ip": "", "ssid": ""}
        self.net_at = -NET_REFRESH
        self.meta = {}                  # filename -> slicer metadata
        self.thumbs = Thumbs(self)

    # Output -----------------------------------------------------------------

    def send(self, command):
        log.debug("-> %s", command)
        self.write(tjc.encode(command))

    def start(self):
        """(Re)initialise the screen and show the right screen."""
        self.canvas.forget()
        self.write(tjc.TERM)      # end whatever half command the screen has
        self.send("bkcmd=2")      # report failed commands only
        self.send("sendxy=1")
        self.send("dim=%d" % self.prefs["brightness"])
        if self.canvas.layout.screen_id:
            self.send("get sys2")
        self.asleep = False
        self.show(self.home_screen())

    def show(self, name, **options):
        self.current = name
        self.canvas.show(name)
        screen = self.screens[name]
        screen.enter(**options)
        screen.refresh(self.state)

    def home_screen(self):
        return "printing" if self.state.busy_printing else "home"

    # Dialogs ----------------------------------------------------------------

    def _open_modal(self, name, **options):
        if self.current not in MODALS:
            self.modal_return = self.current
        self.show(name, **options)

    def close_modal(self):
        self.show(self.modal_return or self.home_screen())

    def keypad(self, title, hint, value, low, high, on_ok, decimals=0,
               negative=False):
        self._open_modal("keypad", title=title, hint=hint, value=value,
                         low=low, high=high, on_ok=on_ok, decimals=decimals,
                         negative=negative)

    def confirm(self, title, body, yes, on_yes):
        self._open_modal("confirm", title=title, body=body, yes=yes,
                         on_yes=on_yes)

    def message(self, title, body):
        self._open_modal("message", title=title, body=body)

    # Printer ----------------------------------------------------------------

    def gcode(self, script, on_done=None):
        log.info("gcode: %s", script.replace("\n", " | "))
        if self.dry_run:
            if on_done:
                on_done(None, None)
            return
        self.runner.submit(lambda: self.mr.gcode(script),
                           on_done or self.report_error)

    def action(self, name, fn, on_done=None):
        """A Moonraker call that must not wait behind G-code."""
        log.info("action: %s", name)
        if self.dry_run:
            if on_done:
                on_done(None, None)
            return
        self.runner.spawn(fn, on_done or self.report_error)

    def report_error(self, _result, error):
        if error is not None:
            self.message("Klipper said no", str(error))

    def metadata(self, filename):
        """Slicer metadata of a file, or None while it is being read."""
        if not filename:
            return {}
        if filename in self.meta:
            return self.meta[filename]
        self.meta[filename] = None

        def done(meta, error):
            self.meta[filename] = meta or {}
            if self.current:
                self.screens[self.current].refresh(self.state)
        self.runner.spawn(lambda: self.mr.metadata(filename), done)
        return None

    def forget_changed_metadata(self, files):
        """Drop metadata and thumbnails of files changed since read."""
        for entry in files:
            meta = self.meta.get(entry.get("path"))
            if meta and meta.get("modified") not in (None,
                                                     entry.get("modified")):
                del self.meta[entry["path"]]
                self.thumbs.forget(entry["path"])

    def pump(self):
        """Background screen work between events: one thumbnail upload."""
        if self.touch_hit is None and not self.asleep:
            self.thumbs.pump()

    def motion_reason(self):
        """Why the axes, extruder and heaters must not be touched now."""
        s = self.state
        if s.busy_printing:
            return "Pause or stop the print first."
        if self.screens["filament"].running or self.screens["tool_run"].running:
            return "Wait for the running job to finish."
        return None

    def refuse_motion(self):
        """Show why motion is blocked; True when it is."""
        reason = self.motion_reason()
        if reason:
            self.message("Not now", reason)
        return bool(reason)

    def busy_reason(self):
        s = self.state
        if not s.online:
            return "Moonraker is not reachable."
        if not s.ready:
            return "Klipper is not ready."
        if s.busy_printing:
            return "Stop the print first."
        if self.screens["filament"].running or self.screens["tool_run"].running:
            return "Wait for the running job to finish."
        return None

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
        for screen in self.screens.values():
            screen.follow(old, state)
        self._follow_print(old, state)
        self._follow_network()
        if self.current:
            self.screens[self.current].refresh(state)
        self._follow_sleep()

    def _follow_print(self, old, new):
        was, now = old.print_state, new.print_state
        if was == now:
            return
        log.info("print state %s -> %s", was, now)
        if now in ("printing", "paused") and self.current in (
                "home", "files", "preview"):
            self.show("printing")
        elif was in ("printing", "paused") and self.current == "printing":
            name = os.path.basename(new.filename or old.filename)
            if now == "complete":
                self.message("Print finished", name)
                self.modal_return = "home"
            elif now == "error":
                self.message("Print failed", new.message or name)
                self.modal_return = "home"
            else:
                self.show("home")

    def _follow_network(self):
        if self.clock() - self.net_at < NET_REFRESH:
            return
        self.net_at = self.clock()
        self.runner.spawn(self.screens["settings"].read_network,
                          self._got_network)

    def _got_network(self, net, error):
        if error is None and net:
            self.net = net

    # Sleep ------------------------------------------------------------------

    def _follow_sleep(self):
        minutes = self.prefs["sleep_minutes"]
        if self.asleep or not minutes:
            return
        if self.clock() - self.last_touch > minutes * 60:
            log.info("screen off")
            self.send("dim=0")
            self.asleep = True

    def wake(self):
        self.send("dim=%d" % self.prefs["brightness"])
        self.asleep = False

    # Input ------------------------------------------------------------------

    def handle(self, event):
        if event.kind == tjc.XY:
            self.on_touch(*event.value)
        elif event.kind == tjc.NUMBER and self.screen_ok is None:
            self.check_screen(event.value)
        elif event.kind == tjc.BOOT:
            log.info("screen booted")
            self.start()
        elif event.kind == tjc.STATUS:
            level = logging.DEBUG if event.value == 0x01 else logging.INFO
            log.log(level, "screen status 0x%02x", event.value)

    def check_screen(self, value):
        expected = self.canvas.layout.screen_id
        self.screen_ok = value == expected
        if self.screen_ok:
            log.info("screen file matches (id %d)", value)
        else:
            log.error("the screen file does not match ui_layout.json (screen "
                      "says %d, expected %d): touches are ignored. Write "
                      "ui/build/plus4ui.tft with python3 -m plus4screen.flash",
                      value, expected)

    def on_touch(self, x, y, pressed):
        if not self.screen_ok:
            if pressed:
                log.warning("touch ignored: screen file not confirmed")
            return
        self.last_touch = self.clock()
        if self.asleep:
            if not pressed:
                return
            self.wake()
            hit = self.canvas.screen and self.canvas.screen.hit_at(x, y)
            if not (hit and hit.id == "estop"):
                self.swallow = True       # the waking touch does nothing
                return
        if self.swallow:
            if not pressed:
                self.swallow = False
            return
        if self.canvas.screen is None:
            return
        hit = self.canvas.screen.hit_at(x, y)
        if pressed:
            self.touch_hit = (self.current, hit.id) if hit else None
            if hit:
                self.canvas.press(hit.id)
            return
        self.canvas.release()
        target, self.touch_hit = self.touch_hit, None
        # Only a release on the same button of the same screen counts.
        if hit is None or target != (self.current, hit.id):
            return
        target = hit.id
        log.info("touch %s.%s", self.current, target)
        self.on_hit(target)

    def on_hit(self, hit_id):
        if hit_id in NAV:
            name = NAV[hit_id]
            if name == "home":
                name = self.home_screen()
            elif name == "tools" and self.screens["tool_run"].job:
                name = "tool_run"
            self.show(name)
        elif hit_id == "estop":
            self.confirm("Emergency stop?", "Klipper stops at once and needs "
                         "a firmware restart afterwards.", "Stop now",
                         lambda: self.action("emergency stop",
                                             self.mr.emergency_stop))
        else:
            self.screens[self.current].touch(hit_id)
