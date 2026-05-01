@echo off
cd /d "%~dp0"
chcp 65001 >nul
echo Stopping YT-DLP...

taskkill /f /im yt-dlp.exe >nul 2>nul
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":38848 "') do (
    taskkill /f /pid %%p >nul 2>nul
)

echo . 2>nul 1>.stop_signal
echo [INFO] YT-DLP stopped
