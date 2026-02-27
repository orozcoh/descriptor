#!/usr/bin/env python3
"""
Semantic Description Grouping Script

This script processes video description JSON files and groups consecutive similar descriptions
into time ranges using semantic similarity analysis. It reads individual video description files
and outputs grouped descriptions in a timeline format.

Usage:
    python des-group.py [input_directory] [--threshold THRESHOLD]

Example:
    python des-group.py content/2026/26-week-1-2 --threshold 0.8
"""

import json
import argparse
import time
import sys
import os
from pathlib import Path
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional

# ANSI escape codes for terminal control
CLEAR_LINE = '\033[K'  # Clear from cursor to end of line
CURSOR_UP = '\033[1A'   # Move cursor up one line
CURSOR_DOWN = '\033[1B' # Move cursor down one line


def are_similar(a: str, b: str, threshold: float = 0.75) -> bool:
    """
    Determine if two descriptions are semantically similar.
    
    Uses SequenceMatcher to calculate similarity ratio between two strings.
    Returns True if the similarity ratio exceeds the specified threshold.
    
    Args:
        a (str): First description string
        b (str): Second description string  
        threshold (float): Similarity threshold (0.0 to 1.0). Default: 0.8 (80%)
    
    Returns:
        bool: True if descriptions are similar enough, False otherwise
    """
    return SequenceMatcher(None, a, b).ratio() > threshold


def format_time_range(start_time: str, end_time: str) -> str:
    """
    Format two timestamps into a time range string.
    
    Args:
        start_time (str): Starting timestamp in [HHH:MM:SS] format
        end_time (str): Ending timestamp in [HHH:MM:SS] format
    
    Returns:
        str: Formatted time range string
    """
    return f"{start_time} - {end_time}"


def convert_timestamp_format(timestamp: str) -> str:
    """
    Convert timestamp from [HHH:MM:SS] format to HH:MM:SS.mmm format.
    If already in HH:MM:SS.mmm format, return as-is.
    
    Args:
        timestamp (str): Timestamp in [HHH:MM:SS] or HH:MM:SS.mmm format
    
    Returns:
        str: Timestamp in HH:MM:SS.mmm format
    """
    # If already in HH:MM:SS.mmm format, return as-is
    if '.' in timestamp and ':' in timestamp:
        return timestamp
    
    # Remove brackets and split by colon
    clean_timestamp = timestamp.strip('[]')
    parts = clean_timestamp.split(':')
    
    if len(parts) == 3:
        hours, minutes, seconds = parts
        # Convert to HH:MM:SS.mmm format (add .000 for milliseconds)
        return f"{hours.zfill(2)}:{minutes.zfill(2)}:{seconds.zfill(2)}.000"
    else:
        # Return original if format is unexpected
        return timestamp


def collapse_noisy_json(json_data: Dict[str, str], threshold: float = 0.8) -> List[Dict[str, str]]:
    """
    Group consecutive similar descriptions into time ranges.
    
    Processes a dictionary of timestamped descriptions and groups consecutive
    descriptions that are semantically similar into time ranges.
    
    Args:
        json_data (Dict[str, str]): Dictionary with timestamps as keys and descriptions as values
        threshold (float): Similarity threshold for grouping (0.0 to 1.0). Default: 0.8
    
    Returns:
        List[Dict[str, str]]: List of grouped timeline entries in format:
            [{"start_time": "HH:MM:SS.mmm", "end_time": "HH:MM:SS.mmm", "description": "text"}]
    """
    # Sort timestamps chronologically
    sorted_times = sorted(json_data.keys())
    if not sorted_times:
        return []
    
    timeline = []
    # Start with the first timestamp and description
    start_time = sorted_times[0]
    anchor_desc = json_data[start_time]
    last_time = start_time
    
    # Process each subsequent timestamp
    for i in range(1, len(sorted_times)):
        current_time = sorted_times[i]
        current_desc = json_data[current_time]
        
        # Compare current description to the anchor description of current block
        if are_similar(anchor_desc, current_desc, threshold):
            # Descriptions are similar, extend the current time range
            last_time = current_time
        else:
            # Descriptions are different enough, finalize current block and start new one
            start_formatted = convert_timestamp_format(start_time)
            end_formatted = convert_timestamp_format(last_time)
            timeline.append({
                "start_time": start_formatted,
                "end_time": end_formatted,
                "description": anchor_desc
            })
            
            # Start new block with current timestamp and description
            start_time = current_time
            anchor_desc = current_desc
            last_time = current_time
    
    # Add the final time block
    start_formatted = convert_timestamp_format(start_time)
    end_formatted = convert_timestamp_format(last_time)
    timeline.append({
        "start_time": start_formatted,
        "end_time": end_formatted,
        "description": anchor_desc
    })
    
    return timeline


def is_video_description_file(file_path: Path) -> bool:
    """
    Check if a file is an individual video description file (not a folder summary).
    
    Folder summary files have the pattern "folder-name.description.json"
    
    Args:
        file_path (Path): Path to the JSON file
    
    Returns:
        bool: True if it's an individual video description file, False if folder summary
    """
    filename = file_path.stem
    folder_name = file_path.parent.name
    # Skip folder summary files
    if filename == f"{folder_name}.description":
        return False
    # Accept all other *.description.json files (individual videos)
    return True


def load_scene_data(video_path: Path) -> Optional[Dict]:
    """
    Load scene data from the corresponding .scene.json file.
    
    Args:
        video_path (Path): Path to the video file (used to find corresponding scene file)
    
    Returns:
        Optional[Dict]: Scene data if found, None if file doesn't exist or can't be loaded
    """
    # Create scene file path with same base name as video
    # Remove .description from the stem if it exists to get the correct video name
    video_stem = video_path.stem
    if video_stem.endswith('.description'):
        video_stem = video_stem.replace('.description', '')
    scene_filename = video_stem + '.scene.json'
    scene_path = video_path.parent / scene_filename
    
    
    if not scene_path.exists():
        return None
    
    try:
        with open(scene_path, 'r', encoding='utf-8') as f:
            scene_data = json.load(f)
        return scene_data
    except Exception as e:
        print(f"  Warning: Could not load scene data from {scene_filename}: {e}")
        return None


def print_progress_bar(current, total, bar_width=20):
    """Print a progress bar that updates in place."""
    if total == 0:
        return
    
    percent = (current / total) * 100
    filled_width = int(bar_width * current // total)
    bar = '█' * filled_width + '░' * (bar_width - filled_width)
    
    # Use \r to return cursor to beginning of line and \033[K to clear the rest of the line
    sys.stdout.write(f'\rProgress: {percent:3.0f}% [{bar}] {current}/{total} files\033[K')
    sys.stdout.flush()


def process_description_file(file_path: Path, threshold: float = 0.8, verbose: bool = False) -> Optional[Path]:
    """
    Process a single description JSON file and create grouped output with merged scene data.
    
    Args:
        file_path (Path): Path to the input description JSON file
        threshold (float): Similarity threshold for grouping
        verbose (bool): Whether to print detailed output
    
    Returns:
        Optional[Path]: Path to the created output file, or None if processing failed
    """
    try:
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract descriptions from the JSON structure
        # Handle both direct description dictionaries and nested structures
        if isinstance(data, dict):
            if 'videos' in data and len(data['videos']) == 1:
                # Extract from nested structure: {"videos": {"VID_xxx": {...}}}
                video_key = list(data['videos'].keys())[0]
                descriptions = data['videos'][video_key]
            elif any(key.startswith('000:') for key in data.keys()):
                # Direct description dictionary: {"000:00:00.000": "description", ...}
                descriptions = data
            else:
                if verbose:
                    print(f"  Warning: Unknown JSON structure in {file_path.name}, skipping")
                return None
        else:
            if verbose:
                print(f"  Warning: Invalid JSON structure in {file_path.name}, skipping")
            return None
        
        # Group the descriptions using semantic similarity
        grouped_timeline = collapse_noisy_json(descriptions, threshold)
        
        # Load corresponding scene data
        scene_data = load_scene_data(file_path)
        
        # If no scene data exists, skip this file (as requested)
        if scene_data is None:
            if verbose:
                print(f"  Skipping {file_path.name} - no corresponding scene file found")
            return None
        
        # Create the merged output structure
        merged_output = {
            "timestamps": grouped_timeline,
            "scenes-info": {
                "scene_threshold": scene_data.get("scene_threshold", 0.4),
                "total_scenes": scene_data.get("total_scenes", 0),
                "scenes": scene_data.get("scenes", [])
            }
        }
        
        # Create output file path with .descriptions.json extension
        # Remove .description from the filename before adding .descriptions.json
        output_filename = file_path.stem.replace('.description', '') + '.descriptions.json'
        output_path = file_path.parent / output_filename
        
        # Save the merged output to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_output, f, indent=2, ensure_ascii=False)
        
        if verbose:
            print(f"  ✓ Created: {output_path.name} (with scene data)")
        return output_path
        
    except json.JSONDecodeError as e:
        if verbose:
            print(f"  Error: Invalid JSON in {file_path.name}: {e}")
        return None
    except Exception as e:
        if verbose:
            print(f"  Error processing {file_path.name}: {e}")
        return None


def find_description_files(directory: Path) -> List[Path]:
    """
    Find all individual video description files in a directory.
    
    Args:
        directory (Path): Directory to search for description files
    
    Returns:
        List[Path]: List of paths to individual video description files
    """
    description_files = []
    
    # Find all .description.json files
    for file_path in directory.rglob("*.description.json"):
        if is_video_description_file(file_path):
            description_files.append(file_path)
    
    return description_files


def create_folder_summary(folder: Path, video_jsons: dict):
    """
    Create a folder summary JSON file from video descriptions.
    
    Args:
        folder (Path): Path to the folder containing the videos
        video_jsons (dict): Dictionary of video descriptions
    """
    summary = {"folder": folder.name, "videos": video_jsons}
    summary_path = folder / f"{folder.name}.description.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nFolder summary saved: {summary_path}")


def create_folder_descriptions_summary(folder: Path, grouped_descriptions: dict, verbose: bool = False):
    """
    Create a folder summary JSON file from grouped video descriptions.
    
    Args:
        folder (Path): Path to the folder containing the videos
        grouped_descriptions (dict): Dictionary of grouped video descriptions
    """
    summary = {"folder": folder.name, "videos": grouped_descriptions}
    summary_path = folder / f"{folder.name}.descriptions.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    if verbose:
        print(f"\nFolder descriptions summary saved: {summary_path}")


def create_local_summaries(root_dir: Path, verbose: bool = False):
    """
    Create per-folder .descriptions.json summaries for folders containing individual video descriptions.
    """
    for root, dirs, files in os.walk(root_dir):
        folder_path = Path(root)
        folder_name = folder_path.name
        
        # Find local individual *.descriptions.json (exclude summaries)
        summary_files = [
            f for f in files 
            if f.endswith('.descriptions.json') and f != f'{folder_name}.descriptions.json'
        ]
        
        if summary_files:
            local_grouped = {}
            for sum_file in summary_files:
                sum_path = folder_path / sum_file
                video_stem = sum_file.replace('.descriptions.json', '')
                try:
                    with open(sum_path, 'r', encoding='utf-8') as f:
                        local_grouped[video_stem] = json.load(f)
                except Exception as e:
                    if verbose:
                        print(f"  Warning: Could not load {sum_file} for summary: {e}")
            
            if local_grouped:
                summary_path = folder_path / f'{folder_name}.descriptions.json'
                summary = {"folder": folder_name, "videos": local_grouped}
                with open(summary_path, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
                
                if verbose:
                    print(f"  Created local summary for {folder_path.name}: {summary_path.name} ({len(local_grouped)} videos)")


def main():
    """
    Main function to process description files and create grouped outputs.
    
    Parses command line arguments, finds description files, processes them,
    and displays execution statistics.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Group similar video descriptions into time ranges using semantic similarity."
    )
    parser.add_argument(
        "input_directory",
        nargs="?",
        default="content",
        help="Directory containing description JSON files (default: content)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Similarity threshold for grouping (0.0 to 1.0, default: 0.8)"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate threshold value
    if not 0.0 <= args.threshold <= 1.0:
        print("Error: Threshold must be between 0.0 and 1.0")
        sys.exit(1)
    
    input_dir = Path(args.input_directory)
    
    # Validate input directory
    if not input_dir.exists():
        print(f"Error: Directory '{input_dir}' does not exist")
        sys.exit(1)
    
    if not input_dir.is_dir():
        print(f"Error: '{input_dir}' is not a directory")
        sys.exit(1)
    
    if args.verbose:
        print(f"Processing description files in: {input_dir}")
        print(f"Similarity threshold: {args.threshold * 100}%")
        print("-" * 50)
    
    # Record start time for performance measurement
    start_time = time.perf_counter()
    
    # Find all individual video description files
    description_files = find_description_files(input_dir)
    
    if not description_files:
        print(f"No individual video description files found in {input_dir}")
        print("Make sure there are *.description.json files from describeAI.py")
        sys.exit(0)
    
    if args.verbose:
        print(f"Found {len(description_files)} video description files")
        print()
    
    # Process each description file
    processed_count = 0
    failed_count = 0
    grouped_descriptions = {}
    
    for i, file_path in enumerate(sorted(description_files), 1):
        if args.verbose:
            print(f"Processing: {file_path.name}")
        
        result = process_description_file(file_path, args.threshold, args.verbose)
        if result:
            processed_count += 1
            # Extract video stem from the output filename for the summary
            video_stem = result.stem.replace('.descriptions', '')
            # Read the grouped descriptions to include in folder summary
            try:
                with open(result, 'r', encoding='utf-8') as f:
                    grouped_descriptions[video_stem] = json.load(f)
            except Exception as e:
                if args.verbose:
                    print(f"  Warning: Could not read grouped descriptions for summary: {e}")
        else:
            failed_count += 1
        
        # Update progress bar in quiet mode
        if not args.verbose:
            print_progress_bar(i, len(description_files))
    
    # Clear the progress line and show final result
    if not args.verbose:
        sys.stdout.write('\r' + ' ' * 80 + '\r')  # Clear line
        sys.stdout.flush()
    
    # Create top-level folder summary if we have any successful processing
    if processed_count > 0:
        if args.verbose:
            print("Creating top-level summary...")
        create_folder_descriptions_summary(input_dir, grouped_descriptions, args.verbose)
        
        # Create local summaries for all folders
        if args.verbose:
            print("Creating per-folder summaries...")
        create_local_summaries(input_dir, args.verbose)
    
    # Calculate and display execution time
    end_time = time.perf_counter()
    total_time = end_time - start_time
    
    if args.verbose:
        print("=" * 50)
        print(f"Processing complete!")
        print(f"Files processed: {processed_count}")
        print(f"Files failed: {failed_count}")
        print(f"Total execution time: {total_time:.2f} seconds")
        
        if processed_count > 0:
            avg_time = total_time / processed_count
            print(f"Average time per file: {avg_time:.2f} seconds")
    else:
        print(f"Processing complete! {processed_count} files processed in {total_time:.2f} seconds")


if __name__ == "__main__":
    main()