#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成《赤壁赋》逻辑动画清单 working/animation_manifest_logic.json。

编排依据
--------
不是给每个对象机械套同一种效果，而是按 outline.md 的教学动作分组：

- 页标题/主结论：fade 或 zoom，先入，给整页定调
- 并列结构（四维目标、五段编号、三悲、三个字）：wipe 或 zoom，横向/成组铺开
- 原文引证：fade / appear，在学生已经知道要看什么之后再出现
- 深层结论、 Expressividade 小结、迁移提问：zoom，聚焦

没有进任何组的对象（底图、装饰线、印章、静默矩形）保持静态，
由 render_semantic_video.py 的 state 0 自动保留。

用法：
    python working/build_animation_manifest.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "working" / "shape_inventory.json"
OUT = ROOT / "working" / "animation_manifest_logic.json"

DECK = "outputs/赤壁赋_可编辑版.pptx"


def ids(*args):
    """把 1..24 这样的区间写法的和离散 id 一起展开成 group objects。"""
    out = []
    for a in args:
        if isinstance(a, tuple):
            lo, hi = a
            out.extend(range(lo, hi + 1))
        else:
            out.append(a)
    return [{"shape_id": str(i)} for i in out]


def g(order, purpose, effect, trigger, objects, reason):
    return {
        "order": order,
        "purpose": purpose,
        "effect": effect,
        "trigger": trigger,
        "objects": objects,
        "reason": reason,
    }


# (slide, click_count, groups)
SPEC = [
    (1, 3, [
        g(1, "主标题", "zoom", "onClick", ids(4, 5, 6), "课题主字先聚焦，建立全课对象"),
        g(2, "作者", "fade", "afterPrevious", ids(7, 8), "作者平稳跟进，不抢主字"),
        g(3, "教材信息", "appear", "onClick", ids((9, 24)), "版本单元信息一次性给出，不需逐个动画"),
    ]),
    (2, 2, [
        g(1, "情境视频", "appear", "onClick", ids(6), "先出视频槽位，播完再由媒体计划接管"),
        g(2, "原文引句", "fade", "afterPrevious", ids(4, 5), "视频之后落到文本，从画面转入课文"),
    ]),
    (3, 3, [
        g(1, "他人评价", "wipe", "onClick", ids(5, 6, 7), "林语堂评价逐行铺开，先树立'乐天派'印象"),
        g(2, "出处", "appear", "afterPrevious", ids(8), "引文出处紧跟评价，保证可查证"),
        g(3, "全课主问题", "zoom", "onClick", ids(9), "最后抛出认知冲突，聚焦主问题"),
    ]),
    (4, 3, [
        g(1, "页标题", "fade", "onClick", ids(13), "先入标题"),
        g(2, "四维目标名", "wipe", "onClick", ids((14, 21)), "四个维度横向铺开，体现并列关系"),
        g(3, "四维目标内容", "appear", "afterPrevious", ids((22, 25)), "目标描述同步出现，逐个读即可"),
    ]),
    (5, 4, [
        g(1, "页标题", "fade", "onClick", ids(8), "先入标题"),
        g(2, "一〇七九节点", "wipe", "onClick", ids(3, 6, 9, 13, 10, 14),
          "乌台诗案：时间、事件与处境按时间轴一次成链出现"),
        g(3, "一〇八二节点", "wipe", "onClick", ids(4, 7, 11, 12), "贬谪四年后的赤壁之游，与前节点对照"),
        g(4, "背景小结", "zoom", "onClick", ids(15), "落到'最艰难的岁月'，为后文悲音铺垫"),
    ]),
    (6, 3, [
        g(1, "页标题", "fade", "onClick", ids(4), "先入标题"),
        g(2, "赋体三要素", "wipe", "onClick", ids(2, 5, 6, 7), "文体/文赋/主客问答三栏横向成组出现"),
        g(3, "三要素说明", "appear", "afterPrevious", ids(8, 9, 10), "说明文字与学生阅读同步给出"),
    ]),
    (7, 4, [
        g(1, "页标题", "fade", "onClick", ids(8), "先入标题"),
        g(2, "五个难字", "wipe", "onClick", ids(10, 13, 16, 19, 22), "难字先整体出现，建立待解决问题"),
        g(3, "读音", "appear", "afterPrevious", ids(9, 12, 15, 18, 21), "读音揭示，适合领读"),
        g(4, "释义", "appear", "onClick", ids(11, 14, 17, 20, 23), "释义最后给，留出学生自测空间"),
    ]),
    (8, 4, [
        g(1, "页标题", "fade", "onClick", ids(7), "先入标题"),
        g(2, "三个情感字", "zoom", "onClick", ids(8, 9, 10), "乐悲喜三字放大聚焦，是全课情感骨架"),
        g(3, "情感词出处", "fade", "afterPrevious", ids(11, 12, 13), "三个词在文中的原句位置"),
        g(4, "段落定位", "appear", "afterPrevious", ids(14, 15, 16), "落到具体段落，方便翻书"),
    ]),
    (9, 3, [
        g(1, "页标题", "fade", "onClick", ids(15), "先入标题"),
        g(2, "五段编号", "wipe", "onClick", ids((16, 20)), "一到五横向展开，先有结构框架"),
        g(3, "五段功能", "appear", "afterPrevious", ids((21, 25)), "功能标注同步给出），对应阅读"),
    ]),
    (10, 3, [
        g(1, "页标题", "fade", "onClick", ids(5), "先入标题"),
        g(2, "乐与悲", "zoom", "onClick", ids(6, 7), "两个字放大，先把转折两端摆出来"),
        g(3, "转折处原句", "appear", "afterPrevious", ids(8, 9), "用原句证明转折确实发生在第二段内"),
    ]),
    (11, 5, [
        g(1, "页标题", "fade", "onClick", ids(7), "先入标题"),
        g(2, "上排两角度", "zoom", "onClick", ids(8, 9), "良辰美景先行，是外在条件"),
        g(3, "上排原文", "appear", "afterPrevious", ids(12, 13), "原文佐证紧随，读得出依据"),
        g(4, "下排两角度", "zoom", "onClick", ids(10, 11), "乐事赏心后出，转入主观感受"),
        g(5, "下排原文", "appear", "afterPrevious", ids(14, 15), "原文佐证同前一组结构保持一致"),
    ]),
    (12, 4, [
        g(1, "原句", "fade", "onClick", ids(5), "先给整句，避免断章"),
        g(2, "关键字", "zoom", "onClick", ids(4), "'纵'字放大，聚焦品读对象"),
        g(3, "字义", "appear", "afterPrevious", ids(6), "字义给出，完成字词层面理解"),
        g(4, "心理实质", "zoom", "onClick", ids(7), "升到心理层面，是本页教学落点"),
    ]),
    (13, 3, [
        g(1, "页标题", "fade", "onClick", ids(4), "先入标题"),
        g(2, "四句描写", "wipe", "onClick", ids(5, 6, 7, 8), "四句逐行擦出，模拟箫声绵延"),
        g(3, "手法小结", "zoom", "onClick", ids(9), "概括夸张与比喻，收束到写法"),
    ]),
    (14, 3, [
        g(1, "页标题", "fade", "onClick", ids(8), "先入标题"),
        g(2, "原句逐字", "wipe", "onClick", ids((9, 21)), "竖排歌词逐字擦出，配合朗读节奏"),
        g(3, "三重含义", "appear", "onClick", ids(22, 23, 24), "从字面到传统再到处境，层层深入"),
    ]),
    (15, 4, [
        g(1, "页标题", "fade", "onClick", ids(3), "先入标题"),
        g(2, "乐与悲", "zoom", "onClick", ids(4, 5), "两端大字先立，回扣上一页"),
        g(3, "由乐入悲", "appear", "afterPrevious", ids(8, 9, 10, 11), "过程标签出现，点明转换"),
        g(4, "双重触发", "appear", "onClick", ids(6, 7), "最后给原因，回答'悲从何来'"),
    ]),
    (16, 3, [
        g(1, "页标题", "fade", "onClick", ids(6), "先入标题"),
        g(2, "三悲名称", "zoom", "onClick", ids(7, 8, 9), "三个维度横向并列，是全段总纲"),
        g(3, "三悲原句", "appear", "afterPrevious", ids(10, 11, 12), "原句佐证，方便对照课本"),
    ]),
    (17, 3, [
        g(1, "页标题", "fade", "onClick", ids(4), "先入标题"),
        g(2, "当年之盛", "zoom", "onClick", ids(5, 6), "先铺曹操之盛，形成反差前提"),
        g(3, "而今之问", "zoom", "onClick", ids(7, 8), "'而今安在哉'对照，反差出悲"),
    ]),
    (18, 3, [
        g(1, "页标题", "fade", "onClick", ids(7), "先入标题"),
        g(2, "生命之悲", "zoom", "onClick", ids(8, 9), "渺小感先出，指向空间与存在"),
        g(3, "理想之悲", "zoom", "onClick", ids(10, 11), "难期后出，指向时间与愿"),
    ]),
    (19, 3, [
        g(1, "页标题", "fade", "onClick", ids(11), "先入标题"),
        g(2, "景事情理", "zoom", "onClick", ids(12, 13, 14, 15), "四个字先整体出现"),
        g(3, "四项对应", "appear", "afterPrevious", ids(16, 17, 18, 19), "对应内容揭示，看缝合关系"),
    ]),
    (20, 2, [
        g(1, "页标题", "fade", "onClick", ids(5), "先入标题"),
        g(2, "不变者观之", "zoom", "onClick", ids(6), "全页唯一结论句，放大收束"),
    ]),
    (21, 4, [
        g(1, "页标题", "fade", "onClick", ids(5), "先入标题"),
        g(2, "两种视角", "wipe", "onClick", ids(6, 8), "有限与无尽两种观照方式并列"),
        g(3, "两种结果", "appear", "afterPrevious", ids(7, 9), "结果对照，看视角选择的后果"),
        g(4, "教学落点", "zoom", "onClick", ids(10), "明确'不是不死'，防止误读"),
    ]),
    (22, 3, [
        g(1, "页标题", "fade", "onClick", ids(3), "先入标题"),
        g(2, "不取与取", "zoom", "onClick", ids(4, 5), "两端对立词先立"),
        g(3, "两句取舍", "appear", "afterPrevious", ids(6, 7), "用原句说明各自边界"),
    ]),
    (23, 5, [
        g(1, "页标题", "fade", "onClick", ids(5), "先入标题"),
        g(2, "客与主", "zoom", "onClick", ids(6, 7), "两个大字先并置，制造对峙感"),
        g(3, "同为一人", "appear", "onClick", ids(10), "揭示同一性，是全页转折"),
        g(4, "两重人格", "appear", "afterPrevious", ids(8, 9), "儒者与道者的分工解释"),
        g(5, "主客关系结论", "zoom", "onClick", ids(11), "落到'自我和解'，回应开篇"),
    ]),
    (24, 4, [
        g(1, "页标题", "fade", "onClick", ids(15), "先入标题"),
        g(2, "两栏表头", "zoom", "onClick", ids(16, 17), "先给配对结构：客之三悲对应苏子之三解"),
        g(3, "三对内容", "wipe", "onClick", ids(18, 19, 20, 21, 22, 23), "六条配对项擦出，留出学生思考时间"),
        g(4, "互动入口", "appear", "afterPrevious", ids(24), "最后给入口，先看清内容再操作"),
    ]),
    (25, 4, [
        g(1, "全课收束", "fade", "onClick", ids(5), "先出景情理总纲句"),
        g(2, "景情理", "zoom", "onClick", ids(6, 7, 8), "三个字放大，回扣全文结构"),
        g(3, "三项落点", "appear", "afterPrevious", ids(9, 10, 11), "具体化三项，便于学生记忆"),
        g(4, "迁移提问", "zoom", "onClick", ids(12), "开放式提问收课，延伸到课外"),
    ]),
]


def main() -> int:
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    by_slide = {s["slide"]: {i["id"]: i for i in s["shapes"]} for s in inv["slides"]}

    manifest = {
        "input": DECK,
        "principles": (
            "背景/装饰静止；页标题先入；并列结构成组 wipe 或 zoom；"
            "原文引证在 student 已知结构后才出现（appear/fade）；"
            "深层结论与迁移提问用 zoom 聚焦"
        ),
        "slides": [],
    }

    missing: list[str] = []
    for slide_no, clicks, groups in SPEC:
        page = by_slide.get(slide_no)
        if page is None:
            missing.append("缺少第 %d 页" % slide_no)
            continue
        checked = []
        for grp in groups:
            objs = []
            for o in grp["objects"]:
                sid = int(o["shape_id"])
                if sid not in page:
                    missing.append("p%02d 无 shape_id=%d" % (slide_no, sid))
                    continue
                objs.append(o)
            if not objs:
                continue
            item = dict(grp)
            item["objects"] = objs
            checked.append(item)
        manifest["slides"].append(
            {"slide": slide_no, "click_count": clicks, "groups": checked}
        )

    if missing:
        print("发现问题：")
        for m in missing:
            print("  -", m)
        return 1

    OUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    total_groups = sum(len(s["groups"]) for s in manifest["slides"])
    total_objs = sum(len(g["objects"]) for s in manifest["slides"] for g in s["groups"])
    covered = {int(o["shape_id"]) for s in manifest["slides"] for g in s["groups"] for o in g["objects"]}
    all_ids = {i["id"] for s in inv["slides"] for i in s["shapes"]}
    print("页 %d / 动画组 %d / 参与对象 %d / 静态对象 %d"
          % (len(manifest["slides"]), total_groups, total_objs, len(all_ids - covered)))
    effects = {}
    for s in manifest["slides"]:
        for g in s["groups"]:
            effects[g["effect"]] = effects.get(g["effect"], 0) + 1
    print("效果分布:", effects)
    print("已写入: %s" % OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
