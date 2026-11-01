#!/bin/bash
# Give the touchscreen back to QIDI's xindi and remove plus4screen.
#   ./uninstall.sh [QIDI.tft]
# If plus4ui.tft is on the screen, QIDI's screen file is written back first:
# the one saved at install time, or the file given. That takes about 30
# minutes (20 MB at 115200 baud); run this in tmux or screen, or with nohup,
# so a dropped SSH connection does not stop it. If writing fails, plus4screen
# is started again and nothing else changes.
set -euo pipefail

UNIT=plus4-screen.service
DEST=/home/mks/plus4-screen
STATE=$DEST/.stock-service
SCREEN_FILE=$DEST/.screen-file
TFT=${1:-/home/mks/qidi-screen-backup.tft}

stock=makerbase-client.service
if [ -f "$STATE" ]; then
    stock="$(cat "$STATE")"
fi
on_screen=qidi
if [ -f "$SCREEN_FILE" ]; then
    on_screen="$(cat "$SCREEN_FILE")"
fi

if [ "$on_screen" = plus4ui ]; then
    if [ ! -f "$TFT" ]; then
        echo "QIDI's screen file $TFT is missing; pass its path (for" >&2
        echo "example UI/xindi_800_480.tft from the repository). Nothing" >&2
        echo "changed." >&2
        exit 1
    fi
    TFT="$(readlink -f "$TFT")"
    echo "Writing QIDI's screen file back ($TFT)"
    sudo systemctl stop "$UNIT" 2>/dev/null || true
    if ! (cd "$DEST" && python3 -m plus4screen.flash "$TFT"); then
        echo "Writing QIDI's screen file failed; starting plus4screen again." >&2
        sudo systemctl start "$UNIT" || true
        exit 1
    fi
    echo qidi > "$SCREEN_FILE"
fi

echo "Removing $UNIT"
sudo systemctl disable --now "$UNIT" 2>/dev/null || true
sudo rm -f /etc/systemd/system/$UNIT
sudo systemctl daemon-reload

echo "Re-enabling $stock"
sudo systemctl enable "$stock"
sudo systemctl start "$stock"

rm -rf "$DEST"
echo "Done. QIDI's screen program is running again."
