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
from pathlib import Path
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional


def are_similar(a: str, b: str, threshold: float = 0.6) -> bool:
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
    
    Folder summary files typically have the pattern "folder-name.description.json"
    while individual video files have patterns like "VID_xxx.description.json"
    
    Args:
        file_path (Path): Path to the JSON file
    
    Returns:
        bool: True if it's an individual video description file, False if folder summary
    """
    filename = file_path.stem
    # Folder summaries typically don't start with "VID_"
    return filename.startswith("VID_")


def process_description_file(file_path: Path, threshold: float = 0.8) -> Optional[Path]:
    """
    Process a single description JSON file and create grouped output.
    
    Args:
        file_path (Path): Path to the input description JSON file
        threshold (float): Similarity threshold for grouping
    
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
                print(f"  Warning: Unknown JSON structure in {file_path.name}, skipping")
                return None
        else:
            print(f"  Warning: Invalid JSON structure in {file_path.name}, skipping")
            return None
        
        # Group the descriptions using semantic similarity
        grouped_timeline = collapse_noisy_json(descriptions, threshold)
        
        # Create output file path with .descriptions.json extension
        # Remove .description from the filename before adding .descriptions.json
        output_filename = file_path.stem.replace('.description', '') + '.descriptions.json'
        output_path = file_path.parent / output_filename
        
        # Save the grouped timeline to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(grouped_timeline, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Created: {output_path.name}")
        return output_path
        
    except json.JSONDecodeError as e:
        print(f"  Error: Invalid JSON in {file_path.name}: {e}")
        return None
    except Exception as e:
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
    
    print(f"Processing description files in: {input_dir}")
    print(f"Similarity threshold: {args.threshold * 100}%")
    print("-" * 50)
    
    # Record start time for performance measurement
    start_time = time.perf_counter()
    
    # Find all individual video description files
    description_files = find_description_files(input_dir)
    
    if not description_files:
        print(f"No individual video description files found in {input_dir}")
        print("Make sure files follow the pattern: VID_*.description.json")
        sys.exit(0)
    
    print(f"Found {len(description_files)} video description files")
    print()
    
    # Process each description file
    processed_count = 0
    failed_count = 0
    
    for file_path in sorted(description_files):
        print(f"Processing: {file_path.name}")
        
        result = process_description_file(file_path, args.threshold)
        if result:
            processed_count += 1
        else:
            failed_count += 1
        print()
    
    # Calculate and display execution time
    end_time = time.perf_counter()
    total_time = end_time - start_time
    
    print("=" * 50)
    print(f"Processing complete!")
    print(f"Files processed: {processed_count}")
    print(f"Files failed: {failed_count}")
    print(f"Total execution time: {total_time:.2f} seconds")
    
    if processed_count > 0:
        avg_time = total_time / processed_count
        print(f"Average time per file: {avg_time:.2f} seconds")


if __name__ == "__main__":
    main()