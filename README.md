# QIDI_PLUS4

<p align="center"><img src="other/QIDI.png" height="240" alt="QIDI's logo" /></p>
<p align="center"><a href="/LICENSE"><img alt="GPL-V3.0 License" src="other/qidi.svg"></a></p>

# About this fork

Personal fork of [QIDITECH/QIDI_PLUS4](https://github.com/QIDITECH/QIDI_PLUS4) for a Plus4 that runs with a single external spool, no QIDI Box, and an open-source touchscreen program. `main` holds the fork's changes on top of QIDI's V1.7.1 and matches what the printer runs.

## What this fork changes

| Area | Change | Details |
| --- | --- | --- |
| Configuration | `config/` is the configuration the printer runs: QIDI's online update after V1.7.1, plus this printer's `printer.cfg` with its input shaper and bed meshes. | [Single-spool changes](#single-spool-changes) |
| Single spool | Box logic off by default, `LOAD_FILAMENT` and `UNLOAD_FILAMENT` macros for Fluidd and the touchscreen. | [Single-spool changes](#single-spool-changes) |
| Touchscreen | `plus4screen` replaces QIDI's closed-source `xindi`: its own interface and screen file, thumbnails, Wi-Fi setup, single-spool load/unload. | [screen/README.md](screen/README.md) |
| Wi-Fi control | `plus4-wifi-gate`, a small root service that passes only the Wi-Fi screen's commands to `wpa_supplicant`. | [screen/README.md](screen/README.md#own-interface) |
| Klipper | The `klipper` submodule points to a snapshot of Klipper as it runs on the printer (`luukverhoeven/klipper`, branch `plus4-printer`). | |
| Analysis | How `xindi` and the TJC screen work, found by reverse engineering. The binary and decompiled code are in a private repository. | [docs/xindi-screen-analysis.md](docs/xindi-screen-analysis.md), [qidi-plus4-analysis](https://github.com/luukverhoeven/qidi-plus4-analysis) (private) |
| Recovery | Reflashing the eMMC and installing V1.6.0. | [docs/emmc-reflash-v1.6.0.md](docs/emmc-reflash-v1.6.0.md) |

Open items and ideas: [docs/improvements.md](docs/improvements.md).

## On the printer

What `screen/install.sh` and a few manual steps changed outside this repository:

- **Services:** `plus4-screen` (the touchscreen program, own interface) and `plus4-wifi-gate` run from systemd. QIDI's `makerbase-client` (`xindi`) is stopped and disabled.
- **Screen file:** `plus4ui.tft` is on the screen. QIDI's screen file is kept as `/home/mks/qidi-screen-backup.tft`; `screen/uninstall.sh` writes it back.
- **Wi-Fi:** `wpa_supplicant`'s control socket is root-only (`ctrl_interface_group=0`, as QIDI ships it). The Wi-Fi screen goes through `/run/plus4-wifi/wlan0`.
- **Time zone:** `Europe/Madrid` (CET/CEST), set with `sudo timedatectl set-timezone Europe/Madrid`. QIDI ships UTC.
- **Box:** `enable_box = 0` in the live `saved_variables.cfg`.

## Single-spool changes

- `config/saved_variables.cfg.bak`: default values for `saved_variables.cfg`, which is the file Klipper reads. Changes here only apply after copying it over `saved_variables.cfg` on the printer.
  - `enable_box = 0`: keeps Box logic off in the print, pause and resume macros, even if a Box is detected. With `box_count = 0` that logic is already skipped.
  - `auto_reload_detect = 0`: on runout the printer pauses instead of calling `AUTO_RELOAD_FILAMENT`, a Box macro that is not defined without the Box config.
- `config/gcode_macro.cfg`: `LOAD_FILAMENT` and `UNLOAD_FILAMENT` macros. They call the stock `M604` (load) and `M603` (cut, then purge what is left in the nozzle; pull the spool back afterwards), without the Box or filament-sensor checks of the touchscreen. Fluidd shows them as buttons on the Macros card.
  - `TEMP` (default `250`, same as stock) must be within the extruder's `min_extrude_temp` and `max_temp`.
  - `LOAD_FILAMENT TYPE=…` (`PLA`, `PETG`, `ABS`, `ASA` or `TPU`) also sets the external spool's filament once the load is done (`filament_slot16`). This stops QIDI Studio's "Not all filaments used in slicing are mapped to the printer" error.
    - QIDI Studio only maps a slicer filament to a spool with the same type and the same nozzle temperature range.
    - Each type therefore sets a filament whose range in the printer's `filament-0.4.json` equals QIDI Studio's Generic profile (QIDI ASA for ASA): PLA Basic, PETG Tough, ABS Rapido, ASA and TPU 95A-HF.
    - PC and PVA are left out: the printer has no entry for them and would report PLA.
    - Without `TEMP`, the type picks its own load temperature. Without `TYPE`, the spool's filament stays as it was.
  - Both refuse to run while printing. Pause the print first.
  - Calls with `T=` do nothing except log a message. QIDI Studio's Plus4 end G-code runs `UNLOAD_FILAMENT T=…` for the QIDI Box. On stock firmware without a Box that command does not exist and is skipped; here it must not cut the filament or end the print in an error.

To switch Box logic off on a running printer without copying files, run `SAVE_VARIABLE VARIABLE=enable_box VALUE=0` from the Fluidd console. Use `VALUE=1` to switch it back on.

## Open-source touchscreen program

[`screen/`](screen/README.md) holds `plus4screen`, an open-source replacement for `xindi`. It runs on the printer with its own interface: a design kept as HTML in [`screen/ui/design`](screen/ui/design), turned into the screen file `plus4ui.tft`, and drawn by `plus4screen` over the serial line. Home, printing, files with thumbnails, move, filament (single spool), temperatures, tools, settings and Wi-Fi are all on the screen. Install with `screen/install.sh`; `screen/uninstall.sh` gives the screen back to `xindi`.

[`tools/hmi_dump.py`](tools/hmi_dump.py) reads QIDI's screen layout (`UI/xindi_800_480.HMI`) without the TJC editor. [`screen/LAYOUT.md`](screen/LAYOUT.md) is its map of every page and button.

## Keeping up with upstream

`main` carries this fork's commits, so QIDI's updates are merged in rather than fast-forwarded:

```bash
git remote add upstream https://github.com/QIDITECH/QIDI_PLUS4.git
git fetch upstream
git switch main && git merge upstream/main && git push origin main
```

A QIDI online update replaces `printer.cfg` (the old one is kept as `printer_{datetime}.cfg`) and can enable `makerbase-client` again. Afterwards, run `screen/install.sh --no-flash` and copy the changed configuration back into `config/`.

# Documentation Guidelines

QIDI PLUS4 is a 3D printer that uses Klipper as its foundation. This repository is used for updates and releases for the PLUS4 model, as well as for issue tracking.

For convenience, QIDI provides version-specific packaged files. Please download the necessary compressed package file prefixed with "PLUS4." Select the appropriate branch for download, with each branch name reflecting the corresponding version.

## V1.7.1 Update Content

**Note:** 
After updating, the Klipper configuration file will be replaced. The previous configuration file will be backed up as `printer_{datetime}.cfg`, printer recalibration will be required.

If you have a multi-color box, it is recommended to disconnect the box power supply. After the firmware update is completed, connect the multi-color box again, and the box will automatically update the firmware

1. Optimized the resume printing function.
2. Optimized the error message for material wrapping during printing.


## The online update version will be uploaded later. If you have already updated this version earlier, please ignore the online update prompt.


## Detailed update process

#### Packaged files

Note that all updates can not be updated from higher versions

1. Select the latest version in the version release bar next to it, download the compressed file package starting with PLUS4 and extract it locally. <a href="https://github.com/QIDITECH/QIDI_PLUS4/releases">Jump link</a>

2. Transfer the files to a USB drive. For example:

    <p align="left"><img src="other/sample.png" height="240" alt="sample"></p>

3. Insert the USB drive into the machine's USB interface, click the `Check for updates` button and an update prompt will appear on the version information interface. Update according to the prompt.

## Report Issues and Make Suggestions

For any concerns or suggestions, feel free to reach out to our [After-Sales Service](https://qidi3d.com/pages/warranty-policy-after-sales-support).

Should you encounter any issues related to machine mechanics, slicing software, firmware, or various other machine-related problems, our after-sales team is ready to assist. They aim to respond to all inquiries within twelve hours. Alternatively, you can post an issue in this repository, our developers will reply to you directly.

## Others
QIDI's 3D printers operate based on the Klipper system. Building on the Klipper open-source project, we've tailored its source code to meet specific user requirements.

Similarly, we've adapted Moonraker to ensure our designed screens align with web operations.

We also use Fluidd as one of the ways for users to interact with the printer.

We extend our gratitude to the developers and maintainers of these open-source projects and encourage users to explore or support these great projects.

| Software      |Official| QIDI edition                                                                     |
| ------------- |----------| -------------------------------------------------------------------------------- |
| **Klipper**   |**[https://github.com/Klipper3d/klipper](https://github.com/Klipper3d/klipper)**| **[https://github.com/QIDITECH/klipper](https://github.com/QIDITECH/klipper)**   |
| **Moonraker** |**[https://github.com/Arksine/moonraker](https://github.com/Arksine/moonraker)**| **[https://github.com/QIDITECH/moonrake](https://github.com/QIDITECH/moonrake)** |
|**Fluidd**|**[https://github.com/fluidd-core/fluidd](https://github.com/fluidd-core/fluidd)**||
