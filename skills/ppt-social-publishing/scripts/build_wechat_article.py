#!/usr/bin/env python3
"""把 article.md（轻量标记）构建为公众号文章 HTML。

默认使用 ``wechat-ios-showcase@1.0`` 精品展示主题；只有用户明确要求旧版时，
才显式传入 ``--theme theme-ios-hig-card``。

标记语法:
  #TITLE: 标题            刊头大标题
  #KICKER: 学段·教材      刊头顶部小字
  #SUBTITLE: 副题         刊头副题
  #CHIPS: a,b,c           兼容旧稿；精品主题不渲染胶囊标签
  ## 章节标题             章节大标题块
  >TIP: 标签|内容         提示段（口诀/重点）
  :::metrics 19|课件页,40|动画组 :::   一行课程信息
  :::resources ... :::    资料清单（每行 `名称 | 元信息`，首字符为 emoji）
  ![说明](路径)           图片：接近正文全宽展示
  普通段落文本            正文段（支持 **加粗蓝色**）

输出: article.html（图片为本地区域路径，由发布脚本上传后替换）+ assets.json（本地素材清单）
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

BLUE = "#2F6BFF"
TEXT = "#243447"
GRAY = "#667085"
GRAY3 = "#98A2B3"
LINE = "#E4EAF1"
FILL = "#F3F6FA"
FONT = "-apple-system,BlinkMacSystemFont,'SF Pro Display','SF Pro Text','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif"
KAITI = "'Kaiti SC','STKaiti','KaiTi','FangSong',serif"
SHOWCASE_THEME = "wechat-ios-showcase@1.0"
LEGACY_THEME = "theme-ios-hig-card"
DEFAULT_THEME = SHOWCASE_THEME


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def hero(kicker, title, subtitle, chips):
    chip_html = "".join(
        f'<span style="display:inline-block;padding:3px 10px;background:#FFFFFF;border-radius:999px;'
        f'font-size:12px;color:{BLUE};margin-right:6px;">{esc(c)}</span>' for c in chips)
    return (f'<section style="margin:0 0 20px 0;padding:18px 16px;background:{FILL};border-radius:14px;">'
            f'<p style="margin:0 0 6px 0;font-size:12px;color:{GRAY};letter-spacing:1px;">{esc(kicker)}</p>'
            f'<p style="margin:0 0 10px 0;font-size:22px;font-weight:600;color:{TEXT};line-height:1.4;">{esc(title)}</p>'
            f'<p style="margin:0 0 12px 0;font-size:14px;color:#3A3A3C;line-height:1.7;">{esc(subtitle)}</p>'
            f'<p style="margin:0;">{chip_html}</p></section>')


def chapter(title):
    return (f'<section style="margin:28px 0 14px 0;">'
            f'<p style="margin:0;font-size:19px;font-weight:600;color:{TEXT};">{esc(title)}</p>'
            f'<div style="margin-top:10px;height:1px;background:{LINE};line-height:1px;font-size:0;">&nbsp;</div></section>')


def paragraph(text):
    text = esc(text)
    while "**" in text:
        text = text.replace("**", f'<strong style="color:{BLUE};">', 1).replace("**", "</strong>", 1)
    return f'<section style="margin:0 0 16px 0;"><p style="margin:0;font-size:15px;color:{TEXT};line-height:1.85;">{text}</p></section>'


def tip(label, content):
    return (f'<section style="margin:0 0 20px 0;padding:14px 16px;background:#EAF3FF;border-radius:14px;">'
            f'<p style="margin:0 0 6px 0;font-size:12px;color:{BLUE};font-weight:600;letter-spacing:1px;">💡 {esc(label)}</p>'
            f'<p style="margin:0;font-size:16px;font-weight:600;color:{TEXT};line-height:1.7;">{esc(content)}</p></section>')


def media(src, caption, is_gif):
    badge = (f'<span style="position:absolute;top:10px;right:10px;padding:2px 8px;background:rgba(0,0,0,0.55);'
             f'border-radius:999px;font-size:11px;color:#FFFFFF;">GIF 动图</span>') if is_gif else ""
    alt = esc(caption or "配图")
    return (f'<section style="margin:0 0 20px 0;"><figure style="margin:0;position:relative;">'
            f'<img src="{esc(src)}" alt="{alt}" style="max-width:100%;height:auto;display:block;margin:0 auto;'
            f'border-radius:12px;border:1px solid {LINE};" />{badge}'
            f'<figcaption style="margin-top:8px;text-align:center;font-size:12px;color:{GRAY3};">{esc(caption or "")}</figcaption>'
            f'</figure></section>')


def metrics(pairs):
    width = 100 / max(len(pairs), 1)
    tds = "".join(
        f'<td style="width:{width:.2f}%;border:none;vertical-align:top;padding:0 3px;">'
        f'<p style="margin:0;font-size:20px;font-weight:600;color:{BLUE};">{esc(v)}</p>'
        f'<p style="margin:2px 0 0 0;font-size:12px;color:{GRAY};">{esc(k)}</p></td>' for v, k in pairs)
    return (f'<section style="margin:0 0 20px 0;padding:14px 0;background:{FILL};border-radius:14px;">'
            f'<table style="width:100%;border-collapse:collapse;text-align:center;"><tr>{tds}</tr></table></section>')


def resources(rows):
    secs = ""
    for i, (name, meta) in enumerate(rows):
        border = f'border-bottom:1px solid {LINE};' if i < len(rows) - 1 else ""
        secs += (f'<section style="padding:11px 16px;{border}">'
                 f'<p style="margin:0 0 3px 0;font-size:14px;color:{TEXT};">{esc(name)}</p>'
                 f'<p style="margin:0;font-size:12px;color:{GRAY3};line-height:1.5;">{esc(meta)}</p></section>')
    return (f'<section style="margin:0 0 20px 0;background:{FILL};border-radius:14px;overflow:hidden;">'
            f'<p style="margin:0;padding:12px 16px 6px 16px;font-size:13px;font-weight:600;color:{GRAY};">资料包清单</p>{secs}</section>')


def planet_card(planet, qr_src=None):
    qr_html = ""
    if qr_src:
        qr_html = (
            f'<figure style="margin:18px 0 0 0;text-align:center;">'
            f'<img src="{esc(qr_src)}" alt="一堂微课知识星球二维码" style="max-width:100%;height:auto;display:block;margin:0 auto;'
            f'border-radius:18px;border:1px solid {LINE};" />'
            f'<figcaption style="margin-top:9px;font-size:12px;color:{GRAY3};line-height:1.6;">点击图片查看大图 · 长按保存后使用微信扫一扫</figcaption>'
            f'</figure>')
    return (f'<section style="margin:34px 4px 12px 4px;padding:24px 18px;background:{FILL};border-radius:22px;">'
            f'<p style="margin:0 0 7px 0;font-size:12px;font-weight:700;color:{BLUE};letter-spacing:1.1px;text-align:center;">完整资料包</p>'
            f'<p style="margin:0 0 9px 0;font-size:20px;font-weight:700;color:{TEXT};line-height:1.5;text-align:center;">进入「{esc(planet)}」查看</p>'
            f'<p style="margin:0;font-size:13px;color:{GRAY};line-height:1.8;text-align:center;">'
            f'可编辑 PPTX、课件动画、离线互动与教学设计</p>'
            '<!-- WECHAT_MINIPROGRAM_INSERT: 在此插入知识星球原生小程序卡片 -->'
            f'{qr_html}</section>')


def showcase_hero(kicker, title, subtitle, chips, cover_src=""):
    """Education-editorial masthead inspired by YiBan's minimal education sets."""
    cover_html = ""
    if cover_src:
        cover_html = (
            '<figure style="margin:24px 0 0 0;">'
            f'<img src="{esc(cover_src)}" alt="课件封面" style="max-width:100%;height:auto;display:block;margin:0 auto;" />'
            '</figure>')
    return (
        '<section style="margin:10px 8px 40px 8px;">'
        f'<p style="margin:0 0 13px 0;text-align:center;font-size:13px;font-weight:600;color:#B4882D;'
        f'letter-spacing:1.5px;line-height:1.7;">{esc(kicker)}</p>'
        f'<p style="margin:0 0 14px 0;text-align:center;font-size:24px;font-weight:700;color:{TEXT};'
        f'line-height:1.5;letter-spacing:0.4px;">{esc(title)}</p>'
        f'<p style="margin:0;text-align:center;font-size:14px;color:{GRAY};line-height:1.85;letter-spacing:0.3px;">{esc(subtitle)}</p>'
        f'{cover_html}</section>')


def showcase_chapter(title, number):
    """教育图文的章节题头，不使用网页分隔线或 UI 标签。"""
    return (
        '<section style="margin:0 8px 22px 8px;text-align:center;">'
        f'<p style="margin:0 0 6px 0;font-size:17px;font-weight:700;color:#D2A13A;letter-spacing:2px;line-height:1.5;">'
        f'{number:02d}</p>'
        f'<p style="margin:0;font-size:20px;font-weight:700;color:{TEXT};line-height:1.55;letter-spacing:0.5px;">{esc(title)}</p>'
        '</section>')


def showcase_subsection(title):
    page_range, separator, heading = title.partition("｜")
    if not separator:
        page_range, heading = "", title
    range_html = (f'<p style="margin:0 0 8px 0;font-size:12px;color:#8A7961;letter-spacing:1px;line-height:1.6;">{esc(page_range)} 页</p>'
                  if page_range else "")
    return (
        '<section style="margin:0 8px 26px 8px;text-align:center;">'
        f'{range_html}'
        f'<p style="margin:0;font-size:18px;font-weight:600;color:#334F50;line-height:1.7;letter-spacing:0.2px;">{esc(heading)}</p>'
        '</section>')


def showcase_block_open(title, number):
    """完整章节纸张区块；阅读节奏来自底色和留白，而非卡片边框。"""
    tones = {"课件简介": "#FAF6EC", "AI 视频": "#F1F5F8",
             "HTML 互动": "#EEF5F0", "资料包内容": "#FAF6EC"}
    tone = tones.get(title, "#FFFFFF")
    padding = "28px 0 0" if title == "PPT 视觉展示" else "28px 12px 8px"
    return (f'<section style="margin:0 0 38px 0;padding:{padding};background:{tone};">'
            + showcase_chapter(title, number))


GROUP_TONES = ("#F5F3EC", "#EFF4F7", "#EEF4F0", "#FAF3E9")


def showcase_group_open(title, number):
    """PPT 长画廊的教学阶段容器，避免所有幻灯片连续铺在同一底色。"""
    tone = GROUP_TONES[(number - 1) % 4]
    page_range, separator, heading = title.partition("｜")
    if not separator:
        page_range, heading = "", title
    range_html = (f'<p style="margin:0 0 6px 0;font-size:12px;color:#8A7961;letter-spacing:1px;line-height:1.6;">{esc(page_range)} 页</p>'
                  if page_range else "")
    heading_html = (
        '<section style="margin:0 8px 26px 8px;text-align:center;">'
        f'{range_html}'
        f'<p style="margin:0;font-size:18px;font-weight:600;color:#334F50;line-height:1.7;letter-spacing:0.2px;">{esc(heading)}</p>'
        '</section>')
    return (f'<section style="margin:28px 0 38px 0;padding:26px 8px 2px;background:{tone};">'
            + heading_html)


def showcase_paragraph(text):
    text = esc(text)
    while "**" in text:
        text = text.replace("**", f'<strong style="color:{BLUE};font-weight:600;">', 1).replace("**", "</strong>", 1)
    return (
        '<section style="margin:0 0 12px 0;padding:0 12px;">'
        f'<p style="margin:0;font-size:16px;color:{TEXT};line-height:1.85;text-align:justify;letter-spacing:0.3px;">{text}</p></section>')


def showcase_tip(label, content):
    return (
        '<section style="margin:8px 12px 30px 12px;padding:18px 20px;background:#FBF8F0;">'
        f'<p style="margin:0 0 8px 0;font-size:12px;font-weight:700;color:#B4882D;letter-spacing:1px;">{esc(label)}</p>'
        f'<p style="margin:0;font-size:17px;font-weight:600;color:{TEXT};line-height:1.85;'
        f'font-family:{KAITI};letter-spacing:0.5px;">{esc(content)}</p></section>')


def showcase_media(src, caption, is_gif):
    """媒体直接融入章节纸张，不为每张图套独立圆角卡片。"""
    caption_text = esc(caption or "")
    alt_text = esc(caption or "配图")
    if is_gif:
        return (
            '<section style="margin:10px 0 20px 0;">'
            '<figure style="margin:0;">'
            f'<img src="{esc(src)}" alt="{alt_text}" style="max-width:100%;height:auto;display:block;margin:0 auto;'
            'background:#FFFFFF;" />'
            f'<figcaption style="margin:8px 8px 0 8px;text-align:center;font-size:12px;color:{GRAY3};line-height:1.7;">{caption_text}</figcaption>'
            '</figure></section>')
    if "互动" in (caption or "") and not (caption or "").startswith("第"):
        label = ('<p style="margin:0 0 8px 0;text-align:center;font-size:12px;font-weight:600;color:#278273;'
                 'letter-spacing:0.8px;">HTML · 离线互动</p>')
    else:
        label = ""
    return (
        '<section style="margin:9px 0 34px 0;">'
        f'{label}<figure style="margin:0;">'
        f'<img src="{esc(src)}" alt="{alt_text}" style="max-width:100%;height:auto;display:block;margin:0 auto;'
        f'" />'
        f'<figcaption style="margin:9px 8px 0 8px;text-align:center;font-size:12px;color:{GRAY3};line-height:1.7;">'
        f'{caption_text}</figcaption></figure></section>')


def showcase_metrics(pairs):
    summary = "　·　".join(f"{esc(value)} {esc(label)}" for value, label in pairs)
    return (
        '<section style="margin:4px 12px 24px 12px;padding:10px 0;">'
        f'<p style="margin:0;text-align:center;font-size:13px;font-weight:600;color:#5F5A50;line-height:1.9;">{summary}</p>'
        '</section>')


def showcase_resources(rows):
    items = []
    for name, meta in rows:
        clean_name = name.lstrip("🎬📝🧩📄 ")
        file_type = meta.split("·", 1)[0].strip().upper()
        items.append(
            '<section style="margin:0 0 20px 0;">'
            f'<p style="margin:0 0 5px 0;font-size:11px;font-weight:700;color:#B4882D;letter-spacing:1.2px;line-height:1.5;">'
            f'{file_type}</p>'
            f'<p style="margin:0 0 5px 0;font-size:16px;font-weight:600;color:{TEXT};line-height:1.6;">{esc(clean_name)}</p>'
            f'<p style="margin:0;font-size:13px;color:{GRAY};line-height:1.7;">{esc(meta)}</p></section>')
    return (
        '<section style="margin:0 14px 36px 14px;">'
        + "".join(items) + '</section>')


def showcase_planet_card(planet, card_src):
    """资料入口：后台在二维码上方插入知识星球原生卡片，二维码始终保留。"""
    qr_html = ""
    if card_src:
        qr_html = (
            '<figure style="margin:0;text-align:center;">'
            f'<img src="{esc(card_src)}" alt="{esc(planet)} 知识星球邀请卡" style="max-width:100%;height:auto;'
            'display:block;margin:0 auto;background:#FFFFFF;" />'
            '<figcaption style="margin-top:10px;font-size:12px;color:#98A2B3;line-height:1.65;">点击图片查看大图 · 长按保存后使用微信扫一扫</figcaption>'
            '</figure>')
    return (f'<section style="margin:8px 0 12px 0;padding:30px 12px 24px;background:#EEF5F0;">'
            '<p style="margin:0 0 5px 0;text-align:center;font-size:18px;font-weight:700;color:#D2A13A;letter-spacing:1px;">END</p>'
            '<p style="margin:0 0 8px 0;text-align:center;font-size:12px;font-weight:600;color:#B4882D;letter-spacing:1px;">完整课件资料</p>'
            f'<p style="margin:0 0 10px 0;text-align:center;font-size:20px;font-weight:700;color:{TEXT};line-height:1.5;">知识星球 · {esc(planet)}</p>'
            f'<p style="margin:0;text-align:center;font-size:13px;color:{GRAY};line-height:1.8;">课件动画视频、可编辑源文件、离线互动与教学设计均已整理</p>'
            '<!-- WECHAT_MINIPROGRAM_INSERT: 在二维码上方插入知识星球原生小程序卡片 -->'
            f'{qr_html}</section>')


def build(md_text: str, planet: str, planet_qr: str | None = None):
    body, assets = [], []
    title = kicker = subtitle = ""
    chips = []

    def reg_local(src):
        if src and not src.startswith(("http://", "https://")):
            if src not in assets:
                assets.append(src)

    lines = md_text.splitlines()
    i, para_buf = 0, []

    def flush_para():
        if para_buf:
            body.append(paragraph(" ".join(para_buf)))
            para_buf.clear()

    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            flush_para()
        elif ln.startswith("#TITLE:"):
            flush_para(); title = ln[len("#TITLE:"):].strip()
        elif ln.startswith("#KICKER:"):
            flush_para(); kicker = ln[len("#KICKER:"):].strip()
        elif ln.startswith("#SUBTITLE:"):
            flush_para(); subtitle = ln[len("#SUBTITLE:"):].strip()
        elif ln.startswith("#CHIPS:"):
            flush_para(); chips = [c.strip() for c in ln[len("#CHIPS:"):].split(",") if c.strip()]
        elif ln.startswith("## "):
            flush_para(); body.append(chapter(ln[3:].strip()))
        elif ln.startswith(">TIP:"):
            flush_para()
            label, content = ln[len(">TIP:"):].split("|", 1)
            body.append(tip(label.strip(), content.strip()))
        elif ln.startswith(":::metrics"):
            flush_para()
            raw = ln[len(":::metrics"):].strip()
            if raw.endswith(":::"):
                raw = raw[:-3].rstrip()
            fields = [p for p in re.split(r"\s*,\s*|\s+(?=[^|\s]+\|)", raw) if p]
            pairs = [tuple(p.split("|", 1)) for p in fields]
            body.append(metrics([(v.strip(), k.strip()) for v, k in pairs]))
        elif ln.strip() == ":::resources":
            flush_para()
            rows, i = [], i + 1
            while i < len(lines) and lines[i].strip() != ":::":
                if "|" in lines[i]:
                    name, meta = lines[i].split("|", 1)
                    rows.append((name.strip(), meta.strip()))
                i += 1
            body.append(resources(rows))
        elif ln.lstrip().startswith("!["):
            flush_para()
            m = re.match(r"!\[(.*?)\]\((.+?)\)", ln.strip())
            caption, src = m.group(1), m.group(2)
            reg_local(src)
            body.append(media(src, caption, src.lower().endswith(".gif")))
        else:
            para_buf.append(ln.strip())
        i += 1
    flush_para()

    if not all((title, kicker, subtitle)):
        raise ValueError("article metadata must include #TITLE, #KICKER and #SUBTITLE")
    body.insert(0, hero(kicker, title, subtitle, chips))
    reg_local(planet_qr)
    html = (f'<section style="background:#FFFFFF;padding:20px 4px;color:{TEXT};'
            f'font-family:{FONT};">' + "".join(body) +
            planet_card(planet, planet_qr) + '</section>')
    return html, assets


def build_showcase(md_text: str, planet: str, planet_qr: str | None = None):
    """Render the opt-in wechat-ios-showcase@1.0 theme without changing legacy output."""
    body, assets = [], []
    title = kicker = subtitle = cover = ""
    chips = []
    chapter_no = 0
    chapter_open = False
    group_open = False
    group_no = 0

    def reg_local(src):
        if src and not src.startswith(("http://", "https://")) and src not in assets:
            assets.append(src)

    lines = md_text.splitlines()
    i, para_buf = 0, []

    def flush_para():
        if para_buf:
            body.append(showcase_paragraph(" ".join(para_buf)))
            para_buf.clear()

    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            flush_para()
        elif ln.startswith("#TITLE:"):
            flush_para(); title = ln[len("#TITLE:"):].strip()
        elif ln.startswith("#KICKER:"):
            flush_para(); kicker = ln[len("#KICKER:"):].strip()
        elif ln.startswith("#SUBTITLE:"):
            flush_para(); subtitle = ln[len("#SUBTITLE:"):].strip()
        elif ln.startswith("#COVER:"):
            flush_para(); cover = ln[len("#COVER:"):].strip(); reg_local(cover)
        elif ln.startswith("#CHIPS:"):
            flush_para(); chips = [c.strip() for c in ln[len("#CHIPS:"):].split(",") if c.strip()]
        elif ln.startswith("## "):
            flush_para()
            if group_open:
                body.append('</section>')
                group_open = False
            if chapter_open:
                body.append('</section>')
            chapter_no += 1
            group_no = 0
            body.append(showcase_block_open(ln[3:].strip(), chapter_no))
            chapter_open = True
        elif ln.startswith("### "):
            flush_para()
            if group_open:
                body.append('</section>')
            group_no += 1
            body.append(showcase_group_open(ln[4:].strip(), group_no))
            group_open = True
        elif ln.startswith(">TIP:"):
            flush_para()
            label, content = ln[len(">TIP:"):].split("|", 1)
            body.append(showcase_tip(label.strip(), content.strip()))
        elif ln.startswith(":::metrics"):
            flush_para()
            raw = ln[len(":::metrics"):].strip()
            if raw.endswith(":::"):
                raw = raw[:-3].rstrip()
            fields = [p for p in re.split(r"\s*,\s*|\s+(?=[^|\s]+\|)", raw) if p]
            pairs = [tuple(p.split("|", 1)) for p in fields]
            body.append(showcase_metrics([(v.strip(), k.strip()) for v, k in pairs]))
        elif ln.strip() == ":::resources":
            flush_para()
            rows, i = [], i + 1
            while i < len(lines) and lines[i].strip() != ":::":
                if "|" in lines[i]:
                    name, meta = lines[i].split("|", 1)
                    rows.append((name.strip(), meta.strip()))
                i += 1
            body.append(showcase_resources(rows))
        elif ln.lstrip().startswith("!["):
            flush_para()
            match = re.match(r"!\[(.*?)\]\((.+?)\)", ln.strip())
            if not match:
                raise ValueError(f"invalid image syntax: {ln}")
            caption, src = match.group(1), match.group(2)
            reg_local(src)
            body.append(showcase_media(src, caption, src.lower().endswith(".gif")))
        else:
            para_buf.append(ln.strip())
        i += 1
    flush_para()

    if not all((title, kicker, subtitle)):
        raise ValueError("article metadata must include #TITLE, #KICKER and #SUBTITLE")
    if group_open:
        body.append('</section>')
    if chapter_open:
        body.append('</section>')
    body.insert(0, showcase_hero(kicker, title, subtitle, chips, cover))
    reg_local(planet_qr)
    article_html = (
        f'<section style="background:#FFFFFF;padding:18px 12px;color:{TEXT};font-family:{FONT};">'
        + "".join(body) + showcase_planet_card(planet, planet_qr) + '</section>')
    return article_html, assets


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--article", required=True, help="article.md 路径")
    ap.add_argument("--planet", default="一堂微课")
    ap.add_argument("--planet-qr", help="知识星球官方邀请卡图片（整卡）")
    ap.add_argument("--out", required=True, help="输出 article.html 路径")
    ap.add_argument("--preview-out", help="可选：输出 640px 本地预览页")
    ap.add_argument("--theme", choices=(SHOWCASE_THEME, LEGACY_THEME), default=DEFAULT_THEME,
                    help=f"主题；默认 {DEFAULT_THEME}，旧版需显式选 {LEGACY_THEME}")
    args = ap.parse_args()

    source = Path(args.article).read_text(encoding="utf-8")
    if args.theme == SHOWCASE_THEME:
        html, assets = build_showcase(source, args.planet, args.planet_qr)
    else:
        html, assets = build(source, args.planet, args.planet_qr)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    Path(out).with_suffix(".assets.json").write_text(
        json.dumps(assets, ensure_ascii=False, indent=1), encoding="utf-8")
    Path(out).with_suffix(".theme.json").write_text(
        json.dumps({
            "theme_id": args.theme,
            "version": "1.0" if args.theme == SHOWCASE_THEME else None,
            "selection": "default" if args.theme == DEFAULT_THEME else "explicit",
            "miniprogram_insert": "manual_after_draft" if args.theme == SHOWCASE_THEME else None,
            "miniprogram_anchor": "WECHAT_MINIPROGRAM_INSERT" if args.theme == SHOWCASE_THEME else None,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.preview_out:
        preview = (
            '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>公众号文章预览</title></head>'
            '<body style="margin:0;background:#FFFFFF;">'
            '<section style="box-sizing:border-box;width:640px;max-width:100%;margin:0 auto;'
            'padding:16px 20px;background:#FFFFFF;">'
            f'{html}</section></body></html>'
        )
        preview_out = Path(args.preview_out)
        preview_out.parent.mkdir(parents=True, exist_ok=True)
        preview_out.write_text(preview, encoding="utf-8")
    print(f"article: {out}")
    if args.preview_out:
        print(f"preview: {args.preview_out}")
    print(f"assets ({len(assets)}):")
    for a in assets:
        print("  ", a)


if __name__ == "__main__":
    main()
