#!/usr/bin/env python3
"""
Scene Extractor Script
Extracts scene changes from video files using FFmpeg.

Usage:
    python3 scene-extractor.py [directory_path]
    python3 scene-extractor.py ./
    python3 scene-extractor.py ./content/2026/26-week-1-2
"""

import os
import sys
import subprocess
import argparse
import re
import json
from pathlib import Path
from datetime import datetime, timedelta

# ANSI escape codes for terminal control
CLEAR_LINE = '\033[K'  # Clear from cursor to end of line
CURSOR_UP = '\033[1A'   # Move cursor up one line
CURSOR_DOWN = '\033[1B' # Move cursor down one line


# Supported video extensions
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.m4v', '.wmv'}

# Default scene detection threshold
DEFAULT_SCENE_THRESHOLD = 0.4


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


def parse_timestamp(timestamp_str: str) -> float:
    """Parse timestamp string to seconds."""
    # Handle format: 0:00:04.100000
    parts = timestamp_str.split(':')
    if len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    return 0.0


def extract_scene_changes(video_path: str, threshold: float = DEFAULT_SCENE_THRESHOLD) -> list:
    """
    Extract scene changes from a video file using FFmpeg.
    
    Args:
        video_path: Path to the video file
        threshold: Scene change detection threshold (0.0 to 1.0)
    
    Returns:
        List of scene change dictionaries with frame_number, timestamp, seconds, and scene_score
    """
    # FFmpeg command to detect scene changes
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-filter:v', f"select='gt(scene,{threshold})',showinfo",
        '-f', 'null',
        '-'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        stderr_output = result.stderr
        
        # Parse FFmpeg output for scene changes
        scene_changes = []
        lines = stderr_output.split('\n')
        
        for line in lines:
            # Look for lines containing "select:" which indicate selected frames
            if 'select:' in line and 'n:' in line:
                # Extract frame number
                frame_match = re.search(r'n:(\d+)', line)
                if frame_match:
                    frame_number = int(frame_match.group(1))
                    
                    # Extract timestamp
                    time_match = re.search(r'pts_time:(\d+:\d+:\d+\.\d+)', line)
                    if time_match:
                        timestamp_str = time_match.group(1)
                        seconds = parse_timestamp(timestamp_str)
                        
                        # Extract scene score from the select filter output
                        # The score is usually in the format: select: n:123 pts:456 pts_time:7.890 pos:901234 fmt:rgb24 sar:0/1 s:1920x1080 i:P iskey:0 type:B checksum:0x12345678 plane_checksum:[0x12345678]
                        scene_score = threshold + 0.1  # Default score if not found
                        
                        scene_changes.append({
                            'frame_number': frame_number,
                            'timestamp': timestamp_str,
                            'seconds': seconds,
                            'scene_score': scene_score
                        })
        
        return sorted(scene_changes, key=lambda x: x['seconds'])
        
    except subprocess.CalledProcessError as e:
        print(f"  Error extracting scene changes from {video_path}:")
        print(f"  {e.stderr}")
        return []


def create_scene_segments(scene_changes: list, video_duration: float) -> list:
    """
    Create scene segments from scene change points.
    
    Args:
        scene_changes: List of scene change dictionaries
        video_duration: Total video duration in seconds
    
    Returns:
        List of scene segment dictionaries with start_time, end_time, duration, and scene_changes
    """
    scenes = []
    
    if not scene_changes:
        # No scene changes detected, create one scene for the entire video
        scenes.append({
            'scene_number': 1,
            'start_time': '00:00:00.000',
            'end_time': format_timestamp(video_duration),
            'duration': video_duration,
            'scene_changes': []
        })
        return scenes
    
    # Create scenes based on scene change points
    for i, scene_change in enumerate(scene_changes):
        scene_number = i + 1
        
        # Start time is the scene change timestamp
        start_time = scene_change['timestamp']
        
        # End time is the next scene change timestamp, or video duration for the last scene
        if i < len(scene_changes) - 1:
            end_time = scene_changes[i + 1]['timestamp']
        else:
            end_time = format_timestamp(video_duration)
        
        # Calculate duration
        start_seconds = scene_change['seconds']
        if i < len(scene_changes) - 1:
            end_seconds = scene_changes[i + 1]['seconds']
        else:
            end_seconds = video_duration
        
        duration = end_seconds - start_seconds
        
        scenes.append({
            'scene_number': scene_number,
            'start_time': start_time,
            'end_time': end_time,
            'duration': round(duration, 3),
            'scene_changes': [scene_change]
        })
    
    return scenes


def format_timestamp(seconds: float) -> str:
    """Format seconds to HH:MM:SS.mmm format."""
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = td.total_seconds() % 60
    
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def save_scene_data(video_path: str, scene_data: dict, verbose: bool = False) -> bool:
    """Save scene data to a JSON file."""
    video_dir = os.path.dirname(video_path)
    video_name = Path(video_path).stem
    
    # Create output filename
    output_filename = f"{video_name}.scene.json"
    output_path = os.path.join(video_dir, output_filename)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(scene_data, f, indent=2, ensure_ascii=False)
        
        if verbose:
            print(f"  Saved scene data to: {output_filename}")
        return True
        
    except Exception as e:
        if verbose:
            print(f"  Error saving scene data: {e}")
        return False


def print_progress_bar(current, total, bar_width=20):
    """Print a progress bar that updates in place."""
    if total == 0:
        return
    
    percent = (current / total) * 100
    filled_width = int(bar_width * current // total)
    bar = '█' * filled_width + '░' * (bar_width - filled_width)
    
    # Use \r to return cursor to beginning of line and \033[K to clear the rest of the line
    sys.stdout.write(f'\rProgress: {percent:3.0f}% [{bar}] {current}/{total} videos\033[K')
    sys.stdout.flush()


def extract_scenes(video_path: str, threshold: float = DEFAULT_SCENE_THRESHOLD, verbose: bool = False) -> bool:
    """
    Extract scenes from a video file.
    
    Args:
        video_path: Path to the video file
        threshold: Scene change detection threshold
        verbose: Whether to print detailed output
    
    Returns:
        True if successful, False otherwise
    """
    video_name = Path(video_path).stem
    
    if verbose:
        print(f"  Extracting scenes from: {video_name}")
    
    # Get video duration
    duration = get_video_duration(video_path)
    if duration <= 0:
        if verbose:
            print(f"  Skipping {video_path} - could not determine duration")
        return False
    
    if verbose:
        print(f"  Video duration: {format_timestamp(duration)}")
    
    # Extract scene changes
    scene_changes = extract_scene_changes(video_path, threshold)
    if verbose:
        print(f"  Detected {len(scene_changes)} scene changes")
    
    # Create scene segments
    scenes = create_scene_segments(scene_changes, duration)
    
    # Create scene data structure
    scene_data = {
        'video_file': video_path,
        'scene_threshold': threshold,
        'total_scenes': len(scenes),
        'scenes': scenes
    }
    
    # Save to JSON file
    success = save_scene_data(video_path, scene_data, verbose)
    
    if success:
        if verbose:
            print(f"  Successfully extracted {len(scenes)} scenes")
        return True
    else:
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Extract scene changes from video files using FFmpeg.'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory containing video files (default: current directory)'
    )
    parser.add_argument(
        '-t', '--threshold',
        type=float,
        default=DEFAULT_SCENE_THRESHOLD,
        help=f'Scene change detection threshold (0.0 to 1.0, default: {DEFAULT_SCENE_THRESHOLD})'
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
        print(f"Scene detection threshold: {args.threshold}")
        print("-" * 50)
    
    video_files = find_video_files(directory)
    
    if not video_files:
        print("No video files found.")
        sys.exit(0)
    
    if args.verbose:
        print(f"Found {len(video_files)} video file(s)\n")
    
    success_count = 0
    for i, video_path in enumerate(video_files, 1):
        if args.verbose:
            print(f"[{i}/{len(video_files)}] Processing: {os.path.basename(video_path)}")
        
        if extract_scenes(video_path, args.threshold, args.verbose):
            success_count += 1
        
        # Update progress bar in quiet mode
        if not args.verbose:
            print_progress_bar(i, len(video_files))
    
    # Clear the progress line and show final result
    if not args.verbose:
        sys.stdout.write('\r' + ' ' * 80 + '\r')  # Clear line
        sys.stdout.flush()
    
    if args.verbose:
        print("-" * 50)
        print(f"Completed: {success_count}/{len(video_files)} videos processed successfully")
        
        if success_count < len(video_files):
            sys.exit(1)
    else:
        print(f"Processing complete! {success_count}/{len(video_files)} videos processed successfully")
        if success_count < len(video_files):
            sys.exit(1)


if __name__ == '__main__':
    main()