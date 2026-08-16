 """
Screen Recorder - GUI App (Windows)
------------------------------------
Features:
- UI se apna record/quit shortcut set karein
- Do global hotkeys:
    1) Record Shortcut       -> turant FULL SCREEN N-second clip record karta hai
    2) Region Record Shortcut-> screen par drag se area select karwata hai,
                                 select karte hi turant usi area ki N-second clip record karta hai
- Recording duration adjustable (1-60 seconds)
- Save folder choose karein
- Beep sound: recording shuru aur khatam par (sirf aapko sunai deti hai)
- ON-SCREEN COUNTDOWN: sirf AAPKO screen par dikhta hai,
  screen recording/video mein capture NAHI hota (WDA_EXCLUDEFROMCAPTURE)
- Clip counter app window mein
- Unique filename: microseconds ke saath, kabhi overwrite nahi
- Quit shortcut + button
- Dono shortcuts background mein kaam karte hain (app minimized ho tab bhi)

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

FPS = 30
WDA_EXCLUDEFROMCAPTURE = 0x00000011   # window screen-capture se chhup jati hai
GA_ROOT = 2


class RecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Screen Recorder")
        self.root.geometry("460x600")
        self.root.resizable(False, False)

        self.save_dir = os.path.join(os.getcwd(), "recordings")
        self.hotkey = "ctrl+alt+r"          # full screen record
        self.region_hotkey = "ctrl+alt+s"   # select region + record
        self.quit_hotkey = "ctrl+alt+q"
        self.hotkey_handle = None
        self.region_hotkey_handle = None
        self.quit_handle = None
        self.recording = False
        self.clip_count = 0
        self.region = None   # last-used region {"left":.., "top":.., "width":.., "height":..}

        tk.Label(root, text="Screen Recorder",
                 font=("Segoe UI", 14, "bold")).pack(pady=10)

        # ---- Duration ----
        f0 = tk.Frame(root); f0.pack(pady=4)
        tk.Label(f0, text="Duration (seconds):").pack(side="left", padx=5)
        self.duration_var = tk.IntVar(value=5)
        tk.Spinbox(f0, from_=1, to=60, width=5,
                   textvariable=self.duration_var).pack(side="left")

        # ---- Quality ----
        fq = tk.Frame(root); fq.pack(pady=4)
        tk.Label(fq, text="Quality:").pack(side="left", padx=5)
        self.quality_var = tk.StringVar(value="Standard (mp4v)")
        tk.OptionMenu(fq, self.quality_var,
                      "Standard (mp4v)",
                      "H.264 (avc1, balanced)",
                      "High Quality (MJPG/.avi, bigger files)").pack(side="left")

        # ---- Shortcuts ----
        fs = tk.LabelFrame(root, text="Shortcuts")
        fs.pack(pady=6, padx=10, fill="x")

        f1 = tk.Frame(fs); f1.pack(pady=4, fill="x")
        tk.Label(f1, text="Full Screen Record:", width=18, anchor="w").pack(side="left", padx=5)
        self.hotkey_var = tk.StringVar(value=self.hotkey)
        tk.Entry(f1, textvariable=self.hotkey_var, width=15).pack(side="left")
        tk.Button(f1, text="Capture", command=self.capture_hotkey).pack(side="left", padx=5)

        f4 = tk.Frame(fs); f4.pack(pady=4, fill="x")
        tk.Label(f4, text="Select Region + Record:", width=18, anchor="w").pack(side="left", padx=5)
        self.region_hotkey_var = tk.StringVar(value=self.region_hotkey)
        tk.Entry(f4, textvariable=self.region_hotkey_var, width=15).pack(side="left")
        tk.Button(f4, text="Capture", command=self.capture_region_hotkey).pack(side="left", padx=5)

        f3 = tk.Frame(fs); f3.pack(pady=4, fill="x")
        tk.Label(f3, text="Quit App:", width=18, anchor="w").pack(side="left", padx=5)
        self.quit_var = tk.StringVar(value=self.quit_hotkey)
        tk.Entry(f3, textvariable=self.quit_var, width=15).pack(side="left")
        tk.Button(f3, text="Capture", command=self.capture_quit).pack(side="left", padx=5)

        tk.Label(root,
                 text="Full Screen Record: turant poori screen ki clip banata hai.\n"
                      "Select Region + Record: pehle drag se area select karo,\n"
                      "select karte hi usi area ki clip turant record hoti hai.",
                 fg="gray", justify="left", wraplength=420).pack(pady=4)

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

    # ---------- Region picker (drag on screen) ----------
    def _pick_region(self, on_done):
        """Poori screen par transparent overlay kholta hai, user drag kar ke
        area select karta hai. Selection complete hote hi on_done(region_or_None) call hota hai.
        Yeh Tkinter MAIN THREAD par hi call karna chahiye.
        Main window ko withdraw/deiconify NAHI karte -- isse app background mein
        (minimized/hidden) jaisi thi waisi hi rehti hai, sirf yeh fullscreen
        overlay upar aata hai aur select hote hi khud ghayab ho jata hai."""
        picker = tk.Toplevel(self.root)
        picker.attributes("-fullscreen", True)
        picker.attributes("-alpha", 0.30)
        picker.configure(bg="black", cursor="cross")
        picker.attributes("-topmost", True)

        canvas = tk.Canvas(picker, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        canvas.create_text(
            picker.winfo_screenwidth() // 2, 30,
            text="Drag to select area  |  Esc to cancel",
            fill="white", font=("Segoe UI", 14, "bold"))

        state = {"x0": 0, "y0": 0, "rect": None, "done": False}

        def finish(region):
            if state["done"]:
                return
            state["done"] = True
            picker.destroy()
            on_done(region)

        def on_press(event):
            state["x0"], state["y0"] = event.x, event.y
            if state["rect"]:
                canvas.delete(state["rect"])
            state["rect"] = canvas.create_rectangle(
                event.x, event.y, event.x, event.y,
                outline="#ff3b3b", width=2)

        def on_drag(event):
            if state["rect"]:
                canvas.coords(state["rect"], state["x0"], state["y0"],
                               event.x, event.y)

        def on_release(event):
            x0, y0 = state["x0"], state["y0"]
            x1, y1 = event.x, event.y
            left, top = min(x0, x1), min(y0, y1)
            width, height = abs(x1 - x0), abs(y1 - y0)
            if width < 10 or height < 10:
                # bohat chhota selection -> dobara try karne do, cancel mat karo
                if state["rect"]:
                    canvas.delete(state["rect"])
                    state["rect"] = None
                return
            finish({"left": left, "top": top, "width": width, "height": height})

        def on_escape(event):
            finish(None)

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        picker.bind("<Escape>", on_escape)
        picker.focus_force()

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

    # ---------- Shortcuts capture (UI) ----------
    def capture_hotkey(self):
        self.status.config(text="Record ke liye key combo dabayein...", fg="blue")
        self.root.update()
        combo = keyboard.read_hotkey(suppress=False)
        self.hotkey_var.set(combo)
        self.status.config(text=f"Record shortcut: {combo}", fg="green")

    def capture_region_hotkey(self):
        self.status.config(text="Region+Record ke liye key combo dabayein...", fg="blue")
        self.root.update()
        combo = keyboard.read_hotkey(suppress=False)
        self.region_hotkey_var.set(combo)
        self.status.config(text=f"Region+Record shortcut: {combo}", fg="green")

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

    # ---------- Start / Stop background hotkeys ----------
    def toggle(self):
        if self.hotkey_handle is None:
            self.hotkey = self.hotkey_var.get().strip()
            self.region_hotkey = self.region_hotkey_var.get().strip()
            self.quit_hotkey = self.quit_var.get().strip()
            try:
                self.hotkey_handle = keyboard.add_hotkey(self.hotkey, self.trigger_full_screen)
                self.region_hotkey_handle = keyboard.add_hotkey(self.region_hotkey, self.trigger_region)
                self.quit_handle = keyboard.add_hotkey(self.quit_hotkey, self.quit_app)
            except Exception as e:
                messagebox.showerror("Error", f"Shortcut galat hai: {e}")
                return
            self.toggle_btn.config(text="Stop", bg="#c62828")
            self.status.config(
                text=f"Running... (Full: {self.hotkey} | Region: {self.region_hotkey})",
                fg="green")
        else:
            keyboard.remove_hotkey(self.hotkey_handle)
            if self.region_hotkey_handle:
                keyboard.remove_hotkey(self.region_hotkey_handle)
            if self.quit_handle:
                keyboard.remove_hotkey(self.quit_handle)
            self.hotkey_handle = None
            self.region_hotkey_handle = None
            self.quit_handle = None
            self.toggle_btn.config(text="Start (Background)", bg="#2e7d32")
            self.status.config(text="Stopped", fg="red")

    # ---------- Trigger: Full screen shortcut ----------
    def trigger_full_screen(self):
        if self.recording:
            return
        self.recording = True   # yahin lock kar do, race condition se bachne ke liye
        duration = max(1, int(self.duration_var.get()))
        self.root.after(0, lambda: self._countdown(duration))
        threading.Thread(target=self.record_clip,
                          args=(duration, None), daemon=True).start()

    # ---------- Trigger: Region-select shortcut ----------
    def trigger_region(self):
        if self.recording:
            return
        self.recording = True   # turant lock, taake dono shortcut ek sath na chal jayein
        # Toplevel/drag UI sirf main thread par ban sakti hai
        self.root.after(0, self._start_region_pick)

    def _start_region_pick(self):
        def on_picked(region):
            if region is None:
                # user ne Esc dabaya, cancel
                self.recording = False
                self._set_status("Region selection cancelled", "gray")
                return
            self.region = region
            self._set_status(
                f"Region selected ({region['width']}x{region['height']}), recording...",
                "orange")
            duration = max(1, int(self.duration_var.get()))
            self.root.after(0, lambda: self._countdown(duration))
            threading.Thread(target=self.record_clip,
                              args=(duration, region), daemon=True).start()

        self._pick_region(on_picked)

    # ---------- Actual capture ----------
    def _make_writer(self, fp_no_ext, w, h):
        """Quality dropdown ke hisaab se codec choose karta hai.
        H.264 fail ho (missing encoder) to khud-ba-khud mp4v par fallback karta hai.
        Returns (writer, actual_filepath)."""
        quality = self.quality_var.get()

        if quality.startswith("High Quality"):
            fp = fp_no_ext + ".avi"
            writer = cv2.VideoWriter(fp, cv2.VideoWriter_fourcc(*"MJPG"), FPS, (w, h))
            return writer, fp

        if quality.startswith("H.264"):
            fp = fp_no_ext + ".mp4"
            writer = cv2.VideoWriter(fp, cv2.VideoWriter_fourcc(*"avc1"), FPS, (w, h))
            if writer.isOpened():
                return writer, fp
            # H.264 encoder available nahi -- mp4v par fallback
            writer.release()
            writer = cv2.VideoWriter(fp, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (w, h))
            return writer, fp

        # Standard
        fp = fp_no_ext + ".mp4"
        writer = cv2.VideoWriter(fp, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (w, h))
        return writer, fp

    def record_clip(self, duration, region):
        os.makedirs(self.save_dir, exist_ok=True)
        stamp = datetime.now().strftime("clip_%Y%m%d_%H%M%S_%f")
        fp_no_ext = os.path.join(self.save_dir, stamp)

        winsound.Beep(1000, 150)   # start beep
        self._set_status("Recording...", "orange")

        with mss.mss() as sct:
            mon = region if region else sct.monitors[1]
            w, h = mon["width"], mon["height"]
            writer, fp = self._make_writer(fp_no_ext, w, h)

            if not writer.isOpened():
                self._set_status("Error: recording save nahi hui (codec issue)", "red")
                self.recording = False
                self.root.after(0, self._hide_overlay)
                return

            interval = 1.0 / FPS
            for _ in range(duration * FPS):
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
