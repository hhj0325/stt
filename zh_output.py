"""将识别结果统一为大陆简体汉字（含繁体、异体常见映射）。"""

from __future__ import annotations

import re

import zhconv

# 少数 ASR 输出会在汉字间加空格；去掉仅夹在汉字之间的空白，保留中英/数字旁的间隔
_CJK_SPACE_CJK = re.compile(
    r"(?<=[\u4e00-\u9fff\u3400-\u4dbf\u3007])\s+(?=[\u4e00-\u9fff\u3400-\u4dbf\u3007])"
)


def collapse_cjk_interchar_spaces(text: str) -> str:
    if not text:
        return text
    t = _CJK_SPACE_CJK.sub("", text)
    return re.sub(r" {2,}", " ", t).strip()


def to_simplified_chinese(text: str) -> str:
    if not text:
        return ""
    text = collapse_cjk_interchar_spaces(text)
    return zhconv.convert(text, "zh-cn")
