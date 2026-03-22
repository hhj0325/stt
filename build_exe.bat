@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo 请先运行 install.bat
  pause
  exit /b 1
)
echo 正在安装 PyInstaller...
".\.venv\Scripts\pip.exe" install -q pyinstaller
echo 正在打包 Whisper 版（输出目录 dist\stt_whisper_gui）...
".\.venv\Scripts\pyinstaller.exe" --noconfirm --clean pyinstaller_whisper.spec
echo 完成。请将 tools\ffmpeg.exe 一并拷贝到目标电脑，并加入 PATH 或放入 exe 同目录的 tools 下。
pause
