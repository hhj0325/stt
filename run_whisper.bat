@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo 请先运行 install.bat
  pause
  exit /b 1
)
".\.venv\Scripts\python.exe" stt_whisper_gui.py
