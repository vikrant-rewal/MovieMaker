#!/usr/bin/env python3
"""Assemble a story video with chroma-keyed character, background image, and voice-over audio.

Expected input files in the working directory:
- character.mp4
- background.jpg
- story_audio.mp3

Example:
    python video_assembler.py \
        --character character.mp4 \
        --background background.jpg \
        --audio story_audio.mp3 \
        --output final_story_video.mp4
"""

from __future__ import annotations

import argparse
from pathlib import Path

from moviepy.editor import (
    AudioClip,
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    VideoClip,
    VideoFileClip,
    vfx,
)
import numpy as np
from imageio.v2 import imwrite


def build_video(
    character_path: Path,
    background_path: Path,
    audio_path: Path,
    output_path: Path,
    width: int = 1920,
    height: int = 1080,
    margin: int = 40,
    chroma_hex: str = "#00FF00",
    threshold: int = 60,
    softness: int = 8,
) -> None:
    """Create the final video composition and export as MP4.

    Args:
        character_path: Path to green-screen character video.
        background_path: Path to background image.
        audio_path: Path to voice-over audio.
        output_path: Destination MP4 path.
        width: Output video width.
        height: Output video height.
        margin: Pixel margin from bottom-right edges.
        chroma_hex: Green screen color used for keying.
        threshold: Keying tolerance (higher removes more shades near chroma color).
        softness: Edge softness for smoother keying.
    """
    # Load the narration first so we can make the timeline match it exactly.
    narration = AudioFileClip(str(audio_path))

    # Build a 1080p background layer with duration exactly equal to the audio duration.
    background = (
        ImageClip(str(background_path))
        .resize((width, height))
        .set_duration(narration.duration)
    )

    # Load and chroma-key the character clip.
    character = VideoFileClip(str(character_path))
    keyed_character = character.fx(
        vfx.mask_color,
        color=chroma_hex,
        thr=threshold,
        s=softness,
    )

    # Resize character to fit nicely in frame (about 45% of output height).
    keyed_character = keyed_character.resize(height=int(height * 0.45))

    # Keep character duration aligned to narration; trim if longer.
    if keyed_character.duration > narration.duration:
        keyed_character = keyed_character.subclip(0, narration.duration)
    else:
        keyed_character = keyed_character.set_duration(narration.duration)

    keyed_character = keyed_character.set_position(
        (width - keyed_character.w - margin, height - keyed_character.h - margin)
    )

    # Composite layers and attach the narration as the main audio track.
    final = CompositeVideoClip([background, keyed_character], size=(width, height)).set_duration(
        narration.duration
    )
    final = final.set_audio(narration)

    # Export in YouTube-friendly H.264 + AAC, 1080p.
    final.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="medium",
        threads=4,
        ffmpeg_params=["-movflags", "+faststart", "-pix_fmt", "yuv420p"],
    )

    # Release resources explicitly.
    final.close()
    keyed_character.close()
    character.close()
    background.close()
    narration.close()


def create_demo_assets(
    character_path: Path,
    background_path: Path,
    audio_path: Path,
    duration: float = 6.0,
    width: int = 1920,
    height: int = 1080,
) -> None:
    """Generate synthetic input assets so users can render a sample output quickly."""
    # 1) Bright, kid-friendly background image.
    x = np.linspace(0, 1, width, dtype=np.float32)
    y = np.linspace(0, 1, height, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    background = np.zeros((height, width, 3), dtype=np.uint8)
    background[..., 0] = (60 + 120 * xx).astype(np.uint8)
    background[..., 1] = (120 + 110 * yy).astype(np.uint8)
    background[..., 2] = (210 - 90 * xx).astype(np.uint8)
    imwrite(background_path, background)

    # 2) Synthetic narration (a soft sine-wave pattern).
    def make_audio_frame(t: np.ndarray | float) -> np.ndarray | float:
        t_arr = np.array(t)
        carrier = np.sin(2 * np.pi * 220 * t_arr)
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 1.2 * t_arr)
        return 0.2 * carrier * envelope

    narration = AudioClip(make_audio_frame, duration=duration, fps=44100)
    narration.write_audiofile(str(audio_path), fps=44100, nbytes=2, bitrate="192k", logger=None)
    narration.close()

    # 3) Simple moving subject over pure green background (#00FF00).
    char_w, char_h = 960, 720

    def make_character_frame(t: float) -> np.ndarray:
        frame = np.zeros((char_h, char_w, 3), dtype=np.uint8)
        frame[..., 1] = 255  # Pure chroma green background

        cx = int(180 + (char_w - 360) * (0.5 + 0.5 * np.sin(2 * np.pi * t / duration)))
        cy = int(char_h * 0.55)
        radius = 120

        yy_i, xx_i = np.ogrid[:char_h, :char_w]
        circle = (xx_i - cx) ** 2 + (yy_i - cy) ** 2 <= radius**2
        frame[circle] = np.array([255, 180, 120], dtype=np.uint8)

        # Simple torso rectangle
        x1, x2 = max(cx - 110, 0), min(cx + 110, char_w)
        y1, y2 = min(cy + 90, char_h - 1), min(cy + 280, char_h)
        frame[y1:y2, x1:x2] = np.array([40, 110, 255], dtype=np.uint8)
        return frame

    character_clip = VideoClip(make_frame=make_character_frame, duration=duration)
    character_clip.write_videofile(
        str(character_path),
        codec="libx264",
        fps=30,
        audio=False,
        logger=None,
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )
    character_clip.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble a kids-story video with MoviePy.")
    parser.add_argument("--character", default="character.mp4", type=Path)
    parser.add_argument("--background", default="background.jpg", type=Path)
    parser.add_argument("--audio", default="story_audio.mp3", type=Path)
    parser.add_argument("--output", default="final_story_video.mp4", type=Path)
    parser.add_argument(
        "--chroma-hex",
        default="#00FF00",
        help="Green-screen hex color to remove (default: #00FF00).",
    )
    parser.add_argument(
        "--threshold",
        default=60,
        type=int,
        help="Chroma-key threshold/tolerance. Increase if green spill remains.",
    )
    parser.add_argument(
        "--softness",
        default=8,
        type=int,
        help="Edge softness for keying (higher = softer edges).",
    )
    parser.add_argument(
        "--make-demo-assets",
        action="store_true",
        help="Create synthetic character/background/audio assets before assembling output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.make_demo_assets:
        create_demo_assets(
            character_path=args.character,
            background_path=args.background,
            audio_path=args.audio,
        )

    build_video(
        character_path=args.character,
        background_path=args.background,
        audio_path=args.audio,
        output_path=args.output,
        chroma_hex=args.chroma_hex,
        threshold=args.threshold,
        softness=args.softness,
    )


if __name__ == "__main__":
    main()
