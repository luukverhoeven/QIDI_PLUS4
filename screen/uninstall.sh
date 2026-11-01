#!/bin/bash
# Give the touchscreen back to QIDI's xindi and remove plus4screen.
set -euo pipefail

UNIT=plus4-screen.service
DEST=/home/mks/plus4-screen
STATE=$DEST/.stock-service

stock=makerbase-client.service
if [ -f "$STATE" ]; then
    stock="$(cat "$STATE")"
fi

echo "Stopping $UNIT"
sudo systemctl disable --now "$UNIT" 2>/dev/null || true
sudo rm -f /etc/systemd/system/$UNIT
sudo systemctl daemon-reload

echo "Re-enabling $stock"
sudo systemctl enable "$stock"
sudo systemctl start "$stock"

rm -rf "$DEST"
echo "Done. QIDI's screen program is running again."
