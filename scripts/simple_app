import av
import time
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from datetime import datetime
import os

recording = False
output = None
stream_out = None
running = True

encode_lock = threading.Lock()


def camera_loop(preview_label):
    """Continuous camera preview using PyAV, handles recording when toggled."""
    global recording, output, stream_out, running

    container = av.open('/dev/video0')
    stream_in = container.streams.video[0]
    stream_in.thread_type = "AUTO"

    frame_interval = 1.0 / 30
    prev_time = time.time()

    print("Camera ready - live preview active.")

    try:
        for frame in container.decode(video=0):
            if not running:
                break

            # Convert frame for display
            img = frame.to_ndarray(format="rgb24")
            img_pil = Image.fromarray(img).resize((640, 360))
            imgtk = ImageTk.PhotoImage(image=img_pil)
            preview_label.imgtk = imgtk
            preview_label.configure(image=imgtk)

            # Encode guarded by lock
            with encode_lock:
                if recording and output and stream_out:
                    try:
                        # Reformat for encoder
                        frame_enc = frame.reformat(width=1920, height=1080, format="yuv420p")

                        # Reset timestamps so each file starts at 0
                        frame_enc.pts = None
                        frame_enc.time_base = stream_out.codec_context.time_base

                        for packet in stream_out.encode(frame_enc):
                            if packet is not None:
                                # Let encoder/container handle fresh timeline
                                packet.pts = None
                                packet.dts = None
                                output.mux(packet)

                    except av.error.FFmpegError as e:
                        if getattr(e, "errno", None) not in (541478725, 22):
                            print(f"Encode warning: {e}")

            # Maintain about 30 fps
            next_time = prev_time + frame_interval
            now = time.time()
            if now < next_time:
                time.sleep(next_time - now)
            prev_time = next_time

    except av.error.FFmpegError as e:
        # Ignore benign EOF or invalid argument during shutdown
        if getattr(e, "errno", None) not in (541478725, 22):
            print(f"Camera loop error: {e}")
    except Exception as e:
        print(f"Camera loop general error: {e}")
    finally:
        try:
            container.close()
        except Exception:
            pass
        print("Camera closed.")


def select_encoder(output, filename):
    """Use libx264 with sane defaults on this machine."""
    try:
        st = output.add_stream(
            "libx264",
            rate=30,
            options={
                "crf": "24",
                "preset": "medium"
            }
        )
        st.width = 1920
        st.height = 1080
        st.pix_fmt = "yuv420p"
        print("Encoder: libx264")
        return st
    except Exception as e:
        print(f"libx264 failed: {e}")
        return None


def start_recording():
    global recording, output, stream_out

    with encode_lock:
        if recording:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"recording_{timestamp}.mp4"

        try:
            output = av.open(filename, mode="w")
        except Exception as e:
            print(f"Open output failed: {e}")
            output = None
            return

        stream_out = select_encoder(output, filename)
        if not stream_out:
            print("No working encoder, abort.")
            try:
                output.close()
            except Exception:
                pass
            output = None
            return

        recording = True
        start_btn.configure(style="Recording.TButton", text="Recording")
        print(f"Recording started: {filename}")


def recording_cleanup():
    global recording, output, stream_out

    # assumes encode_lock is already held by caller
    if not recording and not output and not stream_out:
        return

    if output and stream_out:
        try:
            # Flush pending packets
            for packet in stream_out.encode(None):
                if packet is not None:
                    output.mux(packet)
        except Exception as e:
            print(f"Flush notice: {e}")

        try:
            output.close()
        except Exception as e:
            print(f"Close notice: {e}")

    recording = False
    output = None
    stream_out = None
    start_btn.configure(style="Big.TButton", text="Start")
    print("Recording stopped - preview continues.")


def stop_recording():
    global recording, output, stream_out
    with encode_lock:
        if not recording:
            return
        print("Stopping recording...")
        recording_cleanup()


# GUI
root = tk.Tk()
root.title("Webcam Recorder")
root.geometry("900x520")

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

preview_label = tk.Label(main_frame)
preview_label.pack(side="left", expand=True)

btn_frame = tk.Frame(main_frame)
btn_frame.pack(side="right", fill="y", padx=30, pady=40)

style = ttk.Style()
style.configure("Big.TButton", font=("Helvetica", 16, "bold"), padding=20)
style.configure(
    "Recording.TButton",
    font=("Helvetica", 16, "bold"),
    padding=20,
    background="green",
    foreground="white"
)

start_btn = ttk.Button(btn_frame, text="Start", command=start_recording, style="Big.TButton")
start_btn.pack(pady=20, fill="x")

stop_btn = ttk.Button(btn_frame, text="Stop", command=stop_recording, style="Big.TButton")
stop_btn.pack(pady=20, fill="x")


def on_close():
    global running
    running = False
    with encode_lock:
        if recording:
            recording_cleanup()
    try:
        root.destroy()
    except Exception:
        pass
    os._exit(0)


root.protocol("WM_DELETE_WINDOW", on_close)

threading.Thread(target=camera_loop, args=(preview_label,), daemon=True).start()
root.mainloop()
