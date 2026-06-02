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
Using standard `pip`:
```bash
pip install opencv-python pillow pytesseract python-pptx numpy
```

Or using `uv` (recommended):
```bash
# uv will automatically set up the environment and run scripts
uv run video_ocr.py ...
uv run slides_to_pptx.py ...
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

## Compiling Slides to PowerPoint (.pptx)

Once snapshots and OCR text files are generated via `video_ocr.py`, you can compile them into a highly polished, widescreen PowerPoint presentation (`.pptx`) using `slides_to_pptx.py`.

This tool automatically:
1. **Removes Redundancies**: Compares adjacent frames using **Mean Squared Error (MSE)** and collapses duplicate transition frames, keeping only the final fully-built states.
2. **Crops Canvas**: Extracts slide frames cleanly (removing the presenter's video feed and black letterbox bars).
3. **Applies Hybrid Layouts**: 
   - **Side-by-Side**: Places crisp native text on the left, and the cropped slide graphic on the right.
   - **Full Figure**: Centers large visual-only slides (such as system console layouts or medical diagrams) with custom titles.

### PowerPoint CLI Flags
```
  --video <file>        Compile slide deck for a single video file or OCR text file.
  --dir <path>          Batch-scan a folder to process ALL matching slide OCR outputs.
  --mse <float>         MSE threshold for duplicate slide detection (default: 50.0).
  --crop <left,t,r,b>   Custom crop coordinates for the slide canvas (default: 2,16,591,347).
```

### PowerPoint Usage Examples
```bash
# Compile a slide deck for a single video's snapshots & text
python slides_to_pptx.py --video lecture.mp4

# Batch-compile PowerPoint decks for ALL processed videos in a directory
python slides_to_pptx.py --dir ./lectures

# Compile with a lower duplicate sensitivity threshold
python slides_to_pptx.py --video lecture.mp4 --mse 25.0
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

