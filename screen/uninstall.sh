#!/bin/bash
# Give the touchscreen back to QIDI's xindi and remove plus4screen.
#   ./uninstall.sh [QIDI.tft]
# With plus4screen's own interface installed, QIDI's screen file is written
# back first: the one saved at install time, or the file given. That takes
# about 30 minutes (20 MB at 115200 baud).
set -euo pipefail

UNIT=plus4-screen.service
DEST=/home/mks/plus4-screen
STATE=$DEST/.stock-service
MODE_FILE=$DEST/.mode
TFT=${1:-/home/mks/qidi-screen-backup.tft}

stock=makerbase-client.service
if [ -f "$STATE" ]; then
    stock="$(cat "$STATE")"
fi
mode=qidi
if [ -f "$MODE_FILE" ]; then
    mode="$(cat "$MODE_FILE")"
fi
if [ "$mode" = plus4 ] && [ ! -f "$TFT" ]; then
    echo "QIDI's screen file $TFT is missing; pass its path (for example" >&2
    echo "UI/xindi_800_480.tft from the repository). Nothing changed." >&2
    exit 1
fi

echo "Stopping $UNIT"
sudo systemctl disable --now "$UNIT" 2>/dev/null || true
sudo rm -f /etc/systemd/system/$UNIT
sudo systemctl daemon-reload

if [ "$mode" = plus4 ]; then
    echo "Writing QIDI's screen file back ($TFT)"
    (cd "$DEST" && python3 -m plus4screen.flash "$TFT")
fi

echo "Re-enabling $stock"
sudo systemctl enable "$stock"
sudo systemctl start "$stock"

rm -rf "$DEST"
echo "Done. QIDI's screen program is running again."
