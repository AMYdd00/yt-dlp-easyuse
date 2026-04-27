@echo off
setlocal enabledelayedexpansion
:: 强制使用 UTF-8 编码
chcp 65001 >nul
cd /d "%~dp0"

:: 初始化文件夹
if not exist "logs" mkdir "logs"
if not exist "Downloads" mkdir "Downloads"

:: 启动前清理残留进程和旧日志
taskkill /f /im yt-dlp.exe >nul 2>nul
timeout /t 1 >nul
del /q logs\*.log >nul 2>nul

:: 启动监控服务端
start "Monitor-Server" /b python server.py >nul

echo ===================================================
echo    YT-DLP 终极稳定版录像(VOD)防漏监控 (已限制最新5条)
echo ===================================================

:loop
cls
echo [%time%] === 正在扫描 list.txt ===
echo [提醒] 确保 list.txt 里的链接是频道的 streams 页面
echo ===================================================

for /f "tokens=*" %%i in (list.txt) do (
    set "url=%%i"
    
    :: 提取频道名
    set "name=unknown"
    for /f "tokens=2 delims=@" %%a in ("%%i") do (
        for /f "tokens=1 delims=/" %%b in ("%%a") do set "name=%%b"
    )
    
    :: 检测任务是否在运行
    tasklist /v /fi "imagename eq yt-dlp.exe" | find /i "!name!" >nul
    if errorlevel 1 (
        echo [+] 扫描到频道: !name!，检查最新动态...
        
        start "!name!" /b yt-dlp --js-runtimes node ^
         --proxy "http://127.0.0.1:7890" ^
         "!url!" ^
         --playlist-items 1-5 ^
         --match-filter "live_status = was_live" ^
         --download-archive "archive.txt" ^
         -c ^
         --retries infinite ^
         --fragment-retries infinite ^
         --retry-sleep 10 ^
         --extractor-retries 10 ^
         --abort-on-unavailable-fragment ^
         --concurrent-fragments 4 ^
         --fixup force ^
         --embed-metadata ^
         -f "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" ^
         --merge-output-format mp4 ^
         -o "Downloads/!name!/[%%(upload_date)s] %%(title)s.%%(ext)s" ^
         --progress-template "%%(progress._percent_str)s | %%(progress._speed_str)s | %%(progress._eta_str)s" ^
         --newline ^
         > "logs\!name!.log" 2>&1
    ) else (
        echo [!] !name! 的下载任务正在稳定运行中，跳过。
    )
)

echo.
echo [%time%] 本轮扫描完毕，挂机等待 300 秒后进行下一次检测...
timeout /t 300 >nul
goto loop