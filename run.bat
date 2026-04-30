@echo off
cd /d "%~dp0"
title YT-DLP 监控系统

echo ============================================
echo  ** 注意: 直接关窗口后台服务会继续运行 **
echo  关闭请用 stop.bat
echo  旧 worker.py 会占用资源，别直接关窗口
echo ============================================
echo.

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
echo !wp!>.worker_pid

timeout /t 2 >nul

echo.
echo ========================
echo  YT-DLP 监控系统
echo  地址: http://localhost:38848
echo  关闭请用 stop.bat
echo ========================
echo.

:loop
if exist .stop_signal (
    del .stop_signal
    echo [INFO] 关闭...
    goto cleanup
)
timeout /t 3 >nul
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
echo [INFO] 已停止
timeout /t 2 >nul
exit
