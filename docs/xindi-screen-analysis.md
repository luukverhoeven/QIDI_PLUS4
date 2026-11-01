# How the Plus4 touchscreen app (`xindi`) works

Findings from static analysis of QIDI's closed-source screen app, aimed at changing the touchscreen without a firmware downgrade.

- **Target:** `/root/xindi/build/xindi` from a Plus4 on the online update after V1.7.1. File dated 19 Oct 2026, SHA-256 `29d98488c0de0b6f3afbc24f1132828d6bb7c11601990fb7665471fb533d7e52`. aarch64 ELF, not stripped, so function names are available.
- **Tools:** REA 6.8.0 `decompile-all` with Ghidra 12.1.4, plus `llvm-objdump` and `strings`. All pseudocode is Ghidra output, not QIDI's source.
- **Addresses:** Ghidra loads the program `0x100000` higher than the ELF addresses. All addresses below are Ghidra addresses.
- **Labels:**
  - **Observed:** read directly from decompiled code or strings.
  - **Inferred:** a conclusion from observed facts.
  - **Unknown:** not established.

## Summary

- The screen is a TJC (Nextion-compatible) serial display. `xindi` drives it with plain-text TJC commands and reacts to touch events identified by page and widget number.
- The screen firmware (`.tft`) only defines the layout and which page/widget number each button reports. All behaviour lives in `xindi`.
- The old single-spool load/unload flow is still fully present in `xindi` (pages 37, 39, 40, 41, 71, 72). The installed screen firmware still draws those pages (see [Live screen tests](#live-screen-tests-1-nov-2026)).
- In the current layout, the filament button on the control page leads to the Box page 113. Its **Unload** button runs the old unload and continues into the old load steps (page 40 → 37 → 39 → 41). Only the entry is Box-specific.
- `load_mode`, which decides whether page 39 starts an unload or a load, is only ever set to "load". A screen-layout edit that jumps straight into page 39 therefore only works until the first load after each restart of `xindi`.

## Serial protocol (observed)

- **Port:** `/dev/ttyS1` at 115200 baud. 921600 baud is only used to flash screen firmware (`download_to_screen`).
- **Commands to the screen:** ASCII TJC instructions followed by `FF FF FF`.
  - `send_cmd_txt(fd, obj, value)` writes `<obj>.txt="<value>"` + `FF FF FF` (`0x86cb4c`).
  - `page_to(n)` (`0x86f1d0`) logs the change, stores `previous_page_id` and `current_page_id`, then sends `page <n>`.
  - About 80 other wrappers follow the same pattern: `send_cmd_val`, `send_cmd_vis`, `send_cmd_tsw`, `send_cmd_pic`, `send_cmd_pco`, `send_cmd_click` and more.
  - Widgets are addressed by short names on the current page (`t0`, `b3`), not by page name.
- **Events from the screen,** parsed by `parse_cmd_msg_from_tjc_screen` (`0x86e8e8`):

| First byte | Meaning | Handler |
| --- | --- | --- |
| `0x65` | Touch: page, widget, type | `tjc_event_clicked_handler(page, widget, type)` |
| `0x71` | Value set, carries the page number | `tjc_event_setted_handler` |
| `0x70` | String (keyboard input) | `tjc_event_keyboard` |
| `0x24`, `0x1A`, `0x03`–`0x06` | Standard TJC status and error codes | flags only |
| `0x91` | QIDI-specific | sets page 0, then `page_to(46)` |
| `0x92` / `0x93` | QIDI-specific | enter / leave the network test page |

## Page numbers (observed)

From the `refresh_page_show` switch (`0x7033f8`) and the navigation helpers:

| Page | Purpose | Evidence |
| --- | --- | --- |
| 3 | Main screen | `go_to_main` → `page_to(3)`; refresh `refresh_page_main` |
| 17–19 | Printing | `go_to_main` → `page_to(17)` while printing or paused; refresh `refresh_page_printing` |
| 35 | Control page (move, fans, filament) | `go_to_control` → `page_to(35)` |
| 36–41, 71, 72 | Control sub-pages and the old load/unload steps | share `refresh_page_control` with page 35 |
| 113 | Filament page without a Box | `MultiColorSlots::ShowZeroBoxPage` |
| 114 | Filament page with one Box | `MultiColorSlots::ShowSingleBoxPage` |
| 115 | Filament page with several Boxes | `MultiColorSlots::ShowMultiBoxPage` |

- The same page numbers appear in the V1.6.0 and V1.7.1 builds of `xindi` (`go_to_main` → 3 and 17, `go_to_control` → 41, 71, 40, 35). Page numbering has been stable since V1.6.0.
- In the click handler the page switch uses `page − 3`. Case `0x20` is page 35, `0x22` is page 37, `0x24` is page 39, `0x6e` is page 113.
- The `N` in the `N.pa` entries of `UI/xindi_800_480.HMI` is **not** the page number (main is `5.pa` but page 3). The real page order in the HMI is **unknown**. QIDI's TJC editor shows it.

## Filament flows (observed)

### Current flow (Box screens)

1. Page 3, widget 34 → control page 35. Seen in the printer log `qidi.log`.
2. Page 35, widget 13 → `SetSelectedSlotIndex(-1)` (external spool), `SetSelectedBoxIndex(0)`, `SlotParamsSetConfirm()` → page 113.
3. On page 113, `ShowZeroBoxPage` (`0x7b4474`) enables or disables the Load/Unload buttons (`tsw`). It uses the `filament_width_sensor` state (the Hall sensor) and a field of the selected slot. This matches QIDI's comment in issue #84 that the buttons depend on the Hall value.

### Old flow (still in `xindi`)

| Page | Widget | Action |
| --- | --- | --- |
| 35 or 36 | 3 | `page_to(36)` (temperature keypad) |
| 37 | 9 | `go_to_control()` → page 35 (the **Back** button) |
| 37 | 10 | `load_target = 220`, `page_to(39)` |
| 39 | 6 / 7 / 8 | `load_target` = 220 / 250 / 300 |
| 39 | 9 | `load_mode == 0`: `page_to(35)`. Otherwise: `page_to(37)` |
| 39 | 10 | `load_mode == 0`: `page_to(40)` + `filament_unload()`. Otherwise: `page_to(41)` + `filament_load()` |
| 40 | 9 | `load_position_inited = 1`, `load_mode = 1`, `unload_finished = 1`, `page_to(37)` (unload, then load) |
| 40 | 10 | `finish_unload()` if needed, then `page_to(113)` |
| 72 | 9 | `load_mode = 1`, `filament_load()` |
| 72 | 10 | `page_to(113)` |
| 113 | 3 | Box **Load**: `SetLoadTarget()`, `page_to(127)` (new Box load flow) |
| 113 | 4 | Box **Unload**: `SetLoadTarget()`, `filament_unload()`, `page_to(40)` (old unload page) |

- `filament_load()` (`0x71fe20`) sets `load_step = 1` and sends `M604 S<load_target>` (`F0` added once the position is initialised).
- `filament_unload()` (`0x720040`) sets `unload_step = 1` and sends `M603 S<load_target>`.
- `go_to_control()` (`0x72f590`) goes to page 41 while `load_step == 1`, page 71 while `load_step == 2`, page 40 while an unload runs, otherwise page 35.
- `finish_unload()` (`0x73b26c`) sends `SET_KINEMATIC_POSITION Y=320` and a few moves.
- `refresh_page_filament()` is still in the binary, but nothing calls it.
- The old flow ends on the Box page 113 (page 40 and page 72, widget 10).
- `load_mode` lives in `.bss`, so it is 0 (unload) when `xindi` starts. The only writes set it to 1 (page 40 widget 9, page 72 widget 9). The machine code has four references to it, all in the click handler: two reads, two writes of 1. Nothing resets it to 0.
- `unload_finished = 1` makes several later taps call `finish_unload()`, which sends `SET_KINEMATIC_POSITION Y=320`. Faking page 40 widget 9 without a real unload could therefore give Klipper a wrong Y position.

## Live screen tests (1 Nov 2026)

Commands were written straight to the screen to open pages without going through `xindi`.

- **How:** as `mks`, open `/dev/ttyS1` with `O_WRONLY | O_NONBLOCK | O_NOCTTY` and write `page <n>` + `FF FF FF`. `mks` is in the `dialout` group, so no `sudo` is needed.
- **Don't use a normal open:** the port has `-clocal`, so `printf ... > /dev/ttyS1` blocks forever waiting for a carrier signal.
- **Taps are logged:** the screen's raw replies and touch events appear in `journalctl -u makerbase-client`, which `mks` can read. Page changes and clicks also appear in `qidi.log`.

| Page | What the installed screen shows |
| --- | --- |
| 36 | Temperature keypad ("Extruder", "MAX: 370℃", digits 0–9) |
| 37 | Control layout with "Please confirm that the filament has entered the nozzle.", **Next**, and a "50mm / Back / 100mm" control. **Back** is widget 9 and opens page 35 |
| 39 | Control layout with step icons (home, move X, cutter, filament) and the same **Next** and "50mm / Back / 100mm" controls |

- Pages 37 and 39 exist in the installed screen firmware and their buttons report the widget numbers the click handler expects.
- After a page is opened this way, `xindi` still believes the screen is on the previous page. It keeps updating that page's widgets, and the screen answers with `0x02` (invalid component). Tapping Home brings both back in sync.
- Sending `printh 65 23 08 01 ff ff ff` to the screen did not produce a touch event in `xindi`. Using `printh` to fake taps is **not confirmed**.

## Ways to change the touchscreen

0. **Use the existing path, no changes.** Give the external spool a filament type once on the Box page; issue #84 users report that this enables Unload. **Unload** then runs the old unload (page 40), and page 40's Load button continues through pages 37 → 39 → 41. For a load without a previous unload, use the `LOAD_FILAMENT` macro in Fluidd.
1. **Edit the screen layout (`.HMI`) in the TJC editor (Windows).** Give the filament button on page 35 a local `page 39` or `page 37` action, or add a new button for it. `xindi` would then handle the old steps. But:
   - Because `load_mode` never returns to 0, page 39 would only unload until the first load after each restart of `xindi`.
   - The edited `.tft` has to be flashed onto the screen.
   - Every QIDI update overwrites it.
   - The page numbers above must be checked in the editor first.
2. **Patch `xindi`.** For example, point page 35 widget 13 at `page_to(37)` instead of the Box page. That means binary patching a closed program that QIDI updates replace. Not recommended.
3. **Replace `xindi` with a self-written program** that speaks the protocol above and talks to Moonraker. Full control, but it also has to take over Wi-Fi setup, updates, calibration and printing screens.

## Files on this Mac (not in the repository)

- **Analysis folder:** `~/tools/analysis/xindi/`, with:
  - `xindi-plus4-20261019` (the binary)
  - `pc-app/` and `pc-app2/` (Ghidra pseudocode for Ghidra address ranges `0x560000`–`0x7b0000` and `0x7b0000`–`0x8b0000`, about 20,600 functions)
  - `name_to_file.json` (function name → pseudocode file)
  - `pc-app.manifest.json` and `pc-app2.manifest.json` (REA Evidence records)
- **REA Evidence ID** (first pass): `ev_66b19048c16091f0022b05e18077e5a39ae911d999bd317630b62d52996015b4`.
