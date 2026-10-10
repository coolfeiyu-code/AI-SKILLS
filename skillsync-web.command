#!/bin/bash
# AI-SKILLS 技能管理 Web 仪表盘 —— macOS 双击启动器(就用这一个, 不要双击 .py)
# 首次使用(或换机同步后)请在终端执行一次: chmod +x skillsync-web.command
# 用法: 双击 -> 自动弹出终端并打开浏览器; 关闭终端窗口 = 停止服务
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "[错误] 未找到 python3。请先安装: 终端执行 xcode-select --install, 或到 python.org 下载"
  read -n 1 -s -r -p "按任意键关闭..."
  exit 1
fi

echo "AI-SKILLS 仪表盘启动中: http://localhost:8766   (关闭本窗口即停止服务)"
# 后台延时 1.5 秒等服务起来, 再自动打开浏览器
( sleep 1.5; open "http://localhost:8766" ) &
exec python3 skillsync_web.py
