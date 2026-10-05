"""麦克风录音：按住热键期间采集音频，松开后输出 16kHz 单声道 WAV 字节。"""
import io
import wave

import numpy as np
import sounddevice as sd


class Recorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._stream: sd.InputStream | None = None
        self._frames: list[np.ndarray] = []
        self._recording = False

    @property
    def recording(self) -> bool:
        return self._recording

    def _callback(self, indata, frames, time_info, status):
        if status:
            print(f"[录音] {status}")
        self._frames.append(indata.copy())

    def start(self):
        if self._recording:
            return
        self._frames = []
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()
        self._recording = True

    def stop(self) -> bytes:
        """停止录音，返回去掉首尾静音的 WAV 字节。"""
        if not self._recording:
            return b""
        self._recording = False
        try:
            self._stream.stop()
            self._stream.close()
        except Exception as exc:
            print(f"[录音] 关闭失败: {exc}")
        self._stream = None

        if not self._frames:
            return b""
        audio = np.concatenate(self._frames, axis=0).reshape(-1)
        audio = self._trim_silence(audio)
        if audio.size == 0:
            return b""
        pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2")

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm.tobytes())
        return buf.getvalue()

    def _trim_silence(self, audio: np.ndarray, threshold: float = 0.01,
                      pad_ms: float = 150.0) -> np.ndarray:
        if audio.size == 0:
            return audio
        mask = np.abs(audio) > threshold
        if not mask.any():
            return audio
        pad = int(self.sample_rate * pad_ms / 1000)
        start = max(0, int(np.argmax(mask)) - pad)
        end = min(audio.size, audio.size - int(np.argmax(mask[::-1])) + pad)
        return audio[start:end]
