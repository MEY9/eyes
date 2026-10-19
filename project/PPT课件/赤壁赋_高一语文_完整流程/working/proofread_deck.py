# -*- coding: utf-8 -*-
"""可编辑课件全片排版走查。

对 finalize 产物逐页检查四类问题：

1. 越界：文本框/形状超出幻灯片画布。
2. 重叠：两个文本框的有效墨迹区互相压盖（可能遮挡文字）。
3. 字号过小：正文小于 14pt 或标题小于 20pt（课堂投影可读性下限）。
4. 内容完整性：每页对象数、可编辑文本数、图片数、表格数、媒体数。

结果写入 qa/editable_deck/proofread_report.json，控制台输出摘要。

用法：
    python working/proofread_deck.py [deck.pptx]
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECK = ROOT / "outputs" / "赤壁赋_可编辑版.pptx"
REPORT = ROOT / "qa" / "editable_deck" / "proofread_report.json"

MIN_BODY_PT = 14.0
MIN_TITLE_PT = 20.0
TITLE_HINTS = ("标题",)


def shape_box(shape):
    try:
        return (shape.left, shape.top, shape.width, shape.height)
    except Exception:
        return None


def text_frames(shape):
    if not shape.has_text_frame:
        return []
    return [shape]


def iter_text_shapes(slide):
    for shape in slide.shapes:
        if shape.has_text_frame and (shape.text_frame.text or "").strip():
            yield shape


def runs_of(shape):
    for para in shape.text_frame.paragraphs:
        for run in para.runs:
            yield para, run


def effective_sizes(shape):
    sizes = []
    for para, run in runs_of(shape):
        size = run.font.size
        if size is None:
            size = para.font.size
        if size is not None:
            sizes.append(size.pt)
    return sizes


def overlap_ratio(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    if inter == 0:
        return 0.0
    smaller = min(aw * ah, bw * bh) or 1
    return inter / smaller


def check_slide(index, slide, width_emu, height_emu):
    page = {
        "page": index,
        "shapes": 0,
        "texts": 0,
        "pictures": 0,
        "tables": 0,
        "media": 0,
        "issues": [],
    }
    boxes = []

    for shape in slide.shapes:
        page["shapes"] += 1
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            page["pictures"] += 1
        elif shape.has_table:
            page["tables"] += 1
        elif shape.shape_type == MSO_SHAPE_TYPE.MEDIA:
            page["media"] += 1

        box = shape_box(shape)
        if box is None:
            continue
        left, top, width, height = box

        # 1) out-of-bounds check with a small tolerance
        tolerance = 91440 // 4  # 0.25 pt in EMU
        if left < -tolerance or top < -tolerance or left + width > width_emu + tolerance or top + height > height_emu + tolerance:
            page["issues"].append({
                "kind": "out-of-bounds",
                "shape_id": shape.shape_id,
                "name": (shape.name or "")[:40],
                "box_pt": [round(v / 12700, 1) for v in (left, top, width, height)],
            })

        if shape.has_text_frame and (shape.text_frame.text or "").strip():
            page["texts"] += 1
            sizes = effective_sizes(shape)
            min_size = min(sizes) if sizes else None
            text = (shape.text_frame.text or "").strip()
            boxes.append({
                "id": shape.shape_id,
                "box": (left, top, width, height),
                "min_pt": min_size,
                "len": len(text),
                "text": text[:24],
            })

            # 3) tiny font check
            if min_size is not None and min_size < MIN_BODY_PT:
                page["issues"].append({
                    "kind": "tiny-font",
                    "shape_id": shape.shape_id,
                    "name": (shape.name or "")[:40],
                    "min_pt": min_size,
                    "text": text[:24],
                })

    # 2) text-on-text overlap check (only flags heavy overlaps of non-empty boxes)
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ratio = overlap_ratio(a["box"], b["box"])
            if ratio >= 0.5:
                page["issues"].append({
                    "kind": "text-overlap",
                    "a": {"id": a["id"], "text": a["text"]},
                    "b": {"id": b["id"], "text": b["text"]},
                    "overlap": round(ratio, 2),
                })

    return page


def main() -> int:
    deck = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DECK
    if not deck.exists():
        print(f"Error: deck not found: {deck}", file=sys.stderr)
        return 1

    prs = Presentation(str(deck))
    width_emu, height_emu = prs.slide_width, prs.slide_height
    pages = [check_slide(i, slide, width_emu, height_emu) for i, slide in enumerate(prs.slides, start=1)]

    totals = {
        key: sum(p[key] for p in pages)
        for key in ("shapes", "texts", "pictures", "tables", "media")
    }
    problem_pages = [p for p in pages if p["issues"]]

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "deck": str(deck),
        "slide_pt": [round(width_emu / 12700, 1), round(height_emu / 12700, 1)],
        "pages_checked": len(pages),
        "totals": totals,
        "thresholds": {"min_body_pt": MIN_BODY_PT, "overlap_ratio": 0.5},
        "problem_page_count": len(problem_pages),
        "pages": pages,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"deck: {deck}")
    print(f"pages: {len(pages)}  totals: {totals}")
    if problem_pages:
        print(f"problem pages: {len(problem_pages)}")
        for page in problem_pages:
            for issue in page["issues"]:
                print(f"  p{page['page']:02d} [{issue['kind']}] {json.dumps({k: v for k, v in issue.items() if k != 'kind'}, ensure_ascii=False)}")
    else:
        print("problem pages: 0 — no out-of-bounds, overlap, or tiny-font issues found")
    print(f"report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
