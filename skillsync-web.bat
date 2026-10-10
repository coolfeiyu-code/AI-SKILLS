@echo off
setlocal
:: AI-SKILLS 技能管理 Web 仪表盘 —— 一键启动(所有机器通用: 仅需 Python 3.11+ 与 git)
:: 注意: 本文件必须保存为 ANSI/GBK 编码(中文 Windows cmd 默认代码页)。
::       若用 UTF-8 保存, 中文会乱码甚至被 cmd 当作命令执行。
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    echo [Error] python not found. Install Python 3.11+ and add it to PATH.
    pause
    exit /b 1
)
:: 启动前清理占用 8766 端口的旧实例(避免旧进程带着旧代码继续服务)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8766 " ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
:: 可选: 解除 GitHub API 限流(60次/小时 -> 5000次/小时)。推荐用用户环境变量(token 不进仓库):
::   setx GITHUB_TOKEN "你的只读PAT"     然后重新双击本 bat 生效
:: (不要把 token 直接写进本文件——本文件会提交到 GitHub, 等于公开泄露)
start "AI-SKILLS Dashboard" python skillsync_web.py
:: 静默等 1 秒让服务先起来, 再打开浏览器(ping 延时法, 无按键提示、无倒计时)
ping -n 2 127.0.0.1 >nul
start "" http://localhost:8766
exit /b 0
