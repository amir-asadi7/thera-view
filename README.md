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

