#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${CODEX_SKILLS_DIR:-}" ]]; then
  echo "请先设置 CODEX_SKILLS_DIR，例如：export CODEX_SKILLS_DIR=\"/Users/sk/.codex/skills\"" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="$ROOT_DIR/skills/education-ppt-product"
TARGET_DIR="$CODEX_SKILLS_DIR/education-ppt-product"

if [[ ! -f "$SOURCE_DIR/SKILL.md" ]]; then
  echo "找不到 Skill 源文件：$SOURCE_DIR/SKILL.md" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"
cp -R "$SOURCE_DIR/." "$TARGET_DIR/"
echo "已同步：$SOURCE_DIR -> $TARGET_DIR"
