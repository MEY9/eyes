# -*- coding: utf-8 -*-
"""把 gpt-image 1K 输出（1536x1024, 3:2）转为 16:9 教学幻灯片尺寸。

流程：中央裁切 1536x864 -> Lanczos 放大 2560x1440。
提示词已要求关键内容位于中央 84% 区域，因此裁切不损失正文。
"""
import sys
from pathlib import Path
from PIL import Image

TARGET = (2560, 1440)


def to_16x9(src: Path) -> Path:
    im = Image.open(src).convert("RGB")
    w, h = im.size
    target_ratio = 16 / 9
    ratio = w / h
    if abs(ratio - target_ratio) < 0.01:
        cropped = im
    elif ratio > target_ratio:
        # 太宽，裁两侧
        new_w = int(round(h * target_ratio))
        left = (w - new_w) // 2
        cropped = im.crop((left, 0, left + new_w, h))
    else:
        # 太高，裁上下
        new_h = int(round(w / target_ratio))
        top = (h - new_h) // 2
        cropped = im.crop((0, top, w, top + new_h))
    out = cropped.resize(TARGET, Image.LANCZOS)
    dst = src.with_name(src.stem + "_16x9" + src.suffix)
    out.save(dst, "PNG", optimize=True)
    print(f"{src.name} {im.size} -> crop {cropped.size} -> {TARGET}  => {dst.name}")
    return dst


if __name__ == "__main__":
    for p in sys.argv[1:]:
        to_16x9(Path(p))
