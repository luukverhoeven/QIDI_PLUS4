#!/bin/bash
# Install plus4screen on the printer and switch the touchscreen over to it.
# Run on the printer, from this directory:
#   ./install.sh                 own interface: writes ui/build/plus4ui.tft to
#                                the screen (about 3 minutes)
#   ./install.sh --no-flash      own interface, plus4ui.tft is already on the
#                                screen
#   ./install.sh --qidi-screen   keep QIDI's screen file (QIDI's layout)
#   --force                      write plus4ui.tft even without a saved copy
#                                of QIDI's screen file
# Undo with ./uninstall.sh
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST=/home/mks/plus4-screen
UNIT=plus4-screen.service
STATE=$DEST/.stock-service
MODE_FILE=$DEST/.mode
SCREEN_FILE=$DEST/.screen-file     # which screen file is on the screen
TFT="$SRC/ui/build/plus4ui.tft"
BACKUP=/home/mks/qidi-screen-backup.tft
WPA_CONF=/etc/wpa_supplicant/wpa_supplicant-wlan0.conf
WPA_UNIT=makerbase-wlan0.service

mode=plus4
flash=1
force=0
for arg in "$@"; do
    case "$arg" in
        --no-flash) flash=0 ;;
        --qidi-screen) mode=qidi; flash=0 ;;
        --force) force=1 ;;
        *) echo "unknown option: $arg" >&2; exit 2 ;;
    esac
done
if [ "$mode" = plus4 ] && [ "$flash" = 1 ] && [ ! -f "$TFT" ]; then
    echo "$TFT is missing. Nothing changed." >&2
    exit 1
fi
if [ "$mode" = qidi ] && [ "$(cat "$SCREEN_FILE" 2>/dev/null)" = plus4ui ]; then
    echo "plus4ui.tft is on the screen; QIDI's layout needs QIDI's screen" >&2
    echo "file. Run ./uninstall.sh first. Nothing changed." >&2
    exit 1
fi
if [ "$mode" = plus4 ] && [ "$flash" = 1 ] && [ "$force" = 0 ] \
        && [ ! -f "$BACKUP" ] && ! sudo test -f /root/800_480.tft.bak; then
    echo "No copy of QIDI's screen file ($BACKUP or" >&2
    echo "/root/800_480.tft.bak), so it could not be put back later." >&2
    echo "Use --force to write plus4ui.tft anyway. Nothing changed." >&2
    exit 1
fi

# QIDI's screen program (xindi) runs from a systemd service: makerbase-client
# on V1.7.x. Other units also live in /root/xindi (makerbase-byid runs
# mks-id.sh), so only a unit that starts xindi/build counts.
find_stock_service() {
    local unit
    if systemctl list-unit-files --no-legend makerbase-client.service \
            2>/dev/null | grep -q '^makerbase-client.service'; then
        echo makerbase-client.service
        return
    fi
    for unit in $(systemctl list-unit-files --type=service --no-legend \
                  | awk '{print $1}'); do
        [ "$unit" = "$UNIT" ] && continue
        if systemctl cat "$unit" 2>/dev/null \
                | grep -qE '^ExecStart=.*xindi/build'; then
            echo "$unit"
            return
        fi
    done
}

stock="$(find_stock_service)"
if [ -z "$stock" ]; then
    echo "Could not find QIDI's screen service. Nothing changed." >&2
    exit 1
fi
echo "QIDI screen service: $stock"
systemctl cat "$stock" | grep -E '^(ExecStart|User)=' || true

echo "Installing to $DEST ($mode interface)"
mkdir -p "$DEST"
rm -rf "$DEST/plus4screen"
cp -r "$SRC/plus4screen" "$DEST/"
echo "$stock" > "$STATE"
echo "$mode" > "$MODE_FILE"

sed "s|^ExecStart=.*|ExecStart=/usr/bin/python3 -m plus4screen --ui $mode|" \
    "$SRC/systemd/$UNIT" | sudo tee /etc/systemd/system/$UNIT >/dev/null
sudo systemctl daemon-reload

echo "Stopping and disabling $stock"
sudo systemctl stop "$stock"
sudo systemctl disable "$stock"
sudo systemctl stop "$UNIT" 2>/dev/null || true

if [ "$mode" = plus4 ]; then
    # QIDI's program keeps the screen file it last wrote in /root.
    if [ ! -f "$BACKUP" ] && sudo test -f /root/800_480.tft.bak; then
        sudo cp /root/800_480.tft.bak "$BACKUP"
        sudo chown "$(id -u):$(id -g)" "$BACKUP"
        echo "Saved QIDI's screen file as $BACKUP"
    fi
    if [ "$flash" = 1 ]; then
        echo "Writing plus4ui.tft to the screen"
        (cd "$DEST" && python3 -m plus4screen.flash "$TFT")
        sleep 6
    fi
    echo plus4ui > "$SCREEN_FILE"
fi

if [ "$mode" = plus4 ]; then
    # The Wi-Fi screen talks to wpa_supplicant's control socket. Let the
    # netdev group (mks is a member) use it; QIDI's file has group 0.
    if sudo grep -q '^ctrl_interface_group=0$' "$WPA_CONF" 2>/dev/null; then
        sudo cp -p "$WPA_CONF" "$WPA_CONF.plus4screen-backup"
        sudo sed -i 's/^ctrl_interface_group=0$/ctrl_interface_group=netdev/' \
            "$WPA_CONF"
        echo "Wi-Fi control: allowed for group netdev. Wi-Fi restarts in a few"
        echo "seconds ($WPA_UNIT); the connection drops briefly."
        sudo systemd-run --quiet --on-active=8 \
            /bin/systemctl restart "$WPA_UNIT"
    fi
fi

echo "Starting $UNIT"
sudo systemctl enable --now "$UNIT"
sleep 2
systemctl --no-pager status "$UNIT" | head -n 5
echo
echo "Logs: journalctl -u $UNIT -f"
echo "Undo: $SRC/uninstall.sh"
