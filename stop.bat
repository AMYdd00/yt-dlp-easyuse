@echo off
cd /d "%~dp0"
echo [INFO] 正在停止 YT-DLP 服务...

:: 通过 PID 文件精确杀进程，不影响其他 Python 服务
if exist .server_pid (
    set /p pid=<.server_pid
    taskkill /f /pid !pid! >nul 2>nul
    echo [INFO] 已停止 API 服务 (PID: !pid!)
)
if exist .worker_pid (
    set /p pid=<.worker_pid
    taskkill /f /pid !pid! >nul 2>nul
    echo [INFO] 已停止 Worker (PID: !pid!)
)

:: 停止 yt-dlp 下载进程
taskkill /f /im yt-dlp.exe >nul 2>nul

:: 发送停止信号给 run.bat（如果窗口还开着）
echo . > .stop_signal

echo [INFO] YT-DLP 服务已全部停止
timeout /t 2 >nul
