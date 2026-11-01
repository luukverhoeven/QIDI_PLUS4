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
- The old single-spool load/unload flow is still fully present in `xindi` (pages 37, 39, 40, 41, 71, 72). In the current layout, the filament button on the control page leads to the Box page 113 instead.
- **Inferred:** a modified screen layout that sends the user into page 37 could bring back the old flow without changing `xindi`. Whether the installed `.tft` still contains working pages 37–41 is **unknown**.

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
| 35 or 36 | 3 | `page_to(36)` |
| 37 | 10 | `load_target = 220`, `page_to(39)` |
| 39 | 10 | `load_mode == 0`: `page_to(40)` + `filament_unload()`. Otherwise: `page_to(41)` + `filament_load()` |
| 40 | 9 | `load_mode = 1`, `page_to(37)` (unload, then load) |
| 40 | 10 | `finish_unload()` if needed, then `page_to(113)` |
| 72 | 9 | `load_mode = 1`, `filament_load()` |
| 72 | 10 | `page_to(113)` |

- `filament_load()` (`0x71fe20`) sets `load_step = 1` and sends `M604 S<load_target>` (`F0` added once the position is initialised).
- `filament_unload()` (`0x720040`) sets `unload_step = 1` and sends `M603 S<load_target>`.
- `go_to_control()` (`0x72f590`) goes to page 41 while `load_step == 1`, page 71 while `load_step == 2`, page 40 while an unload runs, otherwise page 35.
- `finish_unload()` (`0x73b26c`) sends `SET_KINEMATIC_POSITION Y=320` and a few moves.
- `refresh_page_filament()` is still in the binary, but nothing calls it.
- The old flow ends on the Box page 113 (page 40 and page 72, widget 10).

### Unknowns

- No `page_to(37)` is reachable from page 35 or 36 in `xindi`. The only entries into page 37 come from pages 40 and 72, which are inside the old flow. **Unknown** whether the current `.tft` has a button that opens page 37 by itself.
- **Unknown** whether pages 37–41, 71 and 72 in the installed `.tft` still have the widgets the handler expects (widget 10 on 37/39, 9 and 10 on 40 and 72).

## Ways to change the touchscreen

1. **Edit the screen layout (`.HMI`) in the TJC editor (Windows).** Give the filament button on page 35 a local `page 37` action, or add a new button for it. `xindi` would then handle pages 37 → 39 → 40/41 as before. Smallest change, but:
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
