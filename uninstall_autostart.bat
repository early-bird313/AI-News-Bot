@echo off
title Remove AI News Windows Autostart
cd /d "%~dp0"

echo =====================================================================
echo  Removing AI News Windows Autostart
echo =====================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "Remove-Item \"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\AINewsMonitoring.lnk\" -ErrorAction SilentlyContinue"

echo [INFO] Autostart shortcut removed from Windows Startup folder.
echo.
pause
