@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo 请先运行 install.bat
  pause
  exit /b 1
)
".\.venv\Scripts\python.exe" stt_whisper_gui.py
if errorlevel 1 (
  echo.
  echo 启动失败，请查看上方报错。
  pause
)
