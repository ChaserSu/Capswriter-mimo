"""MiMo 文本润色（可选）：mimo-v2.6-flash 对识别文本做单行润色。"""
from openai import OpenAI

from config import ApiConfig

SYSTEM_PROMPTS = {
    "zh": (
        "你是语音输入润色助手。请润色用户给出的一句话文本：修正错别字和语法问题，"
        "保持原意、语气与语言种类不变，不要增删信息。只输出润色后的单行文本，"
        "不要解释、不要引号、不要换行。"
    ),
    "en": (
        "You are a voice-input polishing assistant. Fix typos and grammar in the "
        "given text while preserving the original meaning and language. Output only "
        "the polished single line, no explanation and no quotes."
    ),
}


def polish(text: str, language: str = "zh") -> str:
    """润色文本；失败时原样返回，保证上屏不中断。"""
    text = (text or "").strip()
    if not text:
        return ""
    try:
        client = OpenAI(api_key=ApiConfig.api_key, base_url=ApiConfig.base_url,
                        timeout=ApiConfig.timeout)
        resp = client.chat.completions.create(
            model=ApiConfig.polish_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["zh"])},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
        )
        polished = (resp.choices[0].message.content or "").strip()
        if not polished:
            return text
        # 简单兜底：润色结果异常膨胀时放弃润色
        if len(polished) > max(80, len(text) * 3):
            return text
        return polished
    except Exception as exc:
        print(f"[润色] 失败，使用原文: {exc}")
        return text
