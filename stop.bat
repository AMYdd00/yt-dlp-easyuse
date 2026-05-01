@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
echo [INFO] 正在停止 YT-DLP 服务...

taskkill /f /im yt-dlp.exe >nul 2>nul
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":38848 "') do (
    taskkill /f /pid %%p >nul 2>nul
)
if exist .worker_pid (
    set /p wp=<.worker_pid
    taskkill /f /pid !wp! >nul 2>nul
    del .worker_pid
)

echo . 2>nul 1>.stop_signal
echo [INFO] YT-DLP 服务已停止
timeout /t 2 >nul
