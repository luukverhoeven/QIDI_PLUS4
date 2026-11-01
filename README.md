# QIDI_PLUS4

<p align="center"><img src="other/QIDI.png" height="240" alt="QIDI's logo" /></p>
<p align="center"><a href="/LICENSE"><img alt="GPL-V3.0 License" src="other/qidi.svg"></a></p>

# About this fork

Personal fork of [QIDITECH/QIDI_PLUS4](https://github.com/QIDITECH/QIDI_PLUS4) for running a Plus4 with a single external spool and no QIDI Box.

- `main` tracks upstream. Changes live on the `single-spool` branch.
- `config/` on `single-spool` starts from the configuration the printer runs after the online update past V1.7.1.

## Single-spool changes

- `config/saved_variables.cfg.bak`: default values for `saved_variables.cfg`, which is the file Klipper reads. Changes here only apply after copying it over `saved_variables.cfg` on the printer.
  - `enable_box = 0`: keeps Box logic off in the print, pause and resume macros, even if a Box is detected. With `box_count = 0` that logic is already skipped.
  - `auto_reload_detect = 0`: on runout the printer pauses instead of calling `AUTO_RELOAD_FILAMENT`, a Box macro that is not defined without the Box config.
- `config/gcode_macro.cfg`: `LOAD_FILAMENT` and `UNLOAD_FILAMENT` macros. They call the stock `M604` (load) and `M603` (cut, then purge what is left in the nozzle; pull the spool back afterwards), without the Box or filament-sensor checks of the touchscreen. Fluidd shows them as buttons on the Macros card.
  - `TEMP` (default `250`, same as stock) must be within the extruder's `min_extrude_temp` and `max_temp`.
  - Both refuse to run while printing. Pause the print first.

With QIDI's closed-source screen program (`xindi`), the touchscreen keeps the Box loading screen.

## Open-source touchscreen program

[`screen/`](screen/README.md) holds `plus4screen`, an open-source replacement for `xindi`. It drives the built-in touchscreen with QIDI's existing pages, talks to Klipper through Moonraker, and turns the control page's filament button into a single-spool load/unload flow. Nothing is flashed onto the screen; `screen/uninstall.sh` gives the screen back to `xindi`. It has not been tested on a printer yet: start with `--dry-run`.

[`tools/hmi_dump.py`](tools/hmi_dump.py) reads QIDI's screen layout (`UI/xindi_800_480.HMI`) without the TJC editor. [`screen/LAYOUT.md`](screen/LAYOUT.md) is its map of every page and button.

To switch Box logic off on a running printer without copying files, run `SAVE_VARIABLE VARIABLE=enable_box VALUE=0` from the Fluidd console. Use `VALUE=1` to switch it back on.

To get the single-spool touchscreen back, reflash the eMMC and install V1.6.0: see [docs/emmc-reflash-v1.6.0.md](docs/emmc-reflash-v1.6.0.md).

## Keeping up with upstream

```bash
git remote add upstream https://github.com/QIDITECH/QIDI_PLUS4.git
git fetch upstream
git switch main && git merge --ff-only upstream/main && git push origin main
git switch single-spool && git rebase main
```

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
