"""文本后处理：繁简转换、中文数字转阿拉伯数字、空白规范化。"""
import re

from zhconv import convert as _zh_convert

_CN_DIGITS = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
              "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_CN_UNITS = {"十": 10, "百": 100, "千": 1000, "万": 10000, "亿": 100000000}
_CN_NUM_RE = re.compile(r"[零一二两三四五六七八九十百千万亿]+")
_CN_PCT_RE = re.compile(r"百分之([零一二两三四五六七八九十百千万亿]+)")


def _cn2int(s: str) -> int | None:
    """把中文数字串转成整数（如 三十二 -> 32），无法解析返回 None。"""
    total, section, number = 0, 0, 0
    for ch in s:
        if ch in _CN_DIGITS:
            number = _CN_DIGITS[ch]
        elif ch in _CN_UNITS:
            unit = _CN_UNITS[ch]
            if unit >= 10000:
                section += number
                total += (section if section else 1) * unit
                section, number = 0, 0
            else:
                section += (number if number else 1) * unit
                number = 0
        else:
            return None
    return total + section + number


def itn(text: str) -> str:
    """中文数字 -> 阿拉伯数字。保守规则，避免误伤普通词语。"""
    text = _CN_PCT_RE.sub(lambda m: f"{_cn2int(m.group(1))}%", text)

    def _replace(m: re.Match) -> str:
        run = m.group(0)
        # 纯数字串（如 二零二六）按逐位拼接：2026
        if not any(u in run for u in _CN_UNITS):
            if len(run) < 2:
                return run
            return "".join(str(_CN_DIGITS[ch]) for ch in run)
        # 含单位（十百千万亿）按完整算法解析；解析失败保留原文
        value = _cn2int(run)
        return str(value) if value is not None else run

    return _CN_NUM_RE.sub(_replace, text)


def to_simplified(text: str) -> str:
    return _zh_convert(text, "zh-cn")


def normalize_spaces(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    # 去掉汉字之间误加的空格
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    return text.strip()


def post_process(text: str, enable_zhconv: bool = True, enable_itn: bool = True) -> str:
    if not text:
        return text
    if enable_zhconv:
        text = to_simplified(text)
    if enable_itn:
        text = itn(text)
    text = normalize_spaces(text)
    return text
