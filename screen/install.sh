#!/bin/bash
# Install plus4screen on the printer and switch the touchscreen over to it.
# Run on the printer, from this directory:  ./install.sh
# Undo with ./uninstall.sh
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST=/home/mks/plus4-screen
UNIT=plus4-screen.service
STATE=/home/mks/plus4-screen/.stock-service

# QIDI's screen program (xindi) runs from a systemd service. Find it by the
# xindi path in its unit, falling back to the name seen on V1.7.x.
find_stock_service() {
    local unit
    for unit in $(systemctl list-unit-files --type=service --no-legend \
                  | awk '{print $1}'); do
        [ "$unit" = "$UNIT" ] && continue
        if systemctl cat "$unit" 2>/dev/null | grep -q 'xindi'; then
            echo "$unit"
            return
        fi
    done
    if systemctl list-unit-files makerbase-client.service >/dev/null 2>&1; then
        echo makerbase-client.service
    fi
}

stock="$(find_stock_service)"
if [ -z "$stock" ]; then
    echo "Could not find QIDI's screen service. Nothing changed." >&2
    exit 1
fi
echo "QIDI screen service: $stock"
systemctl cat "$stock" | grep -E '^(ExecStart|User)=' || true

echo "Installing to $DEST"
mkdir -p "$DEST"
rm -rf "$DEST/plus4screen"
cp -r "$SRC/plus4screen" "$DEST/"
echo "$stock" > "$STATE"

sudo cp "$SRC/systemd/$UNIT" /etc/systemd/system/$UNIT
sudo systemctl daemon-reload

echo "Stopping and disabling $stock"
sudo systemctl stop "$stock"
sudo systemctl disable "$stock"

echo "Starting $UNIT"
sudo systemctl enable --now "$UNIT"
sleep 2
systemctl --no-pager status "$UNIT" | head -n 5
echo
echo "Logs: journalctl -u $UNIT -f"
echo "Undo: $SRC/uninstall.sh"
