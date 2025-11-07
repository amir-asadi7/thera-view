# thera-view

Thera-View coordinates two Raspberry Pi devices, each connected to a webcam, to
record synchronized video streams of physiotherapy or occupational therapy
sessions.

## USB webcam recording test helper

The `scripts/test_webcam_recording.py` helper records one-minute samples from a
USB webcam while sweeping every combination of resolution, bitrate, and frame
rate that you provide. This is useful for gauging how different encoder settings
affect quality and performance on a Raspberry Pi.

Example usage:

```bash
python scripts/test_webcam_recording.py --device /dev/video0
```

Each sample is saved under `recordings/<timestamp>/` with filenames that encode
the requested settings, and a `manifest.csv` file is produced alongside the
videos to record the requested parameters. Adjust the default lists within the
script or pass `--resolutions`, `--bitrates`, and `--framerates` arguments to
tailor the tests to your hardware.

After recordings complete you can summarize the actual results with
`scripts/analyze_recordings.py`, which uses `ffprobe` to inspect each MP4 file
and writes a CSV table of metrics (real frame rate, bitrate, file size, etc.).

```bash
python scripts/analyze_recordings.py recordings/<timestamp>
```

## Live viewer and recorder

The `app/main.py` script provides a simple graphical application for previewing
and recording a webcam feed on Linux desktop environments (including Ubuntu and
Raspberry Pi OS). It displays the live video stream, reports the current FPS and
resolution, and lets you start/stop recordings with on-screen controls. Each
recorded MP4 embeds the current date and time in the video frames. Additional
controls let you open the recordings directory or adjust capture settings such
as the camera index, target resolution, FPS, and output location.

### Running the app

1. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Launch the GUI:

   ```bash
   python app/main.py
   ```

Recordings are saved in the directory configured via the **Config** button
(`recordings/` by default). Use the **Open Recordings Folder** button to view
finished clips in your system's file manager.

