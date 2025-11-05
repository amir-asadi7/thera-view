"""Utility to exercise different USB webcam recording settings on Raspberry Pi.

This script records one-minute video samples while sweeping every combination
of resolution, bitrate, and frames per second (FPS) that you provide. The
resulting files are written to a timestamped directory with descriptive names
and a ``manifest.csv`` file that lists the requested parameters for each run.

Run the script directly on the Raspberry Pi once an ffmpeg-compatible webcam is
connected.  Example:

    python scripts/test_webcam_recording.py --device /dev/video0

Each recording is stored under ``recordings/<timestamp>/`` with filenames
describing the settings used.  Adjust the ``--resolutions``, ``--bitrates``, and
``--framerates`` flags to match your hardware.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging
import subprocess
from pathlib import Path
from typing import Iterable, List, NamedTuple, Tuple


class Variation(NamedTuple):
    """Container describing a single recording variation."""

    width: int
    height: int
    bitrate: str
    fps: int

    def label(self) -> str:
        return f"{self.width}x{self.height}-{self.bitrate}-{self.fps}fps"

    def to_manifest_row(self, file_name: str) -> List[str]:
        return [
            file_name,
            str(self.width),
            str(self.height),
            self.bitrate,
            str(self.fps),
        ]

DEFAULT_RESOLUTIONS: Tuple[Tuple[int, int], ...] = (
    (640, 480),
    (1280, 720),
    (1920, 1080),
)

DEFAULT_BITRATES: Tuple[str, ...] = (
    "2M",
    "4M",
    "8M",
)

DEFAULT_FRAMERATES: Tuple[int, ...] = (
    15,
    30,
    60,
)

DEFAULT_DURATION_SECONDS = 60
DEFAULT_DEVICE = "/dev/video0"
DEFAULT_OUTPUT_DIR = Path("recordings")
DEFAULT_CODEC = "libx264"
DEFAULT_PRESET = "veryfast"


def build_output_path(base_dir: Path, run_id: str, label: str) -> Path:
    """Create the full output path for a recording."""
    directory = base_dir / run_id
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{label}.mp4"


def run_ffmpeg(
    *,
    device: str,
    width: int,
    height: int,
    bitrate: str,
    fps: int,
    duration: int,
    output_path: Path,
    codec: str,
    preset: str,
) -> None:
    """Invoke ffmpeg to record from the USB webcam with the given settings."""
    command = [
        "ffmpeg",
        "-y",  # overwrite without prompt
        "-f",
        "v4l2",
        "-framerate",
        str(fps),
        "-video_size",
        f"{width}x{height}",
        "-i",
        device,
        "-c:v",
        codec,
        "-preset",
        preset,
        "-b:v",
        bitrate,
        "-t",
        str(duration),
        str(output_path),
    ]

    logging.info(
        "Running ffmpeg for %s at %dx%d, %s, %sfps -> %s",
        device,
        width,
        height,
        bitrate,
        fps,
        output_path,
    )

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        logging.error("ffmpeg failed with return code %s", exc.returncode)
        raise


def record_variations(
    variations: Iterable[Variation],
    *,
    device: str,
    duration: int,
    output_dir: Path,
    run_id: str,
    codec: str,
    preset: str,
) -> List[Tuple[Variation, Path]]:
    """Record each variation and return the resulting file paths."""

    recorded: List[Tuple[Variation, Path]] = []
    for index, variation in enumerate(variations, start=1):
        label = f"{index:03d}-{variation.label()}"
        output_path = build_output_path(output_dir, run_id, label)
        run_ffmpeg(
            device=device,
            width=variation.width,
            height=variation.height,
            bitrate=variation.bitrate,
            fps=variation.fps,
            duration=duration,
            output_path=output_path,
            codec=codec,
            preset=preset,
        )
        recorded.append((variation, output_path))

    return recorded


def write_manifest(
    recorded: Iterable[Tuple[Variation, Path]],
    *,
    manifest_path: Path,
) -> None:
    """Persist a manifest describing the requested settings for each file."""

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["file_name", "width", "height", "target_bitrate", "target_fps"])
        for variation, path in recorded:
            writer.writerow(variation.to_manifest_row(path.name))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device",
        default=DEFAULT_DEVICE,
        help="Video4Linux device path for the USB webcam",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION_SECONDS,
        help="Recording duration for each sample in seconds",
    )
    parser.add_argument(
        "--resolutions",
        nargs="*",
        default=[f"{w}x{h}" for w, h in DEFAULT_RESOLUTIONS],
        help="Resolutions to test, e.g. 1280x720 1920x1080",
    )
    parser.add_argument(
        "--bitrates",
        nargs="*",
        default=list(DEFAULT_BITRATES),
        help="Video bitrates to test (ffmpeg format, e.g. 2M, 5M)",
    )
    parser.add_argument(
        "--framerates",
        type=int,
        nargs="*",
        default=list(DEFAULT_FRAMERATES),
        help="Frames-per-second values to test",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to store recordings",
    )
    parser.add_argument(
        "--codec",
        default=DEFAULT_CODEC,
        help="Video codec passed to ffmpeg's -c:v option",
    )
    parser.add_argument(
        "--preset",
        default=DEFAULT_PRESET,
        help="ffmpeg encoding preset",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    return parser.parse_args()


def parse_resolution(value: str) -> Tuple[int, int]:
    width, height = value.lower().split("x", 1)
    return int(width), int(height)


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    resolutions = tuple(parse_resolution(item) for item in args.resolutions)
    bitrates = tuple(args.bitrates)
    framerates = tuple(args.framerates)

    if not resolutions:
        raise SystemExit("No resolutions provided. Specify at least one via --resolutions.")
    if not bitrates:
        raise SystemExit("No bitrates provided. Specify at least one via --bitrates.")
    if not framerates:
        raise SystemExit("No framerates provided. Specify at least one via --framerates.")

    logging.info("Using device %s", args.device)
    logging.info("Testing resolutions: %s", resolutions)
    logging.info("Testing bitrates: %s", bitrates)
    logging.info("Testing framerates: %s", framerates)

    run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    logging.info("Recording samples into %s", args.output_dir / run_id)

    variations = [
        Variation(width=w, height=h, bitrate=b, fps=f)
        for w, h in resolutions
        for b in bitrates
        for f in framerates
    ]

    logging.info("Preparing %s recording variations", len(variations))
    recorded = record_variations(
        variations,
        device=args.device,
        duration=args.duration,
        output_dir=args.output_dir,
        run_id=run_id,
        codec=args.codec,
        preset=args.preset,
    )

    manifest_path = args.output_dir / run_id / "manifest.csv"
    write_manifest(recorded, manifest_path=manifest_path)
    logging.info("Wrote manifest to %s", manifest_path)


if __name__ == "__main__":
    main()
