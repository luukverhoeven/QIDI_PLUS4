# Reflash the Plus4 eMMC and install firmware V1.6.0

Goal: get the V1.6.0 touchscreen back (single-spool load/unload, no QIDI Box pages) on a Plus4 that runs V1.7.x.

Why not a USB downgrade: the V1.6.0 and V1.7.x update packages are both the Debian package `QIDI-X-Plus4` version `1.0.1`. Installing V1.6.0 over V1.7.x makes `dpkg` delete every file that only V1.7.x ships, including `klippy.py`, `gcode.py`, `save_variables.py` and the filament sensor modules. A clean factory image followed by the V1.6.0 update avoids that.

Written for macOS. Commands run in Terminal.

## Before you start

- **Trade-offs:** V1.6.0 has no QIDI Box support and none of the V1.7.x fixes. Printer settings and calibration are reset.
- **Rollback:** step 3 makes a full image of the current eMMC. Restoring that image puts the printer back exactly as it is today.
- **Unverified:** QIDI documents the eMMC flash and the USB update separately. No one has confirmed the full route (factory image, then V1.6.0) in the QIDI issue tracker.

## What you need

| Item | Notes |
| --- | --- |
| MKS EMMC-Adapter V2 (USB 3.0) | Standalone USB reader for the eMMC module. No extra card reader needed. |
| USB stick | Any size. Gets erased and formatted as FAT32. |
| Small Phillips screwdriver | For the rear maintenance cover and the 2 eMMC screws. |
| About 40 GB free on the Mac | Backup image plus the factory image. |
| [balenaEtcher](https://etcher.balena.io/) | Writes images to the eMMC. |
| `7zz` | Already installed (`brew install sevenzip`). Unpacks the factory image. |

## 1. Download and unpack the files

1. Factory image: open [QIDI's eMMC page](https://wiki.qidi3d.com/en/Memo/flash-emmc). Click **QIDI Plus 4 Image for eMMC**, then download `PLus4_2024_6_29.7z` (1.51 GB) from Google Drive.
2. Firmware V1.6.0: download `PLUS4_V1.6.0.rar` (16.3 MB) from the [V1.6.0 release](https://github.com/QIDITECH/QIDI_PLUS4/releases/tag/Plus4_V1.6.0).
3. Unpack both into a work folder:

```bash
mkdir -p ~/Plus4-reflash && cd ~/Plus4-reflash
```

```bash
7zz x ~/Downloads/PLus4_2024_6_29.7z
```

```bash
tar -xf ~/Downloads/PLUS4_V1.6.0.rar
```

`tar` gives a `QD_Update` folder with `QD_Plus4_SOC` (about 5 MB) and `QD_Plus4_UI` (about 29 MB). Use the macOS `tar` for this archive: `7zz` fails on `QD_Plus4_UI` with "Unsupported Method".

## 2. Save the current configuration

1. In Fluidd (`http://192.168.86.210`), open **Configuration**. Download `printer.cfg`, `gcode_macro.cfg` and `saved_variables.cfg`. They hold your current calibration values for reference.
2. Write down your Wi-Fi name and password. The new image starts without them.
3. If a QIDI Box is connected, power it off and unplug it. V1.6.0 does not support it.

## 3. Take the eMMC out and back it up

1. Turn the printer off and unplug the power cord.
2. Open the maintenance cover on the back of the printer.
3. Find the eMMC module on the mainboard. It is a small separate board held by 2 small screws. Take a photo of how it sits before removing anything.
4. Remove the 2 screws and lift the module straight off its connector. Don't touch the connector pins.
5. Put the module on the MKS EMMC-Adapter V2 and plug the adapter into the Mac.
6. If macOS says the disk is not readable, click **Ignore**. Never click **Initialize**.
7. Find the eMMC's disk number. It is the external disk of about 31 GB:

```bash
diskutil list external physical
```

In the commands below, replace `diskN` with that number, for example `disk4`. A wrong number erases another drive.

8. Unmount the disk, then copy the whole eMMC into a compressed image (10–20 minutes):

```bash
diskutil unmountDisk /dev/diskN
```

```bash
sudo dd if=/dev/rdiskN bs=4m status=progress | gzip -1 > ~/Plus4-reflash/plus4-emmc-v1.7-backup.img.gz
```

9. Check that the backup is complete and readable:

```bash
gzip -t ~/Plus4-reflash/plus4-emmc-v1.7-backup.img.gz && echo "backup OK"
```

Don't continue until it prints `backup OK`.

## 4. Write the factory image

1. Open balenaEtcher.
2. **Flash from file:** choose the `.img` file that `7zz` unpacked into `~/Plus4-reflash`.
3. **Select target:** choose the eMMC adapter, about 31 GB. Check the size before you continue.
4. Click **Flash**. Etcher writes the image and then verifies it.
5. When it is done, eject the disk, remove the module from the adapter and refit it on the mainboard with the 2 screws.

## 5. First boot on the factory image

1. Close the cover, plug in the printer and turn it on.
2. The screen may show a Chinese error saying the UI version does not match the firmware. That is expected: the screen still has the V1.7.x screen firmware. The V1.6.0 update in step 6 replaces it.
3. Connect the printer to your network: Wi-Fi from the screen, or an Ethernet cable.

## 6. Install V1.6.0 from USB

1. Format the USB stick as FAT32. In Disk Utility: select the stick, **Erase**, format **MS-DOS (FAT)**, scheme **Master Boot Record**. Check that you picked the stick and not another disk.
2. Copy the `QD_Update` folder from `~/Plus4-reflash` to the top level of the stick, so the path is `/QD_Update/QD_Plus4_SOC`.
3. Remove the hidden macOS `._` files from the stick, then eject it (replace `STICK` with the stick's name):

```bash
dot_clean -m /Volumes/STICK
```

4. Put the stick in the printer. On the screen, open the version information and tap **Check for updates**. Follow the prompts.
5. Don't power off while it updates. Flashing the screen firmware takes several minutes.
6. Afterwards the version screen should show V1.6.0.

If the printer doesn't offer the update, check that the folder is called exactly `QD_Update` and sits at the top level of a FAT32 stick.

## 7. Set up and calibrate

1. Recalibrate from the screen: bed leveling and Z offset at minimum. The V1.6.0 release notes say recalibration is required.
2. Check the old filament screen: load and unload should work without Box pages.
3. When the printer offers an online update to V1.7.x, decline it. Accepting brings back the Box screens.
4. Don't upload `config/` files from the `single-spool` branch to this printer. They are made for V1.7.x macros.

## Roll back to the current state

1. Turn the printer off, take the eMMC out and put it on the adapter (steps 3.1 to 3.7).
2. In balenaEtcher, choose `plus4-emmc-v1.7-backup.img.gz` as the file and the eMMC as the target. Etcher reads `.img.gz` directly.
3. Refit the module. The printer starts exactly as it was before step 3.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| Etcher doesn't list the adapter | Try another USB port or cable, and check that the module sits flat on the adapter. |
| Klipper reports an MCU protocol error after the update | Stop, then roll back with the backup image. Both packages declare MCU firmware `V0.12.0`, so this is not expected. |
| Screen stays on the Chinese version error after the update | Run the USB update again. If it persists, roll back. |
| Printer has a new IP address | Look it up in your router. Fluidd and the slicer need the new address. |
