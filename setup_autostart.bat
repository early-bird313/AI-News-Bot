@echo off
title Setup AI News Windows Autostart
cd /d "%~dp0"

echo =====================================================================
echo  AI News Monitoring - Windows Autostart Setup
echo =====================================================================
echo.
echo Installing background startup task...

:: Method: Create a shortcut in the user's Windows Startup folder
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut(\"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\AINewsMonitoring.lnk\"); $s.TargetPath = \"wscript.exe\"; $s.Arguments = '\"' + (Get-Item '%~dp0start_background.vbs').FullName + '\"'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'AI News Monitoring Background Service'; $s.Save()"

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] Windows Startup Task configured successfully!
    echo The system will now automatically run silently in the background
    echo every time you start or log into your PC.
    echo.
    echo To test starting it in the background right now:
    echo Double-click "start_background.vbs" or run "run.bat"
) else (
    echo.
    echo [WARNING] Could not create startup shortcut.
)

echo.
pause
