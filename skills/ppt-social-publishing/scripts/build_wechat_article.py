#!/usr/bin/env python3
"""把 article.md（轻量标记）构建为公众号文章 HTML。

默认保留原有 ``theme-ios-hig-card`` 输出；显式传入
``--theme wechat-ios-showcase@1.0`` 时启用独立精品展示主题。

标记语法:
  #TITLE: 标题            刊头大标题
  #KICKER: 学段·教材      刊头顶部小字
  #SUBTITLE: 副题         刊头副题
  #CHIPS: a,b,c           刊头胶囊章
  ## 章节标题             章节大标题块
  >TIP: 标签|内容         提示卡（口诀/重点）
  :::metrics 19|课件页,40|动画组 :::   指标条
  :::resources ... :::    资料清单（每行 `名称 | 元信息`，首字符为 emoji）
  ![说明](路径)           图片：.gif → GIF 卡；其他 → 整页图卡
  普通段落文本            正文段（支持 **加粗蓝色**）

输出: article.html（图片为本地区域路径，由发布脚本上传后替换）+ assets.json（本地素材清单）
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

BLUE = "#007AFF"
TEXT = "#1C1C1E"
GRAY = "#6E6E73"
GRAY3 = "#8E8E93"
LINE = "#E5E5EA"
FILL = "#F2F2F7"
FONT = "-apple-system,'PingFang SC','Helvetica Neue','Microsoft YaHei',sans-serif"
SHOWCASE_THEME = "wechat-ios-showcase@1.0"
DEFAULT_THEME = "theme-ios-hig-card"


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


def planet_card(planet, qr_src):
    return (f'<section style="margin:24px 0 20px 0;padding:18px 16px;background:{FILL};border-radius:14px;">'
            f'<p style="margin:0 0 8px 0;font-size:17px;font-weight:600;color:{TEXT};text-align:center;">完整资料包已上传知识星球</p>'
            f'<p style="margin:0 0 14px 0;font-size:13px;color:{GRAY};line-height:1.7;text-align:center;">'
            f'全部课件的动画视频、可编辑源文件与互动课件<br />持续更新，成员免费下载</p>'
            f'<figure style="margin:0 0 12px 0;text-align:center;">'
            f'<img src="{esc(qr_src)}" alt="知识星球二维码" style="width:180px;height:180px;display:block;margin:0 auto;'
            f'border-radius:12px;border:1px solid {LINE};" />'
            f'<figcaption style="margin-top:8px;font-size:12px;color:{GRAY3};">长按识别二维码 · 加入「{esc(planet)}」</figcaption></figure>'
            f'<p style="margin:0;text-align:center;"><span style="display:inline-block;padding:9px 34px;background:{BLUE};'
            f'color:#FFFFFF;border-radius:999px;font-size:14px;font-weight:600;">加入知识星球，领取全部资料</span></p></section>')


def footer():
    return (f'<section style="margin:20px 0 0 0;text-align:center;">'
            f'<div style="height:1px;background:{LINE};line-height:1px;font-size:0;margin:0 0 12px 0;">&nbsp;</div>'
            f'<p style="margin:0;font-size:12px;color:{GRAY3};letter-spacing:1px;">精研AI教育，接顶制</p></section>')


def showcase_hero(kicker, title, subtitle, chips):
    chip_html = "".join(
        f'<span style="display:inline-block;margin:0 6px 6px 0;padding:4px 10px;background:#F2F2F7;'
        f'border-radius:999px;font-size:12px;color:#3A3A3C;line-height:1.5;">{esc(c)}</span>' for c in chips)
    return (
        '<section style="margin:0 0 24px 0;padding:10px 12px 20px 12px;background:#FFFFFF;">'
        f'<p style="margin:0 0 12px 0;font-size:12px;font-weight:600;color:{BLUE};letter-spacing:1.2px;line-height:1.6;">'
        f'{esc(kicker)}</p>'
        f'<p style="margin:0 0 12px 0;font-size:23px;font-weight:700;color:{TEXT};line-height:1.42;letter-spacing:-0.3px;">'
        f'{esc(title)}</p>'
        '<div style="width:42px;height:3px;margin:0 0 14px 0;background:#007AFF;border-radius:999px;line-height:3px;font-size:0;">&nbsp;</div>'
        f'<p style="margin:0 0 14px 0;font-size:15px;color:#3A3A3C;line-height:1.8;">{esc(subtitle)}</p>'
        f'<p style="margin:0;line-height:1;">{chip_html}</p></section>')


def showcase_chapter(title, number):
    return (
        '<section style="margin:34px 0 16px 0;padding:0 12px;">'
        f'<p style="margin:0 0 5px 0;font-size:12px;font-weight:700;color:{BLUE};letter-spacing:1.4px;">'
        f'CHAPTER {number:02d}</p>'
        f'<p style="margin:0;font-size:20px;font-weight:700;color:{TEXT};line-height:1.5;">{esc(title)}</p>'
        '</section>')


def showcase_paragraph(text):
    text = esc(text)
    while "**" in text:
        text = text.replace("**", f'<strong style="color:{BLUE};font-weight:600;">', 1).replace("**", "</strong>", 1)
    return (
        '<section style="margin:0 0 16px 0;padding:0 12px;">'
        f'<p style="margin:0;font-size:15px;color:{TEXT};line-height:1.9;text-align:justify;">{text}</p></section>')


def showcase_tip(label, content):
    return (
        '<section style="margin:4px 8px 22px 8px;padding:15px 16px;background:#F2F7FF;border-left:3px solid #007AFF;'
        'border-radius:4px 16px 16px 4px;">'
        f'<p style="margin:0 0 6px 0;font-size:12px;font-weight:700;color:{BLUE};letter-spacing:1px;">{esc(label)}</p>'
        f'<p style="margin:0;font-size:16px;font-weight:600;color:{TEXT};line-height:1.75;">{esc(content)}</p></section>')


def showcase_media(src, caption, is_gif):
    kind = "动态演示" if is_gif else "课件实景"
    return (
        '<section style="margin:4px 4px 24px 4px;padding:8px 8px 12px 8px;background:#F2F2F7;border-radius:18px;">'
        '<figure style="margin:0;">'
        f'<img src="{esc(src)}" alt="{esc(caption or "配图")}" style="max-width:100%;height:auto;display:block;margin:0 auto;'
        'border-radius:13px;border:1px solid #E5E5EA;background:#FFFFFF;" />'
        f'<figcaption style="margin:10px 4px 0 4px;font-size:12px;color:{GRAY};line-height:1.65;">'
        f'<span style="display:inline-block;margin-right:7px;padding:2px 7px;background:#FFFFFF;border-radius:999px;'
        f'font-size:11px;font-weight:600;color:{BLUE};">{kind}</span>{esc(caption or "")}</figcaption>'
        '</figure></section>')


def showcase_metrics(pairs):
    width = 100 / max(len(pairs), 1)
    tds = "".join(
        f'<td style="width:{width:.2f}%;border:none;vertical-align:top;padding:12px 3px;">'
        f'<p style="margin:0;font-size:21px;font-weight:700;color:{TEXT};line-height:1.2;">{esc(v)}</p>'
        f'<p style="margin:5px 0 0 0;font-size:11px;color:{GRAY};line-height:1.4;">{esc(k)}</p></td>'
        for v, k in pairs)
    return (
        '<section style="margin:2px 4px 24px 4px;padding:5px;background:#F2F2F7;border-radius:18px;">'
        f'<table style="width:100%;border-collapse:collapse;text-align:center;background:#FFFFFF;border-radius:14px;"><tr>{tds}</tr></table>'
        '</section>')


def showcase_resources(rows):
    sections = ""
    for i, (name, meta) in enumerate(rows):
        border = 'border-bottom:1px solid #E5E5EA;' if i < len(rows) - 1 else ""
        sections += (
            f'<section style="padding:13px 15px;{border}">'
            f'<p style="margin:0 0 4px 0;font-size:15px;font-weight:600;color:{TEXT};line-height:1.55;">{esc(name)}</p>'
            f'<p style="margin:0;font-size:12px;color:{GRAY};line-height:1.6;">{esc(meta)}</p></section>')
    return (
        '<section style="margin:0 4px 24px 4px;padding:5px;background:#F2F2F7;border-radius:18px;">'
        '<section style="background:#FFFFFF;border-radius:14px;overflow:hidden;">'
        f'<p style="margin:0;padding:14px 15px 6px 15px;font-size:12px;font-weight:700;color:{BLUE};letter-spacing:1px;">PACKAGE CONTENTS</p>'
        f'{sections}</section></section>')


def showcase_planet_card(planet, qr_src):
    return (
        '<section style="margin:34px 4px 22px 4px;padding:20px 16px;background:#F2F2F7;border-radius:20px;">'
        f'<p style="margin:0 0 7px 0;text-align:center;font-size:12px;font-weight:700;color:{BLUE};letter-spacing:1.2px;">完整资料包</p>'
        f'<p style="margin:0 0 9px 0;text-align:center;font-size:19px;font-weight:700;color:{TEXT};line-height:1.5;">进入「{esc(planet)}」继续学习</p>'
        f'<p style="margin:0 0 14px 0;text-align:center;font-size:13px;color:{GRAY};line-height:1.75;">'
        '课件动画视频、可编辑源文件、离线互动与教学设计均已整理</p>'
        '<!-- WECHAT_MINIPROGRAM_INSERT: 在此插入知识星球原生小程序卡片；保留下方二维码作为回退入口 -->'
        '<section style="margin:0 0 14px 0;padding:11px 12px;background:#FFFFFF;border-radius:12px;">'
        f'<p style="margin:0;font-size:12px;color:{GRAY};line-height:1.65;text-align:center;">发布草稿时，请在本提示卡上方插入知识星球小程序卡片</p>'
        '</section>'
        f'<figure style="margin:0;text-align:center;">'
        f'<img src="{esc(qr_src)}" alt="知识星球二维码" style="width:168px;max-width:100%;height:auto;display:block;margin:0 auto;'
        'border-radius:14px;border:1px solid #E5E5EA;background:#FFFFFF;" />'
        f'<figcaption style="margin-top:9px;font-size:12px;color:{GRAY3};line-height:1.6;">'
        f'若小程序卡片暂未显示，可长按识别二维码进入「{esc(planet)}」</figcaption></figure></section>')


def showcase_footer():
    return (
        '<section style="margin:22px 12px 4px 12px;text-align:center;">'
        '<div style="height:1px;background:#E5E5EA;line-height:1px;font-size:0;margin:0 0 14px 0;">&nbsp;</div>'
        f'<p style="margin:0;font-size:12px;color:{GRAY3};letter-spacing:1px;">精研AI教育，接顶制</p></section>')


def build(md_text: str, planet: str, planet_qr: str):
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
            import re
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
            planet_card(planet, planet_qr) + footer() + '</section>')
    return html, assets


def build_showcase(md_text: str, planet: str, planet_qr: str):
    """Render the opt-in wechat-ios-showcase@1.0 theme without changing legacy output."""
    body, assets = [], []
    title = kicker = subtitle = ""
    chips = []
    chapter_no = 0

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
        elif ln.startswith("#CHIPS:"):
            flush_para(); chips = [c.strip() for c in ln[len("#CHIPS:"):].split(",") if c.strip()]
        elif ln.startswith("## "):
            flush_para(); chapter_no += 1; body.append(showcase_chapter(ln[3:].strip(), chapter_no))
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
    body.insert(0, showcase_hero(kicker, title, subtitle, chips))
    reg_local(planet_qr)
    article_html = (
        f'<section style="background:#FFFFFF;padding:18px 4px;color:{TEXT};font-family:{FONT};">'
        + "".join(body) + showcase_planet_card(planet, planet_qr) + showcase_footer() + '</section>')
    return article_html, assets


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--article", required=True, help="article.md 路径")
    ap.add_argument("--planet", default="一堂微课")
    ap.add_argument("--planet-qr", required=True, help="星球二维码图片路径")
    ap.add_argument("--out", required=True, help="输出 article.html 路径")
    ap.add_argument("--preview-out", help="可选：输出 640px 本地预览页")
    ap.add_argument("--theme", choices=(DEFAULT_THEME, SHOWCASE_THEME), default=DEFAULT_THEME,
                    help=f"主题；默认 {DEFAULT_THEME}，精品展示请显式选 {SHOWCASE_THEME}")
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
            "selection": "explicit" if args.theme == SHOWCASE_THEME else "default",
            "miniprogram_insert": "manual_after_draft" if args.theme == SHOWCASE_THEME else None,
            "miniprogram_anchor": "WECHAT_MINIPROGRAM_INSERT" if args.theme == SHOWCASE_THEME else None,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.preview_out:
        preview = (
            '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>公众号文章预览</title></head>'
            '<body style="margin:0;background:#E8E8ED;">'
            '<section style="box-sizing:border-box;width:640px;max-width:100%;margin:24px auto;'
            'padding:16px 20px;background:#FFFFFF;border-radius:8px;">'
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
