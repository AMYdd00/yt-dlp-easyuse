@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: === 清理旧进程（精确杀，不碰其他 Python）===

:: 1. 杀 yt-dlp 下载器
taskkill /f /im yt-dlp.exe >nul 2>nul

:: 2. 杀占用 38848 端口的进程（旧 server.py）
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":38848 "') do (
    taskkill /f /pid %%p >nul 2>nul
)

:: 3. 杀旧 worker.py（通过 PID 文件）
if exist "ytdlp_worker.pid" (
    set /p wpid=<ytdlp_worker.pid
    taskkill /f /pid !wpid! >nul 2>nul
    del ytdlp_worker.pid >nul 2>nul
)

:: === 初始化文件夹 ===
if not exist "logs" mkdir logs
if not exist "Downloads" mkdir Downloads

echo [+] 启动 API 服务...
start /b "" python server.py >nul 2>nul
echo [+] 启动下载调度...
start /b "" python worker.py >nul 2>nul
timeout /t 2 >nul

echo ============================================
echo   YT-DLP 监控系统
echo   服务地址: http://localhost:38848
echo   退出本窗口即可停止所有服务
echo ============================================
echo.

:hold
choice /c:xc /t 10 /d c /m "按 X 退出服务, 或等待10秒..." >nul
if errorlevel 2 goto :hold
if errorlevel 1 goto :cleanup

:cleanup
echo.
echo 正在停止服务...
taskkill /f /im yt-dlp.exe >nul 2>nul

:: 杀 server.py（按端口）
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":38848 "') do (
    taskkill /f /pid %%p >nul 2>nul
)

:: 杀 worker.py（按 PID 文件）
if exist "ytdlp_worker.pid" (
    set /p wpid=<ytdlp_worker.pid
    taskkill /f /pid !wpid! >nul 2>nul
    del ytdlp_worker.pid >nul 2>nul
)

echo 已停止，按任意键退出
pause >nul
