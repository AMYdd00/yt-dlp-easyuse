@echo off
chcp 65001 >nul
title YT-DLP 监控系统
cd /d "%~dp0"

:: === 清理旧进程 ===
taskkill /f /im yt-dlp.exe >nul 2>nul

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":38848 "') do (
    taskkill /f /pid %%p >nul 2>nul
)

:: === 确保目录存在 ===
if not exist "logs" mkdir logs
if not exist "Downloads" mkdir Downloads
if exist ".stop_signal" del .stop_signal

:: === 后台启动 ===
echo [INFO] 启动 API 服务...
start /b "" python server.py >nul 2>nul
echo [INFO] 启动 下载调度...
start /b "" python worker.py >nul 2>nul
timeout /t 2 >nul

echo ============================================
echo   YT-DLP 监控系统
echo   地址: http://localhost:38848
echo   关闭 请 运行 stop.bat
echo ============================================
echo.

:loop
if exist ".stop_signal" (
    del .stop_signal
    echo.
    echo [INFO] 收到停止信号...
    goto cleanup
)
timeout /t 3 >nul
goto loop

:cleanup
taskkill /f /im yt-dlp.exe >nul 2>nul
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":38848 "') do (
    taskkill /f /pid %%p >nul 2>nul
)
echo [INFO] 已停止所有服务
timeout /t 2 >nul
exit
