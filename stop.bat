@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在停止 YT-DLP 相关进程...

:: 杀 yt-dlp 下载进程
taskkill /f /im yt-dlp.exe >nul 2>nul

:: 只杀占用 38848 端口的进程（不杀其他 Python）
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":38848 "') do (
    taskkill /f /pid %%p >nul 2>nul
)

echo 已停止（不影响其他 Python 应用）
timeout /t 3 >nul
