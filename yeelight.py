#!/usr/bin/env python3
import socket
import json
import time
import numpy as np
from PIL import ImageGrab
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit,
    QSystemTrayIcon, QMenu
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
import os

CONFIG_FILE = "config.json"

class YeelightThread(QThread):
    finished = pyqtSignal()

    def __init__(self, ip):
        super().__init__()
        self.ip = ip
        self.running = True

    def get_average_screen_color(self):
        screen = ImageGrab.grab().resize((100, 100))
        arr = np.array(screen)
        if arr.shape[2] == 4:
            arr = arr[:, :, :3]
        avg = arr.mean(axis=(0,1))
        return tuple(int(x) for x in avg)

    def send_color(self, sock, r, g, b):
        cmd = {
            "id": 1,
            "method": "set_rgb",
            "params": [(r << 16) + (g << 8) + b, "sudden", 0]
        }
        try:
            sock.send((json.dumps(cmd) + "\r\n").encode())
        except Exception as e:
            print("Error sending color:", e)

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.ip, 55443))
            print(f"Connected to Yeelight {self.ip}.")
        except Exception as e:
            print("Connection error:", e)
            return
        while self.running:
            r, g, b = self.get_average_screen_color()
            self.send_color(sock, r, g, b)
            time.sleep(0.1)
        sock.close()
        self.finished.emit()

    def stop(self):
        self.running = False

class YeelightApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yeelight Screen Sync")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.resize(250, 130)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # IP input
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter Yeelight IP")
        self.layout.addWidget(self.ip_input)

        # Load last IP
        self.load_ip()

        # Start/Stop button
        self.button = QPushButton("Start")
        self.layout.addWidget(self.button)
        self.button.clicked.connect(self.toggle)

        # Quit button
        self.quit_btn = QPushButton("Quit")
        self.layout.addWidget(self.quit_btn)
        self.quit_btn.clicked.connect(self.quit_app)

        self.thread = None

        # Tray icon
        self.tray = QSystemTrayIcon(QIcon.fromTheme("preferences-desktop-color"), self)
        self.tray.setToolTip("Yeelight Screen Sync")

        tray_menu = QMenu()
        restore_action = QAction("Restore")
        quit_action = QAction("Quit")
        tray_menu.addAction(restore_action)
        tray_menu.addAction(quit_action)
        self.tray.setContextMenu(tray_menu)

        restore_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.quit_app)
        self.tray.activated.connect(self.on_tray_click)
        self.tray.show()

    def toggle(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
            self.thread = None
            self.button.setText("Start")
        else:
            ip = self.ip_input.text().strip()
            if not ip:
                print("Enter a valid IP")
                return
            self.save_ip(ip)
            self.thread = YeelightThread(ip)
            self.thread.finished.connect(self.thread_stopped)
            self.thread.start()
            self.button.setText("Stop")

    def thread_stopped(self):
        self.button.setText("Start")
        self.thread = None

    def quit_app(self):
        if self.thread and self.thread.isRunning():
            self.thread.stop()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show()

    def save_ip(self, ip):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump({"ip": ip}, f)
        except Exception as e:
            print("Failed to save IP:", e)

    def load_ip(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    ip = data.get("ip", "")
                    self.ip_input.setText(ip)
            except Exception as e:
                print("Failed to load IP:", e)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = YeelightApp()
    window.show()
    sys.exit(app.exec())
