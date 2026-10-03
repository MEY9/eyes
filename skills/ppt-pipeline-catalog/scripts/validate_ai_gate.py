#!/usr/bin/env python3
"""Validate required AI-enrichment tasks before PPT production can continue."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PASS_BEFORE_INTEGRATION = {"qa_passed", "integrated", "delivered"}
PASS_AFTER_INTEGRATION = {"integrated", "delivered"}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"missing JSON: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON {path}: {exc}")
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def resolve(project: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else project / path


def task_list(packet: dict[str, Any]) -> list[dict[str, Any]]:
    raw = packet.get("ai_tasks") or packet.get("ai_empowerment") or []
    if isinstance(raw, dict):
        raw = list(raw.values())
    if not isinstance(raw, list):
        raise ValueError("ai_tasks/ai_empowerment must be a list")
    tasks = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"AI task #{index} must be an object")
        item = dict(item)
        item.setdefault("ai_id", f"AI-{index:02d}")
        item.setdefault("required", not bool(item.get("optional", False)))
        tasks.append(item)
    return tasks


def state_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = state.get("tasks") or state.get("ai_tasks") or []
    if isinstance(raw, dict):
        raw = list(raw.values())
    result: dict[str, dict[str, Any]] = {}
    for item in raw if isinstance(raw, list) else []:
        if isinstance(item, dict) and item.get("ai_id"):
            result[str(item["ai_id"])] = item
    return result


def artifact_paths(project: Path, task: dict[str, Any], state: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    for value in [task.get("resource_path"), state.get("resource_path"), state.get("artifact_dir")]:
        path = resolve(project, value if isinstance(value, str) else None)
        if path:
            paths.append(path)
    artifacts = state.get("artifacts", {})
    if isinstance(artifacts, dict):
        for value in artifacts.values():
            path = resolve(project, value if isinstance(value, str) else None)
            if path:
                paths.append(path)
    return list(dict.fromkeys(paths))


def find_artifact(paths: list[Path], names: set[str], suffixes: set[str] | None = None) -> Path | None:
    for path in paths:
        if path.is_file() and (path.name in names or (suffixes and path.suffix.lower() in suffixes)):
            return path
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and (candidate.name in names or (suffixes and candidate.suffix.lower() in suffixes)):
                    return candidate
    return None


def runtime_ok(path: Path) -> bool:
    try:
        data = load_json(path)
    except ValueError:
        return False
    if str(data.get("status", "")).lower() in {"pass", "passed", "ok"}:
        return True
    checks = data.get("checks")
    if isinstance(checks, dict) and checks:
        for value in checks.values():
            status = value.get("status") if isinstance(value, dict) else value
            if str(status).lower() not in {"pass", "passed", "ok", "not_applicable"}:
                return False
        return True
    return False


def validate(project: Path, require_integrated: bool) -> dict[str, Any]:
    packet_path = project / "working" / "lesson_packet.json"
    packet = load_json(packet_path)
    tasks = task_list(packet)
    state_path = project / "working" / "ai_task_state.json"
    state = load_json(state_path) if state_path.exists() else {}
    states = state_map(state)
    allowed = PASS_AFTER_INTEGRATION if require_integrated else PASS_BEFORE_INTEGRATION
    results: list[dict[str, Any]] = []
    errors: list[str] = []

    for task in tasks:
        ai_id = str(task["ai_id"])
        current = states.get(ai_id, {})
        required = bool(task.get("required", True))
        status = str(current.get("status", task.get("status", "planned")))
        item_errors: list[str] = []
        if not current:
            item_errors.append("missing ai_task_state entry")
        if required and status not in allowed:
            item_errors.append(f"status={status}, expected one of {sorted(allowed)}")
        if not required and status not in allowed and status != "not_applicable":
            item_errors.append(f"optional task has invalid status={status}")

        paths = artifact_paths(project, task, current)
        ai_type = str(task.get("ai_type", "")).lower()
        if "html" in ai_type:
            required_names = {
                "ai-html-01.html", "preview.png", "fallback-static.png",
                "embed-spec.json", "runtime-check.json", "task-result.json",
            }
            for name in required_names:
                if not find_artifact(paths, {name}):
                    item_errors.append(f"missing HTML artifact: {name}")
            runtime = find_artifact(paths, {"runtime-check.json"})
            if runtime and not runtime_ok(runtime):
                item_errors.append("runtime-check.json is not passed")
        elif "素材" in ai_type or "material" in ai_type:
            if not find_artifact(paths, set(), {".png", ".jpg", ".jpeg", ".svg", ".webp"}):
                item_errors.append("missing generated material asset")
            if not find_artifact(paths, {"prompt.txt", "prompt.md", "generation-prompt.txt"}):
                item_errors.append("missing generation prompt")
        elif "视频" in ai_type or "video" in ai_type:
            if required and not find_artifact(paths, set(), {".mp4", ".mov", ".webm"}):
                item_errors.append("missing required AI video")
        elif required and not paths:
            item_errors.append("missing evidence/resource path")

        if item_errors:
            errors.extend(f"{ai_id}: {error}" for error in item_errors)
        results.append({"ai_id": ai_id, "required": required, "status": status, "ok": not item_errors, "errors": item_errors})

    return {"ok": not errors, "project": str(project), "task_count": len(tasks), "tasks": results, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--require-integrated", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        result = validate(args.project.expanduser().resolve(), args.require_integrated)
    except ValueError as exc:
        result = {"ok": False, "errors": [str(exc)]}
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
