@echo off
setlocal
:: AI-SKILLS 技能管理 Web 仪表盘 —— 一键启动(所有机器通用: 仅需 Python 3.11+ 与 git)
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    echo [Error] python not found. Install Python 3.11+ and add it to PATH.
    pause
    exit /b 1
)
start "AI-SKILLS Dashboard" python skillsync_web.py
timeout /t 1 >nul
start "" http://localhost:8765
exit /b 0
