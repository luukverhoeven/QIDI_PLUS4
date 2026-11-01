# plus4screen's own interface: from design to screen file

The interface is designed as HTML and turned into the screen file `build/plus4ui.tft` and the layout map `../plus4screen/ui_layout.json`.

```
design/ui.html, ui.css, ui.js   --build_assets.py-->  build/pictures/*.png  --TJC editor-->  build/plus4ui.tft
 (all screens, annotated)                             ../plus4screen/ui_layout.json
```

## Files

| Path | What it is |
| --- | --- |
| `design/ui.html` | Every screen at 800x480, with annotations: `data-hit` (touch target), `data-on` (toggle), `data-text` + `data-font` (live text), `data-bar`, `data-dot`, `data-thumb` |
| `design/ui.css`, `design/ui.js` | Colours, fonts and components; the navigation rail; the build modes |
| `design/fonts/` | Inter (SIL Open Font License, `OFL.txt`) |
| `design/icons/` | Lucide icons used by the design (ISC License, `LICENSE`) |
| `build_assets.py` | Renders the pictures and writes `ui_layout.json` |
| `hmi/plus4ui.HMI` | The TJC editor project of the screen file |
| `hmi/f0.zi` … `f4.zi` | The screen fonts, made with the editor's font tool |
| `build/plus4ui.tft` | The compiled screen file |
| `emulator.py`, `preview_app.py` | Draw what the screen would show, without a printer |

`build/pictures`, `build/preview`, `build/app-preview` and `build/layout.json` are generated and not in git.

## Change the design

1. Edit `design/ui.html` / `ui.css`. Open `design/ui.html` in a browser through a local web server to see all screens, for example `python3 -m http.server -d screen/ui/design` and http://localhost:8000/ui.html.
2. Render: `~/.venvs/rustwright/bin/python screen/ui/build_assets.py` (Chromium through [rustwright](https://pypi.org/project/rustwright/) or Playwright). It checks for duplicate IDs and annotations outside the screen, and writes:
   - `build/pictures/NNN_<screen>_<kind>.png`: per screen `bg`, `pressed` (all touch targets pressed) and `on` (all toggles selected). Picture N must get ID N in the editor.
   - `build/preview/<screen>.png` with sample values.
   - `build/layout.json` and its copy `../plus4screen/ui_layout.json`.
3. Check the whole program: `python3 screen/ui/preview_app.py` (needs Pillow) runs plus4screen against a made-up printer and saves each step to `build/app-preview/`.
4. If any picture changed, rebuild the screen file (below) and write it to the screen.

Layout-only changes (positions, texts, colours of live values) need step 4 too, because the pictures carry the layout.

## Build the screen file

Needs the TJC editor "USART HMI" (Windows; version 1.68.2 was used) and the Inter fonts installed in Windows.

1. Open `hmi/plus4ui.HMI`. Device: TJC8048X250_011, 0°, utf-8.
2. Pictures: delete all, then add every file of `build/pictures` in name order, so the IDs match the file numbers.
3. Fonts: keep `f0`–`f4` in this order (`build_assets.py` lists them in `FONTS`). To remake one: Tools → font maker, Inter, encoding utf-8, anti-aliased, characters: printable ASCII plus `° · … – — ± ✓ × →`.

   | Font | Inter | Height | CSS size in the design |
   | --- | --- | --- | --- |
   | f0 | SemiBold | 16 | 13 px |
   | f1 | Bold | 18 | 15 px |
   | f2 | Bold | 24 | 20 px |
   | f3 | Bold | 40 | 34 px |
   | f4 | ExtraBold | 88 | 72 px |

4. Pages: `page0` shows picture 0 and runs `printh 91` before it is drawn (plus4screen sees the screen start); `page1` is empty with background colour 2146 (`#0A0E13`).
5. `Program.s` must contain `baud=115200`.
6. Compile, then File → output production file, and copy `plus4ui.tft` to `build/`.

## Write it to the screen

On the printer, with plus4screen and QIDI's screen program stopped:

```bash
python3 -m plus4screen.flash plus4ui.tft      # about 3 minutes
```

The upload is the one QIDI's own program uses (`whmi-wri <size>,115200,0`, 4 KiB blocks acknowledged with `0x05`). If it stops halfway the screen waits for a new upload; run it again.
