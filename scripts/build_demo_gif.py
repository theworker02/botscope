#!/usr/bin/env python3
"""Build animated GIF + strip from docs screenshots (interim demo assets)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "docs" / "assets" / "screenshots"
DEMO = ROOT / "docs" / "assets" / "demo"

ORDER = [
    ("observatory-dashboard.png", "Observatory"),
    ("global-observatory.png", "Global sources"),
    ("events.png", "Events"),
    ("bot-library.png", "Bot Library"),
    ("sources.png", "Sources"),
    ("settings.png", "Settings"),
]


def _caption_font(size: int = 16) -> ImageFont.ImageFont:
    candidates = [
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "segoeui.ttf",
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "arial.ttf",
    ]
    for path in candidates:
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def main() -> None:
    DEMO.mkdir(parents=True, exist_ok=True)
    frames: list[Image.Image] = []
    target_w = 960
    font = _caption_font(16)
    for name, caption in ORDER:
        im = Image.open(SHOTS / name).convert("RGB")
        w, h = im.size
        crop_h = min(h, int(w * 0.72))
        im = im.crop((0, 0, w, crop_h))
        ratio = target_w / im.width
        im = im.resize((target_w, int(im.height * ratio)), Image.Resampling.LANCZOS)
        bar_h = 36
        canvas = Image.new("RGB", (im.width, im.height + bar_h), (21, 32, 43))
        canvas.paste(im, (0, bar_h))
        draw = ImageDraw.Draw(canvas)
        draw.text((14, 8), f"BotScope — {caption}", fill=(216, 226, 235), font=font)
        frames.append(canvas)

    gif_path = DEMO / "botscope-tour.gif"
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=1600,
        loop=0,
        optimize=True,
    )
    print(f"wrote {gif_path} ({gif_path.stat().st_size} bytes)")

    thumbs: list[Image.Image] = []
    tw = 320
    for name, _caption in ORDER[:4]:
        im = Image.open(SHOTS / name).convert("RGB")
        w, h = im.size
        crop_h = min(h, int(w * 0.65))
        im = im.crop((0, 0, w, crop_h))
        ratio = tw / im.width
        im = im.resize((tw, int(im.height * ratio)), Image.Resampling.LANCZOS)
        thumbs.append(im)

    gap = 8
    strip_h = max(t.height for t in thumbs)
    strip = Image.new("RGB", (tw * 4 + gap * 3, strip_h), (238, 243, 247))
    x = 0
    for t in thumbs:
        strip.paste(t, (x, 0))
        x += tw + gap
    strip_path = DEMO / "botscope-tour-strip.png"
    strip.save(strip_path, "PNG", optimize=True)
    print(f"wrote {strip_path} ({strip_path.stat().st_size} bytes)")

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        mp4_path = DEMO / "botscope-demo.mp4"
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(gif_path),
            "-movflags",
            "+faststart",
            "-pix_fmt",
            "yuv420p",
            "-vf",
            "fps=8,scale=trunc(iw/2)*2:trunc(ih/2)*2",
            str(mp4_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"wrote {mp4_path} ({mp4_path.stat().st_size} bytes)")
        except (subprocess.CalledProcessError, OSError) as exc:
            print(f"ffmpeg present but MP4 build failed: {exc}")
    else:
        print("ffmpeg not found — skipped botscope-demo.mp4 (GIF + strip refreshed)")


if __name__ == "__main__":
    main()
