"""
Whisper 版：批量选择 m4a 等音频 -> 同目录「主文件名_raw.txt」（本地 faster-whisper）。
"""

from __future__ import annotations

import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from audio_utils import (
    format_duration_cn,
    get_media_duration_seconds,
    gpu_error_should_fallback_cpu,
    open_containing_folder,
    output_raw_txt_path,
    prepend_tools_ffmpeg_to_path,
    require_ffmpeg,
    write_transcript_txt,
)

prepend_tools_ffmpeg_to_path()

from faster_whisper import WhisperModel
from cn_stock_asr import WHISPER_USE_VAD_FILTER, WHISPER_VAD_PARAMETERS
from zh_output import to_simplified_chinese


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("语音转文字 — Whisper（本地）")
        self.geometry("720x480")
        self._audio_paths: list[str] = []
        self._model: WhisperModel | None = None
        self._model_key: str | None = None
        self._busy = False

        frm = ttk.Frame(self, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)

        row1 = ttk.Frame(frm)
        row1.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(row1, text="选择录音文件（可多选）", command=self._pick_file).pack(
            side=tk.LEFT
        )
        self.lbl_file = ttk.Label(row1, text="未选择文件")
        self.lbl_file.pack(side=tk.LEFT, padx=12)

        row2 = ttk.Frame(frm)
        row2.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(row2, text="模型：").pack(side=tk.LEFT)
        ttk.Label(row2, text="medium").pack(side=tk.LEFT, padx=(0, 16))
        ttk.Label(row2, text="设备：").pack(side=tk.LEFT)
        self.cmb_device = ttk.Combobox(
            row2, state="readonly", width=10, values=("cuda", "cpu")
        )
        self.cmb_device.set("cuda")
        self.cmb_device.pack(side=tk.LEFT)

        row3 = ttk.Frame(frm)
        row3.pack(fill=tk.X, pady=(0, 6))
        self.btn_run = ttk.Button(row3, text="开始转换", command=self._start)
        self.btn_run.pack(side=tk.LEFT)

        ttk.Label(frm, text="日志：").pack(anchor=tk.W)
        self.log = scrolledtext.ScrolledText(frm, height=18, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

    def _after_batch_done(
        self, last_out: Path | None, total: int, errors: list[str]
    ) -> None:
        if errors and last_out is None:
            messagebox.showerror(
                "失败", "全部未成功：\n" + "\n".join(errors[:8])
            )
            return
        ok = total - len(errors)
        if errors:
            messagebox.showwarning(
                "部分完成",
                f"成功 {ok}/{total} 个。\n失败 {len(errors)} 个（见日志）。\n"
                + "\n".join(errors[:6]),
            )
        else:
            messagebox.showinfo(
                "完成",
                f"已处理 {total} 个文件，输出为「主文件名_raw.txt」。",
            )
        if last_out is not None:
            open_containing_folder(last_out)

    def _log_from_worker(self, s: str) -> None:
        """在工作线程中调用：主线程追加一行并刷新界面后再返回，保证日志按处理顺序逐条、逐个文件出现。"""
        if threading.current_thread() is threading.main_thread():
            self._append_log(s)
            self.update_idletasks()
            return
        done = threading.Event()

        def run() -> None:
            try:
                self._append_log(s)
                self.update_idletasks()
            finally:
                done.set()

        self.after(0, run)
        done.wait()

    def _append_log(self, s: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {s}"
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, line + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        st = tk.DISABLED if busy else tk.NORMAL
        self.btn_run.configure(state=st)
        self.cmb_device.configure(state=st)

    def _pick_file(self) -> None:
        paths = filedialog.askopenfilenames(
            title="选择录音文件（可按住 Ctrl 多选）",
            filetypes=[
                ("常见音频", "*.m4a *.mp3 *.wav *.mp4 *.aac *.flac *.ogg *.wma"),
                ("全部", "*.*"),
            ],
        )
        if not paths:
            return
        self._audio_paths = list(paths)
        n = len(self._audio_paths)
        if n == 1:
            self.lbl_file.configure(text=self._audio_paths[0])
        else:
            self.lbl_file.configure(text=f"已选 {n} 个文件")

    def _ensure_model(self, name: str, device_sel: str) -> WhisperModel:
        """仅在工作线程中调用；不得操作 Tk 控件。device_sel 为 cuda 或 cpu；GPU 缺库时自动回退 CPU。"""
        dev = device_sel
        compute_type = "float16" if dev == "cuda" else "int8"
        key = f"{name}|{dev}|{compute_type}"
        if self._model is not None and self._model_key == key:
            return self._model

        try:
            self._model = WhisperModel(name, device=dev, compute_type=compute_type)
            self._model_key = key
            return self._model
        except Exception as e:
            if dev != "cpu" and gpu_error_should_fallback_cpu(e):
                self._log_from_worker(
                    "GPU 不可用（缺少 CUDA/cuBLAS 等运行库，例如 cublas64_12.dll），已改用 CPU。"
                )
                self._log_from_worker(f"详情：{e}")
                dev, compute_type = "cpu", "int8"
                key = f"{name}|{dev}|{compute_type}"
                self._model = WhisperModel(name, device=dev, compute_type=compute_type)
                self._model_key = key
                return self._model
            raise

    def _start(self) -> None:
        if self._busy:
            return
        if not self._audio_paths:
            messagebox.showwarning("提示", "请先选择录音文件。")
            return
        try:
            require_ffmpeg()
        except RuntimeError as e:
            messagebox.showerror("缺少 ffmpeg", str(e))
            return

        paths = list(self._audio_paths)
        model_name = "medium"
        device_sel = self.cmb_device.get().strip()
        threading.Thread(
            target=self._worker, args=(paths, model_name, device_sel), daemon=True
        ).start()

    def _transcribe_to_text(self, path: str, model_name: str, device_sel: str) -> str:
        """加载模型并转写；可能抛出 GPU 相关错误（含在迭代 segments 时）。"""
        model = self._ensure_model(model_name, device_sel)
        self._log_from_worker(f"开始识别：{path}")
        tw_kw: dict = {
            "beam_size": 5,
            "vad_filter": WHISPER_USE_VAD_FILTER,
            "language": "zh",
            "without_timestamps": True,
            "no_speech_threshold": None,
        }
        if WHISPER_USE_VAD_FILTER:
            tw_kw["vad_parameters"] = WHISPER_VAD_PARAMETERS
        segments, _ = model.transcribe(path, **tw_kw)
        parts: list[str] = []
        for seg in segments:
            parts.append(seg.text.strip())
        return "\n".join(t for t in parts if t).strip()

    def _worker(self, paths: list[str], model_name: str, device_sel: str) -> None:
        self.after(0, self._set_busy, True)
        errors: list[str] = []
        last_out: Path | None = None
        dev = device_sel
        n = len(paths)
        try:
            self._log_from_worker(
                f"任务开始，共 {n} 个文件；输出规则：同目录「主文件名_raw.txt」（覆盖）；日志按文件顺序逐条输出。"
            )
            self._log_from_worker(
                f"加载 Whisper：{model_name} / {dev}（首次会下载模型，后续文件复用）"
            )
            t_batch = time.perf_counter()
            for i, path in enumerate(paths, 1):
                self._log_from_worker(f"-------- [{i}/{n}] --------")
                self._log_from_worker(f"文件：{path}")
                dur = get_media_duration_seconds(path)
                if dur is not None:
                    self._log_from_worker(
                        f"媒体时长：{format_duration_cn(dur)}（{dur:.2f} 秒）"
                    )
                else:
                    self._log_from_worker(
                        "媒体时长：未能读取（请将 ffprobe.exe 与 ffmpeg 同置于 tools 或加入 PATH）"
                    )
                t0 = time.perf_counter()
                try:
                    text = self._transcribe_to_text(path, model_name, dev)
                except Exception as e:
                    if dev != "cpu" and gpu_error_should_fallback_cpu(e):
                        self._log_from_worker(
                            "识别阶段 GPU 失败（常见于缺少 cublas64_12.dll），已清空缓存并改用 CPU 重试本文件。"
                        )
                        self._log_from_worker(f"详情：{e}")
                        self._model = None
                        self._model_key = None
                        dev = "cpu"
                        try:
                            text = self._transcribe_to_text(path, model_name, "cpu")
                        except Exception as e2:
                            errors.append(f"{path}: {e2}")
                            self._log_from_worker(f"错误（跳过本文件）：{e2}")
                            continue
                    else:
                        errors.append(f"{path}: {e}")
                        self._log_from_worker(f"错误（跳过本文件）：{e}")
                        continue
                try:
                    text = to_simplified_chinese(text)
                    out = output_raw_txt_path(path)
                    write_transcript_txt(out, text)
                    elapsed = time.perf_counter() - t0
                    self._log_from_worker("输出：简体中文（大陆规范汉字）")
                    self._log_from_worker(f"已保存：{out}")
                    self._log_from_worker(
                        f"本文件转换耗时：{format_duration_cn(elapsed)}（{elapsed:.2f} 秒，含识别、简体与写盘）"
                    )
                    last_out = out
                except Exception as e:
                    errors.append(f"{path}: {e}")
                    self._log_from_worker(f"错误（跳过本文件）：{e}")
            batch_elapsed = time.perf_counter() - t_batch
            self._log_from_worker(
                f"批量结束：成功 {n - len(errors)}/{n}，总耗时 {format_duration_cn(batch_elapsed)}（{batch_elapsed:.2f} 秒）"
            )
            self.after(
                0,
                lambda lo=last_out, tot=n, err=list(errors): self._after_batch_done(
                    lo, tot, err
                ),
            )
        except Exception as e:
            self._log_from_worker(f"错误：{e}")
            self.after(0, lambda m=str(e): messagebox.showerror("失败", m))
        finally:
            self.after(0, self._set_busy, False)


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
