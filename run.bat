@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   Lightroom 预设生成器
echo ========================================

where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

if not exist "venv\" (
    echo 首次运行：创建虚拟环境并安装依赖...
    python -m venv venv
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

python main.py
if errorlevel 1 pause
