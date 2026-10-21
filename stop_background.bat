@echo off
title Stop AI News Monitoring Background Service
cd /d "%~dp0"

echo [INFO] Searching for background service running on port 8000...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Host 'Terminated process on port 8000 (PID:' $_.OwningProcess ')' }"

echo [INFO] Background service stopped.
pause
