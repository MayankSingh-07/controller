@echo off
title Ultra-Low Latency Phone Game Controller
color 0b
echo ===================================================
echo   Starting Ultra-Low Latency Phone Controller
echo ===================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

python run_controller.py %*
pause
