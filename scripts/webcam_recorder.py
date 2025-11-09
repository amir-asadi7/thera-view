"""Simple full-screen webcam recording application for Raspberry Pi OS.

The app displays a live preview and provides large Start/Stop buttons on the
right-hand side. Recordings are encoded with MJPG by default and saved using the
current date and time as the filename.
"""

from __future__ import annotations

import configparser
import datetime as dt
import sys
from pathlib import Path
from typing import Optional

import cv2
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk


class WebcamRecorderApp:
    """Tkinter-based webcam recorder with start/stop controls."""

    def __init__(self, root: tk.Tk, config_path: Path) -> None:
        self.root = root
        self.root.title("Webcam Recorder")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="black")
        self.root.bind("<Escape>", lambda _event: self.close())

        self.config = self._load_config(config_path)
        self.cap: Optional[cv2.VideoCapture] = None
        self.writer: Optional[cv2.VideoWriter] = None
        self.recording = False

        self.video_frame = tk.Frame(self.root, bg="black")
        self.controls_frame = tk.Frame(self.root, bg="#1c1c1c", width=int(self.root.winfo_screenwidth() * 0.25))

        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.controls_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

        self.preview_label = tk.Label(self.video_frame, bg="black")
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(
            self.controls_frame,
            textvariable=self.status_var,
            fg="white",
            bg="#1c1c1c",
            font=("Helvetica", 24),
            wraplength=400,
            justify=tk.LEFT,
        )
        self.status_label.pack(side=tk.TOP, pady=40, padx=20)

        button_font = ("Helvetica", 36, "bold")
        self.start_button = tk.Button(
            self.controls_frame,
            text="START",
            command=self.start_recording,
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            activeforeground="white",
            font=button_font,
            padx=40,
            pady=40,
        )
        self.start_button.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.stop_button = tk.Button(
            self.controls_frame,
            text="STOP",
            command=self.stop_recording,
            state=tk.DISABLED,
            bg="#e74c3c",
            fg="white",
            activebackground="#c0392b",
            activeforeground="white",
            font=button_font,
            padx=40,
            pady=40,
        )
        self.stop_button.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=20)

        self._initialize_camera()
        self._update_preview()

    def _load_config(self, config_path: Path) -> configparser.SectionProxy:
        parser = configparser.ConfigParser()
        if not config_path.exists():
            messagebox.showerror("Configuration missing", f"Config file not found: {config_path}")
            sys.exit(1)

        parser.read(config_path)
        if "video" not in parser:
            messagebox.showerror("Configuration error", "[video] section missing in config file")
            sys.exit(1)
        return parser["video"]

    def _initialize_camera(self) -> None:
        camera_index = self.config.getint("camera_index", fallback=0)
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            messagebox.showerror("Camera error", "Unable to open the webcam.")
            self.root.destroy()
            return

        width = self.config.getint("frame_width", fallback=1920)
        height = self.config.getint("frame_height", fallback=1080)
        fps = self.config.getint("fps", fallback=30)
        input_fourcc = self.config.get("input_fourcc", fallback="MJPG")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        if input_fourcc:
            fourcc = cv2.VideoWriter_fourcc(*input_fourcc)
            self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)

        if self.config.get("autofocus", fallback="").lower() == "off":
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)

        if self.config.get("brightness"):
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.config.getfloat("brightness"))
        if self.config.get("contrast"):
            self.cap.set(cv2.CAP_PROP_CONTRAST, self.config.getfloat("contrast"))

        self.fps = fps
        self.frame_size = (
            int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )

    def _update_preview(self) -> None:
        if self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.status_var.set("Camera frame unavailable")
            self.root.after(1000 // max(self.fps, 1), self._update_preview)
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)

        window_width = self.video_frame.winfo_width() or self.frame_size[0]
        window_height = self.video_frame.winfo_height() or self.frame_size[1]
        resampling = getattr(Image, "Resampling", Image)
        image = image.resize((window_width, window_height), resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image=image)

        self.preview_label.configure(image=photo)
        self.preview_label.image = photo

        if self.recording and self.writer is not None:
            self.writer.write(frame)

        delay = max(int(1000 / max(self.fps, 1)), 1)
        self.root.after(delay, self._update_preview)

    def start_recording(self) -> None:
        if self.recording:
            return
        if self.cap is None:
            messagebox.showerror("Camera error", "Camera is not initialized.")
            return

        output_dir = Path(self.config.get("output_directory", fallback="recordings")).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)

        file_extension = self.config.get("file_extension", fallback="avi").lstrip(".")
        filename = dt.datetime.now().strftime("%Y%m%d_%H%M%S") + f".{file_extension}"
        filepath = output_dir / filename

        fourcc_code = self.config.get("recording_fourcc", fallback="MJPG")
        fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
        self.writer = cv2.VideoWriter(str(filepath), fourcc, self.fps, self.frame_size)
        if not self.writer.isOpened():
            messagebox.showerror("Recording error", f"Unable to start recording to {filepath}.")
            self.writer.release()
            self.writer = None
            return

        self.recording = True
        self.status_var.set(f"Recording...\n{filepath}")
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)

    def stop_recording(self) -> None:
        if not self.recording:
            return
        self.recording = False
        if self.writer is not None:
            self.writer.release()
            self.writer = None
        self.status_var.set("Saved recording.")
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)

    def close(self) -> None:
        self.stop_recording()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()
        self.root.destroy()


def main() -> None:
    config_path = Path(__file__).resolve().parent / "webcam_config.ini"
    root = tk.Tk()
    app = WebcamRecorderApp(root, config_path)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()


if __name__ == "__main__":
    main()
