@echo off
chcp 65001 >nul
setlocal
:: 把本技能库一键连接到本机所有 coding 工具(探测式, 幂等, 零污染)
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    echo [Error] python not found. Install Python 3.11+ and add it to PATH.
    pause
    exit /b 1
)
python tools\link.py --all
echo.
python tools\link.py --status
echo.
echo 完成后各 coding 工具重启即可读到技能。
pause
