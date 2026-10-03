#!/usr/bin/env python3
"""Build a thumbnail contact sheet for visual QA; never used as a final slide image."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck_dir", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--width", type=int, default=480)
    args = parser.parse_args()

    image_dir = args.deck_dir / "origin_image"
    images = sorted(image_dir.glob("slide_*.png"))
    if not images:
        raise SystemExit(f"No slide images found in {image_dir}")
    if args.columns < 1:
        raise SystemExit("--columns must be >= 1")

    first = Image.open(images[0]).convert("RGB")
    ratio = first.height / first.width
    thumb_h = max(1, int(args.width * ratio))
    label_h = 34
    gap = 18
    rows = math.ceil(len(images) / args.columns)
    canvas_w = args.columns * args.width + (args.columns + 1) * gap
    canvas_h = rows * (thumb_h + label_h) + (rows + 1) * gap
    sheet = Image.new("RGB", (canvas_w, canvas_h), "#F3F4F6")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 20)
    except OSError:
        font = ImageFont.load_default()

    for index, path in enumerate(images):
        image = Image.open(path).convert("RGB")
        image.thumbnail((args.width, thumb_h), Image.Resampling.LANCZOS)
        col = index % args.columns
        row = index // args.columns
        x = gap + col * (args.width + gap)
        y = gap + row * (thumb_h + label_h + gap)
        sheet.paste(image, (x, y))
        draw.text((x, y + thumb_h + 7), path.stem, fill="#111827", font=font)

    output = args.out or (args.deck_dir / "qa" / "deck_contact_sheet.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
