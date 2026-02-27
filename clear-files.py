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

# ANSI escape codes for terminal control
CLEAR_LINE = '\033[K'  # Clear from cursor to end of line
CURSOR_UP = '\033[1A'   # Move cursor up one line
CURSOR_DOWN = '\033[1B' # Move cursor down one line


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


def print_progress_bar(current, total, bar_width=20):
    """Print a progress bar that updates in place."""
    if total == 0:
        return
    
    percent = (current / total) * 100
    filled_width = int(bar_width * current // total)
    bar = '█' * filled_width + '░' * (bar_width - filled_width)
    
    # Use \r to return cursor to beginning of line and \033[K to clear the rest of the line
    sys.stdout.write(f'\rProgress: {percent:3.0f}% [{bar}] {current}/{total} items\033[K')
    sys.stdout.flush()


def delete_frames_directories(frames_dirs: List[Path], verbose: bool = False) -> Tuple[int, List[str]]:
    """Delete frames directories and return count and any errors."""
    deleted_count = 0
    errors = []
    
    for i, frames_dir in enumerate(frames_dirs, 1):
        try:
            if frames_dir.exists():
                shutil.rmtree(frames_dir)
                if verbose:
                    print(f"Deleted: {frames_dir}")
                deleted_count += 1
                if not verbose:
                    print_progress_bar(i, len(frames_dirs))
        except Exception as e:
            error_msg = f"Error deleting {frames_dir}: {e}"
            if verbose:
                print(f"Warning: {error_msg}")
            errors.append(error_msg)
    
    return deleted_count, errors


def delete_files(file_list: List[Path], verbose: bool = False) -> Tuple[int, List[str]]:
    """Delete files and return count and any errors."""
    deleted_count = 0
    errors = []
    
    for i, file_path in enumerate(file_list, 1):
        try:
            if file_path.exists():
                file_path.unlink()
                if verbose:
                    print(f"Deleted: {file_path}")
                deleted_count += 1
                if not verbose:
                    print_progress_bar(i, len(file_list))
        except Exception as e:
            error_msg = f"Error deleting {file_path}: {e}"
            if verbose:
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
        'target',
        nargs='?',
        help='Directory to search in, or function type (frames/description/descriptions/scenes/purge). If directory, uses default behavior.'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Determine function and path based on the target argument
    if args.target is None:
        # No arguments provided, use default behavior in current directory
        function = None
        root_path = Path('.').resolve()
    elif args.target in ['frames', 'description', 'descriptions', 'scenes', 'purge']:
        # Target is a function, use current directory
        function = args.target
        root_path = Path('.').resolve()
    else:
        # Target is a directory path, use default behavior
        function = None
        root_path = Path(args.target).resolve()
    
    if not root_path.exists():
        print(f"Error: Path '{root_path}' does not exist.")
        sys.exit(1)
    
    if args.verbose:
        print(f"Searching in: {root_path}")
        print()
    
    # Handle purge operation with confirmation
    if function == 'purge':
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
            count, errors = delete_frames_directories(frames_dirs, args.verbose)
            total_deleted += count
            all_errors.extend(errors)
        
        if description_files:
            count, errors = delete_files(description_files, args.verbose)
            total_deleted += count
            all_errors.extend(errors)
        
        if descriptions_files:
            count, errors = delete_files(descriptions_files, args.verbose)
            total_deleted += count
            all_errors.extend(errors)
        
        if scene_files:
            count, errors = delete_files(scene_files, args.verbose)
            total_deleted += count
            all_errors.extend(errors)
        
        # Summary
        if args.verbose:
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
            # Clear progress line and show minimal completion message
            sys.stdout.write('\r' + ' ' * 80 + '\r')  # Clear line
            sys.stdout.flush()
            print(f"Purge complete! {total_deleted} items deleted successfully")
            if all_errors:
                print(f"Errors encountered: {len(all_errors)}")
        
    else:
        # Handle specific operations
        total_deleted = 0
        all_errors = []
        
        # Determine what to delete based on function or default behavior
        delete_frames = function == 'frames' or function is None
        delete_descriptions = function == 'description' or function is None
        delete_descriptions_only = function == 'descriptions'
        delete_scenes = function == 'scenes' or function is None
        
        if delete_frames:
            frames_dirs = find_frames_directories(root_path)
            if frames_dirs:
                if args.verbose:
                    print("Deleting frames directories...")
                count, errors = delete_frames_directories(frames_dirs, args.verbose)
                total_deleted += count
                all_errors.extend(errors)
            elif function == 'frames' and args.verbose:
                print("No frames directories found.")
        
        if delete_descriptions:
            description_files = find_description_files(root_path, "*.description.json")
            if description_files:
                if args.verbose:
                    print("Deleting .description.json files...")
                count, errors = delete_files(description_files, args.verbose)
                total_deleted += count
                all_errors.extend(errors)
            elif function == 'description' and args.verbose:
                print("No .description.json files found.")
        
        if delete_descriptions_only:
            descriptions_files = find_description_files(root_path, "*.descriptions.json")
            if descriptions_files:
                if args.verbose:
                    print("Deleting .descriptions.json files...")
                count, errors = delete_files(descriptions_files, args.verbose)
                total_deleted += count
                all_errors.extend(errors)
            elif args.verbose:
                print("No .descriptions.json files found.")
        
        if delete_scenes:
            scene_files = find_description_files(root_path, "*.scene.json")
            if scene_files:
                if args.verbose:
                    print("Deleting .scene.json files...")
                count, errors = delete_files(scene_files, args.verbose)
                total_deleted += count
                all_errors.extend(errors)
            elif function == 'scenes' and args.verbose:
                print("No .scene.json files found.")
        
        # Summary for non-purge operations
        if total_deleted > 0:
            if args.verbose:
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
            else:
                # Clear progress line and show minimal completion message
                sys.stdout.write('\r' + ' ' * 80 + '\r')  # Clear line
                sys.stdout.flush()
                print(f"Operation complete! {total_deleted} items deleted successfully")
                if all_errors:
                    print(f"Errors encountered: {len(all_errors)}")
        elif function is not None and args.verbose:
            print(f"\nNo files found to delete for function '{function}'.")


if __name__ == "__main__":
    main()