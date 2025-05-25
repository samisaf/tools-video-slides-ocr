#!/usr/bin/env python3
"""
video_tools.py — utilities to list video files, take periodic snapshots from a video, and OCR those snapshots.

Dependencies:
  pip install opencv-python pillow pytesseract
  # On most systems you also need the Tesseract binary installed, e.g.:
  #   sudo apt-get install tesseract-ocr   (Debian/Ubuntu)
  #   brew install tesseract               (macOS)
  #   choco install tesseract-ocr          (Windows)

Usage examples:
  # 1. List videos in current dir
  python video_tools.py --list

  # 2. Extract a snapshot every minute
  python video_tools.py --video movie.mp4 --snapshots

  # 3. OCR previously-generated snapshots (or generate + OCR in one go)
  python video_tools.py --video movie.mp4 --ocr

  # 4. Extract snapshots at 30 secondscadence and OCR them in one command
  python video_tools.py --video movie.mp4 --snapshots --ocr --interval 30
"""

from __future__ import annotations  # Requires Python 3.7+

import argparse
import re
from pathlib import Path
from textwrap import dedent
from typing import Iterable, List

import cv2
from PIL import Image
import pytesseract

# ░▒▓ Constants ▓▒░
VIDEO_EXTENSIONS: set[str] = {
    ".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm",
}
DEFAULT_INTERVAL = 60  # seconds
SNAP_NAME_TEMPLATE = "snapshot_{idx:05d}.jpg"

# ░▒▓ Core functionality ▓▒░

def list_video_files(directory: Path = Path(".")) -> List[Path]:
    """Return every video file (by known extension) in *directory*, sorted alphabetically."""
    return sorted(
        p for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
    )


def extract_snapshots(video_path: Path, interval_seconds: int = DEFAULT_INTERVAL) -> Path:
    """Extract a frame every *interval_seconds* seconds from *video_path*.

    Snapshots are stored as JPEGs inside ``<video_stem>_snapshots`` sitting next to the video.
    The directory path is returned.
    """
    video_path = video_path.expanduser().resolve()
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    out_dir = video_path.parent / f"{video_path.stem}_snapshots"
    out_dir.mkdir(exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0  # Fallback if FPS unavailable
    frame_interval = int(round(fps * interval_seconds)) or 1

    frame_no = 0
    shot_no = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break  # end of video

        if frame_no % frame_interval == 0:
            snap_path = out_dir / SNAP_NAME_TEMPLATE.format(idx=shot_no)
            cv2.imwrite(str(snap_path), frame)
            shot_no += 1
        frame_no += 1

    cap.release()
    return out_dir


def _iter_snapshots(snapshot_dir: Path) -> Iterable[Path]:
    """Yield snapshot paths in natural (numeric) order."""
    snapshots = sorted(snapshot_dir.glob("snapshot_*.jpg"))
    # Natural sort by the numeric part to avoid 10 < 2 issues
    key = lambda p: int(re.search(r"(\d+)(?=\.jpg$)", p.name).group(1))
    return sorted(snapshots, key=key)


def ocr_snapshots(video_path: Path, snapshot_dir: Path | None = None, *, lang: str = "eng") -> Path:
    """Run Tesseract OCR over each snapshot image and collate results into one text file.

    *video_path* is used to derive default locations/names, even if snapshots were generated
    previously.  If *snapshot_dir* is omitted it defaults to ``<video_stem>_snapshots``.
    The combined text is written to ``<video_stem>_ocr.txt`` next to the video and the path
    is returned.
    """
    video_path = video_path.expanduser().resolve()
    if snapshot_dir is None:
        snapshot_dir = video_path.parent / f"{video_path.stem}_snapshots"

    if not snapshot_dir.is_dir():
        raise FileNotFoundError(f"Snapshot directory not found: {snapshot_dir}")

    snapshots = list(_iter_snapshots(snapshot_dir))
    if not snapshots:
        raise RuntimeError(f"No snapshots found in {snapshot_dir}")

    ocr_lines: List[str] = []
    for idx, snap in enumerate(snapshots):
        try:
            img = Image.open(snap)
            text = pytesseract.image_to_string(img, lang=lang)
            ocr_lines.append(f"# Snapshot {idx} — {snap.name}\n{text}\n")
        except Exception as e:
            ocr_lines.append(f"# Snapshot {idx} — {snap.name}\n[OCR failed: {e}]\n")

    out_txt = video_path.with_name(f"{video_path.stem}_ocr.txt")
    out_txt.write_text("\n".join(ocr_lines), encoding="utf‑8")
    return out_txt

# ░▒▓ CLI ▓▒░

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="List video files, extract snapshots, and OCR those snapshots.")

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--list", action="store_true", help="List video files in the current directory.")

    parser.add_argument("--video", type=Path,
                        help="Path to a video file to process (needed for --snapshots / --ocr).")
    parser.add_argument("--snapshots", action="store_true", help="Extract snapshots from the video.")
    parser.add_argument("--ocr", action="store_true", help="Run OCR over snapshots.")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL,
                        help="Snapshot interval in seconds (default: 60).")
    parser.add_argument("--lang", default="eng",
                        help="Tesseract language code(s), e.g. 'eng+fra' (default: eng).")

    args = parser.parse_args()

    # Case 1: just list videos
    if args.list and not (args.snapshots or args.ocr):
        for vid in list_video_files():
            print(vid)
        return

    if not args.video:
        parser.error("--video is required unless you're only using --list")

    video_path: Path = args.video

    # Case 2: extract snapshots (with optional OCR)
    if args.snapshots:
        out_dir = extract_snapshots(video_path, args.interval)
        print(f"Snapshots saved to {out_dir}")
    else:
        # user didn't request new snapshots but OCR might rely on existing ones.
        out_dir = video_path.parent / f"{video_path.stem}_snapshots"

    # Case 3: OCR stage
    if args.ocr:
        txt_path = ocr_snapshots(video_path, out_dir, lang=args.lang)
        print(f"OCR complete → {txt_path}")

    if not (args.snapshots or args.ocr or args.list):
        parser.print_help()


if __name__ == "__main__":
    _cli()

