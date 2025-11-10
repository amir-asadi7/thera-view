import av
import time
import statistics
import os

# ---------- CONFIGURATION ----------
CAMERA_DEVICE = "/dev/video0"
WIDTH, HEIGHT, TARGET_FPS = 1920, 1080, 30
TEST_SECONDS = 20
OUTPUT_DIR = "ffmpeg_tests"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------- FUNCTIONS ----------

def get_video_encoders():
    """Return a list of available video encoder names."""
    encoders = []
    for name in av.codecs_available:
        try:
            c = av.codec.Codec(name, "w")
            if c.type == "video":
                encoders.append(name)
        except Exception:
            pass
    return encoders


def get_supported_pixfmts(encoder_name):
    """Return pixel formats supported by an encoder."""
    try:
        codec = av.codec.Codec(encoder_name, "w")
        return [fmt.name for fmt in codec.video_formats]
    except Exception:
        return []


def open_camera():
    """Open camera device for decoding."""
    container = av.open(CAMERA_DEVICE)
    stream = container.streams.video[0]
    stream.thread_type = "AUTO"
    return container, stream


def test_encoder(encoder_name, pix_fmt):
    """Record a short video using a given encoder and pixel format."""
    filename = f"{OUTPUT_DIR}/test_{encoder_name}_{pix_fmt}.mp4"
    print(f"\n=== Testing {encoder_name} ({pix_fmt}) ===")

    try:
        container, stream_in = open_camera()
    except Exception as e:
        print(f"Camera open failed: {e}")
        return None

    try:
        output = av.open(filename, mode="w")
        stream_out = output.add_stream(encoder_name, rate=TARGET_FPS)
        stream_out.width = WIDTH
        stream_out.height = HEIGHT
        stream_out.pix_fmt = pix_fmt

        frame_times = []
        frame_count = 0
        start_time = time.time()

        for frame in container.decode(video=0):
            now = time.time()
            frame_times.append(now)
            frame_count += 1

            frame_enc = frame.reformat(width=WIDTH, height=HEIGHT, format=pix_fmt)
            packets = stream_out.encode(frame_enc)
            for packet in packets:
                output.mux(packet)

            if now - start_time > TEST_SECONDS:
                break

        # Flush encoder
        for packet in stream_out.encode(None):
            output.mux(packet)

        output.close()
        container.close()

        if len(frame_times) < 2:
            print("No frames captured.")
            return None

        intervals = [frame_times[i+1] - frame_times[i] for i in range(len(frame_times)-1)]
        avg_fps = 1.0 / statistics.mean(intervals)
        print(f"Captured {frame_count} frames at ~{avg_fps:.2f} FPS")
        return avg_fps

    except av.error.FFmpegError as e:
        print(f"Encoder error: {e}")
        return None
    except Exception as e:
        print(f"General error: {e}")
        return None


# ---------- MAIN ----------
if __name__ == "__main__":
    print(f"Scanning available encoders and pixel formats on this system...")
    encoders = get_video_encoders()
    print(f"Found {len(encoders)} video encoders.\n")

    results = []

    for enc in encoders:
        pixfmts = get_supported_pixfmts(enc)
        if not pixfmts:
            continue
        print(f"{enc}: {', '.join(pixfmts)}")

        for pix in pixfmts:
            fps = test_encoder(enc, pix)
            if fps:
                results.append((enc, pix, fps))

    print("\n=== Summary ===")
    for enc, pix, fps in sorted(results, key=lambda x: x[2], reverse=True):
        print(f"{enc:20s} {pix:10s} → {fps:.2f} FPS")

    print(f"\nRecordings saved in: {os.path.abspath(OUTPUT_DIR)}")
