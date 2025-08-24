#!/usr/bin/env python3
import os
import sys
import json
import time
import signal
import logging
from threading import Event

import numpy as np
from mss import mss
from PIL import Image

from yeelight_control import YeelightGroup

STOP = Event()

def setup_logging(log_path=None):
    if log_path is None:
        log_path = os.path.join(os.path.dirname(__file__), "yeelight.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_config():
    cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(cfg_path, "r") as f:
        return json.load(f)

def average_color(img):
    # Downscale for speed
    img_small = img.resize((64, 36), Image.BILINEAR)
    arr = np.asarray(img_small, dtype=np.uint8)
    # Ignore alpha if present
    if arr.shape[-1] == 4:
        arr = arr[:, :, :3]
    # Compute mean
    mean = arr.reshape(-1, 3).mean(axis=0)
    return tuple(int(x) for x in mean)

def color_distance(c1, c2):
    return np.linalg.norm(np.array(c1) - np.array(c2))

def pick_monitor(monitors, index):
    # MSS: monitors[0] is full virtual screen; 1..n are per-monitor
    if index < 0: index = 0
    if index >= len(monitors): index = 0
    return monitors[index]

def apply_crop(region, crop):
    # crop keys: left, top, right, bottom (pixels)
    return {
        "left":  region["left"] + int(crop.get("left", 0)),
        "top":   region["top"] + int(crop.get("top", 0)),
        "width": region["width"] - int(crop.get("left", 0)) - int(crop.get("right", 0)),
        "height":region["height"] - int(crop.get("top", 0)) - int(crop.get("bottom", 0)),
    }

def on_sigterm(sig, frame):
    STOP.set()

def main():
    cfg = load_config()

    # Put logs in the same folder as main.py (default)
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    log_path = os.environ.get("YEELIGHT_LOG", os.path.join(os.path.dirname(__file__), "yeelight-sync.log"))
    setup_logging(log_path)

    # Ensure we have an X11 DISPLAY in a user session
    disp = os.environ.get("DISPLAY")
    if not disp:
        # Best-effort default
        os.environ["DISPLAY"] = ":0"
        logging.warning("DISPLAY not set; defaulting to :0")

    ips = [d["ip"] for d in cfg.get("devices", [])]
    if not ips:
        logging.error("No devices configured in config.json")
        sys.exit(1)

    group = YeelightGroup(ips)

    # Power on & set brightness at startup (optional)
    if cfg.get("startup_power_on", True):
        group.power_on()
    group.set_brightness(cfg.get("brightness", 80))

    min_interval = max(10, int(cfg.get("min_update_interval_ms", 80))) / 1000.0
    threshold = float(cfg.get("color_change_threshold", 10))
    mon_index = int(cfg.get("monitor_index", 0))
    crop = cfg.get("crop", {"left":0, "top":0, "right":0, "bottom":0})

    signal.signal(signal.SIGTERM, on_sigterm)
    signal.signal(signal.SIGINT, on_sigterm)

    last_color = None
    last_send = 0.0

    try:
        with mss() as sct:
            region = pick_monitor(sct.monitors, mon_index)
            region = apply_crop(region, crop)

            logging.info(f"Starting capture on monitor index {mon_index}: {region}")
            while not STOP.is_set():
                start = time.time()
                sct_img = sct.grab(region)
                # Convert to PIL Image
                img = Image.frombytes("RGB", (sct_img.width, sct_img.height), sct_img.rgb)
                color = average_color(img)

                now = time.time()
                should_send = False
                if last_color is None:
                    should_send = True
                else:
                    if color_distance(color, last_color) >= threshold:
                        should_send = True
                if should_send and (now - last_send) >= min_interval:
                    r, g, b = color
                    group.set_rgb(r, g, b)
                    last_color = color
                    last_send = now

                # Simple pacing to ~min_interval or better
                elapsed = time.time() - start
                sleep_time = max(0.0, min_interval - elapsed * 0.5)
                if sleep_time > 0:
                    time.sleep(sleep_time)
    finally:
        # Do not force off here; let sleep/shutdown hooks manage power events
        group.close()
        logging.info("Exiting main loop.")

if __name__ == "__main__":
    main()
