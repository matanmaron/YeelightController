#!/bin/bash
# installer.sh

SCRIPT_DIR="$(pwd)"
USER_NAME="$(whoami)"
SERVICE_DIR="$HOME/.config/systemd/user"
MAIN_SERVICE="$SERVICE_DIR/yeelight-controller.service"
SLEEP_HOOK="/usr/lib/systemd/system-sleep/yeelight.sh"

# Create systemd user directory
mkdir -p "$SERVICE_DIR"

# --- Main service ---
cat > "$MAIN_SERVICE" <<EOL
[Unit]
Description=Yeelight Controller
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $SCRIPT_DIR/main.py
Restart=always
RestartSec=5s
WorkingDirectory=$SCRIPT_DIR

[Install]
WantedBy=default.target
EOL

echo "Main service file created at $MAIN_SERVICE"

# --- System Sleep Hook (off before sleep, on after wake) ---
sudo bash -c "cat > $SLEEP_HOOK" <<EOL
#!/bin/bash
case "\$1" in
  pre)
    /usr/bin/python3 $SCRIPT_DIR/off.py
    ;;
  post)
# Retry until success
    for i in {1..12}; do  # try up to 1 minute (12 × 5s)
      sleep 5
      /usr/bin/python3 $SCRIPT_DIR/on.py && exit 0
      echo "[$(date)] yeelight on.py failed, retrying in 5s..." >> $SCRIPT_DIR/yeelight-sync.log
      sleep 1
      systemctl --user restart yeelight-controller.service
      sleep 1
    done
    ;;
esac
EOL

sudo chmod +x $SLEEP_HOOK
echo "System sleep hook created at $SLEEP_HOOK"

# --- Enable & start main service ---
systemctl --user daemon-reload
systemctl --user enable yeelight-controller.service
systemctl --user start yeelight-controller.service

echo "Yeelight Controller installed with system sleep hook."
/usr/bin/python3 $SCRIPT_DIR/on.py