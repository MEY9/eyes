#!/usr/bin/env python3
"""Verify repository-owned Agent, Skill, plugin, and public MCP contracts.

This script is read-only. It never opens client credential stores, cookies, .env,
SQLite runtime databases, or project delivery directories.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILLS = [
    "read-wechat-articles",
    "ppt-pipeline-catalog",
    "xhs-research",
    "codex-ppt",
    "image-to-editable-ppt",
    "azure-tts",
    "ppt-animation-video",
    "ppt-social-publishing",
]
EXPECTED_ZCODE_AGENTS = [
    "education-design-a.md",
    "education-ppt-b.md",
    "html-courseware.md",
]
SENSITIVE_KEYS = {
    "api_key",
    "access_token",
    "cookie",
    "cookies",
    "password",
    "private_key",
    "secret",
    "token",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def find_sensitive_keys(value: Any, location: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in SENSITIVE_KEYS:
                findings.append(f"{location}.{key}")
            findings.extend(find_sensitive_keys(child, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(find_sensitive_keys(child, f"{location}[{index}]"))
    return findings


def compare_installed_copy(source: Path, installed: Path) -> list[str]:
    drift: list[str] = []
    for source_file in source.rglob("*"):
        if not source_file.is_file() or "__pycache__" in source_file.parts:
            continue
        relative = source_file.relative_to(source)
        installed_file = installed / relative
        if not installed_file.is_file():
            drift.append(f"missing {relative}")
        elif sha256(source_file) != sha256(installed_file):
            drift.append(f"different {relative}")
    return drift


def main() -> int:
    errors: list[str] = []
    notes: list[str] = []

    plugin_path = ROOT / ".zcode-plugin" / "plugin.json"
    marketplace_path = ROOT / "marketplace.json"
    plugin = load_json(plugin_path)
    marketplace = load_json(marketplace_path)

    declared = [Path(item).name for item in plugin.get("skills", [])]
    if declared != EXPECTED_SKILLS:
        errors.append(f"plugin skill order/set differs: {declared!r}")

    market_plugins = marketplace.get("plugins", [])
    market_version = market_plugins[0].get("version") if market_plugins else None
    if plugin.get("version") != market_version:
        errors.append(
            f"plugin version {plugin.get('version')!r} != marketplace {market_version!r}"
        )

    for name in EXPECTED_SKILLS:
        skill_file = ROOT / "skills" / name / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"missing skill contract: {skill_file.relative_to(ROOT)}")
            continue
        head = skill_file.read_text(encoding="utf-8-sig")[:2048]
        match = re.search(r"(?m)^name:\s*(.+?)\s*$", head)
        declared_name = match.group(1).strip() if match else None
        if declared_name != name:
            errors.append(f"{skill_file.relative_to(ROOT)} declares {declared_name!r}")

    deprecated = ROOT / "skills" / "gpt-image2-ppt"
    if deprecated.exists():
        errors.append("deprecated skills/gpt-image2-ppt is present")

    for filename in EXPECTED_ZCODE_AGENTS:
        path = ROOT / "zcode" / "agents" / filename
        if not path.is_file():
            errors.append(f"missing ZCode agent wrapper: {path.relative_to(ROOT)}")
    command = ROOT / "zcode" / "commands" / "education-ppt.md"
    if not command.is_file():
        errors.append("missing zcode/commands/education-ppt.md")

    client_roots = {
        "ZCode": Path.home() / ".zcode" / "skills",
        "Codex": Path.home() / ".codex" / "skills",
    }
    for client, client_root in client_roots.items():
        for name in EXPECTED_SKILLS:
            installed = client_root / name
            if not installed.is_dir():
                continue
            drift = compare_installed_copy(ROOT / "skills" / name, installed)
            if drift:
                preview = ", ".join(drift[:3])
                suffix = " ..." if len(drift) > 3 else ""
                errors.append(
                    f"{client} installed {name} drifts in {len(drift)} file(s): "
                    f"{preview}{suffix}"
                )

    installed_agent_root = Path.home() / ".zcode" / "agents"
    if installed_agent_root.is_dir():
        for filename in EXPECTED_ZCODE_AGENTS:
            source = ROOT / "zcode" / "agents" / filename
            installed = installed_agent_root / filename
            if installed.is_file() and sha256(source) != sha256(installed):
                errors.append(f"ZCode installed agent drifts: {filename}")

    mcp_path = ROOT / "mcp" / "servers.json"
    mcp = load_json(mcp_path)
    leaked_keys = find_sensitive_keys(mcp)
    if leaked_keys:
        errors.append("sensitive MCP keys present: " + ", ".join(leaked_keys))

    for server in mcp.get("servers", []):
        for used_by in server.get("used_by", []):
            if not (ROOT / used_by).exists():
                errors.append(f"MCP {server.get('id')} references missing {used_by}")
        local_path = server.get("local_expected_path")
        if local_path:
            binary = Path(local_path)
            if binary.is_file():
                expected_size = server.get("binary_size_bytes")
                expected_hash = str(server.get("sha256", "")).upper()
                if expected_size is not None and binary.stat().st_size != expected_size:
                    errors.append(f"MCP binary size drift: {binary}")
                if expected_hash and sha256(binary) != expected_hash:
                    errors.append(f"MCP binary hash drift: {binary}")
                notes.append(f"verified local MCP binary: {server.get('id')}")
            else:
                notes.append(f"local MCP binary not installed at optional path: {binary}")

    if errors:
        print("workspace contract: FAILED")
        for error in errors:
            print(f"- {error}")
        for note in notes:
            print(f"- note: {note}")
        return 1

    print("workspace contract: OK")
    print(f"skills: {len(EXPECTED_SKILLS)}")
    print(f"plugin version: {plugin.get('version')}")
    for note in notes:
        print(f"- {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
