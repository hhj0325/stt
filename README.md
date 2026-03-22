# 本地语音转文字（Whisper）

满足需求：选择录音文件（如 `.m4a`，**可多选批量**），在本地用 **faster-whisper** 识别，生成**与录音同目录**的 **`主文件名_raw.txt`**（例如 `20250101上.m4a` → `20250101上_raw.txt`）。**再次转写时覆盖同名 `_raw.txt`**，不保留上一版内容。

## 常见问题：cublas64_12.dll

NVIDIA 官网上 **CUDA Toolkit 可能已更新到 13**，但通过 `pip` 安装的 **faster-whisper（CTranslate2）** 等预编译包，往往仍按 **CUDA 12** 系列去加载动态库，因此报错里会出现 **`cublas64_12.dll`**（数字 **12** 对应 CUDA 大版本，不是“必须装最新版 Toolkit”）。

若使用 **cuda** 时出现该错误，任选其一：

- 在界面里把 **设备** 改为 **`cpu`**（最省事）；或
- 安装与本机 **pip 轮子匹配的 CUDA 12 运行库**：安装 **[CUDA Toolkit 12.x](https://developer.nvidia.com/cuda-downloads)**（若下载页默认只有 13，可到 [CUDA 归档](https://developer.nvidia.com/cuda-toolkit-archive) 选 **12.x**）。安装后把其中的 `bin`（内含 `cublas64_12.dll`）加入系统 **PATH**。**CUDA 12 与 13 可并存**，PATH 里让 **12.x 的 `bin`** 被程序找到即可。
- 若你 intentionally 只装了 CUDA 13，而轮子仍要找 `*_12.dll`，只会继续报错；此时要么 **补装 12.x**，要么等/换用 **明确支持 CUDA 13** 的 `ctranslate2`/`torch` 版本（以各包官方说明为准）。

Whisper 已支持在 GPU 初始化或识别失败时 **自动回退到 CPU**；若仍报错，请直接选 **cpu**。

## 环境要求

- Windows 11，已安装 **Python 3.10 或 3.11**（安装时勾选 “Add to PATH”）。
- **ffmpeg**：用于解码 m4a 等。任选其一：
  - 将 `ffmpeg.exe` 放到项目下的 `tools\` 目录（推荐，便于拷贝整包）；程序启动时会把 `tools` 临时加入进程 **PATH**；或
  - 安装 ffmpeg 并加入系统 PATH。
- **ffprobe**（可选）：与 ffmpeg 同包，建议将 `ffprobe.exe` 一并放入 `tools\` 或 PATH，界面日志可显示**录音时长**；仅有 ffmpeg 时不影响转写，仅不显示时长。

## 一键安装依赖

1. 双击运行 **`install.bat`**（创建 `.venv` 并 `pip install -r requirements.txt`，首次较慢）。
2. 按上文配置 ffmpeg。

## 运行

- 双击 **`run_whisper.bat`**（`faster-whisper`，模型固定 **`medium`**）。**固定中文**（`language=zh`）；无行业提示词/热词，优先保证各段尽量出字（见下节）。

界面操作：**选择录音文件（可多选）** → **开始转换**。按顺序处理列表，日志中带**每条音频时长**与**单文件耗时**及**批量总耗时**。完成后弹出汇总，并**自动打开最后一个成功输出文件所在文件夹**（Windows）。首次运行会从网络下载模型；下载完成后可离线使用（模型缓存在用户目录，见下）。

生成的 **`.txt` 为 UTF-8 编码**，全文经 **`zhconv` 规范为大陆简体**；写文件前会**合并汉字之间多余空格**（`zh_output.collapse_cjk_interchar_spaces`）。若尚未安装依赖，请重新执行 **`install.bat`** 或 `pip install -r requirements.txt`。

## Whisper 通用转写（优先尽量多输出）

- **不传** `initial_prompt` / `hotwords`，按模型默认解码。
- **`no_speech_threshold=None`**：不按「无语音概率」整窗跳过，尽量保留各时间窗的识别结果（长静音里偶发胡编略增，属权衡）。
- **默认关闭 VAD**（[`cn_stock_asr.py`](cn_stock_asr.py) 中 `WHISPER_USE_VAD_FILTER = False`）：减少 BGM/音量起伏导致的误切丢句；极干净人声可改为 `True`。

## 迁移到其他 Win11 电脑

**方式 A（推荐，稳定）**

1. 在本机运行过至少一次识别，确保模型已下载。
2. 将整个项目文件夹打成压缩包（含 `.venv`、`tools\ffmpeg.exe`、脚本等）拷贝到目标电脑。
3. 目标电脑需为 **同架构**（一般均为 64 位），并安装 **同主版本 Python**（如均为 3.11），以便 `venv` 中的路径有效；若目标机 Python 路径不同，可在目标机上删除 `.venv` 后重新执行 **`install.bat`**。

**方式 B（可选，文件夹 exe）**

- 双击 **`build_exe.bat`** 生成 `dist\stt_whisper_gui`（体积较大，PyInstaller 可能需要按报错补 `hiddenimports`）。
- 仍需提供 **ffmpeg**（PATH 或 exe 旁 `tools\ffmpeg.exe`）。

## 模型缓存位置（离线后依赖此目录）

- **Whisper / faster-whisper**：一般在用户目录下 Hugging Face 缓存（如 `~\.cache\huggingface`）。

## 文件说明

| 文件 | 说明 |
|------|------|
| `zh_output.py` | 合并汉字间空格 + 转大陆简体 |
| `cn_stock_asr.py` | Whisper：是否启用 VAD（默认关） |
| `stt_whisper_gui.py` | Whisper 界面 |
| `audio_utils.py` | ffmpeg/ffprobe、`主文件名_raw.txt` 路径、覆盖写入、打开文件夹、时长格式化 |
| `requirements.txt` | Python 依赖 |
| `install.bat` / `run_whisper.bat` | 安装与启动 |
| `pyinstaller_whisper.spec` | 可选打包 |
