@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo 正在启动河北省高考志愿填报系统...
echo.

REM 优先使用本地 venv（用户 clone 后 setup.bat 创建的）
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main.py
) else if exist "..\venv\Scripts\python.exe" (
    ..\venv\Scripts\python.exe main.py
) else (
    echo [错误] 未找到 Python 虚拟环境
    echo 请先双击 setup.bat 安装环境
    echo.
    pause
    exit /b 1
)

if %errorlevel% neq 0 (
    echo.
    echo 启动失败，请检查环境配置
    pause
)
