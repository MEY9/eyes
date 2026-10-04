#!/usr/bin/env python3
"""Package three representative style samples into review PDFs.

Each candidate must contain exactly sample_01.png, sample_02.png and
sample_03.png. The resulting PDFs are review artifacts, never final slides.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def parse_style(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--style 格式必须是 风格1=候选目录")
    label, directory = value.split("=", 1)
    label = label.strip()
    directory = directory.strip()
    if not label or not directory:
        raise argparse.ArgumentTypeError("--style 的名称和目录不能为空")
    return label, Path(directory)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--style", action="append", required=True, type=parse_style, help="重复三次：风格1=目录")
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()

    if len(args.style) != 3:
        raise SystemExit("必须提供恰好三组 --style，分别输出风格1.pdf、风格2.pdf、风格3.pdf。")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for label, directory in args.style:
        paths = [directory / f"sample_{index:02d}.png" for index in range(1, 4)]
        missing = [str(path) for path in paths if not path.is_file()]
        if missing:
            raise SystemExit(f"{label} 缺少样稿：{', '.join(missing)}")
        images = [Image.open(path).convert("RGB") for path in paths]
        first_size = images[0].size
        first_ratio = first_size[0] / first_size[1]
        for image in images[1:]:
            ratio = image.size[0] / image.size[1]
            if abs(ratio - first_ratio) > 0.01:
                raise SystemExit(f"{label} 三张样稿画幅比例差异过大，无法打包为统一 PDF。")
        # Image APIs may return an otherwise identical 16:9 canvas with a
        # one-pixel rounding difference. Normalize only the review PDF; keep
        # the original PNGs untouched for later visual QA and provenance.
        normalized = [images[0]]
        resized_images = []
        for image in images[1:]:
            if image.size != first_size:
                resized = image.resize(first_size, Image.Resampling.LANCZOS)
                resized_images.append(resized)
                normalized.append(resized)
            else:
                normalized.append(image)
        output = args.out_dir / f"{label}.pdf"
        normalized[0].save(output, "PDF", save_all=True, append_images=normalized[1:], resolution=96.0)
        for image in images:
            image.close()
        for image in resized_images:
            image.close()
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
