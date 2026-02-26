from pathlib import Path
import json
import argparse
import time
from collections import defaultdict
from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

def format_timestamp(seconds: int, milliseconds: int = 0) -> str:
    """Format seconds and milliseconds into HH:MM:SS.mmm timestamp format."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:03d}:{m:02d}:{s:02d}.{milliseconds:03d}"

def main(folder_path: str):
    start_time = time.perf_counter()
    folder = Path(folder_path)
    frames_dir = folder / "frames"
    
    if not frames_dir.exists():
        print(f"Error: No 'frames' directory found in {folder}")
        return 1
    
    pngs = list(frames_dir.glob("*.png"))
    if not pngs:
        print("No PNG frames found in frames directory.")
        return 1
    
    # Group frames by video stem: VID_xxx
    groups = defaultdict(list)
    for p in pngs:
        stem = p.stem  # e.g., 'VID_20260224_123820_0001'
        parts = stem.rsplit('_', 1)
        if len(parts) != 2:
            print(f"Skipping invalid frame name: {p.name}")
            continue
        video_stem, frame_str = parts
        try:
            frame_num = int(frame_str)
            groups[video_stem].append((frame_num, p))
        except ValueError:
            print(f"Skipping invalid frame number in: {p.name}")
            continue
    
    if not groups:
        print("No valid video frame groups found.")
        return 1
    
    # Load model once
    print("Loading model...")
    model, processor = load("apple/FastVLM-0.5B")
    config = load_config("apple/FastVLM-0.5B")
    prompt = apply_chat_template(processor, config, "Describe this image in no more than 150 characters", num_images=1)
    
    video_jsons = {}
    for video_stem in sorted(groups.keys()):
        frames_list = groups[video_stem]
        frames_list.sort(key=lambda x: x[0])  # Sort by frame_num
        
        print(f"\nProcessing video '{video_stem}' ({len(frames_list)} frames)")
        desc_dict = {}
        
        for i, (frame_num, img_path) in enumerate(frames_list, 1):
            print(f"  Processing frame {i}/{len(frames_list)}: {img_path.name}")
            output = generate(model, processor, prompt, str(img_path), max_tokens=100, verbose=False)
            ts_sec = frame_num - 1
            ts_key = format_timestamp(ts_sec, 0)
            desc_dict[ts_key] = output.text.strip()
        
        # Save per-video JSON
        json_path = folder / f"{video_stem}.description.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(desc_dict, f, indent=2, ensure_ascii=False)
        video_jsons[video_stem] = desc_dict
        print(f"  Saved: {json_path}")
    
    # Generate folder summary
    summary = {"folder": folder.name, "videos": video_jsons}
    summary_path = folder / f"{folder.name}.description.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nFolder summary saved: {summary_path}")
    
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(f"\nAll done! Total generation time: {total_time:.2f} seconds")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate timestamped descriptions for video frames and folder summary.")
    parser.add_argument("folder", help="Path to the folder containing 'frames/' directory (e.g., 'content/2026/26-week-1-2')")
    args = parser.parse_args()
    exit(main(args.folder))
