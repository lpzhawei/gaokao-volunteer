@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ============================================
echo   河北省高考志愿填报系统 - 环境安装
echo ============================================
echo.

REM 检查 Python 是否安装
where python > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10 或更高版本
    echo 下载地址：https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/3] 正在创建虚拟环境...
python -m venv venv
if %errorlevel% neq 0 (
    echo [错误] 创建虚拟环境失败
    pause
    exit /b 1
)

echo [2/3] 正在安装依赖包（首次安装可能需要几分钟）...
venv\Scripts\pip.exe install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [错误] 安装依赖失败
    pause
    exit /b 1
)

echo [3/3] 安装完成！
echo.
echo 现在可以双击 "启动系统.bat" 运行程序了
echo.
pause
