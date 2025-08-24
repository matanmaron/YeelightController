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

def average_color_raw(sct_img, down_x=64, down_y=36):
    arr = np.frombuffer(sct_img.rgb, dtype=np.uint8)
    arr = arr.reshape(sct_img.height, sct_img.width, 3)
    # Downsample using slicing
    step_y = max(1, arr.shape[0] // down_y)
    step_x = max(1, arr.shape[1] // down_x)
    arr_small = arr[::step_y, ::step_x, :]
    mean = arr_small.mean(axis=(0,1))
    return tuple(int(x) for x in mean)

def color_distance_sq(c1, c2):
    return sum((a-b)**2 for a,b in zip(c1,c2))

def pick_monitor(monitors, index):
    if index < 0: index = 0
    if index >= len(monitors): index = 0
    return monitors[index]

def apply_crop(region, crop):
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

    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    log_path = os.environ.get("YEELIGHT_LOG", os.path.join(base_dir, "yeelight-sync.log"))
    setup_logging(log_path)

    disp = os.environ.get("DISPLAY")
    if not disp:
        os.environ["DISPLAY"] = ":0"
        logging.warning("DISPLAY not set; defaulting to :0")

    ips = [d["ip"] for d in cfg.get("devices", [])]
    if not ips:
        logging.error("No devices configured in config.json")
        sys.exit(1)

    group = YeelightGroup(ips)

    if cfg.get("startup_power_on", True):
        group.power_on()
    group.set_brightness(cfg.get("brightness", 80))

    min_interval = max(10, int(cfg.get("min_update_interval_ms", 80))) / 1000.0
    threshold_sq = float(cfg.get("color_change_threshold", 10)) ** 2
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
                color = average_color_raw(sct_img)

                now = time.time()
                if last_color is None or color_distance_sq(color, last_color) >= threshold_sq:
                    if (now - last_send) >= min_interval:
                        r, g, b = color
                        group.set_rgb(r, g, b)
                        last_color = color
                        last_send = now

                elapsed = time.time() - start
                time.sleep(max(0, min_interval - elapsed))

    finally:
        group.close()
        logging.info("Exiting main loop.")

if __name__ == "__main__":
    main()
