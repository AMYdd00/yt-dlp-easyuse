@echo off
cd /d "%~dp0"
title YT-DLP 监控系统
echo 正在启动 YT-DLP 服务...

taskkill /f /im yt-dlp.exe >nul 2>nul
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":38848 "') do (
    taskkill /f /pid %%p >nul 2>nul
)

if not exist logs mkdir logs
if not exist Downloads mkdir Downloads
if exist .stop_signal del .stop_signal

start /b "" python server.py >nul 2>nul
start /b "" python worker.py >nul 2>nul
timeout /t 2 >nul

echo ================================
echo   YT-DLP 监控系统
echo   地址: http://localhost:38848
echo   关闭请运行 stop.bat
echo ================================
echo.

:loop
if exist .stop_signal (
    del .stop_signal
    echo.
    echo [INFO] 收到停止信号，正在关闭...
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
