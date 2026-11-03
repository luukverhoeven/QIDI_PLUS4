# Open items and ideas

Things that could still be tweaked or improved, roughly by value. Each item says what it would take. Items marked **flash** need a new `plus4ui.tft` on the screen (about 3½ minutes and the TJC editor).

## Touchscreen (`plus4screen`)

- **Bed screw adjustment.** No screen yet for `SCREWS_TILT_CALCULATE` (needs `[screws_tilt_adjust]` first, see [Printer tweaks](#printer-tweaks)). A Tools entry that runs it and lists the turns per screw would cover it.
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

## Printer tweaks

From the community [Plus4-Wiki](https://github.com/qidi-community/Plus4-Wiki) and QIDI's issue tracker, checked against this printer on 31 Oct 2026 and again on 3 Nov. None of them is applied yet; the "Now" column is the printer's current value.

### Low risk, software only

| Tweak | Now | Change |
| --- | --- | --- |
| [Secure SSH](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/ssh-security) | `mks` and `root` still accept the published factory password; `PermitRootLogin yes`. Key login (`ssh qidi-plus4`) works. | `passwd` as `mks` and as `root`, then `PermitRootLogin no` in `/etc/ssh/sshd_config`. |
| [Klipper arc crash](https://github.com/luukverhoeven/klipper/blob/plus4-printer/klippy/extras/gcode_arcs.py) | QIDI's `segments = math.ceil(...)` has no minimum: a zero-length `G2`/`G3` divides by zero and shuts Klipper down mid-print. | `segments = max(1., math.ceil(mm_of_travel / self.mm_per_arc_segment))` as a commit on top of the snapshot in `luukverhoeven/klipper`, plus a small script that deploys `klipper/` changes to the printer. |
| [Adaptive mainboard cooling](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/adaptive-main-board-cooling) | `[controller_fan board_fan]`: the board fan only runs while X/Y move. CPU 64.6 °C idle on 31 Oct. | A `[temperature_fan board_fan]` that follows the CPU temperature. |
| [Square corner velocity](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/square-corner-velocity) | `square_corner_velocity: 8` | `5`, which QIDI's input shaper tuning assumes. |
| [KAMP purge line](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/kamp-purging) | `Line_Purge.cfg` is commented out in `KAMP_Settings.cfg`. | Include it and call `LINE_PURGE` from the slicer's start G-code. |
| [Permanent Z offset](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/making-z-offset-permanent) | `[smart_effector] z_offset: 0.000001`; the offset lives in `saved_variables.cfg` (`z_offset = 0.0`), which sometimes resets to 0. | Put the negated offset in `[smart_effector] z_offset` and set `z_offset = 0` in `saved_variables.cfg`. |
| [Bed screw adjustment](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/Screws-Tilt-Adjust) | `[screws_tilt_adjust]` is commented out in `printer.cfg`. | Enable it with the screw positions from the wiki; a touchscreen page could then show the turns per screw (see above). |

### Try and test (they change print behaviour)

- **[Better bed meshing](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/more-accurate-bed-meshing):** Z `microsteps: 16` (now 128) and single probe samples, to work around a Klipper probing bug. It does not help every machine, and the Z offset must be set again afterwards.
- **[Stepper tweaks](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/stepper-motor-tweaks):** `interpolate: False` (now `True` on all axes) and about 5% more `run_current`. Raise the current only once the mainboard cooling is better.
- **[Skip the PEI nozzle wipe](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/conditional_purging_and_wiping):** the wipe hits the nozzle hard and is suspected of cracking ceramic heat breaks. A replacement `CLEAR_NOZZLE` makes it optional.
- **[Shake & Tune](https://github.com/qidi-community/klippain_v511_for_qidi_plus4):** better input shaper and belt analysis.

### Hardware and maintenance

- **Extruder pressure arm** ([#57](https://github.com/QIDITECH/QIDI_PLUS4/issues/57)): the plastic arm bends over time and the filament slips. Fix with an [aluminium or ABS replacement](https://www.printables.com/model/902986-qidi-x-max3-x-plus3-x-plus4-extruder-part) or a warranty claim.
- **Toolhead play:** two set screws in the pilot holes at the back of the toolhead ([video](https://youtu.be/JCnvmIsikQ8)); QIDI support sends them for free.
- **Belts and lubrication:** [belt tension](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/adjusting-belt-tension), [rods and screws](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/lube-rods-screws).
- **Fans:** a GDSTime GDA30105F as hotend heatsink fan, and an [80 mm mainboard cover](https://www.thingiverse.com/thing:6787302).
- **Prints:** [ejecta chute and bucket](https://www.thingiverse.com/thing:6789666), [rear chamber seal](https://www.printables.com/model/1040774-qidi-plus-4-rear-chamber-cover), [HEPA and carbon filter](https://www.printables.com/model/1022271-qidi-plus-4-filtration-system).

### Only for ABS and ASA

- **Z offset too low on a hot bed** ([#60](https://github.com/QIDITECH/QIDI_PLUS4/issues/60)): the bed's pressure sensors drift with heat. Options: a [software fix that measures with the inductive probe](https://github.com/Hanskubie/QIDI-Plus4-Global-Z-Bed-Leveling-Software-only-solution), or a [Beacon](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/bed-scanning-probes/Beacon3D/RevH-Normal) or [Cartographer](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/bed-scanning-probes/cartographer3d) probe (Cartographer needs the guide updated for 1.7.x).
- **[Adaptive heat-soak start](https://github.com/Tinman-FP/qidi-plus4-codex-macros):** repeats the bed mesh until it stops changing.

### Skipped for this printer

- [Disabling the Wi-Fi adapter](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/8188gu-blacklist): the printer is on Wi-Fi.
- [System tuning script](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/system-tuning): only for `Timer too close` errors, and there are none.
- [Adaptive chamber heater fan](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/adaptive-chamber-heater-fan): tested only on firmware before 1.7.3.
- Box purge fix ([#113](https://github.com/QIDITECH/QIDI_PLUS4/issues/113)): no Box.

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

## Done

For reference, from the work on the own interface:

- Own screen file and interface, installed as a service; screen-file ID check.
- Thumbnails: 192 KB RAM file system, `twfile` with a sync before each upload and an abort when a transfer fails (also at start), size limits before decoding, whole-block JPEGs.
- Page redraws by the screen no longer wipe text: picture background that follows the screen, a pause before drawing, live content drawn again after uploads.
- Wi-Fi setup through an allowlist gate instead of opening `wpa_supplicant` to `netdev`; one request per connection with a deadline.
- Time zone set to `Europe/Madrid`.
- All work merged into `main`; the old branches are deleted and draft PR #1 is closed.
