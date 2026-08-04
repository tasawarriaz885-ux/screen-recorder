"""
Simple 5-second Screen Recorder for Windows
--------------------------------------------
- Ctrl + Alt + R  ->  5 second ki recording start hoti hai aur apne aap save ho jati hai
- Ctrl + Alt + Q  ->  program band karne ke liye

Har clip "recordings" folder mein save hoti hai (clip_YYYYMMDD_HHMMSS.mp4).

Zaroori libraries install karein (ek dafa):
    pip install mss opencv-python numpy keyboard
"""

import os
import time
from datetime import datetime

import cv2
import numpy as np
import mss
import keyboard

# ---------------- Settings (yahan badal sakte hain) ----------------
CLIP_SECONDS = 5          # kitne second ki clip
FPS = 20                  # frames per second (smoothness). 15-30 rakhein
OUTPUT_DIR = "recordings" # kahan save honge clips
START_HOTKEY = "ctrl+alt+r"
QUIT_HOTKEY = "ctrl+alt+q"
# -------------------------------------------------------------------


def record_clip():
    """5 second ki screen record karke mp4 file save karta hai."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = datetime.now().strftime("clip_%Y%m%d_%H%M%S.mp4")
    filepath = os.path.join(OUTPUT_DIR, filename)

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary monitor (poora screen)
        width = monitor["width"]
        height = monitor["height"]

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(filepath, fourcc, FPS, (width, height))

        print(f"[REC] Recording shuru... ({CLIP_SECONDS}s)")
        total_frames = CLIP_SECONDS * FPS
        frame_interval = 1.0 / FPS

        for _ in range(total_frames):
            start = time.time()

            img = np.array(sct.grab(monitor))          # screenshot (BGRA)
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            writer.write(frame)

            # timing sahi rakhne ke liye
            elapsed = time.time() - start
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        writer.release()

    print(f"[OK ] Save ho gayi: {filepath}\n")


def main():
    print("=" * 50)
    print(" 5-Second Screen Recorder ")
    print("=" * 50)
    print(f"  Record karne ke liye : {START_HOTKEY.upper()}")
    print(f"  Band karne ke liye   : {QUIT_HOTKEY.upper()}")
    print("=" * 50)
    print("Program chal raha hai... shortcut ka intezaar hai.\n")

    keyboard.add_hotkey(START_HOTKEY, record_clip)
    keyboard.wait(QUIT_HOTKEY)  # jab tak quit hotkey na dabe, chalta rahega

    print("\nProgram band ho gaya. Khuda hafiz!")


if __name__ == "__main__":
    main()
