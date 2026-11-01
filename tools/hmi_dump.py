#!/usr/bin/env python3
"""Dump the pages and widgets of a TJC/Nextion ``.HMI`` project as JSON.

Usage::

    python3 tools/hmi_dump.py UI/xindi_800_480.HMI > layout.json
    python3 tools/hmi_dump.py --markdown UI/xindi_800_480.HMI \
        > screen/LAYOUT.md

Format (worked out from QIDI's ``xindi_800_480.HMI``, little-endian):

* The HMI file is an archive: ``u32 count`` followed by ``count`` entries of
  ``name[16] offset:u32 size:u32 unknown:u32``. ``N.pa`` entries are pages,
  ``main.HMI`` holds the project settings and the page order.
* ``main.HMI`` lists the pages in display order as ``"pa" pad[6] "N.pa"``.
  The position in that list is the page number used by ``page <n>`` and in
  touch events. The ``N`` in the file name is not the page number.
* A page file starts with a header. ``u32`` at ``0x0c`` is the number of
  objects; the page name is at ``0x18``. At ``0x38`` follows one
  ``offset:u32 size:u32 unknown:u32`` entry per object. Offsets are relative
  to ``0x38``.
* An object is a list of length-prefixed strings (``u32 len`` + bytes).
  ``att-N`` is followed by ``N`` attributes: ``name[16]`` + value. Values of
  up to 4 bytes that are not strings are little-endian integers.
  ``codes<event>-N`` is followed by ``N`` lines of event code.

Only the standard library is used.
"""

import json
import re
import struct
import sys

# Attributes whose value is text, not a number.
STRING_ATTRS = {"objname", "txt", "path", "dir", "filter", "vvs0", "vvs1",
                "vvs2", "vvs3", "format"}

# TJC object type codes (``type`` attribute).
TYPE_NAMES = {
    121: "page", 98: "button", 116: "text", 112: "picture", 113: "crop",
    54: "number", 59: "xfloat", 106: "progress", 53: "dual_button",
    109: "hotspot", 51: "timer", 52: "variable", 1: "slider", 0: "waveform",
    56: "checkbox", 57: "radio", 58: "qrcode", 55: "scrolltext", 122: "gauge",
    67: "combobox", 68: "textselect", 61: "slidetext", 60: "filebrowser",
    64: "datarecord", 65: "fileview", 66: "switch", 5: "gmov", 6: "video",
    7: "audio", 2: "touchcap", 3: "externalpic", 4: "filestream",
}

# A button reporting itself to the host program:
#   prints 0x65,1 / prints dp,1 / prints <widget>,1 / ... 0xff x3
SEND_RE = re.compile(r"^\s*prints\s+0x65\s*,\s*1\s*$")
NUM_RE = re.compile(r"^\s*prints\s+(\d+|0x[0-9a-fA-F]+)\s*,\s*1\s*$")


def read_archive(data):
    count = struct.unpack_from("<I", data, 0)[0]
    files = {}
    for k in range(count):
        o = 4 + 28 * k
        name = data[o:o + 16].split(b"\0")[0].decode("latin1")
        off, size, _ = struct.unpack_from("<III", data, o + 16)
        if name:
            files[name] = data[off:off + size]
    return files


def page_order(main_hmi):
    return [m.group(1).decode() for m in
            re.finditer(rb"pa\x00{6}(\d+\.pa)", main_hmi)]


def decode_value(name, raw):
    if name in STRING_ATTRS or len(raw) > 4:
        return raw.decode("utf-8", "replace")
    return int.from_bytes(raw, "little") if raw else 0


def parse_object(blob):
    strings = []
    p = 0
    while p + 4 <= len(blob):
        n = struct.unpack_from("<I", blob, p)[0]
        p += 4
        strings.append(blob[p:p + n])
        p += n
    attrs, events = {}, {}
    i = 0
    while i < len(strings):
        s = strings[i].decode("utf-8", "replace")
        i += 1
        m = re.match(r"^att-(\d+)$", s)
        if m:
            for raw in strings[i:i + int(m.group(1))]:
                name = raw[:16].split(b"\0")[0].decode("latin1")
                attrs[name] = decode_value(name, raw[16:])
            i += int(m.group(1))
            continue
        m = re.match(r"^codes(\w+?)-(\d+)$", s)
        if m:
            n = int(m.group(2))
            lines = [x.decode("utf-8", "replace") for x in strings[i:i + n]]
            if lines:
                events[m.group(1)] = lines
            i += n
    return attrs, events


def reported_numbers(lines):
    """Widget numbers a code block sends with ``prints 0x65,1``."""
    out = []
    for k, line in enumerate(lines):
        if SEND_RE.match(line) and k + 2 < len(lines):
            m = NUM_RE.match(lines[k + 2])
            if m and lines[k + 1].strip().startswith("prints dp"):
                out.append(int(m.group(1), 0))
    return out


def parse_page(blob):
    count = struct.unpack_from("<I", blob, 0x0C)[0]
    name = blob[0x18:0x28].split(b"\0")[0].decode("latin1")
    objects = []
    for k in range(count):
        off, size, _ = struct.unpack_from("<III", blob, 0x38 + 12 * k)
        attrs, events = parse_object(blob[0x38 + off:0x38 + off + size])
        obj = {
            "id": attrs.get("id"),
            "name": attrs.get("objname"),
            "type": TYPE_NAMES.get(attrs.get("type"), attrs.get("type")),
        }
        for key in ("x", "y", "w", "h", "txt", "val", "pic", "picc", "picc2",
                    "pco", "vscope"):
            if key in attrs and attrs[key] not in ("", None):
                obj[key] = attrs[key]
        sends = {ev: reported_numbers(lines) for ev, lines in events.items()}
        sends = {ev: nums for ev, nums in sends.items() if nums}
        if sends:
            obj["reports"] = sends
        if events:
            obj["events"] = events
        objects.append(obj)
    return name, objects


def dump(path):
    files = read_archive(open(path, "rb").read())
    pages = []
    for number, fname in enumerate(page_order(files["main.HMI"])):
        name, objects = parse_page(files[fname])
        pages.append({"page": number, "file": fname, "name": name,
                      "objects": objects})
    return {"source": path, "pages": pages}


def markdown(layout):
    """Page list plus, per page, the widgets that report touches."""
    out = ["# Screen layout", "",
           "Generated from `%s` by `tools/hmi_dump.py --markdown`. "
           "Do not edit by hand." % layout["source"], "",
           "\"Reports\" is the widget number the screen sends in a touch "
           "event (`65 <page> <widget> FF FF FF`). Labels are the Chinese "
           "defaults in the layout; the screen replaces them per language.",
           "", "## Pages", "", "| Page | Name |", "| --- | --- |"]
    out += ["| %d | %s |" % (p["page"], p["name"]) for p in layout["pages"]]
    for p in layout["pages"]:
        rows = []
        for o in p["objects"]:
            reports = sorted({n for nums in o.get("reports", {}).values()
                              for n in nums})
            if not reports:
                continue
            label = str(o.get("txt", "")).replace("|", "/")
            label = label.replace("\r", " ").replace("\n", " ")[:40]
            rows.append("| %s | %s | %s | %s | %s,%s %sx%s |" % (
                ", ".join(map(str, reports)), o["name"], o["type"], label,
                o.get("x"), o.get("y"), o.get("w"), o.get("h")))
        if rows:
            out += ["", "## %d %s" % (p["page"], p["name"]), "",
                    "| Reports | Widget | Type | Label | x,y wxh |",
                    "| --- | --- | --- | --- | --- |"] + rows
    return "\n".join(out) + "\n"


def main(argv):
    args = [a for a in argv[1:] if a != "--markdown"]
    if len(args) != 1:
        sys.stderr.write(__doc__)
        return 2
    layout = dump(args[0])
    if "--markdown" in argv:
        sys.stdout.write(markdown(layout))
    else:
        json.dump(layout, sys.stdout, ensure_ascii=False, indent=1)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
