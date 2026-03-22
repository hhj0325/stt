"""音频路径、ffmpeg 与转写结果文件：供 Whisper 界面使用。"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def gpu_error_should_fallback_cpu(exc: BaseException) -> bool:
    """
    PyTorch 可能报告 CUDA 可用，但 faster-whisper(CTranslate2) 等仍依赖系统里的
    CUDA/cuBLAS 动态库；缺 cublas64_12.dll 时会报错，此时应回退 CPU。
    """
    msg = str(exc).lower()
    return any(
        k in msg
        for k in (
            "cublas",
            "cudnn",
            "nvrtc",
            "libcudart",
            ".dll",
            "dll is not found",
            "cannot load",
            "error loading",
        )
    )


def _project_base() -> Path:
    """源码运行：脚本所在目录；PyInstaller：exe 所在目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def prepend_tools_ffmpeg_to_path() -> None:
    """
    将项目 tools 目录插到 PATH 最前，便于依赖 ffmpeg 的库在运行时找到 tools\\ffmpeg.exe。
    """
    tools_dir = (_project_base() / "tools").resolve()
    if not (tools_dir / "ffmpeg.exe").is_file() and not (tools_dir / "ffmpeg").is_file():
        return
    d = str(tools_dir)
    current = os.environ.get("PATH", "")
    parts = current.split(os.pathsep) if current else []
    if d not in parts:
        os.environ["PATH"] = d + os.pathsep + current


def resolve_ffmpeg() -> str | None:
    """优先 PATH 中的 ffmpeg，其次项目/tools 或 exe 同目录 tools\\ffmpeg.exe。"""
    w = shutil.which("ffmpeg")
    if w:
        return w
    base = _project_base()
    for name in ("ffmpeg.exe", "ffmpeg"):
        p = base / "tools" / name
        if p.is_file():
            return str(p)
    return None


def require_ffmpeg() -> str:
    ff = resolve_ffmpeg()
    if not ff:
        raise RuntimeError(
            "未找到 ffmpeg。请安装 ffmpeg 并加入 PATH，或将 ffmpeg.exe 放到项目目录 tools\\ 下。"
        )
    return ff


def resolve_ffprobe() -> str | None:
    """与 resolve_ffmpeg 类似：PATH 或 tools\\ffprobe.exe。"""
    w = shutil.which("ffprobe")
    if w:
        return w
    base = _project_base()
    for name in ("ffprobe.exe", "ffprobe"):
        p = base / "tools" / name
        if p.is_file():
            return str(p)
    return None


def get_media_duration_seconds(path: str | Path) -> float | None:
    """用 ffprobe 读取媒体时长（秒），失败返回 None。"""
    probe = resolve_ffprobe()
    if not probe:
        return None
    p = Path(path)
    run_kw: dict = {"capture_output": True, "text": True, "timeout": 120}
    if sys.platform == "win32":
        run_kw["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        r = subprocess.run(
            [
                probe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(p.resolve()),
            ],
            **run_kw,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if r.returncode != 0:
        return None
    try:
        v = float((r.stdout or "").strip())
        if v < 0 or v != v:
            return None
        return v
    except ValueError:
        return None


def format_duration_cn(seconds: float) -> str:
    """人类可读时长（中文）。"""
    if seconds < 0 or seconds != seconds:
        return "未知"
    if seconds >= 3600:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}小时{m}分{s:.1f}秒"
    if seconds >= 60:
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}分{s:.1f}秒"
    return f"{seconds:.1f}秒"


def output_raw_txt_path(audio_path: str | Path) -> Path:
    """与录音同目录，文件名为「主文件名_raw.txt」（原始转写结果，每次覆盖同名文件）。"""
    p = Path(audio_path)
    return p.with_name(f"{p.stem}_raw.txt")


def write_transcript_txt(out: Path, text: str) -> None:
    """UTF-8（无 BOM）写入；若同名文件已存在则整文件覆盖，不保留旧内容。"""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def open_containing_folder(path: str | Path) -> None:
    """在文件管理器中打开 path 所在文件夹（Windows 为资源管理器）。"""
    folder = Path(path).resolve().parent
    if not folder.is_dir():
        return
    try:
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.run(["open", str(folder)], check=False)
        else:
            subprocess.run(["xdg-open", str(folder)], check=False)
    except OSError:
        pass
