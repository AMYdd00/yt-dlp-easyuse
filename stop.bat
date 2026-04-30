@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在停止 YT-DLP 服务...

:: 杀 yt-dlp 下载进程
taskkill /f /im yt-dlp.exe >nul 2>nul

:: 杀 38848 端口（server.py）
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":38848 "') do (
    taskkill /f /pid %%p >nul 2>nul
)

:: 杀 worker.py（通过 PID 文件）
if exist "ytdlp_worker.pid" (
    set /p wpid=<ytdlp_worker.pid
    taskkill /f /pid !wpid! >nul 2>nul
    del ytdlp_worker.pid >nul 2>nul
)

echo 已停止（不影响其他 Python 应用）
timeout /t 3 >nul
