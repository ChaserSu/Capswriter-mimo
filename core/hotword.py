"""音素热词匹配

把识别文本里的同音/近音误写替换为规范写法：

- hot.txt      词表：每行 `规范写法 | 别名1 | 别名2 ...`，`#` 开头为注释
- hot-rule.txt 正则规则：每行 `正则查找 = 替换`（支持 \\2 反向引用）

匹配思路：先做别名精确替换（不区分大小写），再对漏网的误写做拼音（音素）
相似匹配——把声母韵母归一化（zh/z、ch/c、sh/s、l/n、f/h、前后鼻音等视为
相近音素），用编辑相似度在文本滑窗中找最相近的一段并替换为规范写法。
"""
from __future__ import annotations

import re
import threading
from pathlib import Path

from pypinyin import Style, pinyin
from rapidfuzz import fuzz

# 相近音素归一化：映射到同一个“音素键”
_INITIAL_FOLD = {
    "zh": "Z", "z": "Z", "ch": "C", "c": "C", "sh": "S", "s": "S",
    "l": "N", "n": "N", "f": "H", "h": "H",
}
_FINAL_FOLD = {
    "an": "AN", "ang": "AN", "en": "EN", "eng": "EN", "in": "IN", "ing": "IN",
    "ian": "IAN", "iang": "IAN", "uan": "UAN", "uang": "UAN",
}
_INITIAL_RE = re.compile(r"^(zh|ch|sh|[bpmfdtnlgkhjqxrzcsyw])?(.*)$")
_TONE_RE = re.compile(r"\d+$")


def _syllables(text: str) -> list[str]:
    """取整段文本的无调拼音序列；非汉字按字符保留（转小写）。"""
    raw = pinyin(text, style=Style.TONE3, errors=lambda item: list(item))
    out = []
    for item in raw:
        s = _TONE_RE.sub("", str(item[0])).lower()
        if s:
            out.append(s)
    return out


def _fold_syllable(s: str) -> str:
    m = _INITIAL_RE.match(s)
    if not m:
        return s.upper()
    initial, final = m.group(1) or "", m.group(2) or ""
    ini_key = _INITIAL_FOLD.get(initial, initial.upper())
    fin_key = _FINAL_FOLD.get(final, final.upper())
    return f"{ini_key}|{fin_key}"


class HotWordMatcher:
    def __init__(self, hot_path: Path, hot_rule_path: Path, threshold: float = 0.8):
        self.hot_path = Path(hot_path)
        self.hot_rule_path = Path(hot_rule_path)
        self.threshold = threshold
        self._lock = threading.Lock()
        self._mtime = (0.0, 0.0)
        self._entries: list[tuple[str, list[str]]] = []   # (规范写法, [别名...])
        self._rules: list[tuple[str, str]] = []
        self._reload(force=True)

    # ---------- 加载 ----------
    def _reload(self, force: bool = False):
        try:
            mtime = (
                self.hot_path.stat().st_mtime if self.hot_path.exists() else 0.0,
                self.hot_rule_path.stat().st_mtime if self.hot_rule_path.exists() else 0.0,
            )
        except OSError:
            return
        if not force and mtime == self._mtime:
            return

        entries: list[tuple[str, list[str]]] = []
        if self.hot_path.exists():
            for line in self.hot_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split("|")]
                canonical = parts[0]
                aliases = [p for p in parts[1:] if p]
                if canonical:
                    entries.append((canonical, aliases))
        # 长词优先，避免短别名先命中造成误替换
        entries.sort(key=lambda e: max((len(a) for a in e[1] + [e[0]]), default=0),
                     reverse=True)

        rules: list[tuple[str, str]] = []
        if self.hot_rule_path.exists():
            for line in self.hot_rule_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                pat, repl = line.split("=", 1)
                pat, repl = pat.strip(), repl.strip()
                if pat:
                    try:
                        re.compile(pat)
                        rules.append((pat, repl))
                    except re.error:
                        print(f"[热词] 非法正则，已跳过: {pat}")

        with self._lock:
            self._entries = entries
            self._rules = rules
            self._mtime = mtime

    def reload(self):
        self._reload(force=True)

    # ---------- 音素相似匹配 ----------
    def _find_spans(self, text: str, canonical: str, alias: str) -> list[tuple[int, int]]:
        """在 text 中找与 alias 音素相似的片段，返回 [(start, end), ...]。"""
        a_sylls = _syllables(alias)
        if not a_sylls:
            return []
        a_fold = "".join(_fold_syllable(s) for s in a_sylls)
        a_strict = "".join(a_sylls)
        n = len(alias)
        spans = []
        i = 0
        while i < len(text):
            best_score, best_end = 0.0, 0
            for size in {n - 1, n, n + 1}:
                if size <= 0 or i + size > len(text):
                    continue
                window = text[i:i + size]
                if window == canonical:
                    continue
                w_sylls = _syllables(window)
                if not w_sylls or abs(len(w_sylls) - len(a_sylls)) > 1:
                    continue
                w_fold = "".join(_fold_syllable(s) for s in w_sylls)
                w_strict = "".join(w_sylls)
                score = max(
                    fuzz.ratio(a_fold, w_fold),
                    fuzz.ratio(a_strict, w_strict),
                ) / 100.0
                if score > best_score:
                    best_score, best_end = score, i + size
            if best_score >= self.threshold:
                spans.append((i, best_end))
                i = best_end          # 跳过已命中的片段，防止重复替换
            else:
                i += 1
        return spans

    # ---------- 主入口 ----------
    def apply(self, text: str) -> str:
        """对文本依次做：别名精确替换 → 音素相似替换 → 正则规则替换。"""
        if not text:
            return text
        self._reload()
        with self._lock:
            entries = list(self._entries)
            rules = list(self._rules)

        # 1) 收集候选片段：别名精确命中 + 音素相似命中
        candidates: list[tuple[int, int, str, int]] = []  # start, end, 规范写法, 精确优先
        for canonical, aliases in entries:
            for alias in aliases + [canonical]:
                if not alias:
                    continue
                for m in re.finditer(re.escape(alias), text, re.IGNORECASE):
                    candidates.append((m.start(), m.end(), canonical, 1))
        for canonical, aliases in entries:
            for alias in aliases or [canonical]:
                for start, end in self._find_spans(text, canonical, alias):
                    candidates.append((start, end, canonical, 0))

        # 2) 长片段优先、精确命中优先，去掉相互重叠的候选
        candidates.sort(key=lambda c: (-(c[1] - c[0]), -c[3], c[0]))
        selected: list[tuple[int, int, str]] = []
        for start, end, canonical, _prio in candidates:
            if text[start:end] == canonical:
                continue  # 已是规范写法
            if any(not (end <= s or start >= e) for s, e, _ in selected):
                continue  # 与已选片段重叠，跳过
            selected.append((start, end, canonical))
        for start, end, canonical in sorted(selected, key=lambda c: c[0], reverse=True):
            text = text[:start] + canonical + text[end:]

        # 3) 正则规则
        for pat, repl in rules:
            try:
                text = re.sub(pat, repl, text)
            except re.error:
                continue
        return text
