# 本地语音转文字（Whisper）

基于 `faster-whisper` 的 Windows 本地离线转写工具，提供简单 GUI，支持批量选择音频并输出文本文件。

## 1. 项目功能

- 批量选择音频文件（如 `.m4a` / `.mp3` / `.wav` / `.mp4`）。
- 本地转写（Whisper，模型固定 `medium`）。
- 输出到音频同目录，命名规则为 `主文件名_raw.txt`。
- 同名输出文件直接覆盖，不保留历史版本。
- 日志带时间戳，显示媒体时长、单文件耗时、批量总耗时。
- 转写结束后自动打开最后一个成功输出文件所在目录。

## 2. 输出规则

- 输入：`20250101上.m4a`
- 输出：`20250101上_raw.txt`
- 编码：UTF-8（无 BOM）
- 文本后处理：
  - 合并汉字之间多余空格（`zh_output.collapse_cjk_interchar_spaces`）
  - 转为大陆简体（`zhconv`）

## 3. 环境要求

- 操作系统：Windows 11
- Python：3.10 或 3.11（安装时勾选 Add to PATH）
- ffmpeg：必需（用于解码音频）
- ffprobe：可选（用于显示媒体时长）

`ffmpeg/ffprobe` 可用两种方式提供：
- 放在项目 `tools\` 目录（推荐）
- 安装到系统并加入 PATH

## 4. 安装与运行

### 4.1 安装

1. 双击 `install.bat`（创建 `.venv` 并安装依赖）。
2. 确保 `ffmpeg` 可被程序找到（见上节）。

### 4.2 运行

双击 `run_whisper.bat`。

界面流程：
1. 选择录音文件（可多选）
2. 选择设备（`cuda` 或 `cpu`，默认 `cuda`）
3. 点击“开始转换”

说明：
- 首次运行会下载 Whisper 模型，后续复用缓存，可离线使用。
- 若程序启动失败，`run_whisper.bat` 会暂停并显示报错，不会直接闪退。

## 5. 转写参数（与代码一致）

- 语言固定：`language=zh`
- 不使用：`initial_prompt` / `hotwords`
- `no_speech_threshold=None`（尽量减少整窗跳过）
- VAD 默认关闭（见 `cn_stock_asr.py` 的 `WHISPER_USE_VAD_FILTER=False`）

## 6. CUDA 常见问题（cublas64_12.dll）

若选择 `cuda` 时出现 `cublas64_12.dll`、`cudnn`、`nvrtc` 等动态库错误：

- 方案 A：切换设备为 `cpu`（最直接）
- 方案 B：安装匹配的 CUDA 12.x 运行库，并将其 `bin` 加入 PATH  
  - 下载页：[CUDA Downloads](https://developer.nvidia.com/cuda-downloads)  
  - 归档页：[CUDA Toolkit Archive](https://developer.nvidia.com/cuda-toolkit-archive)

程序已实现 GPU 失败自动回退 CPU（初始化或识别阶段）。

## 7. 迁移到其他电脑

### 7.1 推荐方式：拷贝整个项目目录

1. 在当前机器上至少成功转写一次（确保模型已下载）。
2. 打包整个项目目录（可包含 `.venv` 与 `tools\`）。
3. 目标机器保持相同 Python 主版本（建议同为 3.11）。
4. 若 `.venv` 不可用，删除 `.venv` 后重新执行 `install.bat`。

### 7.2 可选方式：PyInstaller

- 使用 `build_exe.bat`（配置见 `pyinstaller_whisper.spec`）
- 仍需可用的 `ffmpeg`

## 8. 模型缓存位置

- Whisper 通常缓存在用户目录下 Hugging Face 缓存（如 `~\.cache\huggingface`）。

## 9. 文件说明

| 文件 | 说明 |
|------|------|
| `stt_whisper_gui.py` | GUI 主程序（批量转写流程） |
| `audio_utils.py` | ffmpeg/ffprobe、输出路径、写盘、打开目录、时长格式化 |
| `cn_stock_asr.py` | Whisper 相关开关（VAD 默认关闭） |
| `zh_output.py` | 中文文本后处理（空格清理 + 简体转换） |
| `requirements.txt` | 依赖列表 |
| `install.bat` | 一键安装依赖 |
| `run_whisper.bat` | 启动 GUI |
| `build_exe.bat` | 可选打包脚本 |
| `pyinstaller_whisper.spec` | PyInstaller 配置 |
