# MovieMaker Story Video Assembler

This repo includes `video_assembler.py`, a MoviePy script that automates:

1. Loading `background.jpg` for the full duration of `story_audio.mp3`
2. Removing green-screen from `character.mp4`
3. Placing the keyed character in the bottom-right corner
4. Exporting a 1080p YouTube-ready MP4 (`final_story_video.mp4`)

## Install

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install moviepy
```

> Note: MoviePy requires FFmpeg. Install FFmpeg if it is missing.

## Run with your own files

```bash
python video_assembler.py \
  --character character.mp4 \
  --background background.jpg \
  --audio story_audio.mp3 \
  --output final_story_video.mp4
```

## Best green-screen color for Adobe Express

Use **`#00FF00`** (pure chroma green).

If green edges remain, tune:

- `--threshold` (default: `60`)
- `--softness` (default: `8`)

Example:

```bash
python video_assembler.py --threshold 70 --softness 10
```

## Create local demo/sample assets and render a sample output

If you want a quick synthetic sample without external media files, run:

```bash
python video_assembler.py --make-demo-assets --output sample_output.mp4
```

This creates:

- `character.mp4` (cartoon-like moving subject on pure green background)
- `background.jpg` (colorful gradient-style static background)
- `story_audio.mp3` (short synthetic beep-like narration placeholder)
- `sample_output.mp4` (final composited sample)
