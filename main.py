"""MiMo 语音输入 · 主程序

用法：
  python main.py              启动常驻服务（按住右 Command 说话，松开识别上屏）
  python main.py --cli a.wav  识别指定 WAV 文件并打印结果（不粘贴，用于调试）
  python main.py --probe      测试接口连通性（调用 mimo-v2.6-flash）
  python main.py --selftest   热词/文本处理逻辑自测（不联网）

功能链路：录音 -> mimo-v2.5-asr 识别 -> 音素热词匹配 -> 文本后处理
          ->（可选）mimo-v2.6-flash 润色 -> 粘贴到光标处
字幕/对齐功能已按需求删除。
"""
import argparse
import sys
import threading
import time

from pynput import keyboard

from config import ApiConfig, Config
from core.asr import transcribe
from core.hotword import HotWordMatcher
from core.output import paste_text
from core.polish import polish
from core.recorder import Recorder
from core.textproc import post_process


class VoiceInputApp:
    def __init__(self):
        self.recorder = Recorder(Config.sample_rate, Config.channels)
        self.matcher = HotWordMatcher(
            Config.hot_path, Config.hot_rule_path, Config.hotword_threshold
        )
        self._pending_polish = False
        self._busy = False

    # ---------- 完整流水线 ----------
    def run_pipeline(self, wav_bytes: bytes, force_polish: bool = False):
        try:
            if not wav_bytes:
                return
            t0 = time.time()
            text = transcribe(wav_bytes, Config.language)
            if not text:
                print("[识别] 未识别到内容")
                return
            text = self.matcher.apply(text)
            text = post_process(text, Config.enable_zhconv, Config.enable_itn)
            if force_polish or Config.enable_polish:
                print("[润色] 调用 mimo-v2.6-flash ...")
                text = polish(text, Config.polish_language)
            paste_text(text, Config.paste_after_recognize)
            print(f"[上屏] {text}   （{time.time() - t0:.2f}s）")
        except Exception as exc:
            print(f"[错误] {exc}")
        finally:
            self._busy = False

    # ---------- 热键回调 ----------
    def _key_matches(self, key, name: str) -> bool:
        target = getattr(keyboard.Key, name, None)
        return target is not None and key == target

    def on_press(self, key):
        if self._key_matches(key, Config.shortcut_key):
            if not self.recorder.recording:
                self.recorder.start()
                print("[录音] 开始 ...")
            return
        if self._key_matches(key, Config.force_polish_key):
            self._pending_polish = True
            if not self.recorder.recording:
                self.recorder.start()
                print("[录音] 开始（润色模式）...")

    def on_release(self, key):
        is_shortcut = self._key_matches(key, Config.shortcut_key)
        is_polish = self._key_matches(key, Config.force_polish_key)
        if not (is_shortcut or is_polish):
            return
        if is_shortcut and self._pending_polish:
            return  # 润色模式下等 alt_r 松开再统一处理
        if not self.recorder.recording:
            self._pending_polish = False
            return
        wav_bytes = self.recorder.stop()
        force_polish = self._pending_polish or is_polish
        self._pending_polish = False
        if not wav_bytes:
            print("[录音] 时长过短或无声，已忽略")
            return
        print(f"[录音] 结束，音频 {len(wav_bytes) / 1024:.0f}KB，识别中 ...")
        threading.Thread(
            target=self.run_pipeline, args=(wav_bytes, force_polish), daemon=True
        ).start()

    def run_forever(self):
        print("=" * 46)
        print("  MiMo 语音输入 已启动")
        print(f"  按住 [{Config.shortcut_key}] 说话，松开识别上屏")
        print(f"  按住 [{Config.force_polish_key}] 说话，松开后润色上屏")
        print(f"  识别模型: {ApiConfig.asr_model}   润色模型: {ApiConfig.polish_model}")
        print(f"  热词: {Config.hot_path.name} / {Config.hot_rule_path.name}"
              f"（{len(self.matcher._entries)} 条词表，{len(self.matcher._rules)} 条规则）")
        print("  按 Ctrl+C 退出")
        print("=" * 46)
        with keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        ) as listener:
            listener.join()


# ---------- 调试命令 ----------
def cmd_cli(wav_path: str):
    with open(wav_path, "rb") as f:
        wav_bytes = f.read()
    app = VoiceInputApp()
    text = transcribe(wav_bytes, Config.language)
    print(f"[识别] {text}")
    text = app.matcher.apply(text)
    text = post_process(text, Config.enable_zhconv, Config.enable_itn)
    print(f"[处理] {text}")


def cmd_probe():
    print(f"[探测] base_url = {ApiConfig.base_url}")
    print(f"[探测] 调用 {ApiConfig.polish_model} ...")
    result = polish("这是一个连通性测试", "zh")
    print(f"[探测] 返回: {result}")
    print("[探测] 接口连通正常" if result else "[探测] 异常：返回为空")


def cmd_selftest():
    app = VoiceInputApp()
    cases = {
        "迷墨很好用，容量是三十二毫安时": "音素热词 + ITN + 规则",
        "請幫我把這個檔案轉成簡體": "繁简转换",
        "我的电话号码是一三八零零一三八零零": "数字串逐位转换",
    }
    for src, label in cases.items():
        out = app.matcher.apply(src)
        out = post_process(out, Config.enable_zhconv, Config.enable_itn)
        print(f"[{label}] {src}\n    -> {out}")
    print("[自测] 完成（不联网）")


def main():
    parser = argparse.ArgumentParser(description="MiMo 语音输入")
    parser.add_argument("--cli", metavar="WAV", help="识别指定 WAV 文件后退出")
    parser.add_argument("--probe", action="store_true", help="测试接口连通性")
    parser.add_argument("--selftest", action="store_true", help="热词/文本逻辑自测")
    args = parser.parse_args()

    if args.cli:
        cmd_cli(args.cli)
    elif args.probe:
        cmd_probe()
    elif args.selftest:
        cmd_selftest()
    else:
        try:
            VoiceInputApp().run_forever()
        except KeyboardInterrupt:
            print("\n[退出] 再见")
            sys.exit(0)


if __name__ == "__main__":
    main()
