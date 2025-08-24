# Yeelight Screen Sync

This document serves as a GitHub-ready page (README-style) for the Yeelight Screen Sync project.

---

## Overview

`Yeelight Screen Sync` is a Python script to synchronize your Yeelight smart bulbs with the average color of your monitor. The script captures the screen, computes the dominant color, and updates the bulbs in real-time.

This optimized version minimizes CPU usage and improves responsiveness.

**Important:** Currently, the script only supports X11 or Wayland sessions with XWayland enabled. Native Wayland screen capture is not supported.

---

## Features

* Real-time screen color synchronization.
* Multi-monitor support.
* Configurable color change threshold and update interval.
* Graceful shutdown via `SIGINT` or `SIGTERM`.
* Automatic brightness and power-on at startup.
* Configurable crop region for partial screen sync.
* System sleep handling: bulbs turn off before sleep and restore after wake.
* Full installer and uninstaller scripts for easy setup.

---

## Requirements

* Python 3.8+
* `numpy`
* `mss`
* `yeelight_control` (custom library for controlling Yeelight bulbs)
* Linux with X11 or Wayland (XWayland required for Wayland sessions)
* Systemd for service management

Install dependencies:

```bash
pip install numpy mss
```

Ensure your user session can access the display (X11 or XWayland).

---

## Installation

Run the provided installer script:

```bash
bash install.sh
```

This will:

* Create a systemd user service to run `main.py` on login.
* Set up a system sleep hook to turn off bulbs before sleep and restore them after wake.
* Start the Yeelight Controller service automatically.

---

## Configuration

Create or edit `config.json` in the same folder as `main.py`:

```json
{
  "devices": [
    {"ip": "192.168.1.100"},
    {"ip": "192.168.1.101"}
  ],
  "brightness": 80,
  "min_update_interval_ms": 80,
  "color_change_threshold": 10,
  "monitor_index": 0,
  "crop": {"left":0, "top":0, "right":0, "bottom":0},
  "startup_power_on": true
}
```

* **devices**: list of Yeelight device IPs.
* **brightness**: initial brightness (0-100).
* **min\_update\_interval\_ms**: minimum update interval in milliseconds.
* **color\_change\_threshold**: threshold for color changes to trigger updates.
* **monitor\_index**: which monitor to capture (0 = full virtual screen, 1+ = monitor index).
* **crop**: crop region in pixels.
* **startup\_power\_on**: whether to turn on bulbs at startup.

---

## Usage

Run the script manually:

```bash
python3 main.py
```

Or let the systemd service handle it automatically. Stop the service with:

```bash
systemctl --user stop yeelight-controller.service
```

Gracefully stop manual runs with `Ctrl+C` or send a `SIGTERM`.

---

## Uninstallation

To remove the service and sleep hook:

```bash
bash uninstall.sh
```

This will disable the systemd service and delete the sleep hook.

---

## Optimization Notes

* Avoids PIL for faster color computation.
* Downsamples captured image to 64x36 pixels for performance.
* Uses squared distance for faster color change detection.
* Maintains consistent update pacing.
* Only supports X11 or Wayland with XWayland; native Wayland not supported.

---

## License

MIT License
