@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo 正在启动河北省高考志愿填报系统...
venv\Scripts\python.exe main.py
if %errorlevel% neq 0 (
    echo 启动失败，请检查环境配置
    pause
)
