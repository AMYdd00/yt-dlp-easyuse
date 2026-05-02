@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title YT-DLP Monitor

:: Cleanup stale PID files
if exist .server_pid (
    set /p old_pid=<.server_pid
    taskkill /f /pid !old_pid! >nul 2>nul
)
if exist .worker_pid (
    set /p old_pid=<.worker_pid
    taskkill /f /pid !old_pid! >nul 2>nul
)
if exist .stop_signal del .stop_signal

if not exist logs mkdir logs
if not exist Downloads mkdir Downloads

echo [INFO] Starting API...
start /b "" python server.py >nul 2>nul
echo [INFO] Starting worker...
start /b "" python worker.py >nul 2>nul
timeout /t 2 >nul

echo ================================
echo   YT-DLP Monitor
echo   http://localhost:38848
echo   Use stop.bat to shutdown
echo   Close window anytime, runs in background
echo ================================

:loop
:: Check if backend processes are alive
if exist .server_pid (
    set /p pid=<.server_pid
    tasklist /fi "PID eq !pid!" 2>nul | findstr /i "python" >nul 2>nul
    if errorlevel 1 (
        echo [WARN] API process !pid! died, restarting...
        start /b "" python server.py >nul 2>nul
        timeout /t 2 >nul
    )
)
if exist .worker_pid (
    set /p pid=<.worker_pid
    tasklist /fi "PID eq !pid!" 2>nul | findstr /i "python" >nul 2>nul
    if errorlevel 1 (
        echo [WARN] Worker process !pid! died, restarting...
        start /b "" python worker.py >nul 2>nul
        timeout /t 2 >nul
    )
)
if exist .stop_signal (
    del .stop_signal
    goto cleanup
)
timeout /t 5 >nul
goto loop

:cleanup
if exist .server_pid (
    set /p pid=<.server_pid
    taskkill /f /pid !pid! >nul 2>nul
)
if exist .worker_pid (
    set /p pid=<.worker_pid
    taskkill /f /pid !pid! >nul 2>nul
)
taskkill /f /im yt-dlp.exe >nul 2>nul
echo [INFO] Stopped
exit
