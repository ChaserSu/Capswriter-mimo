"""MiMo 语音输入 · 全局配置

密钥加载顺序：环境变量 MIMO_API_KEY > 本地 config_local.py（已 gitignore）> 空。
安全起见仓库中不含真实密钥：把 config_local.example.py 复制为 config_local.py 并填入。
"""
import os
import platform
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"

try:
    from config_local import MIMO_API_KEY as _LOCAL_MIMO_API_KEY
except Exception:
    _LOCAL_MIMO_API_KEY = ""


class ApiConfig:
    base_url = os.environ.get("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")
    api_key = os.environ.get("MIMO_API_KEY") or _LOCAL_MIMO_API_KEY
    asr_model = "mimo-v2.5-asr"        # 语音识别
    polish_model = "mimo-v2.6-flash"   # 文本润色（可选）
    timeout = 60                        # 单次请求超时（秒）


class Config:
    # 录音
    sample_rate = 16000
    channels = 1

    # 热键（pynput 键名），按操作系统自动适配，也可手动改
    # macOS: cmd_r=右 Command；Windows/Linux: ctrl_r=右 Ctrl
    shortcut_key = "cmd_r" if IS_MAC else "ctrl_r"   # 按住说话，松开识别上屏
    force_polish_key = "alt_r"   # 右 Option / 右 Alt：松开后强制润色上屏

    # 识别
    language = "auto"            # auto / zh / en
    enable_polish = False        # True 时每句话都自动润色；False 仅按 force_polish_key 时润色
    polish_language = "zh"       # 润色提示词语言

    # 热词
    hot_path = BASE_DIR / "hot.txt"
    hot_rule_path = BASE_DIR / "hot-rule.txt"
    hotword_threshold = 0.8      # 音素相似度阈值（0~1），越高越严格

    # 上屏
    paste_after_recognize = True  # 识别后自动粘贴到光标处；False 则只进剪贴板

    # 文本后处理
    enable_itn = True            # 中文数字转阿拉伯数字（如 三十二 -> 32）
    enable_zhconv = True         # 繁体转简体
