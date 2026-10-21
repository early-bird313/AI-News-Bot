@echo off
title AI News Monitoring and Daily Digest System
cd /d "%~dp0"

echo =====================================================================
echo  AI News Monitoring and Daily Digest System
echo  Localhost: http://localhost:8000
echo  Telegram Digests: 10:00 AM, 2:00 PM, 9:00 PM
echo =====================================================================
echo.

if not exist "backend\.venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment not found in backend\.venv.
    pause
    exit /b 1
)

echo [INFO] Starting Backend Server and Live Dashboard...
echo [INFO] Press Ctrl+C at any time to stop the server.
echo.

:: Open browser after 2 seconds in background
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000"

cd backend
".venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Server exited with code %ERRORLEVEL%.
    pause
)
