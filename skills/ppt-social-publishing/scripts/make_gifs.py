#!/usr/bin/env python3
"""从语义动画视频截取片段生成公众号用 GIF（默认 640px、调色板优化、≤10MB）。

用法:
  python make_gifs.py --video 视频.mp4 --segments "5.8-9.8:电子转移,30-36:集合关系" \
      --out-dir gifs/ [--width 640] [--fps 12] [--crop "772:434:138:317"]

segments 语法: 起秒-止秒:标签（多个用逗号分隔）。--crop 可选 w:h:x:y 裁剪（如媒体窗口）。
"""
import argparse
import subprocess
import sys
from pathlib import Path


def make_one(video: str, start: float, end: float, label: str, out: Path, width: int, fps: int,
             crop: str = "", max_mb: float = 9.5):
    out.parent.mkdir(parents=True, exist_ok=True)
    video = str(Path(video).resolve())
    palette = (out.parent / (out.stem + ".palette.png")).resolve()
    duration = max(0.5, end - start)
    chain = (f"crop={crop}," if crop else "") + f"scale={width}:-1:flags=lanczos,fps={fps}"

    def run(extra_inputs, filter_part, out_file):
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(start), "-t", f"{duration:.2f}", "-i", video,
             *extra_inputs, "-filter_complex", filter_part, "-loop", "0", str(out_file)],
            check=True)

    run([], f"{chain},palettegen=max_colors=128:stats_mode=diff", palette)
    run(["-i", str(palette)], f"[0:v]{chain}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3", out)
    palette.unlink(missing_ok=True)
    return out.stat().st_size


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True)
    ap.add_argument("--segments", required=True, help="起-止:标签，逗号分隔")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--crop", default="", help="w:h:x:y 裁剪（如媒体窗口）")
    ap.add_argument("--max-mb", type=float, default=9.5)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    segs = []
    for item in args.segments.split(","):
        seg, label = item.split(":", 1)
        a, b = seg.split("-")
        segs.append((float(a), float(b), label.strip()))

    for i, (a, b, label) in enumerate(segs, 1):
        out = out_dir / f"gif_{i:02d}_{label}.gif"
        width, fps = args.width, args.fps
        size = make_one(args.video, a, b, label, out, width, fps, args.crop, args.max_mb)
        tries = 0
        while size > args.max_mb * 1048576 and tries < 3:
            width, fps = max(480, int(width * 0.8)), max(10, fps - 2)
            size = make_one(args.video, a, b, label, out, width, fps, args.crop, args.max_mb)
            tries += 1
        flag = "OK" if size <= args.max_mb * 1048576 else "超限!"
        print(f"[{i}] {out.name}: {size/1048576:.2f}MB ({width}px/{fps}fps) {flag}")


if __name__ == "__main__":
    main()
