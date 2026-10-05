#!/usr/bin/env bash
# MiMo 语音输入 Linux 一键启动（双击或终端运行，首次自动建 venv 装依赖）
cd "$(dirname "$0")"

PY=".venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "[初始化] 创建虚拟环境 ..."
  if ! python3 -m venv .venv; then
    echo "[错误] 创建虚拟环境失败（Debian/Ubuntu 请先执行: sudo apt install python3-venv）"
    read -r -p "按回车退出 ..."
    exit 1
  fi
  "$PY" -m ensurepip --upgrade >/dev/null 2>&1
  echo "[初始化] 安装依赖 ..."
  if ! "$PY" -m pip install -q -r requirements.txt; then
    # zhconv 在个别环境构建失败时，用免构建隔离方式补装
    "$PY" -m pip install -q --no-build-isolation zhconv
    "$PY" -m pip install -q -r requirements.txt
  fi
fi

if ! command -v xclip >/dev/null 2>&1 && ! command -v wl-copy >/dev/null 2>&1; then
  echo "[提示] 未检测到剪贴板工具，建议安装: sudo apt install xclip（X11）或 wl-clipboard（Wayland）"
fi

exec "$PY" main.py
