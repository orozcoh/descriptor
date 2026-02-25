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


def extract_frames(video_path: str, interval: float = 1.0) -> bool:
    """
    Extract frames from a video file using FFmpeg.
    
    Args:
        video_path: Path to the video file
        interval: Time interval between frames in seconds (default: 1.0)
    
    Returns:
        True if successful, False otherwise
    """
    video_dir = os.path.dirname(video_path)
    video_name = Path(video_path).stem
    
    # Create frames directory
    frames_dir = os.path.join(video_dir, 'frames')
    os.makedirs(frames_dir, exist_ok=True)
    
    # Get video duration
    duration = get_video_duration(video_path)
    if duration <= 0:
        print(f"  Skipping {video_path} - could not determine duration")
        return False
    
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
        print(f"  Extracting frames to: {frames_dir}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Count extracted frames
        frame_count = len([f for f in os.listdir(frames_dir) if f.endswith('.png') and f.startswith(video_name)])
        print(f"  Successfully extracted {frame_count} frames from {video_name}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  Error extracting frames from {video_path}:")
        print(f"  {e.stderr}")
        return False


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
    
    print(f"Scanning for videos in: {directory}")
    print(f"Frame interval: {args.interval} seconds")
    print("-" * 50)
    
    video_files = find_video_files(directory)
    
    if not video_files:
        print("No video files found.")
        sys.exit(0)
    
    print(f"Found {len(video_files)} video file(s)\n")
    
    success_count = 0
    for i, video_path in enumerate(video_files, 1):
        print(f"[{i}/{len(video_files)}] Processing: {os.path.basename(video_path)}")
        if extract_frames(video_path, args.interval):
            success_count += 1
        print()
    
    print("-" * 50)
    print(f"Completed: {success_count}/{len(video_files)} videos processed successfully")
    
    if success_count < len(video_files):
        sys.exit(1)


if __name__ == '__main__':
    main()
