@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在创建虚拟环境 .venv 并安装依赖（首次较慢）...
py -3.11 -m venv .venv 2>nul
if errorlevel 1 py -3.10 -m venv .venv
if errorlevel 1 python -m venv .venv
".\.venv\Scripts\python.exe" -m pip install -U pip
".\.venv\Scripts\pip.exe" install -r requirements.txt
echo.
echo 安装完成。请将 ffmpeg.exe 放入 tools 文件夹（见 tools\PLACE_FFMPEG_HERE.txt），或安装 ffmpeg 并加入 PATH。
pause
