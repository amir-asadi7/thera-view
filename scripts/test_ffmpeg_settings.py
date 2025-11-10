import av
import time
import statistics

# Device and core test settings
CAMERA_DEVICE = "/dev/video0"
TEST_SECONDS = 5
WIDTH, HEIGHT, TARGET_FPS = 1920, 1080, 30

# Define encoders and settings to test
ENCODER_TESTS = [
    # ---------- Software encoders ----------
    ("libx264", {"preset": "ultrafast", "crf": "30"}),
    ("libx264", {"preset": "veryfast", "crf": "26"}),
    ("libx264", {"preset": "medium", "crf": "23"}),
    ("libx265", {"preset": "ultrafast", "crf": "30"}),  # HEVC (may be slower)
    ("mpeg4", {"qscale": "5"}),  # Legacy fallback
    ("libvpx", {"cpu-used": "8", "deadline": "realtime", "b": "2M"}),  # VP8

    # ---------- Hardware encoders ----------
    ("h264_v4l2m2m", {"bitrate": "4000000"}),  # Raspberry Pi 4 hardware H.264
    ("h264_omx", {"bitrate": "4000000"}),      # OMX hardware encoder (older Pi)
    ("h264_mmal", {"bitrate": "4000000"}),     # MMAL encoder (Pi-specific legacy)
    ("hevc_v4l2m2m", {"bitrate": "4000000"}),  # Hardware HEVC (newer kernels)
]

def open_camera():
    container = av.open(CAMERA_DEVICE)
    stream = container.streams.video[0]
    stream.thread_type = "AUTO"
    return container, stream

def test_encoder(encoder_name, options):
    print(f"\n=== Testing {encoder_name} with options {options} ===")
    try:
        container, stream_in = open_camera()
    except Exception as e:
        print(f"Camera open failed: {e}")
        return None

    try:
        output = av.open("test_output.mp4", mode="w")
        stream_out = output.add_stream(encoder_name, rate=TARGET_FPS, options=options)
        stream_out.width = WIDTH
        stream_out.height = HEIGHT
        stream_out.pix_fmt = "yuv420p"

        frame_times = []
        frame_count = 0
        start_time = time.time()

        for frame in container.decode(video=0):
            now = time.time()
            frame_times.append(now)
            frame_count += 1

            frame_enc = frame.reformat(width=WIDTH, height=HEIGHT, format="yuv420p")
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

        meets_target = avg_fps >= TARGET_FPS * 0.95
        print("✓ PASS" if meets_target else "✗ FAIL")

        return avg_fps

    except av.error.FFmpegError as e:
        print(f"Encoder error: {e}")
        return None
    except Exception as e:
        print(f"General error: {e}")
        return None

if __name__ == "__main__":
    print("Starting FFmpeg encoder performance test for 1080p@30fps\n")
    results = {}
    for name, opts in ENCODER_TESTS:
        fps = test_encoder(name, opts)
        if fps:
            results[f"{name} {opts}"] = fps

    print("\n=== Summary ===")
    for name, fps in sorted(results.items(), key=lambda x: x[1], reverse=True):
        print(f"{name:60s} → {fps:.2f} FPS")
