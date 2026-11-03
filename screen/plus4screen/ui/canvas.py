"""Draws the screens of ``plus4ui.tft`` with plain TJC drawing commands.

The screen file has no buttons or text fields. Each screen is a full-size
picture (``pic``); pressed and selected looks are cut from two more
pictures of the same screen (``xpic``); live text is drawn with ``xstr``
on top of the picture it sits on, so it never needs a background colour.

Everything sent is remembered, so a refresh only sends what changed.

The screen repaints the page by itself while a file (a thumbnail) is
written to it: from the page's own background picture, then the thumbnail
objects, wiping everything drawn here. So page 1 has a picture background
(``sta`` 2) that follows the screen shown (``page1.pic``), and ``repaint``
draws the live content again after each upload.

Such a redraw (also the one a change of ``page1.pic`` asks for) runs only
once the screen has worked through all commands it has received. Drawing
sent straight after would be wiped, so ``settle`` pauses first.
"""

from .. import tjc

CANVAS_PAGE = 1          # the empty page of plus4ui.tft
ALIGN = {"left": 0, "center": 1, "right": 2}


def intersects(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def inside(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return bx <= ax and by <= ay and ax + aw <= bx + bw and ay + ah <= by + bh


class Canvas:
    def __init__(self, send, layout, settle=None):
        self.send = send
        self.layout = layout
        # Lets the screen run a pending page redraw (time.sleep on the
        # printer, nothing in tests).
        self.settle = settle or (lambda: None)
        self.screen = None
        self.page = None
        self.pressed = None          # hit id drawn pressed
        self.toggles = {}            # toggle id -> on
        self.texts = {}              # text id -> (value, colour)
        self.bars = {}               # bar id -> (fraction, colour)
        self.dots = {}               # dot id -> colour
        self.fills = []              # (rect, colour) painted by blank()
        self.objects = {}            # visible picture object -> (rect, path)

    # Screens ----------------------------------------------------------------

    def show(self, name):
        """Draw a screen from scratch."""
        if self.page != CANVAS_PAGE:
            self.send("page %d" % CANVAS_PAGE)
            self.send("vis 255,0")   # the thumbnail objects start hidden
            self.page = CANVAS_PAGE
            self.objects = {}
        # Hide thumbnails before the picture: hiding repaints their area.
        for number in sorted(self.objects):
            self.send("vis exp%d,0" % number)
        self.objects = {}
        self.screen = self.layout[name]
        self.pressed = None
        self.toggles = {}
        self.texts = {}
        self.bars = {}
        self.dots = {}
        self.fills = []
        self.send("page%d.pic=%d" % (CANVAS_PAGE, self.screen.bg))
        self.settle()
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

    def thumb(self, number, rect, path, reload=False):
        """Show picture object ``exp<number>`` at ``rect`` with a file
        written to the screen (see thumbs.py); ``reload`` after the file
        was written again under the same name."""
        if self.objects.get(number) == (tuple(rect), path) and not reload:
            return
        x, y, _, _ = rect
        self.send('exp%d.path="%s"' % (number, path))
        self.send("exp%d.x=%d" % (number, x))
        self.send("exp%d.y=%d" % (number, y))
        if number in self.objects:
            self.send("ref exp%d" % number)
        else:
            self.send("vis exp%d,1" % number)
        self.objects[number] = (tuple(rect), path)

    def hide_thumb(self, number):
        shown = self.objects.pop(number, None)
        if shown is not None:
            self.send("vis exp%d,0" % number)
            self.settle()            # the screen redraws the area first
            self._restore(shown[0])

    def blank(self, rect, color):
        """Paint over a region and forget the live content drawn in it."""
        hidden = [n for n, (r, _) in self.objects.items()
                  if intersects(r, rect)]
        for number in hidden:
            self.send("vis exp%d,0" % number)
            del self.objects[number]
        if hidden:
            self.settle()            # the screen redraws the area first
        self.fill(rect, color)
        self.fills.append((tuple(rect), color))
        for cache, items in ((self.texts, self.screen.texts),
                             (self.bars, self.screen.bars),
                             (self.dots, self.screen.dots)):
            for item_id in [i for i in cache
                            if intersects(items[i].rect, rect)]:
                del cache[item_id]

    def restore(self, rect):
        """Cut a region from its picture again (after ``blank``)."""
        self.fills = [f for f in self.fills if not inside(f[0], rect)]
        self._restore(rect)

    def repaint(self):
        """Draw the live content again after the screen repainted the page
        from its background picture."""
        s = self.screen
        if s is None:
            return
        if s.on is not None:
            for toggle_id, on in sorted(self.toggles.items()):
                if on:
                    self._cut(s.toggles[toggle_id].rect, s.on)
        if self.pressed is not None and s.pressed is not None:
            self._cut(s.hit(self.pressed).rect, s.pressed)
        for rect, color in self.fills:
            self.fill(rect, color)
        for text_id, (value, color) in self.texts.items():
            self._draw_text(s.texts[text_id], value, color)
        for bar_id, key in self.bars.items():
            self._draw_bar(s.bars[bar_id], key)
        for dot_id, color in self.dots.items():
            self._draw_dot(s.dots[dot_id], color)

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
        self._cut(rect, self.picture_at(rect))
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
        for number, (obj_rect, _) in sorted(self.objects.items()):
            if intersects(obj_rect, rect):
                self.send("ref exp%d" % number)

    def _cut(self, rect, picture):
        x, y, w, h = rect
        self.send("xpic %d,%d,%d,%d,%d,%d,%d" % (x, y, w, h, x, y, picture))

    def _draw_text(self, item, value, color):
        x, y, w, h = item.rect
        self.send('xstr %d,%d,%d,%d,%d,%d,%d,%d,1,0,"%s"'
                  % (x, y, w, h, item.font, color,
                     self.picture_at(item.rect), ALIGN[item.align],
                     tjc.quote(value)))

    def _draw_bar(self, item, key):
        width, color = key
        x, y, w, h = item.rect
        self._cut(item.rect, self.picture_at(item.rect))
        if width > 0:
            self.send("fill %d,%d,%d,%d,%d" % (x, y, width, h, color))

    def _draw_dot(self, item, color):
        x, y, w, h = item.rect
        self.send("cirs %d,%d,%d,%d" % (x + w // 2, y + h // 2,
                                        max(1, w // 2), color))
