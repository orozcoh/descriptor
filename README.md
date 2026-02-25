# Frame Extractor

A Python3 script that extracts frames from video files using FFmpeg.

## Description

This script extracts individual frames from video files (MP4, AVI, MOV, MKV, WebM, FLV, M4V, WMV) at specified intervals. Each frame is saved as a PNG image with 720p resolution (downscaled if the source is larger).

## Prerequisites

- **Python 3** - The script uses only Python standard library modules
- **FFmpeg** - Required for video processing

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use a package manager like Chocolatey:
```bash
choco install ffmpeg
```

## Usage

```bash
python3 frame-extractor <directory_path> [options]
```

### Examples

Extract frames at 1 second intervals from a specific directory:
```bash
python3 frame-extractor ./content/2026/26-week-1-2
```

Extract frames at 0.5 second intervals:
```bash
python3 frame-extractor ./content/2026/26-week-1-2 -i 0.5
```

Extract frames from the current directory:
```bash
python3 frame-extractor .
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `directory` | Directory containing video files | `.` (current directory) |
| `-i, --interval` | Interval between frames in seconds | `1.0` |
| `-v, --verbose` | Enable verbose output | `false` |

## Output

Frames are saved in a `frames` subdirectory within each video's directory.

### Naming Convention

Frames are named as: `<video_filename>_<frame_number>.png`

Example:
```
Content/2026/26-week-1-2/
├── VID_20260224_123820.mp4
└── frames/
    ├── VID_20260224_123820_0001.png
    ├── VID_20260224_123820_0002.png
    ├── VID_20260224_123820_0003.png
    └── ...
```

### Resolution

All frames are scaled to 720p (1280x720) using Lanczos scaling with aspect ratio preservation. If the source video is smaller than 720p, it remains at original resolution.

## No External Dependencies

This script uses only Python's standard library. No `requirements.txt` or `pip install` needed!

- `os` - File system operations
- `sys` - System arguments
- `subprocess` - Run FFmpeg commands
- `argparse` - Command-line parsing
- `pathlib` - Path handling

---

## Frame Description Script (Des-script)

Generate video descriptions using Moondream AI.

### Prerequisites (use venv)

1. Create & activate venv with Python >=3.10 (moondream requires it):
```bash
/opt/homebrew/bin/python3.14 -m venv venv
source venv/bin/activate  # or venv/bin/Activate.ps1 on Windows
```

2. Install deps:
```bash
pip install -r requirements.txt
```

### Usage

```bash
python3 Des-script <directory_path> [options]
```

### Examples

Generate descriptions for videos in a directory:
```bash
python3 Des-script ./content/2026/26-week-1-2
```

Use custom endpoint:
```bash
python3 Des-script ./content/2026/26-week-1-2 -e http://localhost:2020/v1
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `directory` | Directory containing video files | `.` |
| `-i, --interval` | Frame interval in seconds | `1.0` |
| `-e, --endpoint` | Moondream endpoint URL | `http://localhost:2020/v1` |
| `--force` | Reprocess all videos even if .description.json exists | `false` |

### Output

1. **Per-video descriptions**: `<video_name>.description.json` (all frames + normalized-grouped summaries)
2. **Folder summary**: `<folder_name>.json` (recursive scan of all descriptions with relative paths)

Example folder summary entry:
```json
{
  "video_relative": "VID_20260224_123820.mp4",
  "description_file": "VID_20260224_123820.description.json",
  "total_frames": 123,
  "time_range": "00:00:01 - 00:02:03"
}
```

### Features

- **Resumable**: Skips existing .description.json files
- **Force reprocess**: `--force` to regenerate all
- **Smart grouping**: Normalizes descriptions (lowercase, strip punctuation) for consecutive similar scenes
- **Recursive**: Handles subdirectories, skips frames/

