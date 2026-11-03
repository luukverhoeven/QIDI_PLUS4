"""Print thumbnails on the screen.

The canvas page of plus4ui.tft has nine "external picture" objects:
exp0 (228 px, home), exp1 (212 px, printing), exp2 (272 px, preview) and
exp3-exp8 (96 px, the file list). A thumbnail is the slicer's picture from
Moonraker, turned into a JPEG of the slot's size with Pillow, written to
the screen's RAM with ``twfile`` and shown by pointing an object at it.

Uploads block the serial line (a 96 px picture takes about 0.4 s), so they
are queued and sent one per main-loop pass.
"""

import io
import logging
import posixpath

from .. import images

log = logging.getLogger("plus4screen")

# (screen, thumbnail slot in ui_layout.json) -> object number on the page.
OBJECTS = {("home", "last"): 0, ("printing", "print"): 1,
           ("preview", "preview"): 2}
OBJECTS.update({("files", "file%d" % i): 3 + i for i in range(6)})
JPEG_BACKGROUND = (46, 56, 70)        # the design's thumbnail tile
JPEG_QUALITY = 85
RETRY_AFTER = 60.0     # s before a failed upload is tried again


def pick(metadata, size):
    """Relative path of the smallest thumbnail at least ``size`` wide, or
    of the largest one."""
    thumbs = [t for t in (metadata or {}).get("thumbnails") or []
              if t.get("relative_path")]
    if not thumbs:
        return None
    big = [t for t in thumbs if t.get("width", 0) >= size]
    best = min(big, key=lambda t: t["width"]) if big else \
        max(thumbs, key=lambda t: t.get("width", 0))
    return best["relative_path"]


def make_jpeg(image_bytes, size):
    """A ``size`` x ``size`` baseline JPEG of a (transparent) thumbnail."""
    from PIL import Image            # Pillow is on the printer, not required
    image = images.open_checked(image_bytes).convert("RGBA")
    image.thumbnail((size, size), Image.LANCZOS)
    tile = Image.new("RGB", (size, size), JPEG_BACKGROUND)
    offset = ((size - image.width) // 2, (size - image.height) // 2)
    tile.paste(image, offset, image)
    out = io.BytesIO()
    tile.save(out, "JPEG", quality=JPEG_QUALITY, progressive=False)
    return out.getvalue()


class Thumbs:
    def __init__(self, app):
        self.app = app
        self.jpegs = {}        # (path, size) -> JPEG bytes, or None (none)
        self.building = set()
        self.queue = []        # (screen, slot, path), newest request last
        self.in_ram = {}       # object number -> (path, size) written
        self.failed = {}       # (path, size) -> time of a failed upload

    def show(self, screen, slot, path):
        """Show ``path``'s thumbnail in a slot of the shown screen."""
        if not path or (screen, slot) not in OBJECTS:
            return
        size = self.app.canvas.layout[screen].thumbs[slot].rect.w
        key = (path, size)
        if key not in self.jpegs:
            self._build(key)
            return
        if self.jpegs[key] is None:
            return
        item = (screen, slot, path)
        if item not in self.queue:
            self.queue.append(item)

    def forget(self, path):
        """The file changed: make its thumbnails again."""
        for key in [k for k in self.jpegs if k[0] == path]:
            del self.jpegs[key]
        for number in [n for n, k in self.in_ram.items() if k[0] == path]:
            del self.in_ram[number]

    def _build(self, key):
        if key in self.building:
            return
        self.building.add(key)
        path, size = key
        mr = self.app.mr

        def build():
            meta = mr.metadata(path)
            rel = pick(meta, size)
            if not rel:
                return None
            folder = posixpath.dirname(path)
            image = mr.download("gcodes", posixpath.join(folder, rel))
            return make_jpeg(image, size)

        def done(jpeg, error):
            self.building.discard(key)
            if error is not None:
                log.info("no thumbnail for %s: %s", path, error)
            self.jpegs[key] = jpeg if error is None else None
            screen = self.app.current
            if jpeg and screen:
                self.app.screens[screen].refresh(self.app.state)
        self.app.runner.spawn(build, done)

    def pump(self):
        """Write one queued thumbnail to the screen; True if one was sent."""
        app = self.app
        while self.queue:
            screen, slot, path = self.queue.pop(0)
            if screen != app.current or app.upload is None:
                continue
            rect = app.canvas.layout[screen].thumbs[slot].rect
            number = OBJECTS[(screen, slot)]
            key = (path, rect.w)
            name = "ram/t%d.jpg" % number
            written = self.in_ram.get(number) != key
            if written:
                if app.clock() - self.failed.get(key, -1e9) < RETRY_AFTER:
                    continue
                sent = app.upload(name, self.jpegs[key])
                # Writing a file makes the screen repaint the page (see
                # canvas.py): let it, then draw the live content again.
                app.canvas.settle()
                app.canvas.repaint()
                if not sent:
                    log.warning("thumbnail upload failed: %s", path)
                    self.in_ram.pop(number, None)
                    self.failed[key] = app.clock()
                    return True
                log.info("thumbnail written: %s (%s)", name, path)
                self.in_ram[number] = key
            app.canvas.thumb(number, rect, name, reload=written)
            return True
        return False
