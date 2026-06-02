#!/usr/bin/env python3
"""
main.py — Lecture Processing Pipeline Orchestrator

This script provides an interactive prompt asking the user for a directory of lectures,
and then runs video_ocr.py (to extract frames and run OCR) and slides_to_pptx.py (to compile
the slides and text into a polished widescreen PowerPoint) back to back.
"""

import sys
import time
import subprocess
from pathlib import Path

# ANSI colors for beautiful terminal output
BOLD = "\033[1m"
GREEN = "\033[32m"
BLUE = "\033[34m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"

def print_header(title: str):
    width = 65
    print(f"\n{CYAN}{'=' * width}{RESET}")
    print(f"{BOLD}{CYAN}{title.center(width)}{RESET}")
    print(f"{CYAN}{'=' * width}{RESET}\n")

def print_success(message: str):
    print(f"\n{GREEN}{BOLD}✔ {message}{RESET}\n")

def print_warning(message: str):
    print(f"\n{YELLOW}{BOLD}⚠ {message}{RESET}\n")

def print_error(message: str):
    print(f"\n{RED}{BOLD}✘ {message}{RESET}\n")

def main():
    print_header("Lecture Video to Widescreen Slides OCR & Presentation Orchestrator")
    
    print(f"{BOLD}Welcome to the Lecture Processing Pipeline!{RESET}")
    print("This pipeline will process your lecture videos back-to-back in two steps:")
    print(f"  1. {CYAN}video_ocr.py{RESET} — Extracts slide snapshots and performs OCR.")
    print(f"  2. {CYAN}slides_to_pptx.py{RESET} — Cleans OCR text, deduplicates, and creates premium slides.")
    print("-" * 65)

    # Interactive input prompt
    while True:
        try:
            user_input = input(f"\n{BOLD}Enter the directory of your lectures (e.g. ~/lectures or .): {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting pipeline.")
            sys.exit(0)

        if not user_input:
            print_warning("No directory entered. Please enter a valid path.")
            continue

        # Path resolution and expansion
        target_dir = Path(user_input).expanduser().resolve()
        
        if not target_dir.exists():
            print_error(f"The directory does not exist: {target_dir}")
            continue
            
        if not target_dir.is_dir():
            print_error(f"The path entered is not a directory: {target_dir}")
            continue
            
        break

    print(f"\n{GREEN}{BOLD}→ Target Directory Confirmed:{RESET} {target_dir}")
    print(f"{YELLOW}Proceeding to execute pipeline steps back-to-back...{RESET}\n")
    
    # Locate scripts relative to main.py to handle different working directories robustly
    script_dir = Path(__file__).parent.resolve()
    video_ocr_script = script_dir / "video_ocr.py"
    slides_to_pptx_script = script_dir / "slides_to_pptx.py"
    
    # Verify the internal scripts exist
    if not video_ocr_script.exists():
        print_error(f"Required script missing: {video_ocr_script}")
        sys.exit(1)
    if not slides_to_pptx_script.exists():
        print_error(f"Required script missing: {slides_to_pptx_script}")
        sys.exit(1)

    start_total_time = time.time()

    # Step 1: Video OCR
    print_header("Step 1: Extracting Snapshots & OCR-ing Lecture Videos")
    print(f"{BOLD}Command:{RESET} {sys.executable} {video_ocr_script.name} --dir \"{target_dir}\" --snapshots --ocr\n")
    
    step1_start = time.time()
    try:
        # Run Step 1 subprocess
        subprocess.run(
            [sys.executable, str(video_ocr_script), "--dir", str(target_dir), "--snapshots", "--ocr"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print_error(f"Step 1 (Video OCR) failed with exit code {e.returncode}.")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print_error("Pipeline interrupted by user.")
        sys.exit(1)
        
    step1_duration = time.time() - step1_start
    print_success(f"Step 1 completed successfully in {step1_duration:.2f} seconds!")

    # Step 2: Compile Presentation
    print_header("Step 2: Compiling Premium Widescreen PPTX Presentations")
    print(f"{BOLD}Command:{RESET} {sys.executable} {slides_to_pptx_script.name} --dir \"{target_dir}\"\n")
    
    step2_start = time.time()
    try:
        # Run Step 2 subprocess
        subprocess.run(
            [sys.executable, str(slides_to_pptx_script), "--dir", str(target_dir)],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print_error(f"Step 2 (Presentation Compilation) failed with exit code {e.returncode}.")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print_error("Pipeline interrupted by user.")
        sys.exit(1)

    step2_duration = time.time() - step2_start
    total_duration = time.time() - start_total_time

    print_success(f"Step 2 completed successfully in {step2_duration:.2f} seconds!")

    # Final summary
    print_header("Pipeline Summary")
    print(f"{BOLD}{GREEN}All steps completed successfully!{RESET}")
    print(f"  • {BOLD}Target Directory:{RESET} {target_dir}")
    print(f"  • {BOLD}Step 1 Duration (OCR):{RESET} {step1_duration:.2f} seconds")
    print(f"  • {BOLD}Step 2 Duration (PPTX):{RESET} {step2_duration:.2f} seconds")
    print(f"  • {BOLD}Total Execution Time:{RESET} {total_duration:.2f} seconds")
    print(f"{CYAN}{'=' * 65}{RESET}\n")

if __name__ == "__main__":
    main()
