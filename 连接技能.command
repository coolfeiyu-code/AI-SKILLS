#!/bin/zsh
# 把本技能库一键连接到本机所有 coding 工具(探测式, 幂等, 零污染)
cd "$(dirname "$0")" || exit 1
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
PY=""
for candidate in python3 /usr/bin/python3 /usr/local/bin/python3 /opt/homebrew/bin/python3; do
  if command -v "$candidate" >/dev/null 2>&1; then PY="$candidate"; break; fi
done
if [ -z "$PY" ]; then
  echo "✗ 没找到 python3（装一个即可: xcode-select --install）"
  read -r "REPLY?按回车关闭…"
  exit 1
fi
"$PY" tools/link.py --all
echo
"$PY" tools/link.py --status
echo
echo "完成后各 coding 工具重启即可读到技能。"
read -r "REPLY?按回车关闭…"
