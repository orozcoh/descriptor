#!/usr/bin/env python3
"""
Frame Extractor Script
Extracts frames from video files using FFmpeg.

Usage:
    python3 frame-extractor <directory_path>
    python3 frame-extractor ./
    python3 frame-extractor ./content/2026/26-week-1-2
"""

import os
import sys
import subprocess
import argparse
import re
from pathlib import Path

# ANSI escape codes for terminal control
CLEAR_LINE = '\033[K'  # Clear from cursor to end of line
CURSOR_UP = '\033[1A'   # Move cursor up one line
CURSOR_DOWN = '\033[1B' # Move cursor down one line

# Supported video extensions
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.m4v', '.wmv'}

# Target resolution for downscaling
TARGET_WIDTH = 1280
TARGET_HEIGHT = 720


def find_video_files(directory: str) -> list:
    """Recursively find all video files in the given directory."""
    video_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in VIDEO_EXTENSIONS:
                video_files.append(os.path.join(root, file))
    
    return sorted(video_files)


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using FFprobe."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"  Warning: Could not determine duration for {video_path}: {e}")
        return 0


def extract_frames(video_path: str, interval: float = 1.0, verbose: bool = False) -> int:
    """
    Extract frames from a video file using FFmpeg.
    
    Args:
        video_path: Path to the video file
        interval: Time interval between frames in seconds (default: 1.0)
        verbose: Whether to print detailed output
    
    Returns:
        Number of frames extracted, or 0 if failed
    """
    video_dir = os.path.dirname(video_path)
    video_name = Path(video_path).stem
    
    # Create frames directory
    frames_dir = os.path.join(video_dir, 'frames')
    os.makedirs(frames_dir, exist_ok=True)
    
    # Get video duration
    duration = get_video_duration(video_path)
    if duration <= 0:
        if verbose:
            print(f"  Skipping {video_path} - could not determine duration")
        return 0
    
    # Output pattern for frames
    output_pattern = os.path.join(frames_dir, f'{video_name}_%04d.png')
    
    # FFmpeg command with 720p downscaling
    # Use fps filter to extract frames at specified interval
    # Scale to 720 height while maintaining aspect ratio, then pad to 1280x720 if needed
    fps_value = 1 if interval == 1.0 else 1/interval
    
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vf', f'fps={fps_value},scale=-2:720:flags=lanczos',
        '-q:v', '2',
        '-y',
        output_pattern
    ]
    
    try:
        if verbose:
            print(f"  Extracting frames to: {frames_dir}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Count extracted frames
        frame_count = len([f for f in os.listdir(frames_dir) if f.endswith('.png') and f.startswith(video_name)])
        if verbose:
            print(f"  Successfully extracted {frame_count} frames from {video_name}")
        return frame_count
        
    except subprocess.CalledProcessError as e:
        if verbose:
            print(f"  Error extracting frames from {video_path}:")
            print(f"  {e.stderr}")
        return 0


def print_progress_bar(current, total, bar_width=20):
    """Print a progress bar that updates in place."""
    if total == 0:
        return
    
    percent = (current / total) * 100
    filled_width = int(bar_width * current // total)
    bar = '█' * filled_width + '░' * (bar_width - filled_width)
    
    # Use \r to return cursor to beginning of line and \033[K to clear the rest of the line
    sys.stdout.write(f'\rProgress: {percent:3.0f}% [{bar}] {current}/{total} frames\033[K')
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(
        description='Extract frames from video files using FFmpeg.'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory containing video files (default: current directory)'
    )
    parser.add_argument(
        '-i', '--interval',
        type=float,
        default=1.0,
        help='Interval between frames in seconds (default: 1.0, use 0.5 for half-second)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    directory = os.path.abspath(args.directory)
    
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        sys.exit(1)
    
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a directory.")
        sys.exit(1)
    
    if args.verbose:
        print(f"Scanning for videos in: {directory}")
        print(f"Frame interval: {args.interval} seconds")
        print("-" * 50)
    
    video_files = find_video_files(directory)
    
    if not video_files:
        if args.verbose:
            print("No video files found.")
        else:
            print("No video files found.")
        sys.exit(0)
    
    if args.verbose:
        print(f"Found {len(video_files)} video file(s)\n")
    else:
        print(f"Found {len(video_files)} video file(s)")
    
    # Calculate total frames to be extracted (estimate based on duration)
    total_frames_estimate = 0
    for video_path in video_files:
        duration = get_video_duration(video_path)
        if duration > 0:
            estimated_frames = int(duration / args.interval)
            total_frames_estimate += estimated_frames
    
    success_count = 0
    total_extracted_frames = 0
    
    for i, video_path in enumerate(video_files, 1):
        if args.verbose:
            print(f"[{i}/{len(video_files)}] Processing: {os.path.basename(video_path)}")
        
        # Extract frames and get count
        video_dir = os.path.dirname(video_path)
        video_name = Path(video_path).stem
        frames_dir = os.path.join(video_dir, 'frames')
        
        frame_count = extract_frames(video_path, args.interval, args.verbose)
        if frame_count > 0:
            success_count += 1
            total_extracted_frames += frame_count
        
        if args.verbose:
            print()
        
        # Update progress bar
        if not args.verbose:
            print_progress_bar(total_extracted_frames, total_frames_estimate)
    
    if not args.verbose:
        # Clear the progress line and show final result
        sys.stdout.write('\r' + ' ' * 80 + '\r')  # Clear line
        sys.stdout.flush()
    
    if args.verbose:
        print("-" * 50)
    
    print(f"Completed: {success_count}/{len(video_files)} videos processed successfully")
    
    if success_count < len(video_files):
        sys.exit(1)


if __name__ == '__main__':
    main()
