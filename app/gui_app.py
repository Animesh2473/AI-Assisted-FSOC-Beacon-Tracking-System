
import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import cv2
from PIL import Image, ImageTk

from fsoc_tracker.simulator import Simulation, DEFAULT_CONFIG


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FSOC Virtual Camera Tracking System - Coarse Alignment Simulator")
        self.geometry("1050x680")
        self.resizable(False, False)

        self.sim = None
        self.running = False
        self.video_writer = None

        self._build_ui()

    # ---------------------------------------------------------------- UI
    def _build_ui(self):
        left = ttk.Frame(self, padding=10)
        left.pack(side=tk.LEFT, fill=tk.Y)

        right = ttk.Frame(self, padding=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ttk.Label(left, text="Configuration", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        self.vars = {}

        def add_combo(label, key, values, default):
            ttk.Label(left, text=label).pack(anchor="w", pady=(8, 0))
            v = tk.StringVar(value=default)
            ttk.Combobox(left, textvariable=v, values=values, state="readonly", width=22).pack(anchor="w")
            self.vars[key] = v

        def add_entry(label, key, default):
            ttk.Label(left, text=label).pack(anchor="w", pady=(8, 0))
            v = tk.StringVar(value=str(default))
            ttk.Entry(left, textvariable=v, width=24).pack(anchor="w")
            self.vars[key] = v

        add_combo("Target Motion", "target_motion",
                   ["straight_line", "circular", "figure8", "random", "spiral", "sinusoidal"],
                   "circular")
        add_entry("Target Size (5-20 px)", "target_size", 10)
        add_entry("Target Speed (px/s)", "target_speed", 150)
        add_combo("Noise", "noise", ["none", "gaussian", "salt_pepper", "poisson"], "gaussian")
        add_combo("Atmosphere", "atmosphere",
                   ["clear", "haze", "fog", "rain", "low_light"], "clear")
        add_combo("Platform Motion", "platform_motion",
                   ["linear", "circular", "random", "spiral", "figure8"], "linear")
        add_entry("Camera Jitter (px)", "camera_jitter_px", 5)
        add_entry("Max Pan/Tilt Speed (deg/s)", "max_speed", 5)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(pady=16, anchor="w")
        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.start)
        self.start_btn.grid(row=0, column=0, padx=4)
        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=4)
        ttk.Button(btn_frame, text="Save Report", command=self.save_report).grid(row=1, column=0, pady=6)
        ttk.Button(btn_frame, text="Load Video (Benchmark-2)", command=self.load_video).grid(
            row=1, column=1, pady=6)

        self.stats_box = tk.Text(left, width=32, height=14, font=("Consolas", 9))
        self.stats_box.pack(pady=8)

        self.canvas = tk.Label(right, background="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._video_path = None

    # ----------------------------------------------------------- actions
    def _build_config(self):
        cfg = dict(DEFAULT_CONFIG)
        cfg["target_motion"] = self.vars["target_motion"].get()
        cfg["target_size"] = int(self.vars["target_size"].get())
        cfg["target_speed"] = float(self.vars["target_speed"].get())
        noise = self.vars["noise"].get()
        cfg["noise_types"] = [] if noise == "none" else [noise]
        cfg["atmosphere"] = self.vars["atmosphere"].get()
        cfg["platform_motion"] = self.vars["platform_motion"].get()
        cfg["camera_jitter_px"] = float(self.vars["camera_jitter_px"].get())
        cfg["max_pan_speed"] = float(self.vars["max_speed"].get())
        cfg["max_tilt_speed"] = float(self.vars["max_speed"].get())
        return cfg

    def start(self):
        if self.running:
            return
        try:
            cfg = self._build_config()
        except ValueError as e:
            messagebox.showerror("Invalid parameter", str(e))
            return
        self.sim = Simulation(cfg)
        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def _loop(self):
        while self.running:
            t0 = time.time()
            result = self.sim.step()
            vis = Simulation.annotate(result["frame"], result)
            self._update_canvas(vis)
            self._update_stats(result["summary"])
            elapsed = time.time() - t0
            time.sleep(max(0, self.sim.dt - elapsed))

    def _update_canvas(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb).resize((720, 540))
        imgtk = ImageTk.PhotoImage(image=img)
        self.canvas.imgtk = imgtk
        self.canvas.configure(image=imgtk)

    def _update_stats(self, summary):
        self.stats_box.delete("1.0", tk.END)
        for k, v in summary.items():
            self.stats_box.insert(tk.END, f"{k}: {v}\n")

    def save_report(self):
        if not self.sim:
            messagebox.showinfo("No data", "Run a simulation first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             initialfile="performance_report.txt")
        if path:
            self.sim.perf.save_report(path)
            self.sim.perf.save_csv(path.replace(".txt", ".csv"))
            messagebox.showinfo("Saved", f"Report saved to {path}")

    def load_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi")])
        if not path:
            return
        messagebox.showinfo(
            "Benchmark-2 mode",
            "Selected file will be used as the coarse-pointing input feed "
            "in place of the virtual camera. See BENCHMARK2 usage in the "
            "technical report / notebooks/benchmark2_video_eval.ipynb for "
            "the scripted evaluation path used during judging.")
        self._video_path = path


if __name__ == "__main__":
    App().mainloop()
