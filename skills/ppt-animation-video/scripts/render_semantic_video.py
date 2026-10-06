#!/usr/bin/env python3
"""Render a PPTX animation manifest into a continuous MP4 without a GUI player.

The script renders object-level reveal states from an editable PPTX, recreates
the manifest's semantic entrance effects, and inserts embedded-media source
files at their declared point in the timeline. It preserves the slide aspect
ratio and carries only audio from declared PPT media sources.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.oxml.ns import qn


P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, check=True, env=env)


def shape_id(element: Any) -> int | None:
    node = element.find(f".//{{{P_NS}}}cNvPr")
    if node is None:
        return None
    try:
        return int(node.get("id"))
    except (TypeError, ValueError):
        return None


def remove_hidden_shapes(element: Any, hidden_ids: set[int]) -> None:
    for child in list(element):
        local = child.tag.rsplit("}", 1)[-1]
        sid = shape_id(child)
        if sid in hidden_ids:
            element.remove(child)
            continue
        if local == "grpSp":
            remove_hidden_shapes(child, hidden_ids)


def keep_one_slide(prs: Presentation, slide_index: int) -> None:
    slide_ids = prs.slides._sldIdLst
    for index in range(len(slide_ids) - 1, -1, -1):
        if index == slide_index:
            continue
        slide_id = slide_ids[index]
        try:
            prs.part.drop_rel(slide_id.rId)
        except Exception:
            pass
        del slide_ids[index]


def write_state_variant(
    source: Path,
    slide_index: int,
    visible_ids: set[int],
    animated_ids: set[int],
    destination: Path,
) -> None:
    prs = Presentation(str(source))
    keep_one_slide(prs, slide_index)
    slide = prs.slides[0]
    shape_tree = slide._element.find(f".//{{{P_NS}}}spTree")
    if shape_tree is None:
        raise RuntimeError(f"slide {slide_index + 1} has no shape tree")
    remove_hidden_shapes(shape_tree, animated_ids - visible_ids)
    timing = slide._element.find(qn("p:timing"))
    if timing is not None:
        slide._element.remove(timing)
    transition = slide._element.find(qn("p:transition"))
    if transition is not None:
        slide._element.remove(transition)
    prs.save(str(destination))


def render_states(
    source: Path,
    manifest: dict[str, Any],
    state_dir: Path,
    soffice: str,
    pdftoppm: str,
    fontconfig: Path | None,
    dpi: int,
) -> list[dict[str, Any]]:
    state_dir.mkdir(parents=True, exist_ok=True)
    render_env = os.environ.copy()
    if fontconfig:
        render_env["FONTCONFIG_FILE"] = str(fontconfig.resolve())
        render_env["FONTCONFIG_PATH"] = str(fontconfig.resolve().parent)

    sequence: list[dict[str, Any]] = []
    for slide_index, slide_plan in enumerate(manifest["slides"]):
        slide_number = int(slide_plan.get("slide", slide_index + 1))
        groups = slide_plan["groups"]
        all_ids = {
            int(obj["shape_id"])
            for group in groups
            for obj in group.get("objects", [])
        }
        slide_dir = state_dir / f"slide_{slide_number:02d}"
        slide_dir.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f"ppt-video-{slide_number:02d}-") as tmp:
            tmp_dir = Path(tmp)
            variants: list[Path] = []
            revealed: set[int] = set()
            for state_index in range(len(groups) + 1):
                if state_index:
                    revealed.update(
                        int(obj["shape_id"])
                        for obj in groups[state_index - 1].get("objects", [])
                    )
                variant = tmp_dir / f"slide_{slide_number:02d}_state_{state_index:02d}.pptx"
                write_state_variant(
                    source,
                    slide_index,
                    revealed,
                    all_ids,
                    variant,
                )
                variants.append(variant)

            profile_dir = tmp_dir / "lo-profile"
            command = [
                soffice,
                f"-env:UserInstallation={profile_dir.as_uri()}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(tmp_dir),
                *[str(path) for path in variants],
            ]
            run(command, env=render_env)

            for state_index, variant in enumerate(variants):
                pdf = variant.with_suffix(".pdf")
                if not pdf.exists():
                    raise RuntimeError(f"LibreOffice did not render {variant.name}")
                prefix = tmp_dir / f"png_{state_index:02d}"
                run([
                    pdftoppm,
                    "-png",
                    "-singlefile",
                    "-r",
                    str(dpi),
                    str(pdf),
                    str(prefix),
                ])
                rendered = prefix.with_suffix(".png")
                target = slide_dir / f"state_{state_index:02d}.png"
                shutil.move(str(rendered), str(target))
                effect = "initial" if state_index == 0 else groups[state_index - 1]["effect"]
                purpose = "initial" if state_index == 0 else groups[state_index - 1]["purpose"]
                sequence.append({
                    "slide": slide_number,
                    "state": state_index,
                    "group": state_index,
                    "effect": effect,
                    "purpose": purpose,
                    "path": str(target.resolve()),
                })
        print(f"rendered slide {slide_number}: {len(groups) + 1} states", flush=True)
    return sequence


def load_sequence(state_dir: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    sequence: list[dict[str, Any]] = []
    for slide_index, slide_plan in enumerate(manifest["slides"]):
        slide_number = int(slide_plan.get("slide", slide_index + 1))
        groups = slide_plan["groups"]
        for state_index in range(len(groups) + 1):
            path = state_dir / f"slide_{slide_number:02d}" / f"state_{state_index:02d}.png"
            if not path.exists():
                raise RuntimeError(f"missing rendered state: {path}")
            sequence.append({
                "slide": slide_number,
                "state": state_index,
                "group": state_index,
                "effect": "initial" if state_index == 0 else groups[state_index - 1]["effect"],
                "purpose": "initial" if state_index == 0 else groups[state_index - 1]["purpose"],
                "path": str(path.resolve()),
            })
    return sequence


def probe_duration(ffprobe: str, path: Path) -> float:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def probe_has_audio(ffprobe: str, path: Path) -> bool:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def media_geometry(source: Path, entry: dict[str, Any], width: int, height: int) -> dict[str, int]:
    if all(key in entry for key in ("x", "y", "width", "height")):
        return {key: int(entry[key]) for key in ("x", "y", "width", "height")}
    prs = Presentation(str(source))
    slide = prs.slides[int(entry["slide"]) - 1]
    sid = int(entry["shape_id"])
    for shape in slide.shapes:
        if shape.shape_id == sid:
            return {
                "x": round(shape.left / prs.slide_width * width),
                "y": round(shape.top / prs.slide_height * height),
                "width": round(shape.width / prs.slide_width * width),
                "height": round(shape.height / prs.slide_height * height),
            }
    raise RuntimeError(f"media shape {sid} not found on slide {entry['slide']}")


def transition_frame(previous: Image.Image, current: Image.Image, effect: str, progress: float) -> Image.Image:
    progress = min(max(progress, 0.0), 1.0)
    if effect == "appear":
        return current if progress >= 0.5 else previous
    if effect == "wipe":
        frame = previous.copy()
        reveal_width = max(1, round(current.width * progress))
        frame.paste(current.crop((0, 0, reveal_width, current.height)), (0, 0))
        return frame
    if effect in {"zoom", "circle", "circle(in)"}:
        mask = Image.new("L", current.size, 0)
        draw = ImageDraw.Draw(mask)
        radius = math.hypot(current.width, current.height) * 0.55 * progress
        cx, cy = current.width / 2, current.height / 2
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=255)
        return Image.composite(current, previous, mask)
    return Image.blend(previous, current, progress)


@dataclass
class Timing:
    fps: int
    frame: int = 0

    @property
    def seconds(self) -> float:
        return self.frame / self.fps


def write_base_video(
    sequence: list[dict[str, Any]],
    media_entries: list[dict[str, Any]],
    base_output: Path,
    timeline_output: Path,
    ffmpeg: str,
    width: int,
    height: int,
    fps: int,
    transition_seconds: float,
    initial_hold: float,
    group_hold: float,
    slide_hold: float,
    media_tail_hold: float,
) -> tuple[float, list[dict[str, Any]]]:
    base_output.parent.mkdir(parents=True, exist_ok=True)
    media_lookup = {(int(item["slide"]), int(item["after_group"])): item for item in media_entries}
    timing = Timing(fps=fps)
    timeline: list[dict[str, Any]] = []
    command = [
        ffmpeg,
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(base_output),
    ]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE)
    if proc.stdin is None:
        raise RuntimeError("failed to open ffmpeg input pipe")

    def emit(image: Image.Image, count: int) -> None:
        rgb = image.convert("RGB")
        payload = np.asarray(rgb, dtype=np.uint8).tobytes()
        for _ in range(max(0, count)):
            proc.stdin.write(payload)
            timing.frame += 1

    previous: Image.Image | None = None
    previous_slide: int | None = None
    try:
        for item in sequence:
            current = Image.open(item["path"]).convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
            start = timing.seconds
            is_new_slide = previous_slide is not None and item["slide"] != previous_slide
            if previous is None:
                transition_frames = 0
            else:
                transition_frames = round(transition_seconds * fps)
                effect = "fade" if is_new_slide else item["effect"]
                for index in range(transition_frames):
                    alpha = (index + 1) / transition_frames
                    emit(transition_frame(previous, current, effect, alpha), 1)
            hold = initial_hold if item["state"] == 0 else group_hold
            if item["state"] == 0 and is_new_slide:
                hold = slide_hold
            emit(current, round(hold * fps))
            timeline.append({
                "kind": "state",
                "slide": item["slide"],
                "group": item["group"],
                "effect": item["effect"],
                "purpose": item["purpose"],
                "start": round(start, 3),
                "end": round(timing.seconds, 3),
            })

            media = media_lookup.get((int(item["slide"]), int(item["group"])))
            if media:
                media_start = timing.seconds
                emit(current, round(float(media["duration"]) * fps))
                media_end = timing.seconds
                emit(current, round(media_tail_hold * fps))
                media["start"] = round(media_start, 3)
                media["end"] = round(media_end, 3)
                timeline.append({
                    "kind": "media",
                    "slide": item["slide"],
                    "after_group": item["group"],
                    "shape_id": media.get("shape_id"),
                    "file": media["file"],
                    "start": media["start"],
                    "end": media["end"],
                    "duration": round(float(media["duration"]), 3),
                    "audio_source": "ppt_media" if media.get("has_audio") else "none",
                })
            previous = current
            previous_slide = int(item["slide"])
    finally:
        proc.stdin.close()
        return_code = proc.wait()
        if return_code:
            raise RuntimeError(f"ffmpeg base-video encoder failed with exit code {return_code}")

    timeline_output.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    return timing.seconds, timeline


def compose_media(
    base_video: Path,
    media_entries: list[dict[str, Any]],
    output: Path,
    ffmpeg: str,
    total_duration: float,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [ffmpeg, "-y", "-i", str(base_video)]
    for entry in media_entries:
        command += ["-i", str(Path(entry["file"]))]
    command += ["-f", "lavfi", "-t", f"{total_duration:.6f}", "-i", "anullsrc=r=48000:cl=stereo"]

    filters: list[str] = []
    video_source = "[0:v]"
    for index, entry in enumerate(media_entries, start=1):
        geometry = entry["geometry"]
        filters.append(
            f"[{index}:v]scale={geometry['width']}:{geometry['height']}:force_original_aspect_ratio=decrease,"
            f"pad={geometry['width']}:{geometry['height']}:(ow-iw)/2:(oh-ih)/2:black,"
            f"setpts=PTS-STARTPTS+{entry['start']}/TB[mv{index}]"
        )
        next_video = f"[vo{index}]"
        filters.append(
            f"{video_source}[mv{index}]overlay={geometry['x']}:{geometry['y']}:"
            f"enable='between(t,{entry['start']},{entry['end']})':eof_action=pass{next_video}"
        )
        video_source = next_video

    audio_inputs: list[str] = []
    for index, entry in enumerate(media_entries, start=1):
        if not entry.get("has_audio"):
            continue
        delay = round(float(entry["start"]) * 1000)
        filters.append(f"[{index}:a]aresample=48000,adelay={delay}|{delay}[ma{index}]")
        audio_inputs.append(f"[ma{index}]")

    silence_index = len(media_entries) + 1
    if audio_inputs:
        filters.append(
            f"[{silence_index}:a]{''.join(audio_inputs)}amix=inputs={len(audio_inputs) + 1}:duration=first:dropout_transition=0[aout]"
        )
    else:
        filters.append(f"[{silence_index}:a]anull[aout]")

    command += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        video_source,
        "-map",
        "[aout]",
        "-t",
        f"{total_duration:.6f}",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output),
    ]
    run(command)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--media-plan", type=Path)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--base-output", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeline", required=True, type=Path)
    parser.add_argument("--soffice", default="soffice")
    parser.add_argument("--pdftoppm", default="pdftoppm")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--fontconfig", type=Path)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--dpi", type=int, default=144)
    parser.add_argument("--transition-seconds", type=float, default=0.35)
    parser.add_argument("--initial-hold", type=float, default=1.2)
    parser.add_argument("--group-hold", type=float, default=0.9)
    parser.add_argument("--slide-hold", type=float, default=0.75)
    parser.add_argument("--media-tail-hold", type=float, default=0.35)
    parser.add_argument("--skip-render", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if len(manifest.get("slides", [])) != len(Presentation(str(args.input)).slides):
        raise RuntimeError("manifest and PPTX slide counts differ")

    if args.skip_render:
        sequence = load_sequence(args.state_dir, manifest)
    else:
        if args.state_dir.exists():
            shutil.rmtree(args.state_dir)
        sequence = render_states(
            args.input,
            manifest,
            args.state_dir,
            args.soffice,
            args.pdftoppm,
            args.fontconfig,
            args.dpi,
        )

    media_entries: list[dict[str, Any]] = []
    if args.media_plan:
        media_entries = json.loads(args.media_plan.read_text(encoding="utf-8"))["media"]
    for entry in media_entries:
        media_file = Path(entry["file"]).resolve()
        if not media_file.exists():
            raise RuntimeError(f"media file not found: {media_file}")
        entry["file"] = str(media_file)
        entry["duration"] = probe_duration(args.ffprobe, media_file)
        entry["has_audio"] = probe_has_audio(args.ffprobe, media_file)
        entry["geometry"] = media_geometry(args.input, entry, args.width, args.height)

    total_duration, _ = write_base_video(
        sequence,
        media_entries,
        args.base_output,
        args.timeline,
        args.ffmpeg,
        args.width,
        args.height,
        args.fps,
        args.transition_seconds,
        args.initial_hold,
        args.group_hold,
        args.slide_hold,
        args.media_tail_hold,
    )
    compose_media(args.base_output, media_entries, args.output, args.ffmpeg, total_duration)
    print(json.dumps({
        "output": str(args.output.resolve()),
        "slides": len(manifest["slides"]),
        "groups": sum(len(slide["groups"]) for slide in manifest["slides"]),
        "states": len(sequence),
        "media": media_entries,
        "duration": round(total_duration, 3),
        "resolution": f"{args.width}x{args.height}",
        "fps": args.fps,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
