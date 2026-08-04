# 5-Second Screen Recorder

A lightweight Windows screen recorder that captures 5-second clips with a global hotkey. Built for quick clip / data gathering from any video source on screen (YouTube, players, games, etc.).

## Features

- **Global hotkey** — set your own shortcut, works in the background
- **5-second clips** — press the hotkey, it records 5 seconds and saves automatically
- **Custom save folder** — choose where clips are stored
- **Beep sound** — audible cue on start and end of each recording
- **On-screen countdown** — a 5,4,3,2,1 indicator visible only to you; it does **not** appear in the recorded video (uses Windows `WDA_EXCLUDEFROMCAPTURE`)
- **Clip counter** — tracks how many clips you've recorded (in-app only)
- **Unique filenames** — timestamped down to microseconds, nothing gets overwritten
- **Quit hotkey + button** — stop the recorder from anywhere

## Requirements

- Windows 10 (build 19041+) or Windows 11
- Python 3.9+

## Installation

Install the dependencies:

```bash
pip install mss opencv-python numpy keyboard
```

## Usage

Run the app (open CMD **as Administrator** so the global hotkey works in the background):

```bash
python recorder_app.py
```

1. Set your **Record** and **Quit** shortcuts (or keep the defaults).
2. Click **Choose Save Folder** to pick where clips are saved.
3. Click **Start (Background)** and minimize the window.
4. Press your record shortcut anywhere — it records 5 seconds and saves to your folder.
5. Press the quit shortcut or click **Quit App** to stop.

Defaults: Record = `Ctrl+Alt+R`, Quit = `Ctrl+Alt+Q`.

## Build a standalone .exe (optional)

To run on any PC without Python installed:

```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name "ScreenRecorder" recorder_app.py
```

The executable will be in the `dist` folder. For the global hotkey to work, run it as Administrator (right-click the `.exe` → Properties → Compatibility → "Run this program as an administrator").

## Notes

- The global hotkey library may trigger false-positive antivirus warnings because it uses keyboard hooks. This is expected for this type of tool.
- Recording quality depends on your monitor resolution and the source video. Play the source in full screen for best results.

## License

MIT
