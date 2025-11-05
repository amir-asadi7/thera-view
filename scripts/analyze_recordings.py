"""Analyze recorded webcam samples and summarize actual encoding stats.

The script expects a directory produced by ``test_webcam_recording.py`` that
contains MP4 samples and an optional ``manifest.csv`` file.  It invokes
``ffprobe`` to compute the real bitrate, frame rate, duration, and other details
for each file and writes a consolidated CSV report.

Example:

    python scripts/analyze_recordings.py recordings/20240101-120000
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_MANIFEST_NAME = "manifest.csv"
DEFAULT_REPORT_NAME = "analysis.csv"


class AnalysisError(RuntimeError):
    """Raised when ffprobe fails to analyze a recording."""


def parse_fraction(value: str) -> float:
    """Convert an ffprobe fraction string (e.g. "30000/1001") to float."""

    if not value or value in {"0", "0/0"}:
        return 0.0
    if "/" not in value:
        return float(value)
    numerator, denominator = value.split("/", 1)
    if not denominator or denominator == "0":
        return 0.0
    return float(numerator) / float(denominator)


def load_manifest(path: Path) -> Dict[str, Dict[str, str]]:
    """Load manifest rows keyed by file name."""

    mapping: Dict[str, Dict[str, str]] = {}
    if not path.exists():
        return mapping

    with path.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            file_name = row.get("file_name")
            if not file_name:
                continue
            mapping[file_name] = row
    return mapping


def run_ffprobe(ffprobe_path: str, file_path: Path) -> Dict[str, object]:
    """Invoke ffprobe and return the parsed JSON output."""

    command = [
        ffprobe_path,
        "-v",
        "error",
        "-show_entries",
        "format=bit_rate,duration,size:stream=index,avg_frame_rate,nb_frames,width,height,codec_name",
        "-of",
        "json",
        str(file_path),
    ]

    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - requires ffprobe failure
        raise AnalysisError(f"ffprobe failed for {file_path}: {exc.stderr}") from exc

    return json.loads(completed.stdout)


def summarize_recording(
    ffprobe_path: str,
    file_path: Path,
    manifest_row: Optional[Dict[str, str]],
) -> List[str]:
    """Gather statistics for a single recording and return CSV row values."""

    info = run_ffprobe(ffprobe_path, file_path)

    format_info = info.get("format", {})
    streams = info.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("index") == 0), {})

    size_bytes = int(format_info.get("size", file_path.stat().st_size))
    duration_seconds = float(format_info.get("duration", 0.0))
    actual_bitrate = float(format_info.get("bit_rate", 0.0))
    avg_frame_rate = parse_fraction(str(video_stream.get("avg_frame_rate", "0")))
    nb_frames = video_stream.get("nb_frames")
    codec = video_stream.get("codec_name", "")
    width = video_stream.get("width")
    height = video_stream.get("height")

    target_bitrate = manifest_row.get("target_bitrate") if manifest_row else ""
    target_fps = manifest_row.get("target_fps") if manifest_row else ""

    return [
        file_path.name,
        manifest_row.get("width", "") if manifest_row else "",
        manifest_row.get("height", "") if manifest_row else "",
        target_bitrate,
        target_fps,
        f"{avg_frame_rate:.3f}",
        str(nb_frames or ""),
        f"{actual_bitrate/1000:.1f}",
        f"{duration_seconds:.3f}",
        f"{size_bytes / (1024 * 1024):.2f}",
        str(width or ""),
        str(height or ""),
        codec,
    ]


def analyze_directory(
    directory: Path,
    *,
    ffprobe_path: str,
    manifest_path: Path,
    report_path: Path,
) -> None:
    """Analyze all MP4 files in ``directory`` and write a CSV report."""

    manifest = load_manifest(manifest_path)
    mp4_files = sorted(directory.glob("*.mp4"))

    if not mp4_files:
        raise SystemExit(f"No MP4 files found in {directory}")

    header = [
        "file_name",
        "target_width",
        "target_height",
        "target_bitrate",
        "target_fps",
        "actual_avg_fps",
        "actual_frame_count",
        "actual_bitrate_kbps",
        "duration_seconds",
        "file_size_megabytes",
        "detected_width",
        "detected_height",
        "codec",
    ]

    with report_path.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        for file_path in mp4_files:
            manifest_row = manifest.get(file_path.name)
            writer.writerow(summarize_recording(ffprobe_path, file_path, manifest_row))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directory",
        type=Path,
        help="Path to the directory containing MP4 recordings",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Path to the manifest.csv generated during recording",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Where to write the CSV report (defaults to <directory>/analysis.csv)",
    )
    parser.add_argument(
        "--ffprobe",
        default="ffprobe",
        help="Path to the ffprobe executable",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    directory = args.directory.expanduser().resolve()
    if not directory.exists():
        raise SystemExit(f"Directory does not exist: {directory}")

    manifest_path = args.manifest or directory / DEFAULT_MANIFEST_NAME
    report_path = args.output or directory / DEFAULT_REPORT_NAME

    analyze_directory(
        directory,
        ffprobe_path=args.ffprobe,
        manifest_path=manifest_path,
        report_path=report_path,
    )
    print(f"Wrote analysis report to {report_path}")


if __name__ == "__main__":
    main()
