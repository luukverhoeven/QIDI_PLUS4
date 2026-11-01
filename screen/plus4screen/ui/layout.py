"""The screen layout made by ``screen/ui/build_assets.py``.

``ui_layout.json`` describes, per screen, the pictures in the screen file
(normal, pressed, selected) and where the touch targets, toggles, live
texts, bars, dots and thumbnail slots are. All positions are pixels on the
800x480 panel.
"""

import json
import os

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "ui_layout.json")


class Rect(tuple):
    """(x, y, w, h)"""

    def __new__(cls, rect):
        return super().__new__(cls, (int(v) for v in rect))

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    @property
    def w(self):
        return self[2]

    @property
    def h(self):
        return self[3]

    def contains(self, px, py):
        x, y, w, h = self
        return x <= px < x + w and y <= py < y + h

    def inside(self, other):
        x, y, w, h = self
        ox, oy, ow, oh = other
        return ox <= x and oy <= y and x + w <= ox + ow and y + h <= oy + oh


class Item:
    def __init__(self, data):
        self.id = data["id"]
        self.rect = Rect(data["rect"])
        self.font = data.get("font")
        self.color = data.get("color")
        self.align = data.get("align", "left")
        self.track = data.get("track")
        self.fill = data.get("fill")


class Screen:
    def __init__(self, name, data):
        self.name = name
        self.bg = data["bg"]
        self.pressed = data.get("pressed")
        self.on = data.get("on")
        self.hits = [Item(d) for d in data.get("hits", [])]
        self.toggles = {d["id"]: Item(d) for d in data.get("toggles", [])}
        self.texts = {d["id"]: Item(d) for d in data.get("texts", [])}
        self.bars = {d["id"]: Item(d) for d in data.get("bars", [])}
        self.dots = {d["id"]: Item(d) for d in data.get("dots", [])}
        self.thumbs = {d["id"]: Item(d) for d in data.get("thumbs", [])}

    def hit_at(self, x, y):
        """The touch target under (x, y); the smallest one if they nest."""
        found = [h for h in self.hits if h.rect.contains(x, y)]
        if not found:
            return None
        return min(found, key=lambda h: h.rect.w * h.rect.h)

    def hit(self, hit_id):
        for h in self.hits:
            if h.id == hit_id:
                return h
        raise KeyError(hit_id)


class Layout:
    def __init__(self, data):
        self.size = tuple(data["size"])
        self.screens = {name: Screen(name, d)
                        for name, d in data["screens"].items()}

    @classmethod
    def load(cls, path=DEFAULT_PATH):
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f))

    def __getitem__(self, name):
        return self.screens[name]
