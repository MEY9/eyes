#!/usr/bin/env python3
"""Package the single 16:9 course-video master into a 9:16 vertical canvas.

Rule enforced here: the slide content stays a complete, undistorted 16:9
region centered on the canvas; the top/bottom fill is a blurred, dimmed
copy of the same frame. Never crop the master and never stretch it.

Usage:
  python package_vertical_video.py <master_16x9.mp4> -o <output_9x16.mp4>
      [--canvas 1080x1920] [--blur 28] [--dim -0.08] [--crf 18] [--preset medium]

Prints a JSON summary (paths, durations, sha256) for publication_manifest.json.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def die(msg: str) -> None:
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
    sys.exit(1)


def run(cmd, err_hint: str):
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr or "").strip().splitlines()[-15:])
        die(f"{err_hint}\n{tail}")
    return proc.stdout


def probe(path: Path) -> dict:
    out = run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height:format=duration",
            "-of", "json", str(path),
        ],
        f"ffprobe 无法读取 {path}",
    )
    data = json.loads(out)
    streams = data.get("streams") or []
    if not streams:
        die(f"{path} 中没有视频流")
    width, height = int(streams[0]["width"]), int(streams[0]["height"])
    duration = float(data["format"]["duration"])
    audio = run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0", str(path),
        ],
        f"ffprobe 无法读取 {path} 音频流",
    ).strip()
    return {"width": width, "height": height, "duration": duration, "has_audio": bool(audio)}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description="16:9 母版 → 9:16 竖版画布包装（幻灯片完整 16:9 居中）")
    ap.add_argument("master", help="唯一 16:9 视频母版路径")
    ap.add_argument("-o", "--output", required=True, help="输出 video_9x16.mp4 路径")
    ap.add_argument("--canvas", default="1080x1920", help="竖版画布尺寸，默认 1080x1920")
    ap.add_argument("--blur", type=float, default=28.0, help="背景高斯模糊 sigma，默认 28")
    ap.add_argument("--dim", type=float, default=-0.08, help="背景压暗 brightness，默认 -0.08")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="medium")
    args = ap.parse_args()

    master = Path(args.master)
    if not master.is_file():
        die(f"母版不存在: {master}")

    m = re.fullmatch(r"(\d+)x(\d+)", args.canvas)
    if not m:
        die(f"--canvas 需要形如 1080x1920，收到: {args.canvas}")
    canvas_w, canvas_h = int(m.group(1)), int(m.group(2))

    info = probe(master)
    master_w, master_h = info["width"], info["height"]

    # 幻灯片层等比缩放到画布宽度，高度取偶数；绝不裁切、绝不拉伸。
    fg_h = round(canvas_w * master_h / master_w)
    if fg_h >= canvas_h:
        die(f"母版按画布宽 {canvas_w} 等比缩放后高 {fg_h} 已超过画布高 {canvas_h}，请检查母版比例")
    if fg_h % 2:
        fg_h -= 1

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    filter_complex = (
        f"[0:v]split=2[bg][fg];"
        f"[bg]scale={canvas_w}:{canvas_h}:force_original_aspect_ratio=increase,"
        f"crop={canvas_w}:{canvas_h},gblur=sigma={args.blur},eq=brightness={args.dim}[bgb];"
        f"[fg]scale={canvas_w}:{fg_h}[fgs];"
        f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )

    cmd = [
        "ffmpeg", "-y", "-v", "error", "-i", str(master),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-c:v", "libx264", "-crf", str(args.crf), "-preset", args.preset,
        "-movflags", "+faststart",
    ]
    if info["has_audio"]:
        cmd += ["-map", "0:a?", "-c:a", "copy"]
    else:
        cmd += ["-an"]
    cmd.append(str(out_path))

    run(cmd, "ffmpeg 包装失败")
    out_info = probe(out_path)

    if (out_info["width"], out_info["height"]) != (canvas_w, canvas_h):
        die(f"输出画布为 {out_info['width']}x{out_info['height']}，应为 {canvas_w}x{canvas_h}")
    if abs(out_info["duration"] - info["duration"]) > max(1.0, info["duration"] * 0.02):
        die(f"输出时长 {out_info['duration']:.2f}s 与母版 {info['duration']:.2f}s 不一致")

    print(json.dumps({
        "ok": True,
        "master": str(master),
        "master_resolution": f"{master_w}x{master_h}",
        "master_duration": round(info["duration"], 3),
        "output": str(out_path),
        "canvas": f"{canvas_w}x{canvas_h}",
        "slide_region": {"width": canvas_w, "height": fg_h, "ratio": "16:9 centered"},
        "output_duration": round(out_info["duration"], 3),
        "audio": "copied" if info["has_audio"] else "none",
        "sha256": sha256_of(out_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
