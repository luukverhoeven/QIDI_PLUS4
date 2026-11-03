"""Limits for pictures from the printer, checked before they are decoded.

Thumbnails come from files anyone on the network can upload. A small file
can declare a huge picture whose decoding needs more memory than the Plus4
has (1 GB, shared with Klipper).
"""

import io

MAX_SIDE = 1024          # px; slicer thumbnails are much smaller


def check_size(width, height):
    if width > MAX_SIDE or height > MAX_SIDE:
        raise ValueError("picture is %dx%d px, more than %d"
                         % (width, height, MAX_SIDE))


def open_checked(image_bytes):
    """A Pillow image of ``image_bytes``, refused if too large; Pillow has
    only read the header at this point."""
    from PIL import Image            # Pillow is on the printer, not required
    image = Image.open(io.BytesIO(image_bytes))
    check_size(*image.size)
    return image
