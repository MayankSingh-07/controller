@echo off
setlocal enabledelayedexpansion
title Ultra-Low Latency Phone Game Controller
color 0b
echo ===================================================
echo   Starting Ultra-Low Latency Phone Controller
echo ===================================================
echo.

set "PYTHON_EXE="
where python >nul 2>nul && set "PYTHON_EXE=python"
if not defined PYTHON_EXE (
    where py >nul 2>nul && set "PYTHON_EXE=py"
)
if not defined PYTHON_EXE (
    where python3 >nul 2>nul && set "PYTHON_EXE=python3"
)

if not defined PYTHON_EXE (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

%PYTHON_EXE% run_controller.py %*
pause
