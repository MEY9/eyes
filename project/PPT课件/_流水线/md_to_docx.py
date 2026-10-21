# -*- coding: utf-8 -*-
"""通用 Markdown → 正式 DOCX 渲染器（语文课件流水线）。

用途：把结构化 Markdown 源文件（如 teaching_design.md）渲染为正式 Word 交付件。

排版口径（Agent A 规则 6 / 规则 4）：
- 黑色、五号（10.5pt）、宋体，包括标题、正文、表格、脚注、图注；
- 标题层级用加粗、编号、缩进、段前后间距区分，**不改变字号**；
- 表格使用普通 Word 表格；
- 不得出现横线、引用符号、加粗标记、代码块标记、反引号、Markdown 表格或字符画。

用法：
    python _流水线/md_to_docx.py --md <项目>/teaching_design.md \
                                  --out <项目>/outputs/teaching_design.docx
可选：
    --title "主标题"（默认取 md 首个 # 行）
    --no-first-heading （md 首行 # 已作文件名时可不重复输出）
"""
import argparse
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

FONT = "宋体"
SIZE = Pt(10.5)  # 五号
BLACK = RGBColor(0, 0, 0)

# 行内加粗标记：**text**
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
# 行内代码标记：`text` —— 正式文档中只保留内容，去掉反引号符号
INLINE_CODE_RE = re.compile(r"`([^`]+)`")


def _set_run(p, text, bold=False):
    r = p.add_run(text)
    r.font.name = FONT
    r.font.size = SIZE
    r.font.bold = bold
    r.font.color.rgb = BLACK
    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    return r


def _add_rich(p, text, base_bold=False):
    """渲染行内加粗标记（输出为真加粗 run），并去掉行内代码反引号符号。"""
    text = INLINE_CODE_RE.sub(r"\1", text)
    pos = 0
    for m in BOLD_RE.finditer(text):
        if m.start() > pos:
            _set_run(p, text[pos:m.start()], base_bold)
        _set_run(p, m.group(1), True)
        pos = m.end()
    if pos < len(text):
        _set_run(p, text[pos:], base_bold)


class Doc:
    def __init__(self):
        self.doc = Document()
        st = self.doc.styles["Normal"]
        st.font.name = FONT
        st.font.size = SIZE
        st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    def _para(self, text="", indent=0, bold=False, align=None,
              space_before=0, space_after=0, line=None):
        p = self.doc.add_paragraph()
        pf = p.paragraph_format
        if indent:
            pf.left_indent = Pt(indent * 21)  # 约等于两个字符
        pf.space_before = Pt(space_before)
        pf.space_after = Pt(space_after)
        if line:
            pf.line_spacing = line
        if align is not None:
            p.alignment = align
        if text:
            _add_rich(p, text, bold)
        return p

    def title(self, text):
        self._para(text, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
                   space_before=0, space_after=12)

    def subtitle(self, text):
        self._para(text, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)

    def h(self, level, text):
        """1→一级节标题，2→二级，3→三级。只靠加粗/缩进/间距区分，字号不变。"""
        ind = {1: 0, 2: 1, 3: 2}.get(level, 0)
        before = {1: 12, 2: 8, 3: 6}.get(level, 6)
        self._para(text, indent=ind, bold=True,
                   space_before=before, space_after=4)

    def body(self, text, indent=1):
        self._para(text, indent=indent, space_after=3)

    def list_item(self, text, depth=0, marker=None):
        t = f"{marker}{text}" if marker else text
        self._para(t, indent=1 + depth, space_after=2)

    def quote(self, text):
        self._para(text, indent=2, space_after=3)

    def code_block(self, lines):
        """板书等预格式化内容：等宽感的缩进段落组，不使用代码块标记。"""
        for ln in lines:
            self._para(ln if ln else " ", indent=3, space_after=0)

    def caption(self, text):
        self._para(text, indent=1, space_after=6)

    def table(self, headers, rows):
        t = self.doc.add_table(rows=1, cols=len(headers))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, h in enumerate(headers):
            c = t.rows[0].cells[i]
            c.text = ""
            _add_rich(c.paragraphs[0], h, True)
        for row in rows:
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = ""
                _add_rich(cells[i].paragraphs[0], str(v))
        self._para("", space_after=4)

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(path)


def _split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _is_separator(line):
    return bool(re.match(r"^\|?[\s:\-\|]+\|?$", line)) and "-" in line


def render(md_text: str, d: Doc, emit_first_heading=True):
    lines = md_text.split("\n")
    i = 0
    first_h1_done = False
    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()

        # 空行
        if not stripped:
            i += 1
            continue

        # 分隔线 --- → 空段落（严禁横线）
        if re.match(r"^-{3,}$", stripped) or re.match(r"^\*{3,}$", stripped):
            d._para("", space_after=4)
            i += 1
            continue

        # 代码块（板书设计）
        if stripped.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i].rstrip())
                i += 1
            i += 1  # 跳过结束 ```
            d.code_block(buf)
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 1 and not first_h1_done:
                first_h1_done = True
                if emit_first_heading:
                    d.title(text)
            elif level == 1:
                d.h(1, text)
            elif level == 2:
                d.h(1, text)
            elif level == 3:
                d.h(2, text)
            else:
                d.h(3, text)
            i += 1
            continue

        # 表格
        if stripped.startswith("|") and i + 1 < len(lines) and _is_separator(lines[i + 1].strip()):
            headers = _split_row(stripped)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_split_row(lines[i].strip()))
                i += 1
            # 补齐列数
            width = len(headers)
            rows = [r + [""] * (width - len(r)) if len(r) < width else r[:width] for r in rows]
            d.table(headers, rows)
            continue

        # 引用
        if stripped.startswith(">"):
            d.quote(stripped.lstrip(">").strip())
            i += 1
            continue

        # 有序列表
        m = re.match(r"^(\s*)(\d+)[.、]\s+(.*)$", line)
        if m:
            depth = len(m.group(1)) // 2
            d.list_item(m.group(3).strip(), depth=depth, marker=f"{m.group(2)}. ")
            i += 1
            continue

        # 无序列表 → 转为圆点引导的缩进段落（不保留 - 符号）
        m = re.match(r"^(\s*)[-*+]\s+(.*)$", line)
        if m:
            depth = len(m.group(1)) // 2
            d.list_item(m.group(2).strip(), depth=depth, marker="· ")
            i += 1
            continue

        # 普通段落
        if stripped.startswith("*") and stripped.endswith("*"):
            # 斜体行（如标注约定）→ 作为小字说明段落，去掉星号
            d.caption(stripped.strip("*"))
        else:
            d.body(stripped)
        i += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-first-heading", action="store_true")
    args = ap.parse_args()

    md_path = Path(args.md)
    if not md_path.is_file():
        print(f"ERROR: 找不到 Markdown 源文件 {md_path}", file=sys.stderr)
        return 1
    md_text = md_path.read_text(encoding="utf-8")

    d = Doc()
    render(md_text, d, emit_first_heading=not args.no_first_heading)
    d.save(args.out)
    print(f"OK: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
