#!/bin/bash
set -e

# Variables
SCRIPT_DIR="$(pwd)"
PAM_FILE="/etc/pam.d/sddm"
SCRIPT_PATH="/usr/local/bin/yeelight-pam.sh"

echo "🔧 Uninstalling Yeelight PAM hook..."

# 1. Remove line from PAM config
if grep -q "yeelight-pam.sh" "$PAM_FILE"; then
    echo " - Removing PAM hook from $PAM_FILE"
    sudo sed -i '/yeelight-pam.sh/d' "$PAM_FILE"
else
    echo " - No PAM hook found in $PAM_FILE"
fi

# 2. Remove helper script
if [ -f "$SCRIPT_PATH" ]; then
    echo " - Removing helper script $SCRIPT_PATH"
    sudo rm -f "$SCRIPT_PATH"
else
    echo " - No helper script found at $SCRIPT_PATH"
fi

/usr/bin/python3 $SCRIPT_DIR/off.py

echo "✅ Uninstall complete. You may need to reboot or restart sddm for changes to fully apply."
