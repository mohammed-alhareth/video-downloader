@echo off
setlocal
cd /d "%~dp0"
echo.
echo ==== Video Downloader by DOSAN - install ====
echo.

where py >nul 2>nul
if errorlevel 1 (
    echo Python is not installed. Install it from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" during setup, then run this file again.
    pause
    exit /b 1
)

echo [1/2] Finding pythonw.exe ...
for /f "delims=" %%i in ('py -3 -c "import sys,os;print(os.path.join(os.path.dirname(sys.executable),'pythonw.exe'))"') do set "PYW=%%i"
if not exist "%PYW%" (
    echo pythonw.exe not found.
    pause
    exit /b 1
)
echo %PYW%

echo.
echo [2/2] Creating desktop shortcut ...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$d=[Environment]::GetFolderPath('Desktop');" ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d 'Video Downloader.lnk'));" ^
  "$s.TargetPath='%PYW%';" ^
  "$s.Arguments='\"%~dp0video_downloader.pyw\"';" ^
  "$s.WorkingDirectory='%~dp0';" ^
  "$s.IconLocation='%~dp0icon.ico';" ^
  "$s.Description='Video Downloader by DOSAN';" ^
  "$s.Save()"

echo   Shortcut created on your desktop.
echo.
echo Now installing the tools (yt-dlp, ffmpeg, deno) ...
for /f "delims=" %%i in ('py -3 -c "import sys;print(sys.executable)"') do set "PYEXE=%%i"
call "%~dp0setup.bat" "%PYEXE%"
