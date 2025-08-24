#!/bin/bash
# uninstaller.sh

SCRIPT_DIR="$(pwd)"
SERVICE_DIR="$HOME/.config/systemd/user"
MAIN_SERVICE="$SERVICE_DIR/yeelight-controller.service"
SLEEP_HOOK="/usr/lib/systemd/system-sleep/yeelight.sh"

echo "Stopping and disabling Yeelight Controller service..."
systemctl --user stop yeelight-controller.service 2>/dev/null
systemctl --user disable yeelight-controller.service 2>/dev/null

echo "Removing service file: $MAIN_SERVICE"
rm -f "$MAIN_SERVICE"

echo "Reloading systemd user daemon..."
systemctl --user daemon-reload

if [ -f "$SLEEP_HOOK" ]; then
  echo "Removing system sleep hook: $SLEEP_HOOK"
  sudo rm -f "$SLEEP_HOOK"
fi

/usr/bin/python3 $SCRIPT_DIR/off.py

echo "✅Uninstallation complete. Yeelight Controller removed."

