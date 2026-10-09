@echo off
setlocal
:: AI-SKILLS 技能管理 Web 仪表盘 —— 一键启动(所有机器通用: 仅需 Python + git)
cd /d "%~dp0"
:: 优先用本机 python(Web 版不需要 tkinter, 任意 3.11+ 即可)
start "" python skillsync_web.py
timeout /t 1 >nul
start "" http://localhost:8765
exit /b 0
