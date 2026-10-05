#!/bin/bash
# MiMo 语音输入 · 一键启动（首次运行自动建 venv 并装依赖）
cd "$(dirname "$0")"

PY=".venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "[初始化] 创建虚拟环境 ..."
  python3 -m venv .venv
  "$PY" -m ensurepip --upgrade >/dev/null 2>&1
  echo "[初始化] 安装依赖 ..."
  if ! "$PY" -m pip install -q -r requirements.txt; then
    # zhconv 在个别环境构建失败时，用免构建隔离方式补装
    "$PY" -m pip install -q --no-build-isolation zhconv
    "$PY" -m pip install -q -r requirements.txt
  fi
fi

exec "$PY" main.py
