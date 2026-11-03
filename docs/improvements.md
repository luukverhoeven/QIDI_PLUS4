# Open items and ideas

Things that could still be tweaked or improved, roughly by value. Each item says what it would take. Items marked **flash** need a new `plus4ui.tft` on the screen (about 3½ minutes and the TJC editor).

## Touchscreen (`plus4screen`)

- **Bed screw adjustment.** No screen yet for `SCREWS_TILT_CALCULATE`. A Tools entry that runs it and lists the turns per screw would cover it.
- **Layer count on Preview.** The count can be far off when Moonraker's numbers do not fit together (750 layers shown for a 41-minute print). Prefer the slicer's `layer_count` from the file metadata when it is there, and only fall back to `object_height / layer_height`.
- **Touch right after a restart.** On 2 Nov a Preheat tap arrived half a second after `plus4-screen` restarted, and the heaters were set to 0 on the screen a few seconds later. It was not confirmed whether that tap was real. Ignoring touches for the first second after start, and flushing serial input after the screen check, would rule out a stale touch frame.
- **Text blinks during an upload.** Writing a thumbnail makes the screen repaint the page; `plus4screen` then draws the live values again. Fewer uploads means less blinking:
  - keep a RAM file per print file instead of per slot, with the oldest dropped when the 192 KB fill up, so paging back through Files needs no upload;
  - write the next page's thumbnails ahead of time while nothing else happens.
- **Exact wait instead of 50 ms.** The pause that lets the screen redraw the page first (`SETTLE` in `__main__.py`) is a measured guess. A `sendme` round trip waits exactly as long as needed, but the main loop then has to keep any touch frames that arrive meanwhile.
- **Touches during an upload are lost.** Touch reports are off (`sendxy=0`) while a thumbnail is written, about 0.4 s for a 96 px picture.
- **Thumbnail objects at whole JPEG blocks (flash).** `exp0` (Home) and `exp1` (Printing) are 228 and 212 px, but the screen's decoder needs whole 16 px blocks, so their pictures are 224 and 208 px with a 2 px margin. Making the objects and the design slots 224 and 208 px removes the margin.
- **No start-up noise (flash).** The nine picture objects start with path `ram/last.jpg`, a file that is not there yet, so the screen answers `0x06` nine times at start. An empty path in the editor avoids that.
- **Wi-Fi limits.** Hidden networks, WEP and WPA-Enterprise are not supported; the gate only allows `ssid`, `psk` and `key_mgmt NONE`.
- **Languages.** The own interface is English only. Texts sit in the design and in `plus4screen/ui/*.py`; a translation would need both.
- **QIDI layout mode.** `--ui qidi` (QIDI's screen file and pages) is still in the code. Once the own interface has run for a while it could be removed, together with `pages.py`, `pictures.py` and `LAYOUT.md`.

## Printer housekeeping

- **Old `saved_variables.cfg.bak`.** The printer still has the copy from before single-spool (`enable_box = 1`, `auto_reload_detect = 1`). The live `saved_variables.cfg` is right; copying [`config/saved_variables.cfg.bak`](../config/saved_variables.cfg.bak) over the printer's copy makes a later restore right too.
- **Leftovers in `/home/mks`.** Test scripts and logs from the screen work (`plus4screen-canvas.*`, `plus4screen-dryrun.*`, `plus4screen-run.*`, `plus4ui-*.sh`), old `printer*.cfg` and `gcode_macro_2024-*.cfg` backups in the config folder, and a stray 20 MB `~/fluidd/Fluidd/` folder. `~/plus4screen-src` is the install source and stays.
- **Logs survive no reboot.** The journal lives in RAM, so the cause of a hang before a restart is lost. `Storage=persistent` with a small `SystemMaxUse` (the eMMC wears) keeps it.
- **QIDI cloud token.** `config.mksini` on the printer holds it. It is not in this repository and must stay out.

## Repository

- **Moonraker snapshot.** The `moonraker` submodule points at QIDI's GitHub commit, but the printer runs QIDI's own build: compiled modules (`extensions.so`), changed files and files removed. A snapshot like the Klipper one (a fork with the printer's tree committed) would make the repository match the printer.
- **Fluidd build.** `fluidd/` is the same version as on the printer (v1.30.4) but a different build: other asset names in `index.html`.
- **Line endings in the Klipper snapshot.** The printer's Klipper files use CRLF; the snapshot stores LF. Content is the same.
- **Tests in CI.** `cd screen && python3 -m unittest discover -s tests` could run on every push with GitHub Actions. The Pillow tests need `pip install pillow`.
- **Old branches.** `single-spool`, `single-spool-j6h54i` and `ui-redesign` are all in `main` now, and draft PR #1 is superseded. They can be closed and deleted.

## Done

For reference, from the work on the own interface:

- Own screen file and interface, installed as a service; screen-file ID check.
- Thumbnails: 192 KB RAM file system, `twfile` with a sync before each upload and an abort when a transfer fails (also at start), size limits before decoding, whole-block JPEGs.
- Page redraws by the screen no longer wipe text: picture background that follows the screen, a pause before drawing, live content drawn again after uploads.
- Wi-Fi setup through an allowlist gate instead of opening `wpa_supplicant` to `netdev`; one request per connection with a deadline.
- Time zone set to `Europe/Madrid`.
