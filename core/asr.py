"""MiMo 语音识别：wav 字节 -> base64 data URL -> mimo-v2.5-asr -> 文本。"""
import base64

from openai import OpenAI

from config import ApiConfig

MAX_AUDIO_B64_BYTES = 10 * 1024 * 1024  # 官方限制：base64 后不超过 10MB


def _make_client() -> OpenAI:
    return OpenAI(api_key=ApiConfig.api_key, base_url=ApiConfig.base_url,
                  timeout=ApiConfig.timeout)


def transcribe(wav_bytes: bytes, language: str = "auto") -> str:
    """识别一段 WAV 音频，返回转写文本（含自动标点）。"""
    if not wav_bytes:
        return ""
    b64 = base64.b64encode(wav_bytes).decode("ascii")
    if len(b64) > MAX_AUDIO_B64_BYTES:
        raise ValueError("音频过大（base64 超过 10MB），请缩短单次说话时长")

    data_url = f"data:audio/wav;base64,{b64}"
    client = _make_client()
    resp = client.chat.completions.create(
        model=ApiConfig.asr_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {"data": data_url},
                    }
                ],
            }
        ],
        extra_body={"asr_options": {"language": language}},
    )
    text = (resp.choices[0].message.content or "").strip()
    return text
