#!/usr/bin/env python3
"""
Clear script files - Delete frames folders and description files created by video processing scripts.

Usage:
    python clear-script-files.py                    # clears frames folders, .description.json, and .scene.json files (default)
    python clear-script-files.py frames             # clears only frames folders
    python clear-script-files.py description        # clears only .description.json files
    python clear-script-files.py descriptions       # clears only .descriptions.json files
    python clear-script-files.py scenes             # clears only .scene.json files
    python clear-script-files.py purge              # clears everything with confirmation
    python clear-script-files.py <func> <path>      # run any function on a specific directory path

Examples:
    python clear-script-files.py purge              # clear everything in current directory
    python clear-script-files.py frames /path/to/folder  # clear frames in specific folder
    python clear-script-files.py description content/2026/26-week-1-2  # clear descriptions in specific folder
    python clear-script-files.py scenes content/2026/26-week-1-2  # clear scene files in specific folder
"""

import os
import sys
import argparse
import shutil
from pathlib import Path
from typing import List, Tuple


def find_frames_directories(root_path: Path) -> List[Path]:
    """Find all 'frames' directories recursively."""
    frames_dirs = []
    for root, dirs, files in os.walk(root_path):
        if 'frames' in dirs:
            frames_dir = Path(root) / 'frames'
            frames_dirs.append(frames_dir)
    return frames_dirs


def find_description_files(root_path: Path, pattern: str) -> List[Path]:
    """Find all files matching the given pattern recursively."""
    return list(root_path.rglob(pattern))


def delete_frames_directories(frames_dirs: List[Path]) -> Tuple[int, List[str]]:
    """Delete frames directories and return count and any errors."""
    deleted_count = 0
    errors = []
    
    for frames_dir in frames_dirs:
        try:
            if frames_dir.exists():
                shutil.rmtree(frames_dir)
                print(f"Deleted: {frames_dir}")
                deleted_count += 1
        except Exception as e:
            error_msg = f"Error deleting {frames_dir}: {e}"
            print(f"Warning: {error_msg}")
            errors.append(error_msg)
    
    return deleted_count, errors


def delete_files(file_list: List[Path]) -> Tuple[int, List[str]]:
    """Delete files and return count and any errors."""
    deleted_count = 0
    errors = []
    
    for file_path in file_list:
        try:
            if file_path.exists():
                file_path.unlink()
                print(f"Deleted: {file_path}")
                deleted_count += 1
        except Exception as e:
            error_msg = f"Error deleting {file_path}: {e}"
            print(f"Warning: {error_msg}")
            errors.append(error_msg)
    
    return deleted_count, errors


def confirm_purge_operation(root_path: Path) -> bool:
    """Ask for confirmation before performing purge operation."""
    print(f"\n⚠️  PURGE OPERATION: This will delete ALL related files in: {root_path}")
    print("This includes:")
    print("  - All 'frames' directories and their contents")
    print("  - All '*.description.json' files")
    print("  - All '*.descriptions.json' files")
    print("  - All '*.scene.json' files")
    print()
    
    response = input("Are you sure you want to continue? (yes/no): ").strip().lower()
    return response in ['yes', 'y']


def main():
    parser = argparse.ArgumentParser(
        description="Delete frames folders and description files created by video processing scripts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        'function',
        nargs='?',
        choices=['frames', 'description', 'descriptions', 'scenes', 'purge'],
        help='Type of files to delete (default: frames + description + scenes)'
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Directory to search in (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Determine root path based on arguments
    if args.function is None:
        # No function provided, use the path if provided, otherwise current directory
        root_path = Path(args.path).resolve() if args.path != '.' else Path('.').resolve()
    else:
        # Function provided, use the path if provided, otherwise current directory
        root_path = Path(args.path).resolve() if args.path != '.' else Path('.').resolve()
    
    if not root_path.exists():
        print(f"Error: Path '{root_path}' does not exist.")
        sys.exit(1)
    
    print(f"Searching in: {root_path}")
    print()
    
    # Handle purge operation with confirmation
    if args.function == 'purge':
        if not confirm_purge_operation(root_path):
            print("Operation cancelled.")
            sys.exit(0)
        
        # Find all files to delete
        frames_dirs = find_frames_directories(root_path)
        description_files = find_description_files(root_path, "*.description.json")
        descriptions_files = find_description_files(root_path, "*.descriptions.json")
        scene_files = find_description_files(root_path, "*.scene.json")
        
        # Delete everything
        total_deleted = 0
        all_errors = []
        
        if frames_dirs:
            count, errors = delete_frames_directories(frames_dirs)
            total_deleted += count
            all_errors.extend(errors)
        
        if description_files:
            count, errors = delete_files(description_files)
            total_deleted += count
            all_errors.extend(errors)
        
        if descriptions_files:
            count, errors = delete_files(descriptions_files)
            total_deleted += count
            all_errors.extend(errors)
        
        if scene_files:
            count, errors = delete_files(scene_files)
            total_deleted += count
            all_errors.extend(errors)
        
        # Summary
        print(f"\n{'='*50}")
        print(f"PURGE COMPLETE")
        print(f"Total files/directories deleted: {total_deleted}")
        if all_errors:
            print(f"Errors encountered: {len(all_errors)}")
            for error in all_errors:
                print(f"  - {error}")
        else:
            print("No errors encountered.")
        print(f"{'='*50}")
        
    else:
        # Handle specific operations
        total_deleted = 0
        all_errors = []
        
        # Determine what to delete based on function or default behavior
        delete_frames = args.function == 'frames' or args.function is None
        delete_descriptions = args.function == 'description' or args.function is None
        delete_descriptions_only = args.function == 'descriptions'
        delete_scenes = args.function == 'scenes' or args.function is None
        
        if delete_frames:
            frames_dirs = find_frames_directories(root_path)
            if frames_dirs:
                print("Deleting frames directories...")
                count, errors = delete_frames_directories(frames_dirs)
                total_deleted += count
                all_errors.extend(errors)
            elif args.function == 'frames':
                print("No frames directories found.")
        
        if delete_descriptions:
            description_files = find_description_files(root_path, "*.description.json")
            if description_files:
                print("Deleting .description.json files...")
                count, errors = delete_files(description_files)
                total_deleted += count
                all_errors.extend(errors)
            elif args.function == 'description':
                print("No .description.json files found.")
        
        if delete_descriptions_only:
            descriptions_files = find_description_files(root_path, "*.descriptions.json")
            if descriptions_files:
                print("Deleting .descriptions.json files...")
                count, errors = delete_files(descriptions_files)
                total_deleted += count
                all_errors.extend(errors)
            else:
                print("No .descriptions.json files found.")
        
        if delete_scenes:
            scene_files = find_description_files(root_path, "*.scene.json")
            if scene_files:
                print("Deleting .scene.json files...")
                count, errors = delete_files(scene_files)
                total_deleted += count
                all_errors.extend(errors)
            elif args.function == 'scenes':
                print("No .scene.json files found.")
        
        # Summary for non-purge operations
        if total_deleted > 0:
            print(f"\n{'='*50}")
            print(f"OPERATION COMPLETE")
            print(f"Total files/directories deleted: {total_deleted}")
            if all_errors:
                print(f"Errors encountered: {len(all_errors)}")
                for error in all_errors:
                    print(f"  - {error}")
            else:
                print("No errors encountered.")
            print(f"{'='*50}")
        elif args.function is not None:
            print(f"\nNo files found to delete for function '{args.function}'.")


if __name__ == "__main__":
    main()