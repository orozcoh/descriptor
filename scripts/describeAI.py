from pathlib import Path
import json
import argparse
import time
import sys
from collections import defaultdict
from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config
import os
from huggingface_hub import snapshot_download

# ANSI escape codes for terminal control
CLEAR_LINE = '\033[K'  # Clear from cursor to end of line
CURSOR_UP = '\033[1A'   # Move cursor up one line
CURSOR_DOWN = '\033[1B' # Move cursor down one line

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


def load_model_and_prompt(verbose: bool = False):
    """Load model, processor, config, and prompt once."""
    # Model loading with progress suppression after first download
    model_id = "apple/FastVLM-0.5B"
    flag_dir = Path.home() / ".descriptor"
    flag_file = flag_dir / "fastvlm_loaded"
    first_load = not flag_file.exists()

    if verbose:
        if first_load:
            print("Loading model (first time - downloading)...")
        else:
            print("Loading model...")
    elif not first_load:
        print("FastVLM Model Loaded successfully")

    if first_load:
        model_path = model_id
        config_path = model_id
    else:
        os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
        model_path = snapshot_download(model_id, local_files_only=True)
        config_path = snapshot_download(model_id, local_files_only=True)

    model, processor = load(model_path)
    config = load_config(config_path)
    prompt = apply_chat_template(processor, config, "Describe this image in no more than 150 characters", num_images=1)

    # Create flag after successful first load
    if first_load:
        flag_dir.mkdir(exist_ok=True)
        flag_file.touch()
        if verbose:
            print("FastVLM model downloaded and ready.")

    return model, processor, prompt


def process_video_frames(folder_path: Path, model, processor, prompt, verbose: bool = False):
    """Process frames in a single video folder and save descriptions."""
    frames_dir = folder_path / "frames"
    
    if not frames_dir.exists():
        if verbose:
            print(f"Error: No 'frames' directory found in {folder_path}")
        return False
    
    pngs = list(frames_dir.glob("*.png"))
    if not pngs:
        if verbose:
            print("No PNG frames found in frames directory.")
        return False
    
    # Group frames by video stem: VID_xxx
    groups = defaultdict(list)
    for p in pngs:
        stem = p.stem  # e.g., 'VID_20260224_123820_0001'
        parts = stem.rsplit('_', 1)
        if len(parts) != 2:
            if verbose:
                print(f"Skipping invalid frame name: {p.name}")
            continue
        video_stem, frame_str = parts
        try:
            frame_num = int(frame_str)
            groups[video_stem].append((frame_num, p))
        except ValueError:
            if verbose:
                print(f"Skipping invalid frame number in: {p.name}")
            continue
    
    if not groups:
        if verbose:
            print("No valid video frame groups found.")
        return False
    
    video_jsons = {}
    total_frames = sum(len(frames) for frames in groups.values())
    current_frame = 0
    
    for video_stem in sorted(groups.keys()):
        frames_list = groups[video_stem]
        frames_list.sort(key=lambda x: x[0])  # Sort by frame_num
        
        if verbose:
            print(f"\nProcessing video '{video_stem}' ({len(frames_list)} frames)")
        desc_dict = {}
        
        for i, (frame_num, img_path) in enumerate(frames_list, 1):
            current_frame += 1
            if verbose:
                print(f"  Processing frame {i}/{len(frames_list)}: {img_path.name}")
            
            output = generate(model, processor, prompt, str(img_path), max_tokens=100, verbose=False)
            ts_sec = frame_num - 1
            ts_key = format_timestamp(ts_sec, 0)
            desc_dict[ts_key] = output.text.strip()
            
            # Update progress bar in quiet mode
            if not verbose:
                print_progress_bar(current_frame, total_frames)
        
        # Save per-video JSON
        json_path = folder_path / f"{video_stem}.description.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(desc_dict, f, indent=2, ensure_ascii=False)
        video_jsons[video_stem] = desc_dict
        if verbose:
            print(f"  Saved: {json_path}")
    
    # Clear the progress line
    if not verbose:
        sys.stdout.write('\r' + ' ' * 80 + '\r')  # Clear line
        sys.stdout.flush()
    
    return True


def format_timestamp(seconds: int, milliseconds: int = 0) -> str:
    """Format seconds and milliseconds into HH:MM:SS.mmm timestamp format."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:03d}:{m:02d}:{s:02d}.{milliseconds:03d}"


def main(folder_path: str, verbose: bool = False):
    start_time = time.perf_counter()
    folder = Path(folder_path)
    model, processor, prompt = load_model_and_prompt(verbose)
    success = process_video_frames(folder, model, processor, prompt, verbose)
    end_time = time.perf_counter()
    total_time = end_time - start_time
    if verbose:
        print(f"\nAll done! Total generation time: {total_time:.2f} seconds")
    else:
        print(f"Processing complete! Total generation time: {total_time:.2f} seconds")
    return 0 if success else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate timestamped descriptions for video frames and folder summary.")
    parser.add_argument("folder", help="Path to the folder containing 'frames/' directory (e.g., 'content/2026/26-week-1-2')")
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    args = parser.parse_args()
    exit(main(args.folder, args.verbose))
