"""
5-Second Screen Recorder - GUI App (Windows)
--------------------------------------------
Features:
- UI se apna record/quit shortcut set karein
- Save folder choose karein
- "Start (Background)" dabayein
- Shortcut dabayein -> 5 sec record -> aapki folder mein save
- Beep sound: recording shuru aur khatam par (sirf aapko sunai deti hai)
- ON-SCREEN COUNTDOWN (5,4,3,2,1): sirf AAPKO screen par dikhta hai,
  screen recording/video mein capture NAHI hota (WDA_EXCLUDEFROMCAPTURE)
- Clip counter app window mein
- Unique filename: milliseconds ke saath, kabhi overwrite nahi
- Quit shortcut + button

Ek dafa install karein (CMD mein):
    pip install mss opencv-python numpy keyboard

Chalane ke liye (CMD ko "Run as administrator" se kholein):
    python recorder_app.py
"""
import os, time, threading, winsound, ctypes
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import cv2, numpy as np, mss, keyboard

CLIP_SECONDS = 5
FPS = 30
WDA_EXCLUDEFROMCAPTURE = 0x00000011   # window screen-capture se chhup jati hai
GA_ROOT = 2


class RecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("5-Second Screen Recorder")
        self.root.geometry("440x400")
        self.root.resizable(False, False)

        self.save_dir = os.path.join(os.getcwd(), "recordings")
        self.hotkey = "ctrl+alt+r"
        self.quit_hotkey = "ctrl+alt+q"
        self.hotkey_handle = None
        self.quit_handle = None
        self.recording = False
        self.clip_count = 0

        tk.Label(root, text="5-Second Screen Recorder",
                 font=("Segoe UI", 14, "bold")).pack(pady=10)

        f1 = tk.Frame(root); f1.pack(pady=4)
        tk.Label(f1, text="Record Shortcut:").pack(side="left", padx=5)
        self.hotkey_var = tk.StringVar(value=self.hotkey)
        tk.Entry(f1, textvariable=self.hotkey_var, width=15).pack(side="left")
        tk.Button(f1, text="Capture", command=self.capture_hotkey).pack(side="left", padx=5)

        f3 = tk.Frame(root); f3.pack(pady=4)
        tk.Label(f3, text="Quit Shortcut:   ").pack(side="left", padx=5)
        self.quit_var = tk.StringVar(value=self.quit_hotkey)
        tk.Entry(f3, textvariable=self.quit_var, width=15).pack(side="left")
        tk.Button(f3, text="Capture", command=self.capture_quit).pack(side="left", padx=5)

        f2 = tk.Frame(root); f2.pack(pady=6)
        tk.Button(f2, text="Choose Save Folder", command=self.choose_folder).pack()
        self.folder_lbl = tk.Label(root, text=self.save_dir, fg="gray", wraplength=400)
        self.folder_lbl.pack(pady=3)

        self.toggle_btn = tk.Button(root, text="Start (Background)",
                                    bg="#2e7d32", fg="white",
                                    font=("Segoe UI", 11, "bold"),
                                    command=self.toggle)
        self.toggle_btn.pack(pady=10, ipadx=10, ipady=4)

        self.counter_lbl = tk.Label(root, text="Clips recorded: 0",
                                    font=("Segoe UI", 11, "bold"), fg="#1565c0")
        self.counter_lbl.pack(pady=4)

        self.status = tk.Label(root, text="Stopped", fg="red", font=("Segoe UI", 10))
        self.status.pack(pady=4)

        tk.Button(root, text="Quit App", command=self.quit_app,
                  bg="#616161", fg="white").pack(pady=6)

        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        self._build_overlay()

    # ---------- On-screen countdown overlay (recording mein capture nahi hota) ----------
    def _build_overlay(self):
        self.overlay = tk.Toplevel(self.root)
        self.overlay.overrideredirect(True)          # koi border/title nahi
        self.overlay.attributes("-topmost", True)
        self.overlay.configure(bg="black")
        self.overlay.attributes("-alpha", 0.85)

        sw = self.overlay.winfo_screenwidth()
        self.overlay.geometry(f"140x140+{sw - 180}+40")  # top-right corner

        self.count_lbl = tk.Label(self.overlay, text="", font=("Segoe UI", 48, "bold"),
                                  fg="#ff3b3b", bg="black")
        self.count_lbl.pack(expand=True, fill="both")

        self.overlay.withdraw()   # shuru mein chhupi rahegi
        self.overlay.update_idletasks()

        # Windows ko bolo: is window ko screen capture se chhupa do
        try:
            hwnd = ctypes.windll.user32.GetAncestor(self.overlay.winfo_id(), GA_ROOT)
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        except Exception:
            pass

    def _show_overlay(self, number):
        self.count_lbl.config(text=str(number))
        self.overlay.deiconify()
        self.overlay.lift()

    def _hide_overlay(self):
        self.overlay.withdraw()

    def _countdown(self, n):
        """Har second number kam karke dikhata hai (sirf aapko)."""
        if n > 0:
            self._show_overlay(n)
            self.root.after(1000, lambda: self._countdown(n - 1))
        else:
            self._hide_overlay()

    # ---------- Shortcuts ----------
    def capture_hotkey(self):
        self.status.config(text="Record ke liye key combo dabayein...", fg="blue")
        self.root.update()
        combo = keyboard.read_hotkey(suppress=False)
        self.hotkey_var.set(combo)
        self.status.config(text=f"Record shortcut: {combo}", fg="green")

    def capture_quit(self):
        self.status.config(text="Quit ke liye key combo dabayein...", fg="blue")
        self.root.update()
        combo = keyboard.read_hotkey(suppress=False)
        self.quit_var.set(combo)
        self.status.config(text=f"Quit shortcut: {combo}", fg="green")

    def choose_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.save_dir = d
            self.folder_lbl.config(text=d)

    def toggle(self):
        if self.hotkey_handle is None:
            self.hotkey = self.hotkey_var.get().strip()
            self.quit_hotkey = self.quit_var.get().strip()
            try:
                self.hotkey_handle = keyboard.add_hotkey(self.hotkey, self.trigger)
                self.quit_handle = keyboard.add_hotkey(self.quit_hotkey, self.quit_app)
            except Exception as e:
                messagebox.showerror("Error", f"Shortcut galat hai: {e}")
                return
            self.toggle_btn.config(text="Stop", bg="#c62828")
            self.status.config(text=f"Running... (Record: {self.hotkey})", fg="green")
        else:
            keyboard.remove_hotkey(self.hotkey_handle)
            if self.quit_handle:
                keyboard.remove_hotkey(self.quit_handle)
            self.hotkey_handle = None
            self.quit_handle = None
            self.toggle_btn.config(text="Start (Background)", bg="#2e7d32")
            self.status.config(text="Stopped", fg="red")

    def trigger(self):
        if not self.recording:
            # countdown main thread par shuru karo (Tkinter safe)
            self.root.after(0, lambda: self._countdown(CLIP_SECONDS))
            threading.Thread(target=self.record_clip, daemon=True).start()

    def record_clip(self):
        self.recording = True
        os.makedirs(self.save_dir, exist_ok=True)
        stamp = datetime.now().strftime("clip_%Y%m%d_%H%M%S_%f")
        fp = os.path.join(self.save_dir, stamp + ".mp4")

        winsound.Beep(1000, 150)   # start beep
        self._set_status("Recording...", "orange")

        with mss.mss() as sct:
            mon = sct.monitors[1]
            w, h = mon["width"], mon["height"]
            writer = cv2.VideoWriter(fp, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (w, h))
            interval = 1.0 / FPS
            for _ in range(CLIP_SECONDS * FPS):
                t = time.time()
                frame = cv2.cvtColor(np.array(sct.grab(mon)), cv2.COLOR_BGRA2BGR)
                writer.write(frame)
                s = interval - (time.time() - t)
                if s > 0:
                    time.sleep(s)
            writer.release()

        winsound.Beep(1500, 200)   # end beep
        self.clip_count += 1
        self.root.after(0, lambda: self.counter_lbl.config(
            text=f"Clips recorded: {self.clip_count}"))
        self.root.after(0, self._hide_overlay)
        self._set_status(f"Saved: {os.path.basename(fp)}", "green")
        self.recording = False

    def _set_status(self, text, color):
        self.root.after(0, lambda: self.status.config(text=text, fg=color))

    def quit_app(self):
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    RecorderApp(root)
    root.mainloop()
