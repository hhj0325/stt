"""
Whisper 可选开关（通用转写，不含行业提示词/热词）。

优先保证尽量多输出：默认关闭 VAD；若录音极干净且想滤静音，可改为 True。
"""

# True 时用 Silero VAD 裁掉「无语音」片段，口播+BGM 时易误切丢句。
WHISPER_USE_VAD_FILTER = False

# 仅在 WHISPER_USE_VAD_FILTER = True 时使用
WHISPER_VAD_PARAMETERS = {
    "threshold": 0.5,
    "min_speech_duration_ms": 0,
    "speech_pad_ms": 400,
    "min_silence_duration_ms": 2000,
}
