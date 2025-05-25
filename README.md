# Video Slides OCR
This is a small command-line tool to help take periodic snapshots from a video lecture and OCR those snapshots. Typical uses include skimming long lectures, and generating thumbnails & transcripts for recorded meetings.

This automates three everyday video‑processing chores:

1. **List videos** in the current folder (quick inventory of *.mp4*, *.avi*, …).
2. **Extract snapshots** every *N* seconds and save them as JPEGs in a sibling `<video>_snapshots/` directory.
3. **OCR the snapshots**, concatenating all recognised text into one `<video>_ocr.txt` file.

## Installation
### System prerequisite
You need the Tesseract binary on your `PATH`:

```
# Debian/Ubuntu
sudo apt‑get install tesseract‑ocr

# macOS (Homebrew)
brew install tesseract

# Windows (Chocolatey)
choco install tesseract-ocr
```

### Python packages
```
pip install opencv-python pillow pytesseract 
```

## CLI Flags
Flags:
```
  --video <file>     Process a single video file (mutually exclusive with --dir).
  --dir <path>       Process **all** recognised videos in the directory.
  --list             Only list the matching video files; no processing.
  --snapshots        Extract snapshots from each video.
  --ocr              Run OCR on the extracted snapshots.
  --interval <sec>   Seconds between snapshots (default 30).
  --lang <codes>     Tesseract language codes, e.g. "eng+fra" (default "eng").
```

## Usage cheat‑sheet

| Goal | Command |
| --- | --- |
| List videos | `python video_ocr.py --list` |
| One shot per min from demo.mp4 | `python video_ocr.py --video demo.mp4 --snapshots` |
| 30 seconds interval | `python video_ocr.py --video demo.mp4 --snapshots --interval 30` |
| OCR existing snapshots | `python video_ocr.py --video demo.mp4 --ocr` |
| Extract and OCR in one go | `python video_ocr.py --video demo.mp4 --snapshots --ocr` |
| Multilingual OCR (English + French) | `python video_ocr.py --video demo.mp4 --snapshots --ocr --lang eng+fra` |
| Process every video in the given directory | `python video_ocr.py --dir ./mydirectory --snapshots --ocr` |

### Output structure

```
.
├── demo.mp4
├── demo_snapshots/
│   ├── snapshot_00000.jpg
│   ├── snapshot_00001.jpg
│   └── …
└── demo_ocr.txt
```

Each text block inside **demo_ocr.txt** is prefixed so you know which snapshot it came from:

```
# Snapshot 0 — snapshot_00000.jpg
Recognized text goes here…
```

## Troubleshooting
* **`RuntimeError: Unable to open <file>`**  →  Check the file path and verify OpenCV supports the codec.
* **OCR empty/garbled**  →  Ensure the video actually contains readable text at the snapshot interval; try `--interval 15` for more frames or specify the right `--lang` codes.

## Usage Examples
```
# Generate snapshots + OCR them in one go (default 30-s cadence)
python video_ocr.py --video lecture.mp4 --snapshots --ocr

# Already have snapshots? Just OCR them (English + Spanish recognition)
python video_ocr.py --video lecture.mp4 --ocr --lang eng+spa
```

## License
MIT License - © Sami Safadi
