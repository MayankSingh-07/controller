@echo off
setlocal enabledelayedexpansion
title Phone Game Controller - Auto Setup
color 0b
echo ====================================================================
echo   PHONE GAME CONTROLLER - 1-CLICK AUTOMATED SETUP FOR WINDOWS 11
echo ====================================================================
echo.

:: Detect Python executable (handles Scoop, Py launcher, standard Python)
set "PYTHON_EXE="
where python >nul 2>nul && set "PYTHON_EXE=python"
if not defined PYTHON_EXE (
    where py >nul 2>nul && set "PYTHON_EXE=py"
)
if not defined PYTHON_EXE (
    where python3 >nul 2>nul && set "PYTHON_EXE=python3"
)

if not defined PYTHON_EXE (
    echo [ERROR] Python was not found in your PATH.
    echo Opening Python download page...
    start https://www.python.org/downloads/
    echo Please install Python (make sure to check "Add python.exe to PATH") and run setup.bat again.
    pause
    exit /b 1
)

echo [*] Using Python executable: %PYTHON_EXE%
echo [*] Installing required gamepad driver library (vgamepad)...
%PYTHON_EXE% -m pip install vgamepad

echo.
echo [*] Verifying Windows Gamepad Driver (ViGEmBus)...
%PYTHON_EXE% -c "from server.driver_setup import auto_setup; auto_setup()"

echo.
echo ====================================================================
echo   [SUCCESS] Setup complete! Starting controller bridge...
echo ====================================================================
echo.
%PYTHON_EXE% run_controller.py %*

pause
