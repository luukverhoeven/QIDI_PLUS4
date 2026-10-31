# Reflash the eMMC and install firmware V1.6.0

This guide replaces the Plus4 system on the eMMC with QIDI's factory image and then installs firmware V1.6.0 from USB. V1.6.0 is the last release with the single-spool filament screen; V1.7.0 and later always show the QIDI Box filament page.

Do not install V1.6.0 directly over V1.7.x. Both update packages install as the same Debian package (`QIDI-X-Plus4` version `1.0.1`), so installing V1.6.0 over V1.7.x removes files that only V1.7.x ships, including `klippy.py`, `gcode.py` and `save_variables.py`. QIDI's own V1.6.0 release notes also advise against downgrading.

**Time:** about 2 hours. **Difficulty:** moderate. Mains-powered electronics are opened.

## What you lose

- All printer state on the eMMC: calibration, `printer.cfg` and `saved_variables.cfg` edits, Wi-Fi settings, QIDI cloud binding, and gcode files stored on the printer.
- QIDI Box support. V1.6.0 predates the Box; disconnect the Box before you start.
- Fixes from V1.7.x, such as the improved resume printing.

Step 2 takes a full image of the current eMMC, so all of this can be restored exactly.

## You need

- MKS EMMC-Adapter V2 (USB 3.0). It is a standalone USB reader; no extra card reader is needed.
- A Mac or PC with a USB 3.0 port (USB-C to USB-A adapter if needed) and about 35 GB free disk space.
- [balenaEtcher](https://etcher.balena.io/).
- A USB stick formatted as FAT32 (in Disk Utility: **MS-DOS (FAT)**).
- A screwdriver for the rear cover and a small one for the eMMC screws.
- On macOS: `7zz` (`brew install sevenzip`) or [Keka](https://www.keka.io/) to unpack the factory image.

## Downloads

| File | Source | Size |
|---|---|---|
| `PLus4_2024_6_29.7z` (factory system image) | Google Drive folder linked as "QIDI Plus 4 Image for eMMC" on [QIDI's eMMC wiki page](https://wiki.qidi3d.com/en/Memo/flash-emmc) | 1.51 GB |
| `PLUS4_V1.6.0.rar` (firmware update) | [QIDI_PLUS4 release Plus4_V1.6.0](https://github.com/QIDITECH/QIDI_PLUS4/releases/tag/Plus4_V1.6.0) | 16.3 MB |

## Step 1: Prepare the downloads

1. Unpack the factory image. It contains an `.img` file.

   ```bash
   7zz x PLus4_2024_6_29.7z
   ```

2. Unpack the firmware update with the `tar` that ships with macOS. Some 7-Zip builds fail on `QD_Plus4_UI` with `Unsupported Method`; `tar` extracts it correctly.

   ```bash
   tar -xf PLUS4_V1.6.0.rar
   ```

   This creates `QD_Update/QD_Plus4_SOC` (about 5 MB) and `QD_Update/QD_Plus4_UI` (about 29 MB).

3. Copy the `QD_Update` folder to the root of the FAT32 USB stick. Keep the stick aside for step 6.

## Step 2: Remove the eMMC and back it up

1. Write down your current calibration values from `printer.cfg` in Fluidd so you can compare later: the `[input_shaper]` values, `pressure_advance` under `[extruder]`, and `z_offset` in `saved_variables.cfg`.
2. Shut down the printer from the screen, switch it off, and **unplug the mains cable**.
3. Remove the rear mainboard cover, the panel with the mainboard fan.
4. Touch a bare metal part of the frame to discharge static electricity.
5. Take a photo of the eMMC module so you know its orientation.
6. Remove the two small screws that hold the eMMC module. Lift the module straight up from its connector; do not lever it at an angle.
7. Plug the module into the MKS EMMC-Adapter V2 and connect the adapter to the Mac.
8. If macOS shows "The disk you inserted was not readable by this computer", click **Ignore**. Never click **Initialize**; that erases the module.
9. Find the disk number. Look for an `external, physical` disk of about 31 GB:

   ```bash
   diskutil list external
   ```

   The rest of this guide uses `disk4` as an example. Use your own number in every command. A wrong number overwrites another disk.

10. Unmount it and take the backup. This reads all 32 GB; expect 10 to 30 minutes.

    ```bash
    diskutil unmountDisk /dev/disk4
    sudo dd if=/dev/rdisk4 bs=4m status=progress | gzip -1 > ~/plus4-emmc-v1.7-backup.img.gz
    ```

11. Check that the backup is complete and readable:

    ```bash
    gzip -t ~/plus4-emmc-v1.7-backup.img.gz && echo "backup OK"
    ```

    Do not continue without `backup OK`. Copy the file to a second location if you can.

## Step 3: Flash the factory image

1. Open balenaEtcher.
2. **Flash from file**: select the `.img` file from step 1.
3. **Select target**: select the MKS adapter (about 31 GB). Check the size; do not pick another drive.
4. Click **Flash** and wait until Etcher has finished writing and validating.
5. Eject the disk, then unplug the adapter.

## Step 4: Put the eMMC back

1. Place the module back in the same orientation as in your photo and press it straight down onto the connector.
2. Fit the two small screws.
3. Refit the rear mainboard cover.
4. Reconnect the mains cable.

## Step 5: First boot on the factory image

1. Switch the printer on. The first boot takes a few minutes.
2. Follow the setup screens (language, Wi-Fi). The printer may get a new IP address from your router.
3. The screen can show a Chinese error message saying that the UI version does not match the firmware. The touchscreen still runs the newer V1.7.x screen firmware; step 6 replaces it.
4. In Fluidd, check that Klipper reaches **Ready**. If it reports an MCU protocol error instead, stop here and restore the backup (see "Roll back to V1.7.x"). The mainboard firmware reports `mcu = V0.12.0` in both V1.6.0 and V1.7.1, so this is not expected.

## Step 6: Install V1.6.0 from USB

1. Insert the USB stick from step 1.
2. On the screen, open the version information page and press **Check for updates**. An update prompt appears.
3. Confirm the update. The touchscreen firmware (`QD_Plus4_UI`) is flashed as part of the update and takes several minutes. **Do not switch the printer off** while the update runs.
4. When it is done, check the version page shows V1.6.0.

QIDI's release notes give no intermediate-version requirement. If the printer refuses to update directly to V1.6.0, install [V1.4.3](https://github.com/QIDITECH/QIDI_PLUS4/releases/tag/Plus4_V1.4.3) first, then V1.6.0.

If the touchscreen stays blank or stuck after the update, see the community guide for [repairing the display firmware](https://github.com/qidi-community/Plus4-Wiki/tree/main/content/display-firmware-repair).

## Step 7: After the update

1. Recalibrate. The update replaces `printer.cfg`. Run the calibration from the screen (bed leveling, Z offset and input shaping), then compare with the values you wrote down in step 2.
2. Ignore every online update prompt. Accepting one installs V1.7.x again and brings back the Box filament page.
3. Change the default SSH passwords. The factory image sets `mks` and `root` back to `makerbase`. Run `passwd` as `mks`, then `sudo passwd root`.
4. Do not copy this fork's `single-spool` configuration onto the printer. It is based on V1.7.x macros. V1.6.0 has single-spool load and unload on the screen, so the `LOAD_FILAMENT` and `UNLOAD_FILAMENT` macros are not needed.

## Roll back to V1.7.x

Repeat step 2 up to the `diskutil unmountDisk` command, then write the backup back to the module:

```bash
gunzip -c ~/plus4-emmc-v1.7-backup.img.gz | sudo dd of=/dev/rdisk4 bs=4m status=progress
```

balenaEtcher can also flash the `.img.gz` file directly. Refit the module as in step 4. The printer then boots exactly as it was before step 2, including calibration and settings.

## References

- [QIDI wiki: Flash System Image (eMMC)](https://wiki.qidi3d.com/en/Memo/flash-emmc)
- [QIDI_PLUS4 release Plus4_V1.6.0](https://github.com/QIDITECH/QIDI_PLUS4/releases/tag/Plus4_V1.6.0)
- [QIDI_PLUS4 issue #84: loading filament without a QIDI Box](https://github.com/QIDITECH/QIDI_PLUS4/issues/84)
- [FreeDi: Plus 4 rollback guide](https://freedi-wiki.github.io/pages/restore-stock/restore-plus4/)
