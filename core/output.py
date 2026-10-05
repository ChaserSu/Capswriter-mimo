"""上屏：复制到剪贴板并模拟粘贴快捷键（macOS Cmd+V / Windows·Linux Ctrl+V）。"""
import platform
import shutil
import subprocess
import time

from pynput.keyboard import Controller, Key

IS_MAC = platform.system() == "Darwin"
PASTE_KEY = Key.cmd if IS_MAC else Key.ctrl


def _copy(text: str) -> bool:
    try:
        import pyclip
        pyclip.copy(text)
        return True
    except Exception:
        pass
    # Linux 兜底：xclip / xsel / wl-copy（Wayland）
    for cmd in (["xclip", "-selection", "clipboard"],
                ["xsel", "--clipboard", "--input"],
                ["wl-copy"]):
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, input=text.encode("utf-8"), check=True)
                return True
            except Exception:
                continue
    return False


def paste_text(text: str, auto_paste: bool = True) -> None:
    if not text:
        return
    if not _copy(text):
        print("[上屏] 剪贴板不可用（Linux 需安装 xclip 或 wl-clipboard）")
        return
    if not auto_paste:
        return
    time.sleep(0.05)
    kb = Controller()
    with kb.pressed(PASTE_KEY):
        kb.press("v")
        kb.release("v")
