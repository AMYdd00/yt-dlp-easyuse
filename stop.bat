@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [INFO] 正在停止 YT-DLP 服务...

taskkill /f /im yt-dlp.exe >nul 2>nul

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":38848 "') do (
    taskkill /f /pid %%p >nul 2>nul
)

echo . > .stop_signal
echo [INFO] YT-DLP 服务 已停止
timeout /t 2 >nul
