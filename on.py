#!/usr/bin/env python3
import json, os
from yeelight_control import YeelightGroup

cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
with open(cfg_path, "r") as f:
    cfg = json.load(f)
ips = [d["ip"] for d in cfg.get("devices", [])]
g = YeelightGroup(ips)
g.power_on()
if "brightness" in cfg:
    g.set_brightness(cfg["brightness"])
g.close()
