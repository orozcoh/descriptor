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
from scripts.describeAI import load_model_and_prompt, process_video_frames


def run_command(cmd, description, cwd=None):
    """Run a command and return success status with status updates."""
    print(f"Running: {description}")
    start_time = time.time()
    try:
        # Run the command and show output in real-time
        result = subprocess.run(cmd, shell=True, check=True, 
                              text=True, cwd=cwd)
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


def run_command_silent(cmd, description, cwd=None):
    """Run a command silently and return success status with status updates."""
    print(f"Running: {description}")
    start_time = time.time()
    try:
        # Run the command with output suppressed
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True, cwd=cwd)
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
    project_root = os.path.dirname(os.path.abspath(__file__))
    
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
    success = run_command(f'python3 scripts/frame-extractor.py "{directory}"', "Frame extraction", cwd=project_root)
    if not success:
        print("Pipeline stopped due to frame extraction failure.")
        sys.exit(1)
    
    # Step 2: Extract scenes
    print("\n2/5 - Extracting scene changes from videos...")
    success = run_command(f'python3 scripts/scene-extractor.py "{directory}"', "Scene extraction", cwd=project_root)
    if not success:
        print("Warning: Scene extraction failed, but continuing pipeline...")
    
    # Step 3: Generate descriptions
    print("\n3/5 - Generating AI descriptions for frames...")
    video_folders = find_video_folders(directory)
    
    if not video_folders:
        print("No video folders found for description generation.")
        descriptions_success = True
    else:
        # Load model once for all folders
        model, processor, prompt = load_model_and_prompt(verbose=False)
        
        descriptions_success = True
        total_folders = len(video_folders)
        for i, folder_path in enumerate(video_folders, 1):
            print(f"  Processing folder {i}/{total_folders}: {folder_path.name}")
            folder_start = time.time()
            success = process_video_frames(folder_path, model, processor, prompt, verbose=False)
            folder_elapsed = time.time() - folder_start
            if success:
                print(f"  ✓ Description generation for {folder_path.name} completed successfully ({folder_elapsed:.1f}s)")
            else:
                descriptions_success = False
                print(f"  ✗ Description generation for {folder_path.name} failed ({folder_elapsed:.1f}s)")
    
    if not descriptions_success:
        print("Pipeline stopped due to description generation failure.")
        sys.exit(1)
    
    # Step 4: Group descriptions
    print("\n4/5 - Grouping similar descriptions...")
    success = run_command(f'python3 scripts/des-group.py "{directory}"', "Description grouping", cwd=project_root)
    if not success:
        print("Pipeline stopped due to description grouping failure.")
        sys.exit(1)
    
    # Step 5: Clean up temporary files
    print("\n5/5 - Cleaning up temporary files...")
    
    # Run clear-files.py to delete frames and .description.json files, keeping .descriptions.json
    success = run_command(f'python3 scripts/clear-files.py "{directory}"', "Cleanup temp files", cwd=project_root)
    if not success:
        print("Warning: Failed to clean up .description.json files")
    
    print("\n" + "=" * 60)
    print("✓ Pipeline completed successfully!")
    print("Final output: *.descriptions.json files with grouped descriptions and scene data")
    print("=" * 60)


if __name__ == "__main__":
    main()