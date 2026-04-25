@echo off
setlocal enabledelayedexpansion
chcp 936 >nul
cd /d "%~dp0"
if not exist "logs" mkdir "logs"

taskkill /f /im yt-dlp.exe >nul 2>nul
timeout /t 1 >nul
del /q logs\*.log >nul 2>nul

start "Monitor-Server" /b python server.py  >nul

:loop
cls
echo [%time%] === Scanning list.txt (VOD Only) ===
for /f "tokens=*" %%i in (list.txt) do (
    set "url=%%i"
    for /f "tokens=2 delims=@" %%a in ("%%i") do (
        for /f "tokens=1 delims=/" %%b in ("%%a") do set "name=%%b"
    )
    
    tasklist /v /fi "imagename eq yt-dlp.exe" | find /i "%%i" >nul
    if errorlevel 1 (
        echo [+] Found Target: !name!
        start "!name!" /b yt-dlp --js-runtimes node ^
         --proxy "http://127.0.0.1:7890" ^
         "!url!" ^
         --match-filter "live_status = was_live" ^
         --ignore-no-formats ^
         --download-archive "archive.txt" ^
         --fragment-retries 10 --retry-sleep 5 ^
         -f "bestvideo[height=1080]+bestaudio/best" ^
         --merge-output-format mp4 ^
         -o "Downloads/%%(uploader)s/[%%(upload_date)s] %%(title)s.%%(ext)s" ^
         --progress-template "%%(progress._percent_str)s | %%(progress._speed_str)s | %%(progress._eta_str)s" ^
         --newline ^
         > "logs\!name!.log" 2>&1
    ) else (
        echo [!] !name! is already running.
    )
)
timeout /t 120
goto loop
