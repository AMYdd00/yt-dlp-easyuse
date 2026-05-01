@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
echo [INFO] 正在停止 YT-DLP 服务...

:: 杀死 yt-dlp
taskkill /f /im yt-dlp.exe >nul 2>nul

:: 杀死 server (端口)
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":38848 "') do (
    taskkill /f /pid %%p >nul 2>nul
)

:: 杀死 worker (|PID 文桶)
if exist .worker_pid (
    set /p wp=<.worker_pid
    taskkill /f /pid !wp! >nul 2>nul
    del .worker_pid
)

:: 关闭 run.bat 窗口
echo [INFO] 关闭 run.bat...
taskkill /f /fi "WINDOWTITLE eq YT-DLP*" >nul 2>nul

echo [INFO] YT-DLP 服务已停止
timeout /t 2 >nul
