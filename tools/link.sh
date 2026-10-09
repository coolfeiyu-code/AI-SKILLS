#!/usr/bin/env bash
# 把本仓库里每个真正的技能目录（含 SKILL.md）软链到指定工具的 skills 目录。
# 用法: ./tools/link.sh <目标skills目录>
#   例如: ./tools/link.sh ~/.workbuddy/skills
#         ./tools/link.sh ~/.claude/skills
set -e
TARGET="${1:?用法: link.sh <目标skills目录>}"
SRC="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$TARGET"
for d in "$SRC"/*/; do
  name="$(basename "$d")"
  [ -f "$d/SKILL.md" ] || continue
  ln -sfn "$d" "$TARGET/$name"
  echo "linked $name -> $TARGET/$name"
done
echo "完成。目标: $TARGET （建议将该目录视为只读引用，勿在内写中间文件）"
