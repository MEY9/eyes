#!/usr/bin/env python3
"""Build a logic-driven, classroom-oriented animated version of the 19-slide deck.

This is intentionally different from per-object auto-animation:
backgrounds stay static, semantic objects are grouped into teaching actions,
and the effect/trigger is chosen per group.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from lxml import etree


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = Path("/private/tmp/powerpoint-animator")
sys.path.insert(0, str(REFERENCE_ROOT))
import auto_animate  # noqa: E402


P = auto_animate.P
NS = auto_animate.NS
INPUT = PROJECT_ROOT / "outputs/诗词三首·行路难_完整流程_可编辑.pptx"
OUTPUT = PROJECT_ROOT / "outputs/诗词三首·行路难_完整流程_逻辑动画版.pptx"
MANIFEST = PROJECT_ROOT / "working/animation_manifest_logic.json"


STATIC_PICTURE_WORDS = (
    "background", "source-preserving", "source-faithful", "cleaned", "clean ",
    "parchment", "xuan-paper", "paper background", "environment background",
    "illustrated landscape", "scenic paper", "landscape background", "region",
    "title brush", "brush banner", "brushstroke", "brush band", "ornament",
    "flourish", "motif", "divider", "accent", "decorative", "cloud-line",
    "red dry brush", "rough red", "dry-brush", "panel", "frame", "branch",
)


def shape_meta(shape):
    tag = etree.QName(shape).localname
    paths = {
        "sp": "./p:nvSpPr/p:cNvPr",
        "pic": "./p:nvPicPr/p:cNvPr",
        "cxnSp": "./p:nvCxnSpPr/p:cNvPr",
        "graphicFrame": "./p:nvGraphicFramePr/p:cNvPr",
    }
    matches = shape.xpath(paths.get(tag, "")) if paths.get(tag) else []
    if not matches:
        return None
    c_nv = matches[0]
    text = " ".join(t.strip() for t in shape.xpath(".//a:t/text()") if t.strip())
    return int(c_nv.get("id")), tag, c_nv.get("name", ""), text


def is_static_picture(name: str) -> bool:
    lowered = name.lower()
    return any(word in lowered for word in STATIC_PICTURE_WORDS)


def select_semantic_shapes(slide_number, slide, shape_source=None):
    """Keep text and meaningful illustrations; discard visual foundations."""
    if shape_source is None:
        shape_source = auto_animate.slide_shapes_xml(slide)
    result = []
    for shape in shape_source:
        meta = shape_meta(shape)
        if not meta:
            continue
        _, tag, name, text = meta
        if tag == "pic" and is_static_picture(name):
            continue
        if tag == "sp" and not text and re.match(r"^(Line|Path|Ellipse|Rect|Roundrect) ", name):
            # Keep the plotted curve on the dedicated emotional-curve slide.
            if slide_number != 7:
                continue
        if tag not in {"sp", "pic", "cxnSp"}:
            continue
        result.append(shape)
    return result


def matches(info, patterns):
    haystack = f"{info.name} {info.text}".lower()
    return any(pattern.lower() in haystack for pattern in patterns)


def make_groups(slide_number, infos):
    """Return ordered semantic groups: (purpose, effect, motion, infos)."""
    unused = {info.sp_id: info for info in infos}
    groups = []

    plans = {
        1: [
            ("封面标题", ["行路难", "李白", "九年级", "从一杯酒读出人生"], "fade", "right"),
            ("人物与主题意象", ["seated Li Bai", "sailing ship", "wine jar", "bronze ewer", "drinking cup"], "zoom", "right"),
        ],
        2: [
            ("单元导入", ["从品酒师"], "fade", "right"),
            ("读：读出酒味", ["读出酒味", "TextBox 28"], "wipe", "right"),
            ("品：画出情感心电图", ["画出情感心电图", "TextBox 29"], "wipe", "right"),
            ("辨：看见诗艺", ["看见诗艺", "TextBox 30"], "appear", "right"),
            ("酿：说出精神力量", ["说出精神力量", "TextBox 31"], "zoom", "right"),
        ],
        3: [
            ("课堂目标", ["今天要酿出什么"], "fade", "right"),
            ("理解诗意诗情", ["理解诗意诗情", "open book"], "wipe", "right"),
            ("绘制情感心电图", ["绘制情感心电图", "heartbeat"], "wipe", "right"),
            ("辨析浪漫主义手法", ["辨析浪漫主义手法", "magnifying"], "appear", "right"),
            ("完成诗歌品鉴卡", ["完成诗歌品鉴卡", "paper and pencil"], "zoom", "right"),
        ],
        4: [
            ("李白与酒", ["李白", "诗仙", "酒仙", "Li Bai seated", "Poet emblem"], "fade", "right"),
            ("酒进入诗歌与生命", ["酒进入李白"], "wipe", "right"),
            ("异常出现", ["停杯不能食"], "zoom", "right"),
        ],
        5: [
            ("阅读任务", ["行路难（其一）", "先读全文"], "fade", "right"),
            ("自由朗读与圈画", ["自由朗读", "圈画酒"], "wipe", "right"),
            ("疏通诗意", ["结合注释"], "wipe", "right"),
            ("寻找异常", ["找出饮酒"], "zoom", "right"),
            ("全诗文本", ["金樽清酒"], "appear", "right"),
        ],
        6: [
            ("关键发现", ["关键发现"], "fade", "right"),
            ("盛宴与不能食", ["金樽清酒", "玉盘珍羞", "酒 vessel", "raised platter"], "wipe", "right"),
            ("动作突变", ["停杯投箸", "fallen cup", "chopsticks"], "zoom", "right"),
            ("内心茫然", ["拔剑四顾", "seated poet"], "fade", "right"),
        ],
        7: [
            ("探究任务", ["探究任务"], "fade", "right"),
            ("情感曲线骨架", ["Line", "Path", "Ellipse"], "wipe", "right"),
            ("四步探究", ["独立阅读", "小组交流", "标注情感高度", "解释上升"], "appear", "right"),
        ],
        8: [
            ("AI互动入口", ["AI互动", "情感心电图"], "fade", "right"),
            ("诗句节点", ["金樽清酒", "停杯投箸", "欲渡黄河", "闲来垂钓", "行路难", "长风破浪"], "wipe", "right"),
            ("操作任务", ["操作任务", "六个诗句节点", "调整情感高度"], "appear", "right"),
            ("AI反馈", ["提交后查看反馈", "看看AI"], "zoom", "right"),
        ],
        9: [
            ("第一处转折", ["金樽清酒", "宴席上升"], "fade", "right"),
            ("第二处转折", ["停杯投箸", "停杯拔剑下沉"], "wipe", "right"),
            ("现实阻隔", ["欲渡黄河", "冰塞川", "现实阻隔"], "zoom", "right"),
        ],
        10: [
            ("情感回升", ["情感曲线二"], "fade", "right"),
            ("两个典故", ["姜尚垂钓", "伊尹梦日", "fisherman", "rising sun"], "wipe", "right"),
            ("共同指向", ["共同指向", "困境中仍有希望"], "zoom", "right"),
        ],
        11: [
            ("再跌与骤升", ["情感曲线三"], "fade", "right"),
            ("追问未来", ["多歧路", "追问未来"], "wipe", "right"),
            ("理想回应", ["长风破浪", "直挂云帆", "sailing ship"], "zoom", "right"),
        ],
        12: [
            ("全诗脉搏", ["全诗朗读", "读出跳荡"], "fade", "right"),
            ("宴席升与不能食沉", ["宴席升", "不能食沉"], "wipe", "right"),
            ("冰塞雪满更沉", ["冰塞雪满"], "wipe", "right"),
            ("垂钓梦日回升", ["垂钓梦日"], "zoom", "right"),
            ("多歧路与云帆", ["多歧路再跋", "云帆济海"], "zoom", "right"),
        ],
        13: [
            ("诗艺问题", ["诗艺问题", "浪漫主义如何"], "fade", "right"),
            ("语言与想象", ["热情奔放", "瑰丽的想象"], "wipe", "right"),
            ("夸张与张力", ["夸张的手法", "理想与现实"], "zoom", "right"),
        ],
        14: [
            ("象征隐喻", ["象征隐喻", "冰塞川"], "wipe", "right"),
            ("用典", ["用典", "垂钓碧溪"], "wipe", "right"),
            ("对比落差", ["对比落差", "盛宴与不能食"], "appear", "right"),
            ("反复反问", ["反复反问", "行路难"], "wipe", "right"),
            ("夸张想象", ["夸张想象", "长风破浪"], "zoom", "right"),
            ("鉴赏链条", ["诗句", "效果", "情感"], "fade", "right"),
        ],
        15: [
            ("证据链练习", ["证据链练习", "把术语说成鉴赏"], "fade", "right"),
            ("手法", ["诗句使用了", "手法"], "wipe", "right"),
            ("内容与效果", ["写出了", "内容", "造成了", "效果"], "wipe", "right"),
            ("情感落点", ["表现了", "情感"], "zoom", "right"),
        ],
        16: [
            ("酿酒隐喻", ["诗心：这杯酒"], "fade", "right"),
            ("原料与酵母", ["原料", "失意", "酵母", "自信"], "wipe", "right"),
            ("工艺与成品", ["工艺", "浪漫主义", "成品", "理想信念"], "wipe", "right"),
            ("诗心结论", ["烈"], "zoom", "right"),
        ],
        17: [
            ("品鉴卡任务", ["完成你的", "诗歌品鉴卡"], "fade", "right"),
            ("原料：失意", ["原料", "失意", "large red-cloth wine jar"], "wipe", "right"),
            ("酵母：自信", ["酵母", "自信", "porcelain vase"], "wipe", "right"),
            ("工艺：浪漫主义手法", ["工艺", "浪漫主义手法", "cooking pot"], "wipe", "right"),
            ("成品：理想信念之酒", ["成品", "理想信念之酒", "amber wine bowl"], "zoom", "right"),
            ("个性表达", ["这杯酒苦在"], "appear", "right"),
        ],
        18: [
            ("展示评价", ["展示评价"], "fade", "right"),
            ("评价标准", ["能用诗句", "能把手法", "能用自己的"], "wipe", "right"),
            ("展示品鉴卡", ["展示2至3份", "诗歌品鉴卡"], "zoom", "right"),
        ],
        19: [
            ("作业与迁移", ["作业与迁移"], "fade", "right"),
            ("背诵与复述", ["背诵并默写", "用情感曲线", "manuscript", "line-chart"], "wipe", "right"),
            ("拓展阅读", ["收集李白", "books"], "wipe", "right"),
            ("鉴赏写作", ["可选", "100字", "Lined paper"], "zoom", "right"),
        ],
    }

    for purpose, patterns, effect, motion in plans.get(slide_number, []):
        selected = [info for info in unused.values() if matches(info, patterns)]
        if selected:
            groups.append({"purpose": purpose, "effect": effect, "motion": motion, "infos": selected})
            for info in selected:
                unused.pop(info.sp_id, None)

    # Remaining semantic objects are presented as a single supporting visual
    # group rather than forcing a separate click for every object.
    rest = sorted(unused.values(), key=lambda info: (info.top, info.left))
    if rest:
        groups.append({"purpose": "辅助视觉组", "effect": "fade", "motion": "right", "infos": rest})
    return groups


def effect_for(info, group):
    effect = group["effect"]
    if effect == "wipe":
        return {"kind": "wipe", "motion": group["motion"], "duration": 650 if info.kind == "text" else 500}
    if effect == "zoom":
        return {"kind": "zoom", "duration": 650 if info.kind != "text" else 500}
    if effect == "appear":
        return {"kind": "appear", "duration": 1}
    return {"kind": "fade", "duration": 500 if info.kind == "text" else 650}


def verified_build_effect(effect, sp_id, ids, node_type="withEffect"):
    """Build a native filter-based entrance effect.

    The reference injector's fade path used a low-level opacity animation and
    its zoom path relied only on a preset ID.  That makes the XML look varied,
    but can collapse to nearly the same visual result in different viewers.
    Here we use PowerPoint's verified ``p:animEffect`` filters directly:
    fade, directional wipe, and circle-in (used as the focus/zoom reveal).
    Appear remains a true instantaneous reveal.
    """
    kind = effect["kind"]
    motion = effect.get("motion", "right")
    duration = str(effect.get("duration", 500))

    if kind == "appear":
        preset_id, preset_subtype, filter_name = "1", "0", None
    elif kind == "fade":
        preset_id, preset_subtype, filter_name = "9", "0", "fade"
    elif kind == "wipe":
        preset_id = "22"
        preset_subtype = {"right": "2", "left": "8", "down": "4", "up": "1"}.get(motion, "2")
        filter_name = f"wipe({motion})"
    elif kind == "zoom":
        # PowerPoint's verified filter vocabulary calls this a circle-in
        # reveal; visually it is the intended focus/zoom entrance.
        preset_id, preset_subtype, filter_name = "18", "12", "circle(in)"
    else:
        preset_id, preset_subtype, filter_name = "1", "0", None

    outer_par = etree.Element(f"{P}par")
    attrs = {
        "id": ids.next(),
        "fill": "hold",
        "nodeType": node_type,
        "grpId": ids.next(),
        "presetID": preset_id,
        "presetClass": "entr",
        "presetSubtype": preset_subtype,
    }
    if filter_name is not None:
        attrs["dur"] = duration
    ctn = auto_animate._sub(outer_par, f"{P}cTn", **attrs)
    st_cond = auto_animate._sub(ctn, f"{P}stCondLst")
    auto_animate._sub(st_cond, f"{P}cond", delay=0)
    child = auto_animate._sub(ctn, f"{P}childTnLst")

    set_el = auto_animate._sub(child, f"{P}set")
    set_bhvr = auto_animate._sub(set_el, f"{P}cBhvr")
    set_ctn = auto_animate._sub(set_bhvr, f"{P}cTn", id=ids.next(), dur=1, fill="hold")
    set_st = auto_animate._sub(set_ctn, f"{P}stCondLst")
    auto_animate._sub(set_st, f"{P}cond", delay=0)
    set_target = auto_animate._sub(set_bhvr, f"{P}tgtEl")
    auto_animate._sub(set_target, f"{P}spTgt", spid=sp_id)
    attr_names = auto_animate._sub(set_bhvr, f"{P}attrNameLst")
    attr_name = etree.SubElement(attr_names, f"{P}attrName")
    attr_name.text = "style.visibility"
    to = auto_animate._sub(set_el, f"{P}to")
    auto_animate._sub(to, f"{P}strVal", val="visible")

    if filter_name is not None:
        anim_effect = auto_animate._sub(
            child, f"{P}animEffect", transition="in", filter=filter_name
        )
        effect_bhvr = auto_animate._sub(anim_effect, f"{P}cBhvr")
        auto_animate._sub(effect_bhvr, f"{P}cTn", id=ids.next(), dur=duration)
        effect_target = auto_animate._sub(effect_bhvr, f"{P}tgtEl")
        auto_animate._sub(effect_target, f"{P}spTgt", spid=sp_id)

    return outer_par


TRANSITIONS = {
    1: ("fade", None), 2: ("push", "l"), 3: ("fade", None),
    4: ("push", "r"), 5: ("fade", None), 6: ("wipe", "l"),
    7: ("fade", None), 8: ("push", "l"), 9: ("fade", None),
    10: ("wipe", "l"), 11: ("fade", None), 12: ("push", "l"),
    13: ("fade", None), 14: ("wipe", "l"), 15: ("fade", None),
    16: ("push", "l"), 17: ("fade", None), 18: ("wipe", "l"),
    19: ("fade", None),
}


def add_transition(slide, slide_number):
    sld = slide._element
    if sld.find(f"{P}transition") is not None:
        return
    kind, direction = TRANSITIONS.get(slide_number, ("fade", None))
    transition = etree.Element(f"{P}transition", spd="fast", advClick="1")
    if kind == "fade":
        etree.SubElement(transition, f"{P}fade")
    elif kind == "push":
        etree.SubElement(transition, f"{P}push", dir=direction or "l")
    else:
        etree.SubElement(transition, f"{P}wipe", dir=direction or "l")
    ext = sld.find(f"{P}extLst")
    timing = sld.find(f"{P}timing")
    if ext is not None:
        ext.addprevious(transition)
    elif timing is not None:
        timing.addprevious(transition)
    else:
        sld.append(transition)


def main():
    original_selector = auto_animate.slide_shapes_xml
    original_processor = auto_animate.process_slide
    original_flow = auto_animate.build_flow
    original_pick = auto_animate.pick_animation
    original_effect_builder = auto_animate._build_effect
    current_groups = []
    current_effects = {}
    manifest = []

    def selector(slide):
        slide_number = len(manifest) + 1
        source_shapes = original_selector(slide)
        selected = select_semantic_shapes(slide_number, slide, source_shapes)
        text_by_id = {
            shape_meta(shape)[0]: shape_meta(shape)[3]
            for shape in source_shapes
            if shape_meta(shape) is not None
        }
        infos = [auto_animate.classify_shape(shape) for shape in selected]
        infos = [info for info in infos if info is not None]
        for info in infos:
            info.text = text_by_id.get(info.sp_id, "")
        groups = make_groups(slide_number, infos)
        current_groups.clear()
        current_effects.clear()
        for group in groups:
            ids = []
            for info in group["infos"]:
                ids.append(info.sp_id)
                current_effects[info.sp_id] = effect_for(info, group)
            current_groups.append(ids)
        manifest.append({
            "slide": slide_number,
            "click_count": len(groups),
            "groups": [
                {
                    "order": i + 1,
                    "purpose": group["purpose"],
                    "effect": group["effect"],
                    "trigger": "onClick" if i == 0 else "afterPrevious",
                    "objects": [
                        {"shape_id": info.sp_id, "name": info.name, "text": info.text, "kind": info.kind}
                        for info in group["infos"]
                    ],
                }
                for i, group in enumerate(groups)
            ],
        })
        return selected

    def flow_builder(shape_infos, orderer=None):
        by_id = {info.sp_id: info for info in shape_infos}
        return [[by_id[sid] for sid in ids if sid in by_id] for ids in current_groups]

    def pick_builder(info):
        return current_effects.get(info.sp_id, original_pick(info))

    def processor(slide, *args, **kwargs):
        add_transition(slide, len(manifest))
        return original_processor(slide, *args, **kwargs)

    auto_animate.slide_shapes_xml = selector
    auto_animate.build_flow = flow_builder
    auto_animate.pick_animation = pick_builder
    auto_animate._build_effect = verified_build_effect
    auto_animate.process_slide = processor
    try:
        auto_animate.process_pptx(str(INPUT), str(OUTPUT), animate_all=True, verbose=True, smart=False)
    finally:
        auto_animate.slide_shapes_xml = original_selector
        auto_animate.build_flow = original_flow
        auto_animate.pick_animation = original_pick
        auto_animate._build_effect = original_effect_builder
        auto_animate.process_slide = original_processor

    MANIFEST.write_text(
        json.dumps({"input": str(INPUT), "output": str(OUTPUT), "slides": manifest}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
