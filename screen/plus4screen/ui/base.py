"""What every screen has in common."""

from .text import AVG_WIDTH, fit, lines


class Screen:
    """One screen of plus4ui.tft. ``name`` is its name in ui_layout.json."""

    name = None

    def __init__(self, app):
        self.app = app

    @property
    def canvas(self):
        return self.app.canvas

    @property
    def state(self):
        return self.app.state

    def enter(self, **options):
        """The screen was just drawn; draw what is not in the picture."""

    def refresh(self, state):
        """Called after each status poll while the screen is shown."""

    def touch(self, hit_id):
        """A touch target of this screen was tapped."""

    def follow(self, old, new):
        """Called after each status poll, shown or not."""

    def wrap(self, text_ids, value):
        """Spread ``value`` over several text boxes, word by word."""
        first = self.canvas.screen.texts[text_ids[0]]
        room = max(1, int(first.rect.w / AVG_WIDTH.get(first.font, 9.0)))
        for text_id, line in zip(text_ids, lines(value, room, len(text_ids))):
            self.text(text_id, line)

    def text(self, text_id, value, color=None):
        item = self.canvas.screen.texts[text_id]
        self.canvas.text(text_id, fit(value, item.rect.w, item.font), color)
