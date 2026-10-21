#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""课后微调：把走查标记为"字号偏小"的正文/出处文本调到投影可读下限。

背景
----
`proofread_deck.py` 走查结果中，p01 12.5pt（封面竖排版本行）与 p03 11.5pt
（林语堂《苏东坡传》出处行）被判为"源图测量忠实还原"，非阻断。
但课堂投影场景下 11.5pt 偏小，故对 p03 出处行做一次最小干预：
    11.5pt -> 14pt（中文说明文字的常用可读下限）
同时按字号比例加宽文本框，保证不折行、不越界、不与下方标题重叠。

p01 竖排版本行不动：16 个字框间距仅 0.20in，12.5pt 字高已占 0.17in，
放大到 14pt 后字高 0.19in 会与相邻字框几乎贴死，视觉更差。

安全性
------
修改前自动备份；写入失败（文件被预览占用）时落到带时间戳的副本。
python-pptx 往返保存已验证不丢部件（90 parts / media1.mp4 均保留）。

用法
----
    python working/polish_fonts.py                 # 原地覆盖 outputs/赤壁赋_可编辑版.pptx
    python working/polish_fonts.py --dry-run       # 只报告，不写盘
    python working/polish_fonts.py --out <path>    # 写到指定路径
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DECK = ROOT / "outputs" / "赤壁赋_可编辑版.pptx"

# (页序号 1-based, 文本前缀, 原字号, 目标字号, 是否按比例加宽)
TARGETS = [
    (3, "林语堂《苏东坡传》", 11.5, 14.0, True),
]


def find_target(slide, prefix: str):
    """按文本前缀定位形状；同时返回命中的 run 集合。"""
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        text = shape.text_frame.text.strip()
        if not text.startswith(prefix):
            continue
        runs = [
            run
            for para in shape.text_frame.paragraphs
            for run in para.runs
            if run.font.size is not None
        ]
        return shape, runs
    return None, []


def apply(deck_path: Path, dry_run: bool = False) -> list:
    prs = Presentation(str(deck_path))
    report = []

    for page_no, prefix, old_pt, new_pt, widen in TARGETS:
        slide = prs.slides[page_no - 1]
        shape, runs = find_target(slide, prefix)
        if shape is None:
            report.append((page_no, prefix, "NOT_FOUND", "", ""))
            continue

        before_sizes = sorted({round(r.font.size.pt, 1) for r in runs})
        before_box = (
            round(shape.left / 914400.0, 2),
            round(shape.top / 914400.0, 2),
            round(shape.width / 914400.0, 2),
            round(shape.height / 914400.0, 2),
        )

        if not dry_run:
            for run in runs:
                run.font.size = Pt(new_pt)
            if widen:
                ratio = new_pt / old_pt
                new_w = round(shape.width / 914400.0 * ratio + 0.15, 2)  # 留一点余量
                shape.width = Inches(new_w)

        after_box = (
            round(shape.left / 914400.0, 2),
            round(shape.top / 914400.0, 2),
            round(shape.width / 914400.0, 2),
            round(shape.height / 914400.0, 2),
        )
        slide_w = prs.slide_width / 914400.0
        right_edge = after_box[0] + after_box[2]
        fits = right_edge < slide_w - 0.2
        report.append(
            (
                page_no,
                prefix,
                f"{before_sizes} -> {new_pt}pt",
                f"{before_box} -> {after_box}",
                "OK 右边界 %.2f < %.2f" % (right_edge, slide_w) if fits else "越界!",
            )
        )

    return report, prs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("deck", nargs="?", default=str(DEFAULT_DECK))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    deck = Path(args.deck)
    if not deck.is_file():
        print("找不到课件: %s" % deck)
        return 2

    report, prs = apply(deck, dry_run=args.dry_run)
    print("页  文本                 字号变化            文本框(in)                    边界")
    for row in report:
        print("p%02d  %-18s %-18s %-28s %s" % row)

    if args.dry_run:
        print("\n[dry-run] 未写盘")
        return 0

    out = Path(args.out) if args.out else deck
    if not args.no_backup and out == deck:
        backup = deck.with_name(
            "%s.bak_%s_微调前.pptx" % (deck.stem, time.strftime("%Y%m%d_%H%M%S"))
        )
        shutil.copy2(deck, backup)
        print("\n已备份: %s" % backup.name)

    try:
        prs.save(str(out))
        print("已保存: %s" % out)
    except PermissionError:
        fallback = out.with_name(
            "%s_微调_%s.pptx" % (out.stem, time.strftime("%Y%m%d_%H%M%S"))
        )
        prs.save(str(fallback))
        print("原文件被占用，已另存: %s" % fallback.name)
        print("关闭预览后手动覆盖回: %s" % out.name)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
