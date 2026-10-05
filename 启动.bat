@echo off
rem MiMo 语音输入 Windows 一键启动（双击运行，首次自动建 venv 装依赖）
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title MiMo Voice Input
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [初始化] 创建虚拟环境 ...
    py -3 -m venv .venv 2>nul || python -m venv .venv
    if not exist ".venv\Scripts\python.exe" (
        echo [错误] 未找到 Python，请先安装 Python 3.10 及以上版本
        echo        下载地址: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    .venv\Scripts\python.exe -m ensurepip --upgrade >nul 2>&1
    echo [初始化] 安装依赖 ...
    .venv\Scripts\python.exe -m pip install -q -r requirements.txt
    if errorlevel 1 (
        rem zhconv 在个别环境构建失败时，用免构建隔离方式补装
        .venv\Scripts\python.exe -m pip install -q --no-build-isolation zhconv
        .venv\Scripts\python.exe -m pip install -q -r requirements.txt
    )
)

.venv\Scripts\python.exe main.py
if errorlevel 1 (
    echo.
    echo [退出] 程序异常结束，请查看上方错误信息
    pause
)
