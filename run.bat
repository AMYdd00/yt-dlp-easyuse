@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title YT-DLP 监控系统

taskkill /f /im yt-dlp.exe >nul 2>nul
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":38848 "') do (
    taskkill /f /pid %%p >nul 2>nul
)
if exist .worker_pid (
    set /p wp=<.worker_pid
    taskkill /f /pid !wp! >nul 2>nul
    del .worker_pid
)

if not exist logs mkdir logs
if not exist Downloads mkdir Downloads
if exist .stop_signal del .stop_signal

echo [INFO] 启动 API...
start /b "" python server.py >nul 2>nul
echo [INFO] 启动 worker...
start /b "" python worker.py >nul 2>nul
for /f "tokens=2" %%a in ('tasklist /fi "IMAGENAME eq python.exe" /fo csv /nh') do set wp=%%a
echo !wp!>.worker_pid 2>nul
timeout /t 2 >nul

echo.
echo ========================
echo  YT-DLP 监控系统
echo  地址: http://localhost:38848
echo  (注意: 直接关窗口后台还在运行)
echo  关闭请用 stop.bat
echo ========================

:loop
if exist .stop_signal (
    del .stop_signal
    echo [INFO] 收到停止信号...
    goto cleanup
)
timeout /t 1 >nul
goto loop

:cleanup
taskkill /f /im yt-dlp.exe >nul 2>nul
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":38848 "') do (
    taskkill /f /pid %%p >nul 2>nul
)
if exist .worker_pid (
    set /p wp=<.worker_pid
    taskkill /f /pid !wp! >nul 2>nul
    del .worker_pid
)
echo [INFO] 已停止所有服务
timeout /t 2 >nul
exit