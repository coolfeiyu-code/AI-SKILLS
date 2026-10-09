@echo off
setlocal
:: AI-SKILLS 技能管理器 —— 一键启动图形界面
:: 优先使用带 tcl/tk 的 CPython(Windows Store 桥接版 3.14), 否则回退到 WindowsApps python
set "GUI_PY=C:\Users\13588\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if not exist "%GUI_PY%" set "GUI_PY=C:\Users\13588\AppData\Local\Microsoft\WindowsApps\python.exe"
if not exist "%GUI_PY%" set "GUI_PY=python"

cd /d "%~dp0"
if not exist "%GUI_PY%" (
    echo 未找到可用的 Python, 无法启动图形界面。
    pause
    exit /b 1
)
start "" "%GUI_PY%" "%~dp0skillsync_gui.py"
exit /b 0
