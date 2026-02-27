# 🎬 Descriptor: AI Video Descriptor

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-orange.svg)](https://ffmpeg.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

AI-powered pipeline that extracts frames from videos, detects scenes, generates descriptions with MLX VLM, groups semantically, and outputs structured JSON.

## 🚀 Quick Start (macOS Apple Silicon Recommended)

**One-command install:**
```bash
curl -sSL https://github.com/orozcoh/descriptor/main/install/curl-install.sh | bash
```

**Use:**
```bash
descriptor .                    # Current directory
descriptor /path/to/videos      # Specific path
descriptor /path/to/videos -v   # Verbose
descriptor --help               # Help
```

## Output
Generates `*.descriptions.json` per video:
- Grouped timestamps with AI descriptions
- Scene change data

Example:
```json
{
  "timestamps": [{"start_time": "00:00:00", "end_time": "00:00:03", "description": "Person walking on sidewalk"}],
  "scenes-info": {"total_scenes": 2, ...}
}
```

## Manual Install
1. Clone: `git clone https://github.com/orozcoh/descriptor.git && cd descriptor`
2. Deps: `pip install -r install/requirements.txt && brew install ffmpeg`
3. Run: `python descriptor.py videos/`

----

**Dev workflow**: Use `./venv` + `python descriptor.py`

**CLI workflow**: `./install/install.sh` for `descriptor` command (isolated `./install/venv`)

Pick one to avoid duplicate venvs.

---

## Troubleshooting
- **FFmpeg missing**: `brew install ffmpeg`
- **Python <3.10**: Use Homebrew Python 3.11+
- **Venv issues**: `rm -rf ./venv` or `./install/venv`; reinstall.

## Advanced
Full docs, scripts, workflows: [AGENT-README.md](AGENT-README.md)