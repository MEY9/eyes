"""生成知识星球用的轻量版课件。

约束：知识星球单个附件不能超过 50MB，原课件 51.9MB 超限。

策略（安全优先）：
- 保留 PNG 格式与文件扩展名，不改动任何 .rels / [Content_Types].xml 引用
- 只把分辨率降到展示所需（PPT 页宽 13.33in，1920px 即 144dpi，足够投影）
- 保留 ppt/media/media1.mp4（内嵌 AI 情境视频），避免 p02 视频对象失效

用法：
  python working/make_light_pptx.py [--max-width 1920] [--out 路径]
"""

from __future__ import annotations

import argparse
import io
import os
import shutil
import sys
import zipfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "outputs", "赤壁赋_可编辑版.pptx")


def build(src: str, out: str, max_width: int, quantize: bool) -> tuple[int, int]:
    src_z = zipfile.ZipFile(src, "r")
    tmp = out + ".tmp"
    saved = 0
    total = 0
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as dst:
        for info in src_z.infolist():
            raw = src_z.read(info.filename)
            name = info.filename
            is_png = name.startswith("ppt/media/") and name.lower().endswith(".png")
            if is_png:
                total += 1
                try:
                    im = Image.open(io.BytesIO(raw))
                    mode = im.mode
                    if im.width > max_width:
                        im = im.resize(
                            (max_width, max(1, round(im.height * max_width / im.width))),
                            Image.LANCZOS,
                        )
                    buf = io.BytesIO()
                    if quantize and mode not in ("RGBA", "LA") and not (
                        mode == "P" and "transparency" in im.info
                    ):
                        im.convert("RGB").convert(
                            "P", palette=Image.ADAPTIVE, colors=256
                        ).save(buf, "PNG", optimize=True)
                    else:
                        im.save(buf, "PNG", optimize=True)
                    data = buf.getvalue()
                    if len(data) < len(raw):
                        saved += len(raw) - len(data)
                        raw = data
                except Exception as exc:  # 压缩失败就原样保留，绝不破坏文件
                    print("  ! 跳过 %s: %s" % (name, exc), file=sys.stderr)
            dst.writestr(name, raw)
    src_z.close()
    shutil.move(tmp, out)
    return total, saved


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=os.path.join(ROOT, "outputs", "social", "zsxq", "可编辑课件.pptx"))
    ap.add_argument("--max-width", type=int, default=1920)
    ap.add_argument("--quantize", action="store_true", help="对无透明通道的图做 256 色量化（体积更小，渐变可能出色带）")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    before = os.path.getsize(args.src)
    n, saved = build(args.src, args.out, args.max_width, args.quantize)
    after = os.path.getsize(args.out)
    print("PNG 处理 %d 张，节省 %.1f MB" % (n, saved / 1048576))
    print("原始 %.2f MB -> 轻量版 %.2f MB" % (before / 1048576, after / 1048576))
    limit = 50 * 1048576
    print("星球 50MB 上限：%s" % ("通过" if after < limit else "仍超限，需加 --quantize 或降低 --max-width"))
    return 0 if after < limit else 1


if __name__ == "__main__":
    raise SystemExit(main())
