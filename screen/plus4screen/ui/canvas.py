"""Draws the screens of ``plus4ui.tft`` with plain TJC drawing commands.

The screen file has no buttons or text fields. Each screen is a full-size
picture (``pic``); pressed and selected looks are cut from two more
pictures of the same screen (``xpic``); live text is drawn with ``xstr``
on top of the picture it sits on, so it never needs a background colour.

Everything sent is remembered, so a refresh only sends what changed.
"""

from .. import tjc

CANVAS_PAGE = 1          # the empty page of plus4ui.tft
ALIGN = {"left": 0, "center": 1, "right": 2}


def intersects(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


class Canvas:
    def __init__(self, send, layout):
        self.send = send
        self.layout = layout
        self.screen = None
        self.page = None
        self.pressed = None          # hit id drawn pressed
        self.toggles = {}            # toggle id -> on
        self.texts = {}              # text id -> (value, colour)
        self.bars = {}               # bar id -> (fraction, colour)
        self.dots = {}               # dot id -> colour

    # Screens ----------------------------------------------------------------

    def show(self, name):
        """Draw a screen from scratch."""
        if self.page != CANVAS_PAGE:
            self.send("page %d" % CANVAS_PAGE)
            self.page = CANVAS_PAGE
        self.screen = self.layout[name]
        self.pressed = None
        self.toggles = {}
        self.texts = {}
        self.bars = {}
        self.dots = {}
        self.send("pic 0,0,%d" % self.screen.bg)

    def forget(self):
        """The screen restarted: draw everything again on the next show."""
        self.page = None
        self.screen = None

    @property
    def name(self):
        return self.screen.name if self.screen else None

    # Live content -----------------------------------------------------------

    def text(self, text_id, value, color=None):
        item = self.screen.texts[text_id]
        value = "" if value is None else str(value)
        color = item.color if color is None else color
        if self.texts.get(text_id) == (value, color):
            return
        self.texts[text_id] = (value, color)
        self._draw_text(item, value, color)

    def toggle(self, toggle_id, on):
        on = bool(on)
        if self.toggles.get(toggle_id, False) == on:
            return               # the plain picture shows every toggle off
        self.toggles[toggle_id] = on
        item = self.screen.toggles[toggle_id]
        self._restore(item.rect)

    def bar(self, bar_id, fraction, color=None):
        item = self.screen.bars[bar_id]
        fraction = max(0.0, min(1.0, fraction or 0.0))
        color = item.fill if color is None else color
        key = (round(fraction * item.rect.w), color)
        if self.bars.get(bar_id) == key:
            return
        self.bars[bar_id] = key
        self._draw_bar(item, key)

    def dot(self, dot_id, color):
        if self.dots.get(dot_id) == color:
            return
        self.dots[dot_id] = color
        self._draw_dot(self.screen.dots[dot_id], color)

    def fill(self, rect, color):
        x, y, w, h = rect
        self.send("fill %d,%d,%d,%d,%d" % (x, y, w, h, color))

    def blank(self, rect, color):
        """Paint over a region and forget the live content drawn in it."""
        self.fill(rect, color)
        for cache, items in ((self.texts, self.screen.texts),
                             (self.bars, self.screen.bars),
                             (self.dots, self.screen.dots)):
            for item_id in [i for i in cache
                            if intersects(items[i].rect, rect)]:
                del cache[item_id]

    def restore(self, rect):
        """Cut a region from its picture again (after ``blank``)."""
        self._restore(rect)

    # Touch feedback ---------------------------------------------------------

    def press(self, hit_id):
        if self.screen.pressed is None:
            return
        hit = self.screen.hit(hit_id)
        if any(hit.rect == t.rect for t in self.screen.thumbs.values()):
            return                   # thumbnails are drawn by the screen
        self.pressed = hit_id
        self._restore(hit.rect)

    def release(self):
        if self.pressed is None:
            return
        hit = self.screen.hit(self.pressed)
        self.pressed = None
        self._restore(hit.rect)

    # Drawing ----------------------------------------------------------------

    def picture_at(self, rect):
        """The picture a region is cut from right now."""
        s = self.screen
        if self.pressed is not None and s.pressed is not None:
            if intersects(rect, s.hit(self.pressed).rect):
                return s.pressed
        if s.on is not None:
            for toggle_id, on in self.toggles.items():
                if on and intersects(rect, s.toggles[toggle_id].rect):
                    return s.on
        return s.bg

    def _restore(self, rect):
        """Cut a region from its current picture, then draw what is in it."""
        x, y, w, h = rect
        self.send("xpic %d,%d,%d,%d,%d,%d,%d"
                  % (x, y, w, h, x, y, self.picture_at(rect)))
        s = self.screen
        for text_id, (value, color) in self.texts.items():
            item = s.texts[text_id]
            if intersects(item.rect, rect):
                self._draw_text(item, value, color)
        for bar_id, key in self.bars.items():
            item = s.bars[bar_id]
            if intersects(item.rect, rect):
                self._draw_bar(item, key)
        for dot_id, color in self.dots.items():
            item = s.dots[dot_id]
            if intersects(item.rect, rect):
                self._draw_dot(item, color)

    def _draw_text(self, item, value, color):
        x, y, w, h = item.rect
        self.send('xstr %d,%d,%d,%d,%d,%d,%d,%d,1,0,"%s"'
                  % (x, y, w, h, item.font, color,
                     self.picture_at(item.rect), ALIGN[item.align],
                     tjc.quote(value)))

    def _draw_bar(self, item, key):
        width, color = key
        x, y, w, h = item.rect
        self.send("xpic %d,%d,%d,%d,%d,%d,%d"
                  % (x, y, w, h, x, y, self.picture_at(item.rect)))
        if width > 0:
            self.send("fill %d,%d,%d,%d,%d" % (x, y, width, h, color))

    def _draw_dot(self, item, color):
        x, y, w, h = item.rect
        self.send("cirs %d,%d,%d,%d" % (x + w // 2, y + h // 2,
                                        max(1, w // 2), color))
