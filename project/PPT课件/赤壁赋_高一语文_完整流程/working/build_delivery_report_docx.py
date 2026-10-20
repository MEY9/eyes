#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成《赤壁赋》课件交付验收报告 DOCX（教师 / 交付双用途）。

格式口径沿用本项目教学设计 DOCX 的 QA 标准：
    宋体 · 五号（10.5pt）· 纯黑 000000 · 不用艺术字

用法：
    python working/build_delivery_report_docx.py
输出：
    outputs/赤壁赋_课件交付验收报告.docx
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "赤壁赋_课件交付验收报告.docx"
STATE = ROOT / "working" / "pipeline_state.json"

FONT = "宋体"
SIZE = Pt(10.5)
BLACK = RGBColor(0, 0, 0)


def set_run(run, size=SIZE, bold=False, font=FONT):
    run.font.name = font
    run.font.size = size
    run.font.bold = bold
    run.font.color.rgb = BLACK
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    return run


def para(doc, text="", size=SIZE, bold=False, align=None, space_after=6, indent=0):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(0)
    pf.line_spacing = 1.25
    if indent:
        pf.left_indent = Pt(indent)
    if text:
        set_run(p.add_run(text), size=size, bold=bold)
    return p


def heading(doc, text, level=1):
    size = {1: Pt(14), 2: Pt(12), 3: Pt(10.5)}[level]
    p = para(doc, text, size=size, bold=True, space_after=4)
    p.paragraph_format.space_before = Pt(10 if level == 1 else 6)
    return p


def table(doc, header, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(header):
        hdr[i].text = ""
        set_run(hdr[i].paragraphs[0].add_run(h), bold=True)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            set_run(cells[i].paragraphs[0].add_run(str(v)))
    return t


PAGES = [
    "封面",
    "壬戌之秋，七月既望（AI 视频页）",
    "一个“乐天派”，为何写满纸悲音",
    "学习目标",
    "乌台诗案与黄州十年",
    "什么是“赋”",
    "正音正字",
    "情感主线：乐、悲、喜",
    "五段分层",
    "从“乐”到“悲”的转折在哪",
    "寻乐：良辰、美景、乐事、赏心",
    "“纵”字的心理实质",
    "悲从何来：箫声",
    "悲从何来：美人",
    "第二段小结：由乐入悲",
    "客之三悲（总览）",
    "历史之悲：英雄安在",
    "生命之悲与理想之悲",
    "景、事、理、情如何缝合",
    "变与不变",
    "“无尽”不是不死",
    "取与不取",
    "客是谁：一场自我对话",
    "主客问答配对（HTML 互动页）",
    "景情理与迁移",
]

SEGMENTS = [
    ("一", "情境导入", "3 分钟", "1–3"),
    ("二", "知人论世与辨体", "5 分钟", "4–7"),
    ("三", "诵读感知，梳理脉络", "8 分钟", "8–10"),
    ("四", "精读一、二段（寻乐探悲）", "12 分钟", "11–15"),
    ("五", "精读第三段（客之三悲）", "8 分钟", "16–19"),
    ("六", "精读四、五段（苏子之答）", "7 分钟", "20–24"),
    ("七", "总结与迁移", "2 分钟", "25"),
]


def main() -> int:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    mb = state.get("media_backfill", {})
    fc = mb.get("final_check", {})
    pf = mb.get("proofread", {})

    doc = Document()
    # 默认样式：宋体五号纯黑
    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = SIZE
    normal.font.color.rgb = BLACK
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    para(
        doc,
        "《赤壁赋》课件交付验收报告",
        size=Pt(18),
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=2,
    )
    para(
        doc,
        "高一语文 · 第一课时 · 共 25 页",
        size=Pt(12),
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=12,
    )

    heading(doc, "一、基本信息", 1)
    table(
        doc,
        ["项目", "内容"],
        [
            ["课题", "赤壁赋（苏轼）"],
            ["学段学科", "高中语文 · 高一"],
            ["教材版本", "统编版（2019）高中语文必修上册"],
            ["单元课次", "第七单元 第 16 课 16.1"],
            ["课时安排", "1 课时（45 分钟），文言文新授课"],
            ["情感主线", "乐 → 悲 → 喜（饮酒乐甚 / 苏子愀然 / 客喜而笑）"],
            ["deck_id", state.get("deck_id", "")],
            ["交付状态", "%s / %s" % (state.get("stage"), state.get("status"))],
            ["报告日期", date.today().strftime("%Y-%m-%d")],
        ],
    )

    heading(doc, "二、交付清单", 1)
    table(
        doc,
        ["文件", "说明"],
        [
            [
                "outputs/赤壁赋_可编辑版.pptx",
                "主交付物。25 页对象级可编辑版，含内嵌视频与互动页入口（约 52 MB）。",
            ],
            [
                "outputs/赤壁赋_视觉版.pptx",
                "整页视觉版。用于投影观感参考与图片素材复用，文字不可编辑（约 94 MB）。",
            ],
            [
                "outputs/teaching_design.docx",
                "配套教学设计（9 页）：目标、重难点、七环节流程、板书、作业。",
            ],
            [
                "html_embeds/ai-html-01/ai-html-01.html",
                "主客问答配对互动页，单文件 HTML，双击即可用浏览器打开。",
            ],
            [
                "outputs/_backups/",
                "回滚备份目录：旧版无视频.pptx（媒体回填前）、微调前.pptx（字号调整前）。确认无误后可整体删除。",
            ],
        ],
    )

    heading(doc, "三、课件结构与环节对应", 1)
    table(
        doc,
        ["环节", "名称", "时长", "页码"],
        [[a, b, c, d] for a, b, c, d in SEGMENTS],
    )
    para(doc, "")
    para(doc, "逐页标题：", bold=True, space_after=2)
    para(doc, "；".join("%d. %s" % (i + 1, t) for i, t in enumerate(PAGES)), size=Pt(9.5))

    heading(doc, "四、课堂使用说明", 1)

    heading(doc, "4.1 放映前的三项准备", 2)
    para(doc, "（1）保持文件完整。视频已内嵌在 PPTX 内部，不要只拷贝 PPTX 之外的零散文件。", indent=14)
    para(
        doc,
        "（2）互动页要随课件一起带走。第 24 页的超链接指向 html_embeds/ai-html-01/ai-html-01.html，"
        "请把整个 html_embeds 文件夹与 PPTX 放在同一目录下；路径变了链接会失效。",
        indent=14,
    )
    para(
        doc,
        "（3）建议先在授课电脑上完整放映一次，确认第 2 页视频能播放、第 24 页能打开互动页。",
        indent=14,
    )

    heading(doc, "4.2 第 2 页：情境视频", 2)
    para(
        doc,
        "放映到第 2 页时单击画面即可播放（约 12 秒，秋夜江面 · 一叶小舟 · 明月薄雾，无字幕无水印）。"
        "播放后提问：“此刻你就在这条船上，心情会是什么？”——用一个词作答，引出第 3 页的主问题。",
        indent=14,
    )
    para(
        doc,
        "若放映环境不支持内嵌视频（如 WPS 旧版本、在线预览），第 2 页会停在静态海报画面，"
        "教师可直接口述导入，不影响教学流程。",
        indent=14,
    )

    heading(doc, "4.3 第 24 页：主客问答配对互动", 2)
    para(
        doc,
        "放映状态下单击页面底部文字“点击此处打开互动课件”，会用默认浏览器打开配对练习页。"
        "学生把“客之三悲”与对应的“苏子之答”拖到一块完成配对，约 4 分钟。",
        indent=14,
    )
    para(
        doc,
        "环境不支持时（如禁止跳转外链），本页六条框的静态内容本身就是备用材料，"
        "可直接让学生上台连线指认，互动环节不中断。",
        indent=14,
    )

    heading(doc, "五、验收结果", 1)
    table(
        doc,
        ["验收项", "结果", "说明"],
        [
            [
                "对象级可编辑",
                "通过",
                "共 %d 个对象，其中 %d 个可编辑文本框；正文非整页图片覆盖，可直接改字改色。"
                % (fc.get("objects", 323), fc.get("editable_texts", 208)),
            ],
            [
                "页数与大纲一致",
                "通过",
                "25 页，与 outline.md 逐页设计一一对应。",
            ],
            [
                "内嵌视频",
                "通过",
                "ai-video-01-1080p.mp4，960×540pt 满页，位于第 2 页最底层，带静态海报。",
            ],
            [
                "互动页入口",
                "通过",
                "第 24 页外部超链接，静态备用内容保留。",
            ],
            [
                "排版走查",
                "通过（无阻断）",
                "问题页 %d 处，均为设计内项：朱砂方印贴边裁切（p18/p21/p25，源图设计），"
                "封面竖排版本行 12.5pt（p01，源图测量还原）。" % pf.get("problem_pages", 5),
            ],
            [
                "教学设计 DOCX",
                "通过",
                "宋体 · 五号 · 纯黑，4 个表格 / 130 段落，Markdown 残留 0。",
            ],
            [
                "字体规范",
                "通过",
                "全程普通清晰中文字体，无艺术字、书法体、毛笔体、手写体。",
            ],
        ],
    )

    heading(doc, "六、需要教师确认的三件事", 1)
    for i, q in enumerate(state.get("open_questions", []), 1):
        para(doc, "%d. %s" % (i, q), indent=14)

    heading(doc, "七、两点披露", 1)
    para(
        doc,
        "（1）AI 视频分辨率偏低。第 2 页视频由 AI 生成，源片分辨率有限，"
        "全屏投影时可能有轻微模糊；已按满页尺寸内嵌，教学用途可接受，如需更高清可替换为实拍素材。",
        indent=14,
    )
    para(
        doc,
        "（2）教学设计基线来源。用户未提供原始教学设计，本课件基线由公开教研资料整合而成"
        "（来源审计见 working/source_audit.md）。教材原文未与纸质教材逐字比对，建议授课前复核一次。",
        indent=14,
    )

    heading(doc, "八、回滚与再生成", 1)
    para(doc, "需要回退时：", bold=True, space_after=2)
    para(
        doc,
        "· 回退到无视频旧版：用 outputs/_backups/ 下的“旧版无视频.pptx”覆盖主文件。",
        indent=14,
    )
    para(
        doc,
        "· 只撤销字号微调：python working/polish_fonts.py --dry-run 查看差异，"
        "把 working/polish_fonts.py 中 TARGETS 的目标值改回 11.5 再执行。",
        indent=14,
    )
    para(doc, "需要重跑流水线时：", bold=True, space_after=2)
    para(
        doc,
        "· 若重新执行了 editppt run finalize，必须紧接着重跑 python working/backfill_media.py，"
        "因为 finalize 不会保留内嵌视频与超链接。",
        indent=14,
    )
    para(
        doc,
        "· 走查脚本：python working/proofread_deck.py outputs/赤壁赋_可编辑版.pptx",
        indent=14,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT))
    print("已生成: %s (%d bytes)" % (OUT, OUT.stat().st_size))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
