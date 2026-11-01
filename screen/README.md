# plus4screen: open-source touchscreen program for the QIDI Plus4

`plus4screen` replaces QIDI's closed-source screen program `xindi`. It drives the Plus4's built-in TJC touchscreen over `/dev/ttyS1` and talks to Klipper through Moonraker.

It has two interfaces:

- **Own interface** (`--ui plus4`, the default): a new design with its own screen file, [`ui/build/plus4ui.tft`](ui/build/plus4ui.tft). Every screen is drawn by `plus4screen`; the design lives in this repository as HTML. See [Own interface](#own-interface).
- **QIDI's layout** (`--ui qidi`): keeps the screen file QIDI flashed and reuses its pages. See [QIDI's layout](#qidis-layout---ui-qidi).

**Dependencies:** Python 3 standard library only. Nothing to `pip install` on the printer.

## Own interface

Home, printing, files, file preview, move, filament (single spool), temperatures and fans, tools (auto bed levelling, input shaping), settings, Wi-Fi, about, plus a keypad, a confirm dialog and a message dialog.

- **Screen file:** `plus4ui.tft` holds only pictures and fonts: a boot page and a canvas page with nine picture objects for thumbnails. It has no buttons. Writing it replaces QIDI's screen file; [`install.sh`](install.sh) saves QIDI's copy first and [`uninstall.sh`](uninstall.sh) writes it back.
- **Drawing:** each screen is a full-size picture (`pic`). Pressed and selected looks are cut from two more pictures of the same screen (`xpic`). Live values are drawn with `xstr` on top of the picture they sit on.
- **Touch:** the screen reports raw touch positions (`sendxy=1`, frames `67 x y press`). `plus4screen` finds the button under the finger in [`plus4screen/ui_layout.json`](plus4screen/ui_layout.json).
- **Screen off:** the backlight goes off after 5 minutes without a touch (Settings: 1, 2, 5, 10, 30 minutes or never). The touch that wakes it does nothing else. Brightness and sleep time are kept in `~/.config/plus4screen.json`.
- **Thumbnails:** the slicer's picture of a file, from Moonraker, made into a JPEG with Pillow (installed on the Plus4) and written to the screen's RAM with `twfile`, one per main-loop pass. The screen repaints the page by itself while a file is written, so the canvas page's background picture follows the screen shown (`page1.pic`) and `plus4screen` draws the live values again afterwards.
- **Wi-Fi:** Settings → Wi-Fi lists the networks in range and joins one, with an on-screen keyboard for the password. It talks to `wpa_supplicant`'s control socket, as QIDI's program does; the password goes only to `wpa_supplicant` and is not logged.
- **Speed:** the screen talks at 115200 baud. If it comes up at the TJC default of 9600, `plus4screen` switches it over at start.
- **Screen check:** the screen file's ID (`sys2`) must match `ui_layout.json`; with another screen file, touches are ignored.

Not done yet: bed screw adjustment.

How the design becomes `plus4ui.tft`: [`ui/README.md`](ui/README.md).

## QIDI's layout (`--ui qidi`)

- **Screen firmware:** unchanged. The `.tft` QIDI flashed onto the screen only holds pages and buttons; all behaviour lives in the host program. `plus4screen` reuses QIDI's pages, so nothing is flashed.
- **Filament:** the control page's filament button opens a single-spool load/unload flow instead of the QIDI Box page.

### What works

| Page | What `plus4screen` does |
| --- | --- |
| Main (3) | Nozzle, bed and chamber temperatures; status line; **STOP** = Klipper emergency stop |
| Control (35) | Temperatures and targets; XY/Z jog with 1/10/50/100 mm steps; home; motors off; extrude/retract; fan percentages |
| Temperature keypad (36) | Sets nozzle (`M104`), bed (`M140`) or chamber (`M141`) target |
| Fans (58) | Sliders, ±20 % buttons and on/off per fan: `cooling_fan`, `auxiliary_cooling_fan`, `chamber_circulation_fan` |
| Filament (39 → 40 / 37 → 41 → 71 → 72) | Pick 220/250/300 °C. **Unload** runs `UNLOAD_FILAMENT TEMP=…`; **Load** shows the insert step, then runs `LOAD_FILAMENT TEMP=…`. Progress follows the nozzle temperature. Blocked while a print is running or paused |
| Files (4) → preview (5) | G-code files from Moonraker, newest first, 6 per page; preview shows the slicer's time estimate; **Print** starts the file |
| Printing (17) | File name, temperatures, speed, layer, progress, elapsed and remaining time, Z offset, flow and speed %; pause/resume; stop (with the confirm page 53); case light |
| Print keypad (18) | Flow (`M221`) and speed (`M220`) |
| Print finished (20), errors (45), screen sleep (43) | Shown when needed |

`LOAD_FILAMENT` and `UNLOAD_FILAMENT` are the macros in [`config/gcode_macro.cfg`](../config/gcode_macro.cfg) on this branch; they must be in the printer's config.

### What does not work (yet)

Use Fluidd (or the stock program) for these:

- **Tools and settings tabs:** Wi-Fi setup, language, updates, calibration, input shaping, Z offset, QIDI Box, drying, cloud/QIDI Link. Taps there are logged and ignored.
- **Not shown:** thumbnails (preview and printing pages), USB-stick files, the Z-offset button on the printing page.
- **QIDI print options:** the three toggles on the preview page (Box, time-lapse, bed levelling) are hidden.
- **Labels:** most come from the screen itself in the language set with `--lang`. The filament page's **Unload**/**Load** buttons are always English.

These are the parts **not verified** on hardware. The code keeps each one in a single place in [`plus4screen/pages.py`](plus4screen/pages.py), so it is easy to fix:

- which picture shows "paused" and "light on" (`TOGGLE_PICC`)

The jog and extruder directions (`W_JOG`, `W_EXTRUDER`) follow what stock `xindi` sends for the same widgets (18 = Z−, 19 = Z+, 20 = retract, 21 = extrude). They are checked against `xindi`, not yet on a printer.

### How it works

```
 touchscreen  --65/71 frames-->  plus4screen  --HTTP-->  Moonraker --> Klipper
 (QIDI .tft) <--"page 35", n0.val=210--
```

- **Touches:** every button runs `prints 0x65,1 / prints dp,1 / prints <n>,1 / 0xff ×3` in the screen's own code, so a tap arrives as `65 <page> <n> FF FF FF`.
- **Values:** sliders and keypads send `71 <page> <widget> <lo> <hi>`, without a terminator.
- **Updates:** `plus4screen` answers with plain TJC commands (`page 35`, `n0.val=210`, `t5.txt="…"`), sending only values that changed.
- **Polling:** once a second it asks Moonraker for the printer objects listed in [`printer.py`](plus4screen/printer.py).
- **Order and blocking:** G-code goes through one worker thread, so commands keep their order. Pause, resume, cancel and emergency stop do not wait behind a running G-code.

All page and widget numbers are in [`plus4screen/pages.py`](plus4screen/pages.py). The full map of QIDI's layout is in [`LAYOUT.md`](LAYOUT.md), generated by [`../tools/hmi_dump.py`](../tools/hmi_dump.py) from `UI/xindi_800_480.HMI`. Background: [`../docs/xindi-screen-analysis.md`](../docs/xindi-screen-analysis.md).

## Try it without installing

On the printer, as `mks`:

```bash
# copy this folder to the printer first, e.g. from your computer:
#   scp -r screen mks@<printer-ip>:~/plus4screen-src
cd ~/plus4screen-src

sudo systemctl stop makerbase-client          # QIDI's screen program
python3 -m plus4screen.flash ui/build/plus4ui.tft   # own interface only, ~3 min
python3 -m plus4screen --dry-run -v           # G-code is only logged
# tap around, watch the log; Ctrl-C to stop
```

- **QIDI's layout instead:** skip the flash step and add `--ui qidi`. Afterwards `sudo systemctl start makerbase-client` gives the stock screen back.
- **After writing `plus4ui.tft`:** QIDI's program no longer fits the screen. `python3 -m plus4screen.flash <QIDI .tft>` writes QIDI's file back (about 30 minutes); QIDI's program keeps its last one as `/root/800_480.tft.bak`.
- **Service name:** `makerbase-client` is the service whose journal shows the screen traffic on V1.7.x. If `systemctl stop` says it does not exist, find the right one with `systemctl list-units | grep -i -e xindi -e makerbase`.
- **Logs:** every tap is logged (`touch home.preheat`, or `touch page=… widget=…` with QIDI's layout).
- **Real run:** without `--dry-run`, G-code and print actions are sent for real.

## Install

```bash
cd ~/plus4screen-src
./install.sh                 # own interface; writes plus4ui.tft (~3 min)
./install.sh --no-flash      # own interface, plus4ui.tft is already on the screen
./install.sh --qidi-screen   # QIDI's layout, nothing is written to the screen
```

The script:
1. finds QIDI's screen service;
2. copies the program to `/home/mks/plus4-screen`;
3. saves QIDI's screen file as `/home/mks/qidi-screen-backup.tft` and writes `plus4ui.tft` (own interface only);
4. stops and disables the stock service;
5. lets the `netdev` group (`mks` is a member) use Wi-Fi control: `ctrl_interface_group=netdev` in `/etc/wpa_supplicant/wpa_supplicant-wlan0.conf` (QIDI's file has `0`), after which Wi-Fi restarts once (own interface only);
6. installs and starts [`systemd/plus4-screen.service`](systemd/plus4-screen.service).

Logs: `journalctl -u plus4-screen -f`.

To undo, run `./uninstall.sh`. With the own interface it first writes QIDI's screen file back (about 30 minutes), then sets Wi-Fi control back to `root` and re-enables QIDI's service.

A QIDI update may re-enable the stock service; run `./install.sh --no-flash` again afterwards.

## Options

```
python3 -m plus4screen [--ui plus4|qidi] [--port /dev/ttyS1]
                       [--moonraker http://127.0.0.1:7125]
                       [--lang 2] [--poll 1.0] [--dry-run] [-v]
python3 -m plus4screen.flash FILE.tft [--baud 115200]
```

`--lang` (QIDI's layout only) is the screen's language index: 0 Chinese, 1 Russian, 2 English, 3 Japanese, 4 French, 5 German, 6 Italian, 7 Spanish, 9 Portuguese.

## Development

```bash
cd screen
python3 -m unittest discover -s tests
```

- **Protocol decoder:** every frame type.
- **Page logic:** against a fake Moonraker.
- **Layout check:** `pages.py` against QIDI's actual `UI/xindi_800_480.HMI`.
- **End-to-end:** the real main loop on a pseudo-terminal with a stub Moonraker HTTP server.
- **Own interface:** taps, keypad, navigation, sleep, the drawing cache, thumbnails and the `twfile` upload against a fake printer and screen ([`tests/test_ui.py`](tests/test_ui.py)).
- **Wi-Fi:** the `wpa_supplicant` client and the Wi-Fi screens against a fake control socket ([`tests/test_wifi.py`](tests/test_wifi.py)).

To add a page to QIDI's layout:
1. Look it up in [`LAYOUT.md`](LAYOUT.md).
2. Add its numbers to `pages.py`.
3. Add `enter_…`/`touch_…` methods in `app.py` and register them in `ENTER`/`TOUCH`.
4. Add a test.
