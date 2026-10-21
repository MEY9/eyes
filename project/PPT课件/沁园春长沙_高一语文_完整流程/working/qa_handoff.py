# -*- coding: utf-8 -*-
"""Agent A 交接包完整性校验：文件、JSON 合法性、字段一致性。"""
import json
import os
from pathlib import Path

ROOT = Path(r"E:\codex\jiaosdhi\eyes\project\PPT课件\赤壁赋_高一语文_完整流程")

required_files = [
    "working/teaching_design.md",
    "outputs/teaching_design.docx",
    "working/change_log.md",
    "working/ai_assets_manifest.md",
    "working/handoff.md",
    "working/source_audit.md",
    "working/rights_manifest.md",
    "working/lesson_packet.json",
    "working/pipeline_state.json",
    "working/catalog_snapshot.json",
    "qa/teaching_design.pdf",
    "qa/preview_p1.png",
    "qa/preview_p2.png",
]

errors = []
print("=== 文件存在性 ===")
for f in required_files:
    p = ROOT / f
    if p.is_file():
        print(f"  OK   {f}  ({p.stat().st_size//1024}KB)")
    else:
        errors.append(f"缺失文件: {f}")
        print(f"  MISS {f}")

# JSON 合法性
print("\n=== JSON 合法性 ===")
jsons = {}
for f in ["working/lesson_packet.json", "working/pipeline_state.json", "working/catalog_snapshot.json"]:
    try:
        jsons[f] = json.loads((ROOT / f).read_text(encoding="utf-8"))
        print(f"  OK   {f}")
    except Exception as e:
        errors.append(f"JSON 解析失败 {f}: {e}")
        print(f"  FAIL {f}: {e}")

lp = jsons.get("working/lesson_packet.json", {})
ps = jsons.get("working/pipeline_state.json", {})

print("\n=== 字段一致性 ===")
checks = [
    ("deck_id 一致", lp.get("deck_id") == ps.get("deck_id") == "chibifu-g1chn-20261019"),
    ("课时一致", lp.get("lesson_hours") == 1),
    ("总时长一致", sum(s["minutes"] for s in lp.get("teaching_steps", [])) == 45),
    ("AI任务数=2", len(lp.get("ai_tasks", [])) == 2),
    ("AI任务均为planned", all(t.get("status") == "planned" for t in lp.get("ai_tasks", []))),
    ("AI任务均required", all(t.get("required") is True for t in lp.get("ai_tasks", []))),
    ("AI任务均有执行人", all(t.get("execution_owner") for t in lp.get("ai_tasks", []))),
    ("AI任务均有备用方案", all(t.get("fallback") for t in lp.get("ai_tasks", []))),
    ("每个环节有师生活动", all(s.get("teacher_action") and s.get("student_action") for s in lp.get("teaching_steps", []))),
    ("每个环节有评价", all(s.get("assessment") for s in lp.get("teaching_steps", []))),
    ("目标4条", len(lp.get("objectives", [])) == 4),
    ("门禁已通过", ps.get("agent_a_gate", {}).get("status") == "passed"),
    ("阻塞项为空", ps.get("blocking_evidence") == []),
    ("stage 正确", ps.get("stage") == "agent_a_handoff"),
]
for name, ok in checks:
    print(f"  {'OK  ' if ok else 'FAIL'} {name}")
    if not ok:
        errors.append(name)

print("\n=== 密钥泄漏扫描 ===")
import re
patterns = [r"sk-[A-Za-z0-9]{16,}", r"Bearer\s+[A-Za-z0-9._-]{20,}", r"[A-Za-z0-9]{32,}-[A-Za-z0-9]{8,}"]
leaks = []
for p in ROOT.rglob("*"):
    if not p.is_file() or p.suffix not in {".md", ".json", ".py", ".txt"}:
        continue
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for pat in patterns:
        if re.search(pat, txt):
            leaks.append(str(p.relative_to(ROOT)))
            break
print("  无泄漏" if not leaks else f"  可疑文件: {leaks}")
if leaks:
    errors.append("疑似密钥泄漏")

print("\n=== 结论 ===", "PASS" if not errors else f"FAIL ({len(errors)})")
for e in errors:
    print("  !", e)
