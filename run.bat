@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: 注册退出时的清理函数
taskkill /f /im yt-dlp.exe >nul 2>nul
taskkill /f /im python.exe /fi "IMAGENAME eq python.exe" >nul 2>nul

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

:: 用 choice 保持窗口打开，同时检测进程
:hold
choice /c:xc /t 10 /d c /m "按 X 退出服务, 或等待10秒..." >nul
if errorlevel 2 goto :hold
if errorlevel 1 goto :cleanup

:cleanup
echo.
echo 正在停止服务...
taskkill /f /im yt-dlp.exe >nul 2>nul
taskkill /f /im python.exe /fi "IMAGENAME eq python.exe" >nul 2>nul
echo 已停止所有进程，按任意键退出
pause >nul
