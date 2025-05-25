#!/usr/bin/env python3
"""
video_ocr.py — utilities to list video files, take periodic snapshots from a video, and OCR those snapshots.

Dependencies:
  - Python: pip install opencv-python pillow pytesseract
  - External: You also need the Tesseract binary installed

Flags:
  --video <file>     Process a single video file (mutually exclusive with --dir).
  --dir <path>       Process **all** recognised videos in the directory.
  --list             Only list the matching video files; no processing.
  --snapshots        Extract snapshots from each video.
  --ocr              Run OCR on the extracted snapshots.
  --interval <sec>   Seconds between snapshots (default 30).
  --lang <codes>     Tesseract language codes, e.g. "eng+fra" (default "eng").

Usage examples:
  # 1. List videos in current dir
  python video_ocr.py --list

  # 2. Extract a snapshot every minute
  python video_ocr.py --video movie.mp4 --snapshots

  # 3. OCR previously-generated snapshots (or generate + OCR in one go)
  python video_ocr.py --video movie.mp4 --ocr

  # 4. Extract snapshots at 30 secondscadence and OCR them in one command
  python video_ocr.py --video movie.mp4 --snapshots --ocr --interval 30

  # 5. Generate snapshots *and* OCR them (30-second cadence)
  python video_ocr.py --dir ~/Movies --snapshots --ocr --interval 30 --lang eng+spa
"""
import argparse, re, cv2, pytesseract
from pathlib import Path
from typing import Iterable, List
from PIL import Image

VIDEO_EXTENSIONS: set[str] = {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"}
DEFAULT_INTERVAL = 30  # seconds
SNAP_NAME_TEMPLATE = "snapshot_{idx:05d}.jpg"

def list_video_files(directory = Path(".")) -> List[Path]:
    """Return every video file (by known extension) in *directory*, sorted alphabetically."""
    return sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS)

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
    key = lambda p: int(re.search(r"(\d+)(?=\.jpg$)", p.name).group(1)) # type: ignore
    return sorted(snapshots, key=key)

def ocr_snapshots(video_path: Path, snapshot_dir: Path | None = None, *, lang: str = "eng") -> Path:
    """Run Tesseract OCR over each snapshot image and collate results into one text file.

    *video_path* is used to derive default locations/names, even if snapshots were generated
    previously.  If *snapshot_dir* is omitted it defaults to ``<video_stem>_snapshots``.
    The combined text is written to ``<video_stem>_slides.txt`` next to the video and the path
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

    out_txt = video_path.with_name(f"{video_path.stem}_slides.txt")
    out_txt.write_text("\n".join(ocr_lines), encoding="utf-8")
    return out_txt

def process_video(video_path: Path, *, do_snaps: bool, do_ocr: bool, interval: int, lang: str) -> None:
    """Apply requested operations to a single video file."""
    print(f"→ {video_path}")
    snapshots_dir: Path | None = None
    if do_snaps:
        snapshots_dir = extract_snapshots(video_path, interval)
        print(f"   Snapshots → {snapshots_dir}")
    else:
        snapshots_dir = video_path.parent / f"{video_path.stem}_snapshots"

    if do_ocr:
        txt = ocr_snapshots(video_path, snapshots_dir, lang=lang)
        print(f"   OCR → {txt}")

def _cli() -> None:
    parser = argparse.ArgumentParser(description="List, snapshot, and OCR video files.")
    parser.add_argument("--list", action="store_true", help="List video files instead of processing.")

    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--video", type=Path, help="Single video file to process.")
    scope.add_argument("--dir", type=Path, help="Process ALL video files inside this directory.")

    parser.add_argument("--snapshots", action="store_true", help="Extract snapshots from video(s).")
    parser.add_argument("--ocr", action="store_true", help="Run OCR on snapshot(s).")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="Snapshot interval in seconds (default 30).")
    parser.add_argument("--lang", default="eng", help="Tesseract language codes, e.g. 'eng+fra'.")

    args = parser.parse_args()

    # Listing mode
    if args.list and not (args.snapshots or args.ocr):
        target_dir = args.dir or Path(".")
        for vid in list_video_files(target_dir):
            print(vid.relative_to(target_dir))
        return

    # Determine worklist of videos
    if args.video:
        work_videos = [args.video.expanduser().resolve()]
    elif args.dir:
        work_videos = list_video_files(args.dir)
    else:
        parser.error("Either --video or --dir must be supplied (or use --list)")

    if not (args.snapshots or args.ocr):
        parser.error("No action specified: add --snapshots and/or --ocr (or use --list)")

    for vid in work_videos:
        process_video(vid, do_snaps=args.snapshots, do_ocr=args.ocr, interval=args.interval, lang=args.lang)

if __name__ == "__main__":
    _cli()