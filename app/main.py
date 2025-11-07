from __future__ import annotations

import os
import subprocess
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from config_manager import AppConfig, load_config, save_config


class TheraViewApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Thera-View Recorder")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.config: AppConfig = load_config()
        self.cap: Optional[cv2.VideoCapture] = None
        self.writer: Optional[cv2.VideoWriter] = None
        self.recording = False
        self.frame_times: deque[float] = deque(maxlen=120)
        self.frame_width = self.config.width
        self.frame_height = self.config.height

        self._build_ui()
        self._ensure_output_dir()
        self._init_capture()
        self._update_video()

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.video_label = ttk.Label(main_frame)
        self.video_label.grid(row=0, column=0, columnspan=4, sticky="nsew")

        controls = ttk.Frame(main_frame)
        controls.grid(row=1, column=0, columnspan=4, pady=(10, 0), sticky="ew")
        controls.columnconfigure((0, 1, 2, 3), weight=1)

        self.start_button = ttk.Button(controls, text="Start Recording", command=self.start_recording)
        self.start_button.grid(row=0, column=0, padx=5, sticky="ew")

        self.stop_button = ttk.Button(controls, text="Stop Recording", command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5, sticky="ew")

        self.open_folder_button = ttk.Button(controls, text="Open Recordings Folder", command=self.open_recordings_folder)
        self.open_folder_button.grid(row=0, column=2, padx=5, sticky="ew")

        self.config_button = ttk.Button(controls, text="Config", command=self.open_config_dialog)
        self.config_button.grid(row=0, column=3, padx=5, sticky="ew")

        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, columnspan=4, pady=(10, 0), sticky="ew")

        self.status_var = tk.StringVar(value="Idle")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky="w")

        self.fps_var = tk.StringVar(value="FPS: --")
        self.fps_label = ttk.Label(status_frame, textvariable=self.fps_var)
        self.fps_label.grid(row=0, column=1, padx=(20, 0), sticky="w")

        self.res_var = tk.StringVar(value="Resolution: --")
        self.res_label = ttk.Label(status_frame, textvariable=self.res_var)
        self.res_label.grid(row=0, column=2, padx=(20, 0), sticky="w")

        self.time_var = tk.StringVar(value="Current Time: --")
        self.time_label = ttk.Label(status_frame, textvariable=self.time_var)
        self.time_label.grid(row=0, column=3, padx=(20, 0), sticky="w")

    def _ensure_output_dir(self) -> None:
        Path(self.config.output_dir).expanduser().mkdir(parents=True, exist_ok=True)

    def _init_capture(self) -> None:
        if self.cap is not None:
            self.cap.release()

        self.cap = cv2.VideoCapture(self.config.device_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)

        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_width = actual_width
        self.frame_height = actual_height
        self.res_var.set(f"Resolution: {actual_width}x{actual_height}")

    def _update_video(self) -> None:
        if not self.cap or not self.cap.isOpened():
            self.status_var.set("Camera not available")
            self.root.after(500, self._update_video)
            return

        ret, frame = self.cap.read()
        if not ret:
            self.status_var.set("Waiting for frame...")
            self.root.after(10, self._update_video)
            return

        now = time.time()
        self.frame_times.append(now)
        if len(self.frame_times) > 1:
            elapsed = self.frame_times[-1] - self.frame_times[0]
            if elapsed > 0:
                fps = (len(self.frame_times) - 1) / elapsed
                self.fps_var.set(f"FPS: {fps:.1f}")
        self.time_var.set(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if not self.recording:
            self.status_var.set("Live preview")

        display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(display_frame)
        imgtk = ImageTk.PhotoImage(image=image)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

        if self.recording and self.writer:
            frame_to_write = frame.copy()
            timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(
                frame_to_write,
                timestamp_text,
                (10, self.frame_height - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            self.writer.write(frame_to_write)

        self.root.after(10, self._update_video)

    def start_recording(self) -> None:
        if self.recording:
            return

        if not self.cap or not self.cap.isOpened():
            messagebox.showerror("Error", "Camera not available")
            return

        self._ensure_output_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(self.config.output_dir).expanduser() / f"recording_{timestamp}.mp4"

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            float(self.config.fps),
            (self.frame_width, self.frame_height),
        )

        if not self.writer.isOpened():
            self.writer = None
            messagebox.showerror("Error", "Unable to start video writer")
            return

        self.recording = True
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.status_var.set(f"Recording to {output_path}")

    def stop_recording(self) -> None:
        if not self.recording:
            return

        self.recording = False
        if self.writer:
            self.writer.release()
            self.writer = None

        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.status_var.set("Recording stopped")

    def open_recordings_folder(self) -> None:
        path = Path(self.config.output_dir).expanduser()
        self._ensure_output_dir()

        try:
            if sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", str(path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            elif sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                messagebox.showinfo("Open Folder", f"Recordings directory: {path}")
        except Exception as exc:  # pragma: no cover - UI feedback
            messagebox.showerror("Error", f"Unable to open folder: {exc}")

    def open_config_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Configuration")
        dialog.grab_set()

        ttk.Label(dialog, text="Device Index:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        device_var = tk.StringVar(value=str(self.config.device_index))
        device_entry = ttk.Entry(dialog, textvariable=device_var, width=10)
        device_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(dialog, text="Width:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        width_var = tk.StringVar(value=str(self.config.width))
        width_entry = ttk.Entry(dialog, textvariable=width_var, width=10)
        width_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(dialog, text="Height:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        height_var = tk.StringVar(value=str(self.config.height))
        height_entry = ttk.Entry(dialog, textvariable=height_var, width=10)
        height_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(dialog, text="Target FPS:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        fps_var = tk.StringVar(value=str(self.config.fps))
        fps_entry = ttk.Entry(dialog, textvariable=fps_var, width=10)
        fps_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(dialog, text="Output Directory:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        output_var = tk.StringVar(value=self.config.output_dir)
        output_entry = ttk.Entry(dialog, textvariable=output_var, width=30)
        output_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        def browse_output() -> None:
            directory = filedialog.askdirectory(initialdir=output_var.get())
            if directory:
                output_var.set(directory)

        browse_button = ttk.Button(dialog, text="Browse", command=browse_output)
        browse_button.grid(row=4, column=2, padx=10, pady=5)

        def save_and_close() -> None:
            try:
                device_index = int(device_var.get())
                width = int(width_var.get())
                height = int(height_var.get())
                fps = int(fps_var.get())
                output_dir = output_var.get().strip()
                if width <= 0 or height <= 0 or fps <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numeric values.")
                return

            self.config = AppConfig(
                device_index=device_index,
                width=width,
                height=height,
                fps=fps,
                output_dir=output_dir or "recordings",
            )
            save_config(self.config)
            self._ensure_output_dir()
            self._init_capture()
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="Save", command=save_and_close).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).grid(row=0, column=1, padx=5)

        dialog.transient(self.root)
        dialog.wait_window()

    def on_close(self) -> None:
        self.stop_recording()
        if self.cap:
            self.cap.release()
        if self.writer:
            self.writer.release()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = TheraViewApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
