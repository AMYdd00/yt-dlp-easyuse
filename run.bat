@echo off
cd /d "%~dp0"
title YT-DLP Monitor
echo Starting YT-DLP services...

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

echo ========================
echo  YT-DLP Monitor
echo  http://localhost:38848
echo  Run stop.bat to exit
echo ========================

:loop
if exist .stop_signal (
    del .stop_signal
    goto cleanup
)
timeout /t 3 >nul
goto loop

:cleanup
taskkill /f /im yt-dlp.exe >nul 2>nul
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":38848 "') do (
    taskkill /f /pid %%p >nul 2>nul
)
echo Done.
timeout /t 2 >nul
exit
