#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""最终成品视觉验收：把交付版 PPTX 渲染成 PDF + 25 页拼版图（contact sheet）。

用途
----
媒体回填与字号微调之后，做一次"看得见"的终检：
- 确认 25 页都能正常渲染（不缺页、不空白）
- 确认第 2 页视频海报在位、第 3 页出处行字号已生效、第 24 页入口文字在位
- 产出一张拼版图，一屏看完整套课件

依赖：LibreOffice（soffice）、PyMuPDF（fitz）、Pillow

用法
----
    python working/render_final_qa.py                    # 默认渲染 outputs/赤壁赋_可编辑版.pptx
    python working/render_final_qa.py --deck <path>
    python working/render_final_qa.py --no-convert       # 已有 PDF，只做渲染
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DECK = ROOT / "outputs" / "赤壁赋_可编辑版.pptx"
QA_DIR = ROOT / "qa" / "editable_deck"

SOFFICE_CANDIDATES = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]

# 拼版：5 列 × 5 行，每格 480px 宽
COLS = 5
CELL_W = 480
LABEL_H = 26
PAD = 10


def find_soffice() -> str:
    for c in SOFFICE_CANDIDATES:
        if Path(c).is_file():
            return c
    return ""


def convert(deck: Path, outdir: Path) -> Path:
    soffice = find_soffice()
    if not soffice:
        raise SystemExit("未找到 LibreOffice 的 soffice.exe")
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        soffice,
        "--headless",
        "--norestore",
        "--convert-to",
        "pdf",
        "--outdir",
        str(outdir),
        str(deck),
    ]
    print("转换中: %s" % deck.name)
    t0 = time.time()
    # Windows 下 soffice 输出可能是 GBK，固定 errors=replace 避免解码中断
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    print("  耗时 %.1fs, exit=%s" % (time.time() - t0, res.returncode))
    pdf = outdir / (deck.stem + ".pdf")
    if not pdf.is_file():
        raise SystemExit("转换失败，未生成 %s\n%s" % (pdf, res.stdout[-800:]))
    return pdf


def render_pages(pdf: Path, png_dir: Path, dpi: int = 110) -> list:
    png_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf))
    out = []
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=dpi)
        name = "final_p%02d.png" % i
        path = png_dir / name
        pix.save(str(path))
        out.append(
            {
                "page": i,
                "png": str(path.relative_to(ROOT)).replace("\\", "/"),
                "w": pix.width,
                "h": pix.height,
            }
        )
    doc.close()
    return out


def build_contact_sheet(pages: list, out_png: Path) -> dict:
    rows = (len(pages) + COLS - 1) // COLS
    cell_h = int(CELL_W * 7.5 / 13.333) + LABEL_H  # 16:9
    W = PAD + COLS * (CELL_W + PAD)
    H = PAD + rows * (cell_h + PAD)
    sheet = Image.new("RGB", (W, H), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)

    for idx, item in enumerate(pages):
        r, c = divmod(idx, COLS)
        x = PAD + c * (CELL_W + PAD)
        y = PAD + r * (cell_h + PAD)
        im = Image.open(item["png"]).convert("RGB")
        im = im.resize((CELL_W, cell_h - LABEL_H), Image.LANCZOS)
        sheet.paste(im, (x, y))
        draw.rectangle([x, y, x + CELL_W - 1, y + cell_h - LABEL_H - 1], outline=(190, 190, 190))
        draw.text((x + 4, y + cell_h - LABEL_H + 6), "p%02d" % item["page"], fill=(60, 60, 60))

    sheet.save(str(out_png))
    return {"rows": rows, "cols": COLS, "w": W, "h": H, "pages": len(pages)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", default=str(DEFAULT_DECK))
    ap.add_argument("--no-convert", action="store_true")
    ap.add_argument("--dpi", type=int, default=110)
    args = ap.parse_args()

    deck = Path(args.deck)
    if not deck.is_file():
        print("找不到课件: %s" % deck)
        return 2

    QA_DIR.mkdir(parents=True, exist_ok=True)

    pdf = QA_DIR / (deck.stem + "_final.pdf")
    if not args.no_convert:
        tmp = convert(deck, QA_DIR)
        shutil.move(str(tmp), str(pdf))
    if not pdf.is_file():
        print("缺少 PDF: %s" % pdf)
        return 2
    print("PDF: %s (%.1f MB)" % (pdf.name, pdf.stat().st_size / 1e6))

    png_dir = QA_DIR / "final_pages"
    if png_dir.exists():
        shutil.rmtree(png_dir)
    pages = render_pages(pdf, png_dir, dpi=args.dpi)
    print("渲染页数: %d" % len(pages))

    # 空白页检测：整页像素方差极低 = 可能渲染失败
    blanks = []
    for item in pages:
        im = Image.open(item["png"]).convert("L").resize((64, 36))
        px = list(im.getdata())
        mean = sum(px) / len(px)
        var = sum((v - mean) ** 2 for v in px) / len(px)
        if var < 25:  # 几乎纯色
            blanks.append({"page": item["page"], "mean": round(mean, 1), "var": round(var, 1)})

    sheet_png = QA_DIR / "final_contact_sheet.png"
    meta = build_contact_sheet(pages, sheet_png)
    print("拼版图: %s (%dx%d)" % (sheet_png.name, meta["w"], meta["h"]))

    report = {
        "deck": str(deck.relative_to(ROOT)).replace("\\", "/"),
        "pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"),
        "contact_sheet": str(sheet_png.relative_to(ROOT)).replace("\\", "/"),
        "pages": len(pages),
        "dpi": args.dpi,
        "blank_pages": blanks,
        "sheet": meta,
        "rendered_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    rp = QA_DIR / "final_render_report.json"
    rp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("报告: %s" % rp.name)
    print("疑似空白页: %s" % (blanks if blanks else "无"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
