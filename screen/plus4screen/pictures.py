"""File pictures in the screen's ``cp0`` objects (main, preview, printing).

``cp0`` takes QIDI's "ColPic" text. QIDI's own converter (``gene4.py`` with
``libColPic.so``) turns a slicer thumbnail into that text; plus4screen
calls it like xindi does. Pictures are made once per file and cached.

* main page: ``cp0`` is global, so it keeps its picture until written again;
  it shows the last printed file.
* preview page: the picture goes into the global ``preview.cp0_text``
  first; the printing page's load event draws its ``cp0`` from that text.
"""

import logging
import os
import posixpath
import subprocess
import tempfile

from . import images
from . import pages as P

log = logging.getLogger("plus4screen")

COLPIC_SCRIPT = "/home/mks/gene4.py"
COLPIC_SIZE = 272
CP0_MAX = 50000          # cp0 buffsize in the layout
CHUNK = 1024             # characters per write command
UNKNOWN = object()       # screen content not known (e.g. left by xindi)


def pick_thumbnail(metadata):
    """Relative path of the best thumbnail for a 272x272 picture."""
    thumbs = (metadata or {}).get("thumbnails") or []
    if not thumbs:
        return None
    best = min(thumbs, key=lambda t: abs(t.get("width", 0) - COLPIC_SIZE))
    return best.get("relative_path")


def make_colpic(image_bytes, suffix):
    """ColPic text for an image, using QIDI's converter."""
    images.open_checked(image_bytes)
    with tempfile.TemporaryDirectory(prefix="plus4screen-") as tmp:
        image = os.path.join(tmp, "thumb" + suffix)
        out = os.path.join(tmp, "colpic.txt")
        with open(image, "wb") as fh:
            fh.write(image_bytes)
        subprocess.run(["python3", COLPIC_SCRIPT, image, out,
                        str(COLPIC_SIZE)], stdout=subprocess.DEVNULL,
                       stderr=subprocess.PIPE, timeout=60, check=True)
        with open(out) as fh:
            text = fh.read().strip()
    if not text or '"' in text or len(text) > CP0_MAX:
        raise ValueError("unusable picture (%d characters)" % len(text))
    return text


def chunks(text):
    return [text[i:i + CHUNK] for i in range(0, len(text), CHUNK)]


class PicturesMixin:
    """Methods ``App`` uses to show file pictures."""

    def reset_pictures(self):
        """Forget what the screen's global picture objects hold.

        Called at start-up (they may still hold xindi's last picture) and
        when the screen reboots.
        """
        self.main_picture = UNKNOWN     # file shown in main's cp0
        self.cp0_text_file = UNKNOWN    # file held in preview.cp0_text

    # Making pictures ---------------------------------------------------

    def with_picture(self, filename, on_ready):
        """Call ``on_ready(text)`` with the file's picture (or None)."""
        if filename in self.pictures:
            on_ready(self.pictures[filename])
            return
        if filename in self.pictures_pending:
            self.pictures_pending[filename].append(on_ready)
            return
        self.pictures_pending[filename] = [on_ready]

        def build():
            rel = pick_thumbnail(self.mr.metadata(filename))
            if not rel:
                return None
            path = posixpath.normpath(posixpath.join(
                posixpath.dirname(filename), rel))
            data = self.mr.download("gcodes", path)
            return make_colpic(data, os.path.splitext(rel)[1] or ".png")

        def done(text, error):
            if error is not None:
                log.warning("no picture for %s: %s", filename, error)
            self.pictures[filename] = text
            for callback in self.pictures_pending.pop(filename, []):
                callback(text)
        self.runner.spawn(build, done)

    # Writing to the screen ---------------------------------------------

    def draw_cp0(self, text):
        """Draw ColPic text into the current page's cp0."""
        self.send("cp0.close()")
        for part in chunks(text or ""):
            self.send('cp0.write("%s")' % part)

    def fill_cp0_text(self, text, prefix=""):
        """Store ColPic text in the global preview.cp0_text."""
        self.send('%scp0_text.txt=""' % prefix)
        for part in chunks(text or ""):
            self.send('%sadd.txt="%s"' % (prefix, part))
            self.send("%scp0_text.txt=%scp0_text.txt+%sadd.txt"
                      % (prefix, prefix, prefix))
        self.send('%sadd.txt=""' % prefix)

    # Main page: last print ---------------------------------------------

    def show_last_print(self):
        def got_job(job, error):
            name = (job or {}).get("filename")
            if not name or (job or {}).get("exists") is False:
                name = None
            self.last_print = name
            if self.page != P.MAIN:
                return
            if not name:
                self.set_vis("q0", False)
                if self.main_picture is not None:
                    self.send("cp0.close()")
                    self.main_picture = None
                return
            self.with_picture(name, lambda text: self._draw_main(name, text))
        self.runner.spawn(self.mr.last_job, got_job)

    def _draw_main(self, name, text):
        if self.page != P.MAIN:
            return
        self.set_vis("q0", bool(text))
        if self.main_picture != name:
            self.draw_cp0(text)
            self.main_picture = name

    # Preview and printing ----------------------------------------------

    def show_preview_picture(self, filename):
        # The page's post-init code writes test data into cp0 and
        # cp0_text; clear both before anything else.
        self.send("cp0.close()")
        self.fill_cp0_text("")
        self.cp0_text_file = None
        self.set_vis("cp0", False)

        def ready(text):
            if self.page != P.PREVIEW or self.selected != filename:
                return
            if text:
                self.fill_cp0_text(text)
                self.cp0_text_file = filename
                self.send("cp0.close()")
                self.send("cp0.write(cp0_text.txt)")
            self.set_vis("cp0", bool(text))
        self.with_picture(filename, ready)

    def show_printing_picture(self):
        filename = self.state.filename
        if not filename or self.cp0_text_file == filename:
            return              # the page's load event already drew it

        def ready(text):
            if self.page != P.PRINTING:
                return
            self.fill_cp0_text(text or "", prefix="preview.")
            self.cp0_text_file = filename
            self.send("cp0.close()")
            if text:
                self.send("cp0.write(preview.cp0_text.txt)")
        self.with_picture(filename, ready)
