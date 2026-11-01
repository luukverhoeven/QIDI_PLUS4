"""Formatting shared by the screens: colours, widths, durations."""

import os
import time


def c565(hexrgb):
    """RGB565 colour from "RRGGBB"."""
    r, g, b = (int(hexrgb[i:i + 2], 16) for i in (0, 2, 4))
    return (r >> 3) << 11 | (g >> 2) << 5 | (b >> 3)


# Colours of the design (screen/ui/design/ui.css).
BG = c565("0A0E13")
TEXT = c565("EAF0F6")
SUB = c565("94A2B4")
MUTE = c565("5D6A7B")
ACC = c565("2DD4BF")
AMBER = c565("FBBF24")
RED = c565("F43F5E")
BLUE = c565("60A5FA")

# Average glyph width in pixels of each screen font (Inter, see
# FONTS in screen/ui/build_assets.py), used to shorten text that would not
# fit its box. A little generous, so text is cut rather than clipped.
AVG_WIDTH = {0: 7.4, 1: 9.0, 2: 12.0, 3: 20.0, 4: 44.0}
ELLIPSIS = "…"


def fit(text, width, font):
    """``text`` shortened with an ellipsis to fit ``width`` pixels."""
    text = text or ""
    room = max(1, int(width / AVG_WIDTH.get(font, 9.0)))
    if len(text) <= room:
        return text
    return text[:room - 1].rstrip() + ELLIPSIS


def lines(text, room, count):
    """Word-wrap ``text`` into ``count`` lines of ``room`` characters."""
    words = (text or "").replace("\n", " ").split()
    out = [""]
    for word in words:
        line = out[-1]
        if not line:
            out[-1] = word
        elif len(line) + 1 + len(word) <= room:
            out[-1] = line + " " + word
        else:
            out.append(word)
    out = out + [""] * (count - len(out))
    if len(out) > count:
        rest = " ".join(out[count - 1:])
        out = out[:count - 1] + [rest]
    return [line if len(line) <= room else line[:room - 1] + ELLIPSIS
            for line in out]


def duration(seconds):
    if not seconds or seconds < 0:
        return "-"
    minutes = int(seconds // 60)
    if minutes < 60:
        return "%dm" % max(1, minutes)
    return "%dh %02dm" % (minutes // 60, minutes % 60)


def temp(value):
    return "%d°" % round(value or 0)


def target(value):
    return "%d°" % round(value) if value and value >= 1 else "off"


def clock(timestamp=None):
    return time.strftime("%H:%M", time.localtime(timestamp))


def file_title(path):
    """A file name as people read it: no folder, no extension."""
    name = os.path.basename(path or "")
    for ext in (".gcode", ".g"):
        if name.lower().endswith(ext):
            name = name[:-len(ext)]
    return name.replace("_", " ").replace("+", " ").strip()


def filament(meta):
    meta = meta or {}
    weight = meta.get("filament_weight_total")
    kind = (meta.get("filament_type") or "").split(";")[0]
    parts = []
    if weight:
        parts.append("%d g" % round(weight))
    if kind:
        parts.append(kind)
    return " · ".join(parts) or "-"
