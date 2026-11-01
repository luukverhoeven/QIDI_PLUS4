"""Draws what plus4ui.tft would show for a list of TJC commands.

A development aid, not used on the printer: it needs Pillow and the
pictures in build/pictures. It understands the commands plus4screen's
canvas sends (page, pic, xpic, xstr, fill, cirs) and approximates the
screen fonts with the Inter files the fonts were made from.
"""

import csv
import io
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
FONTS = os.path.join(HERE, "design", "fonts")
CANVAS_BG = (10, 14, 19)
# TJC font ID -> (file, pixel size); see FONTS in build_assets.py.
FONT_FILES = {0: ("Inter-SemiBold.ttf", 13), 1: ("Inter-Bold.ttf", 15),
              2: ("Inter-Bold.ttf", 20), 3: ("Inter-Bold.ttf", 33),
              4: ("Inter-ExtraBold.ttf", 72)}


def rgb(c565):
    r, g, b = (c565 >> 11) & 31, (c565 >> 5) & 63, c565 & 31
    return (r * 255 // 31, g * 255 // 63, b * 255 // 31)


def split_args(text):
    return next(csv.reader(io.StringIO(text), skipinitialspace=True))


class Emulator:
    def __init__(self, build=BUILD):
        with open(os.path.join(build, "layout.json")) as f:
            layout = json.load(f)
        self.pictures = {p["id"]: Image.open(os.path.join(
            build, "pictures", p["file"])).convert("RGB")
            for p in layout["pictures"]}
        self.fonts = {i: ImageFont.truetype(os.path.join(FONTS, name), size)
                      for i, (name, size) in FONT_FILES.items()}
        self.image = Image.new("RGB", tuple(layout["size"]), (0, 0, 0))
        self.unknown = []

    def run(self, commands):
        for command in commands:
            self.command(command)
        return self.image

    def command(self, command):
        name, _, rest = command.partition(" ")
        if "=" in name and not rest:
            return                    # system variable, e.g. sendxy=1
        handler = getattr(self, "do_" + name, None)
        if handler is None:
            self.unknown.append(command)
            return
        handler(split_args(rest) if rest else [])

    def do_page(self, args):
        page = int(args[0])
        if page == 0:
            self.image.paste(self.pictures[0], (0, 0))
        else:
            self.image.paste(CANVAS_BG, (0, 0, *self.image.size))

    def do_pic(self, args):
        x, y, pid = map(int, args)
        self.image.paste(self.pictures[pid], (x, y))

    def do_xpic(self, args):
        x, y, w, h, x0, y0, pid = map(int, args)
        self.image.paste(self.pictures[pid].crop((x0, y0, x0 + w, y0 + h)),
                         (x, y))

    def do_fill(self, args):
        x, y, w, h, color = map(int, args)
        ImageDraw.Draw(self.image).rectangle((x, y, x + w - 1, y + h - 1),
                                             fill=rgb(color))

    def do_cirs(self, args):
        x, y, r, color = map(int, args)
        ImageDraw.Draw(self.image).ellipse((x - r, y - r, x + r, y + r),
                                           fill=rgb(color))

    def do_xstr(self, args):
        x, y, w, h, font, pco, bco, xcen, ycen, sta = map(int, args[:10])
        text = args[10]
        box = Image.new("RGB", (w, h), rgb(bco))
        if sta == 0:
            box = self.pictures[bco].crop((x, y, x + w, y + h))
        draw = ImageDraw.Draw(box)
        f = self.fonts[font]
        left, top, right, bottom = draw.textbbox((0, 0), text, font=f)
        tw = right - left
        ascent, descent = f.getmetrics()
        tx = {0: 0, 1: (w - tw) // 2, 2: w - tw}[xcen] - left
        ty = (h - ascent - descent) // 2 if ycen == 1 else 0
        draw.text((tx, ty), text, font=f, fill=rgb(pco))
        self.image.paste(box, (x, y))
