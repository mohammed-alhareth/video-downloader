@echo off
setlocal
title Video Downloader - Setup
cd /d "%~dp0"

rem %1 = full path of python.exe (sent by the app). Without it, use the py launcher.
set "PY=%~1"
if "%PY%"=="" (
    set "PY=py -3"
) else (
    set "PY="%~1""
)

echo.
echo ===============================================
echo   Video Downloader - Setup
echo   Installing / updating: yt-dlp, ffmpeg, deno
echo ===============================================
echo.

echo [1/3] yt-dlp (download engine)
echo -----------------------------------------------
%PY% -m pip install -U "yt-dlp[default]"
if errorlevel 1 (echo   ** yt-dlp failed **) else (echo   OK)
echo.

where winget >nul 2>nul
if errorlevel 1 (
    echo winget was not found. Install "App Installer" from Microsoft Store,
    echo then run Setup again.
    goto :end
)

echo [2/3] ffmpeg (merges video and audio)
echo -----------------------------------------------
where ffmpeg >nul 2>nul
if errorlevel 1 (
    winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
) else (
    echo   Already installed
)
echo.

echo [3/3] deno (needed for YouTube)
echo -----------------------------------------------
where deno >nul 2>nul
if errorlevel 1 (
    winget install --id DenoLand.Deno -e --accept-source-agreements --accept-package-agreements
) else (
    echo   Already installed
)
echo.

:end
echo ===============================================
echo   Setup finished.
echo   Close Video Downloader and open it again.
echo ===============================================
echo.
pause
