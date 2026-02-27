#!/usr/bin/env python3
"""
Video Processing Pipeline Script

Runs the complete video processing workflow:
1. frame-extractor.py - Extract frames from videos
2. describeAI.py - Generate AI descriptions for frames  
3. des-group.py - Group similar descriptions
4. clear-files.py - Clean up temporary files

Usage:
    python descriptor.py [directory_path]

Example:
    python descriptor.py content/2026/26-week-1-2
    python descriptor.py ./
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status with status updates."""
    print(f"Running: {description}")
    start_time = time.time()
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True)
        elapsed_time = time.time() - start_time
        print(f"✓ {description} completed successfully ({elapsed_time:.1f}s)")
        return True
    except subprocess.CalledProcessError as e:
        elapsed_time = time.time() - start_time
        print(f"✗ {description} failed ({elapsed_time:.1f}s)")
        print(f"Error: {e.stderr}")
        return False
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"✗ {description} failed with exception: {e} ({elapsed_time:.1f}s)")
        return False


def find_video_folders(directory):
    """Find all folders containing video files that would have frames extracted."""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.m4v', '.wmv'}
    video_folders = set()
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if Path(file).suffix.lower() in video_extensions:
                video_folders.add(Path(root))
                break
    
    return sorted(list(video_folders))


def main():
    parser = argparse.ArgumentParser(
        description="Run complete video processing pipeline."
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory containing video files (default: current directory)'
    )
    
    args = parser.parse_args()
    directory = os.path.abspath(args.directory)
    
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)
    
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a directory.")
        sys.exit(1)
    
    print(f"Starting video processing pipeline in: {directory}")
    print("=" * 60)
    
    # Step 1: Extract frames
    print("\n1/5 - Extracting frames from videos...")
    success = run_command(f"python3 frame-extractor.py {directory}", "Frame extraction")
    if not success:
        print("Pipeline stopped due to frame extraction failure.")
        sys.exit(1)
    
    # Step 2: Extract scenes
    print("\n2/5 - Extracting scene changes from videos...")
    success = run_command(f"python3 scene-extractor.py {directory}", "Scene extraction")
    if not success:
        print("Warning: Scene extraction failed, but continuing pipeline...")
    
    # Step 3: Generate descriptions
    print("\n3/5 - Generating AI descriptions for frames...")
    video_folders = find_video_folders(directory)
    
    if not video_folders:
        print("No video folders found for description generation.")
        descriptions_success = True
    else:
        descriptions_success = True
        for i, folder in enumerate(video_folders, 1):
            print(f"  Processing folder {i}/{len(video_folders)}: {folder.name}")
            success = run_command(f"python3 describeAI.py {folder}", f"Description generation for {folder.name}")
            if not success:
                descriptions_success = False
                print(f"  Warning: Failed to process {folder.name}")
    
    if not descriptions_success:
        print("Pipeline stopped due to description generation failure.")
        sys.exit(1)
    
    # Step 4: Group descriptions
    print("\n4/5 - Grouping similar descriptions...")
    success = run_command(f"python3 des-group.py {directory}", "Description grouping")
    if not success:
        print("Pipeline stopped due to description grouping failure.")
        sys.exit(1)
    
    # Step 5: Clean up temporary files
    print("\n5/5 - Cleaning up temporary files...")
    print("  Keeping: *.descriptions.json files")
    print("  Deleting: frames folders and *.description.json files\n")
    
    # Run clear-files.py to delete frames and .description.json files, keeping .descriptions.json
    success = run_command(f"python3 clear-files.py description {directory}", "Cleanup - removing .description.json files")
    if not success:
        print("Warning: Failed to clean up .description.json files")
    
    # Delete frames directories
    success = run_command(f"python3 clear-files.py frames {directory}", "Cleanup - removing frames directories")
    if not success:
        print("Warning: Failed to clean up frames directories")

    # Delete scenes 
    success = run_command(f"python3 clear-files.py scenes {directory}", "Cleanup - removing *.scene.json files ")
    if not success:
        print("Warning: Failed to clean up *.scene.json files")
    
    print("\n" + "=" * 60)
    print("✓ Pipeline completed successfully!")
    print("Final output: *.descriptions.json files with grouped descriptions and scene data")
    print("=" * 60)


if __name__ == "__main__":
    main()