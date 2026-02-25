from pathlib import Path
from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

# Load once
model, processor = load("apple/FastVLM-0.5B")
config = load_config("apple/FastVLM-0.5B")
prompt = apply_chat_template(processor, config, "Describe this image in no more than 50 words", num_images=1)

# Point to your frames folder
frames_dir = Path("content/2026/26-week-1-2/frames")
images = sorted(frames_dir.glob("*.png"))  # or *.jpg

results = {}
for i, image_path in enumerate(images):
    print(f"Processing {i+1}/{len(images)}: {image_path.name}")
    output = generate(model, processor, prompt, str(image_path), max_tokens=200, verbose=False)
    results[image_path.name] = output
    print(f"  → {output}\n")