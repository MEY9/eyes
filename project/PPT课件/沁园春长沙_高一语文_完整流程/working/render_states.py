#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""本机环境适配：为 render_semantic_video.py 预生成帧影（state PNG）。

为什么需要这个脚本
------------------
render_semantic_video.py 的 --skip-render 模式要求帧影已存在于
`--state-dir/slide_NN/state_MM.png`。官方路径依赖 `pdftoppm`（poppler），
而本机没有安装 poppler，也不打算为此改动共享的 skill 脚本。

因此这里：
1. 直接复用 skill 自带的 `write_state_variant`，保证 PPTX 变体生成逻辑与官方完全一致；
2. 用 LibreOffice headless 把变体转成 PDF；
3. 用 PyMuPDF 按 dpi 光栅化为 PNG（等价于 `pdftoppm -png -singlefile -r <dpi>`）。

产出后，render_semantic_video.py 用 --skip-render 读取即可。

用法：
    python working/render_states.py [--state-dir ...] [--dpi 144]
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = ROOT.parents[2] / "skills" / "ppt-animation-video" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from render_semantic_video import write_state_variant  # noqa: E402

SOFFICE = r"C:\Program Files\LibreOffice\program\soffice.exe"

DECK = ROOT / "outputs" / "赤壁赋_可编辑版.pptx"
MANIFEST = ROOT / "working" / "animation_manifest_logic.json"
STATE_DIR = ROOT / "working" / "semantic-video" / "states"
DPI = 144


def convert_variants(variants: list[Path], tmp: Path) -> list[Path]:
    cmd = [
        SOFFICE,
        f"-env:UserInstallation={(tmp / 'lo-profile').as_uri()}",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(tmp),
        *[str(v) for v in variants],
    ]
    res = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800
    )
    if res.returncode != 0:
        raise RuntimeError("LibreOffice 转换失败: %s" % res.stdout[-500:])
    pdfs = []
    for v in variants:
        pdf = v.with_suffix(".pdf")
        if not pdf.exists():
            raise RuntimeError("缺少 PDF: %s" % pdf.name)
        pdfs.append(pdf)
    return pdfs


def rasterize(pdf: Path, target: Path, dpi: int) -> None:
    doc = fitz.open(str(pdf))
    page = doc[0]
    pix = page.get_pixmap(dpi=dpi)
    pix.save(str(target))
    doc.close()


def main() -> int:
    import json

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if STATE_DIR.exists():
        shutil.rmtree(STATE_DIR)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    total_states = 0

    for slide_index, slide_plan in enumerate(manifest["slides"]):
        slide_number = int(slide_plan.get("slide", slide_index + 1))
        groups = slide_plan["groups"]
        all_ids = {
            int(o["shape_id"]) for g in groups for o in g.get("objects", [])
        }
        slide_dir = STATE_DIR / f"slide_{slide_number:02d}"
        slide_dir.mkdir(exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="cb-states-%02d-" % slide_number) as tmp:
            tmp = Path(tmp)
            variants = []
            revealed: set[int] = set()
            for state_index in range(len(groups) + 1):
                if state_index:
                    revealed.update(
                        int(o["shape_id"]) for o in groups[state_index - 1].get("objects", [])
                    )
                variant = tmp / f"slide_{slide_number:02d}_state_{state_index:02d}.pptx"
                write_state_variant(DECK, slide_index, revealed, all_ids, variant)
                variants.append(variant)

            pdfs = convert_variants(variants, tmp)
            for state_index, pdf in enumerate(pdfs):
                rasterize(pdf, slide_dir / f"state_{state_index:02d}.png", DPI)
            total_states += len(pdfs)

        print(
            "p%02d 帧影 %d 张 (%.0fs)"
            % (slide_number, len(groups) + 1, time.time() - t0),
            flush=True,
        )

    print("完成：%d 页 / %d 张帧影 / %.0fs" % (len(manifest["slides"]), total_states, time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
