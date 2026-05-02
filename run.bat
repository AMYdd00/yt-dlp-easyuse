@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title YT-DLP 监控系统

:: 清理残留
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

echo [INFO] 启动 API...
start /b "" python server.py >nul 2>nul
echo [INFO] 启动 worker...
start /b "" python worker.py >nul 2>nul
timeout /t 2 >nul

echo ================================
echo   YT-DLP 监控系统
echo   地址: http://localhost:38848
echo   关闭请用 stop.bat
echo   本窗口可随时关闭, 后台继续运行
echo ================================

:loop
:: 检测后台进程是否存活
if exist .server_pid (
    set /p pid=<.server_pid
    tasklist /fi "PID eq !pid!" 2>nul | findstr /i "python" >nul 2>nul
    if errorlevel 1 (
        echo [WARN] API 服务已异常退出 (PID: !pid!), 正在重启...
        start /b "" python server.py >nul 2>nul
        timeout /t 2 >nul
    )
)
if exist .worker_pid (
    set /p pid=<.worker_pid
    tasklist /fi "PID eq !pid!" 2>nul | findstr /i "python" >nul 2>nul
    if errorlevel 1 (
        echo [WARN] Worker 已异常退出 (PID: !pid!), 正在重启...
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
echo [INFO] 已停止
exit
