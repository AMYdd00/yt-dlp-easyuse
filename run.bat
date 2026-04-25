@echo off
setlocal enabledelayedexpansion
:: 强制使用 UTF-8 编码，防止特殊字符或日韩文频道名导致抓取错误
chcp 65001 >nul
cd /d "%~dp0"

:: 初始化文件夹
if not exist "logs" mkdir "logs"
if not exist "Downloads" mkdir "Downloads"

:: 启动前清理残留进程和旧日志
taskkill /f /im yt-dlp.exe >nul 2>nul
timeout /t 1 >nul
del /q logs\*.log >nul 2>nul

:: 启动你的 Python 监控服务端
start "Monitor-Server" /b python server.py >nul

echo ===================================================
echo    YT-DLP 稳定版录像(VOD)防漏下载监控已启动
echo ===================================================

:loop
cls
echo [%time%] === 正在扫描 list.txt ===
echo [提醒] 请确保 list.txt 里的链接是频道的 streams 页面
echo [示例] https://www.youtube.com/@ChannelName/streams
echo ===================================================

for /f "tokens=*" %%i in (list.txt) do (
    set "url=%%i"
    
    :: 提取频道名用于防重检测和日志命名
    set "name=unknown"
    for /f "tokens=2 delims=@" %%a in ("%%i") do (
        for /f "tokens=1 delims=/" %%b in ("%%a") do set "name=%%b"
    )
    
    :: 检测该频道的 yt-dlp 是否已经在运行
    tasklist /v /fi "imagename eq yt-dlp.exe" | find /i "!name!" >nul
    if errorlevel 1 (
        echo [+] 扫描到频道: !name!，正在执行下载策略...
        
        start "!name!" /b yt-dlp --js-runtimes node ^
         --proxy "http://127.0.0.1:7890" ^
         "!url!" ^
         --match-filter "live_status != is_live" ^
         --playlist-items 1 ^
         --ignore-no-formats ^
         --download-archive "archive.txt" ^
         -c ^
         --retries 50 --fragment-retries 50 --retry-sleep 10 --extractor-retries 10 ^
         -f "bestvideo[height<=1080]+bestaudio/best" ^
         --merge-output-format mp4 ^
         -o "Downloads/%%(uploader)s/[%%(upload_date)s] %%(title)s.%%(ext)s" ^
         --progress-template "%%(progress._percent_str)s | %%(progress._speed_str)s | %%(progress._eta_str)s" ^
         --newline ^
         > "logs\!name!.log" 2>&1
    ) else (
        echo [!] !name! 的下载任务正在稳定运行中，跳过。
    )
)

echo.
echo [%time%] 本轮扫描完毕，挂机等待 120 秒后进行下一次检测...
timeout /t 120 >nul
goto loop