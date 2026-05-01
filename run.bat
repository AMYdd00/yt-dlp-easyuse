@echo off
cd /d "%~dp0"
chcp 65001 >nul
setlocal enabledelayedexpansion
title YT-DLP Monitor

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

echo [INFO] Starting API...
start /b "" python server.py >nul 2>nul
echo [INFO] Starting worker...
start /b "" python worker.py >nul 2>nul
for /f "tokens=2" %%a in ('tasklist /fi "IMAGENAME eq python.exe" /fo csv /nh') do set wp=%%a
echo !wp!>.worker_pid
ping -n 2 127.0.0.1 >nul

echo.
echo ========================
echo   YT-DLP Monitor
echo   http://localhost:38848
echo   Use stop.bat to quit
echo ========================

:loop
if exist .stop_signal (
    del .stop_signal
    echo [INFO] Shutting down...
    goto cleanup
)
ping -n 2 127.0.0.1 >nul
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
echo [INFO] Stopped
endlocal
exit
