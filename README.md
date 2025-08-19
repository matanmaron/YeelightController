# Yeelight Tray Controller

A simple Python GUI app to control your Yeelight strip based on your screen color. Features include Start/Stop, IP input, minimize to tray, and persistent IP storage.

---

## Features

* Start/Stop the Yeelight color sync.
* Minimize the app to the system tray.
* Right-click tray menu to Quit the app.
* Click tray icon to restore the app.
* Enter and save Yeelight IP for future sessions.

---

## Dependencies

* Python 3.10+
* PyQt6
* Pillow
* numpy

Install dependencies with pip:

```
pip install PyQt6 Pillow numpy
```

---

## Usage

1. Clone or download the repository.
2. Open a terminal and navigate to the project folder.
3. Run the app:

```
python yeelight.py
```

4. Enter your Yeelight IP at the top and press **Start**.
5. Minimize to tray or press **Stop** to stop syncing.

---

## Building with PyInstaller

To create a standalone executable:

```
pyinstaller --onefile --windowed yeelight.py
```

The executable will be created in the `dist/` folder.

---

## Limitations

* Only works with Yeelight devices supporting the LAN control protocol.
* Only tested on Linux and Windows.
* Must have network access to the Yeelight device.
* Tray functionality may vary by OS.

---

## License

MIT License
