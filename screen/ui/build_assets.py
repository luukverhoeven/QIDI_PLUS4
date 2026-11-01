"""Render the screen designs into pictures for the TJC editor and a layout map.

Run on a development machine (not the printer):

    ~/.venvs/rustwright/bin/python screen/ui/build_assets.py

It needs a Chromium driven through rustwright (Playwright API). For every
screen in design/ui.html it writes, into build/:

* pictures/NNN_<screen>_<kind>.png - full-screen pictures in the order the
  TJC editor must import them, so that picture N gets ID N. Kinds:
  ``bg`` (normal), ``pressed`` (every touch target pressed) and ``on``
  (every toggle selected). The screen draws ``bg`` and crops the others.
* preview/<screen>.png - the screen with sample values, for review only.
* layout.json - per screen: picture IDs, touch targets, toggles, live text
  (rectangle, font, colour), bars, dots and thumbnail slots.

plus4screen reads layout.json at runtime (copied to
``plus4screen/ui_layout.json``).
"""

import functools
import hashlib
import http.server
import json
import os
import shutil
import sys
import threading

from rustwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
DESIGN = os.path.join(HERE, "design")
BUILD = os.path.join(HERE, "build")
RUNTIME_COPY = os.path.join(HERE, "..", "plus4screen", "ui_layout.json")
SIZE = (800, 480)

# Screens in picture order. The boot screen comes first so that it is
# picture 0, which the boot page of the screen file shows.
SCREENS = ["boot", "home", "printing", "files", "preview", "move", "filament",
           "temps", "tools", "tool_run", "settings", "about", "keypad",
           "confirm", "message", "wifi", "wifi_pass"]

# Fonts of the screen file, in the order the TJC editor must add them.
# (CSS class, TJC font ID, family, CSS pixel size, weight)
FONTS = [("f0", 0, "Inter SemiBold", 13, 600),
         ("f1", 1, "Inter Bold", 15, 700),
         ("f2", 2, "Inter Bold", 20, 700),
         ("f3", 3, "Inter Bold", 34, 700),
         ("f4", 4, "Inter ExtraBold", 72, 800)]


def rgb565(rgb):
    r, g, b = rgb
    return (r >> 3) << 11 | (g >> 2) << 5 | (b >> 3)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(directory):
    handler = functools.partial(QuietHandler, directory=directory)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def render(page, base, screen, mode, path=None):
    page.goto("%s/ui.html?s=%s&mode=%s" % (base, screen, mode))
    page.evaluate("window.ready")
    if path:
        page.screenshot(path=path, clip={"x": 0, "y": 0,
                                         "width": SIZE[0], "height": SIZE[1]})


def convert(info):
    """Colours to RGB565 and fonts to TJC font IDs."""
    font_ids = {css: tjc for css, tjc, _, _, _ in FONTS}
    for text in info["texts"]:
        if text["font"] not in font_ids:
            raise SystemExit("unknown font %r on text %r"
                             % (text["font"], text["id"]))
        text["font"] = font_ids[text["font"]]
        text["color"] = rgb565(text["color"])
    for bar in info["bars"]:
        bar["track"] = rgb565(bar["track"])
        bar["fill"] = rgb565(bar["fill"])
    for dot in info["dots"]:
        dot["color"] = rgb565(dot["color"])
    return info


def check(name, info):
    """Fail on duplicate IDs and on annotations outside the screen."""
    for kind in ("hits", "toggles", "texts", "bars", "thumbs", "dots"):
        seen = set()
        for item in info[kind]:
            if item["id"] in seen:
                raise SystemExit("%s: duplicate %s id %r"
                                 % (name, kind, item["id"]))
            seen.add(item["id"])
            x, y, w, h = item["rect"]
            if w <= 0 or h <= 0 or x < 0 or y < 0 \
                    or x + w > SIZE[0] or y + h > SIZE[1]:
                raise SystemExit("%s: %s %r has rectangle %r"
                                 % (name, kind, item["id"], item["rect"]))


def screen_id(layout):
    """A number for this set of pictures and fonts. Program.s stores it in
    sys2, so plus4screen can tell that the screen has the matching file."""
    digest = hashlib.sha256()
    for picture in layout["pictures"]:
        with open(os.path.join(BUILD, "pictures", picture["file"]), "rb") as f:
            digest.update(f.read())
    digest.update(json.dumps(layout["fonts"], sort_keys=True).encode())
    return int(digest.hexdigest()[:7], 16) + 1     # 1 to 2^28, never 0


def main():
    # Only what this script makes; build/plus4ui.tft comes from the editor.
    for sub in ("pictures", "preview"):
        shutil.rmtree(os.path.join(BUILD, sub), ignore_errors=True)
        os.makedirs(os.path.join(BUILD, sub))
    server = serve(DESIGN)
    base = "http://127.0.0.1:%d" % server.server_address[1]
    layout = {"size": list(SIZE),
              "fonts": [{"id": tjc, "css": css, "family": family,
                         "css_px": px, "weight": weight}
                        for css, tjc, family, px, weight in FONTS],
              "pictures": [], "screens": {}}

    def add_picture(page, screen, kind):
        pid = len(layout["pictures"])
        name = "%03d_%s_%s.png" % (pid, screen, kind)
        render(page, base, screen, kind,
               os.path.join(BUILD, "pictures", name))
        layout["pictures"].append({"id": pid, "file": name,
                                   "screen": screen, "kind": kind})
        return pid

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": SIZE[0],
                                          "height": SIZE[1]})
        for screen in SCREENS:
            render(page, base, screen, "bg")
            info = convert(page.evaluate("window.collect(%s)"
                                         % json.dumps(screen)))
            check(screen, info)
            entry = {"bg": add_picture(page, screen, "bg")}
            if info["hits"]:
                entry["pressed"] = add_picture(page, screen, "pressed")
            if info["toggles"]:
                entry["on"] = add_picture(page, screen, "on")
            entry.update(info)
            layout["screens"][screen] = entry
            render(page, base, screen, "preview",
                   os.path.join(BUILD, "preview", screen + ".png"))
            print("%-9s pictures %s, %d hits, %d texts"
                  % (screen, [entry.get(k) for k in ("bg", "pressed", "on")
                              if k in entry],
                     len(info["hits"]), len(info["texts"])))
        browser.close()
    server.shutdown()

    layout["screen_id"] = screen_id(layout)
    print("screen id %d: put 'sys2=%d' in Program.s" % (layout["screen_id"],
                                                       layout["screen_id"]))
    for path in (os.path.join(BUILD, "layout.json"), RUNTIME_COPY):
        with open(path, "w") as f:
            json.dump(layout, f, indent=1, sort_keys=True)
            f.write("\n")
    print("%d pictures in %s" % (len(layout["pictures"]), BUILD))


if __name__ == "__main__":
    sys.exit(main())
