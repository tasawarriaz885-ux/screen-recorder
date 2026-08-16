 # Screen Recorder

A lightweight Windows screen recorder that captures short clips with a global hotkey. Built for quick clip / data gathering from any video source on screen (YouTube, players, games, etc.). Record the full screen, or drag-select just a region — both are triggered instantly from the background with their own hotkey.

## Features

- **Two global hotkeys** — one for instant full-screen recording, one for drag-select-region recording; both work in the background
- **Adjustable duration** — set clip length from 1 to 60 seconds (default 5)
- **Select Region + Record** — press the hotkey, drag to select any part of your screen, release, and it records that exact area automatically
- **Custom save folder** — choose where clips are stored
- **Beep sound** — audible cue on start and end of each recording
- **On-screen countdown** — a visible-only-to-you countdown indicator; it does **not** appear in the recorded video (uses Windows `WDA_EXCLUDEFROMCAPTURE`)
- **Clip counter** — tracks how many clips you've recorded (in-app only)
- **Unique filenames** — timestamped down to microseconds, nothing gets overwritten
- **Quit hotkey + button** — stop the recorder from anywhere
- **Stays in the background** — the app window never pops up mid-recording, even during region selection

## Requirements

- Windows 10 (build 19041+) or Windows 11
- Python 3.9+

## Installation

Install the dependencies:

```bash
pip install mss opencv-python numpy keyboard
```

## Usage

Run the app (open CMD **as Administrator** so the global hotkeys work in the background):

```bash
python recorder_app.py
```

1. Set your **Duration** (seconds per clip).
2. Set your **Full Screen Record**, **Select Region + Record**, and **Quit** shortcuts (or keep the defaults).
3. Click **Choose Save Folder** to pick where clips are saved.
4. Click **Start (Background)** and minimize the window.
5. Press your **Full Screen Record** shortcut anywhere — it immediately records the set duration and saves to your folder.
6. Press your **Select Region + Record** shortcut anywhere — drag to select an area of the screen, release, and it immediately records that area for the set duration. Press `Esc` to cancel a selection.
7. Press the quit shortcut or click **Quit App** to stop.

Defaults: Full Screen Record = `Ctrl+Alt+R`, Select Region + Record = `Ctrl+Alt+S`, Quit = `Ctrl+Alt+Q`.

## Build a standalone .exe (optional)

To run on any PC without Python installed:

```bash
pip install pyinstaller
python -m PyInstaller --onefile --windowed --name "ScreenRecorder" recorder_app.py
```

The executable will be in the `dist` folder. For the global hotkeys to work, run it as Administrator (right-click the `.exe` → Properties → Compatibility → "Run this program as an administrator").

## Notes

- The global hotkey library may trigger false-positive antivirus warnings because it uses keyboard hooks. This is expected for this type of tool.
- Recording quality depends on your monitor resolution and the source video. Play the source in full screen for best results.
- If your screen resolution or window layout changes, re-select your region rather than reusing an old selection.

## License

MIT
