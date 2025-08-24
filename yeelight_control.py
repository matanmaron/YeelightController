import socket
import json
import time

class YeelightDevice:
    def __init__(self, ip, port=55443, timeout=1.0):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self._id = 1
        self._sock = None

    def _connect(self):
        if self._sock:
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        s.connect((self.ip, self.port))
        self._sock = s

    def _send(self, method, params):
        try:
            self._connect()
            payload = json.dumps({"id": self._id, "method": method, "params": params}) + "\r\n"
            self._sock.sendall(payload.encode("utf-8"))
            self._id += 1
            # Non-blocking read of response (optional)
            self._sock.settimeout(0.1)
            try:
                _ = self._sock.recv(4096)
            except Exception:
                pass
            return True
        except Exception:
            # Reset socket; will reconnect next time
            self.close()
            return False

    def set_power(self, on=True, effect="smooth", duration=300):
        return self._send("set_power", ["on" if on else "off", effect, duration])

    def set_brightness(self, val, effect="smooth", duration=300):
        val = max(1, min(100, int(val)))
        return self._send("set_bright", [val, effect, duration])

    def set_rgb(self, r, g, b, effect="smooth", duration=300):
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        rgb = (r << 16) + (g << 8) + b
        return self._send("set_rgb", [rgb, effect, duration])

    def close(self):
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None


class YeelightGroup:
    def __init__(self, ips):
        self.devices = [YeelightDevice(ip) for ip in ips]

    def power_on(self):
        ok = True
        for d in self.devices:
            ok = d.set_power(True) and ok
        return ok

    def power_off(self):
        ok = True
        for d in self.devices:
            ok = d.set_power(False) and ok
        return ok

    def set_brightness(self, val):
        ok = True
        for d in self.devices:
            ok = d.set_brightness(val) and ok
        return ok

    def set_rgb(self, r, g, b):
        ok = True
        for d in self.devices:
            ok = d.set_rgb(r, g, b) and ok
        return ok

    def close(self):
        for d in self.devices:
            d.close()
