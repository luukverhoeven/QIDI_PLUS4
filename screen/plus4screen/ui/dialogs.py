"""The keypad, the confirm dialog and the message dialog.

They take the whole screen; closing one shows the screen it was opened
from again (``UIApp.close_modal``).
"""

from .base import Screen
from .text import RED, SUB, lines

BODY_ROOM = 54               # characters per dialog body line
MAX_DIGITS = 7


def number_text(value, decimals):
    if decimals:
        return ("%%.%df" % decimals) % value
    return "%d" % round(value)


class Keypad(Screen):
    name = "keypad"

    def enter(self, title="", hint="", value=0, low=0, high=0, on_ok=None,
              decimals=0, negative=False):
        self.title, self.hint = title, hint
        self.low, self.high = low, high
        self.on_ok = on_ok
        self.decimals, self.negative = decimals, negative
        self.entry = number_text(value, decimals)
        self.fresh = True        # the first key replaces the shown value
        self.text("title", title)
        self.text("hint", hint, SUB)
        self.draw()

    def draw(self):
        self.text("value", self.entry or "0")

    def touch(self, hit_id):
        if hit_id.startswith("k") and hit_id[1:].isdigit():
            self.type(hit_id[1:])
        elif hit_id == "kdot":
            if self.decimals and "." not in self.entry:
                self.type("." if self.entry and not self.fresh else "0.")
        elif hit_id == "ksign":
            if self.negative:
                self.fresh = False
                self.entry = self.entry[1:] if self.entry.startswith("-") \
                    else "-" + self.entry
                self.draw()
        elif hit_id == "kback":
            self.fresh = False
            self.entry = self.entry[:-1]
            self.draw()
        elif hit_id == "cancel":
            self.app.close_modal()
        elif hit_id == "ok":
            self.accept()

    def type(self, chars):
        if self.fresh:
            self.entry = "-" if self.entry.startswith("-") and \
                self.negative and chars != "0." else ""
            self.fresh = False
        if len(self.entry.replace("-", "").replace(".", "")) >= MAX_DIGITS:
            return
        if "." in self.entry and len(self.entry.split(".")[1]) >= \
                self.decimals and chars != ".":
            return
        self.entry += chars
        self.draw()

    def accept(self):
        if self.entry in ("", "-", ".", "-."):
            self.app.close_modal()
            return
        try:
            value = float(self.entry)
        except ValueError:
            value = None
        if value is None or not self.low <= value <= self.high:
            self.text("hint", "Use a value from %s to %s"
                      % (number_text(self.low, self.decimals),
                         number_text(self.high, self.decimals)), RED)
            return
        if not self.decimals:
            value = int(round(value))
        on_ok = self.on_ok
        self.app.close_modal()
        if on_ok:
            on_ok(value)


class Confirm(Screen):
    name = "confirm"

    def enter(self, title="", body="", yes="OK", on_yes=None):
        self.on_yes = on_yes
        self.text("title", title)
        body = lines(body, BODY_ROOM, 2)
        self.text("body1", body[0])
        self.text("body2", body[1])
        self.text("yes", yes)

    def touch(self, hit_id):
        if hit_id == "no":
            self.app.close_modal()
        elif hit_id == "yes":
            on_yes = self.on_yes
            self.app.close_modal()
            if on_yes:
                on_yes()


class Message(Screen):
    name = "message"

    def enter(self, title="", body=""):
        self.text("title", title)
        body = lines(body, BODY_ROOM, 3)
        for i, line in enumerate(body):
            self.text("body%d" % (i + 1), line)

    def touch(self, hit_id):
        if hit_id == "ok":
            self.app.close_modal()


SCREENS = {"keypad": Keypad, "confirm": Confirm, "message": Message}
