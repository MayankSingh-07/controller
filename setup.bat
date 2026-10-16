@echo off
title Phone Game Controller - Auto Setup
color 0b
echo ====================================================================
echo   PHONE GAME CONTROLLER - 1-CLICK AUTOMATED SETUP FOR WINDOWS 11
echo ====================================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed.
    echo Opening Python download page...
    start https://www.python.org/downloads/
    echo Please install Python (make sure to check "Add python.exe to PATH") and run setup.bat again.
    pause
    exit /b 1
)

echo [*] Python detected.
echo [*] Installing / updating required libraries...
python -m pip install --upgrade pip >nul 2>nul
python -m pip install -r requirements.txt

echo.
echo [*] Checking and configuring Windows Gamepad Driver (ViGEmBus)...
python -c "from server.driver_setup import auto_setup; auto_setup()"

echo.
echo ====================================================================
echo   [SUCCESS] Setup complete! Starting controller bridge...
echo ====================================================================
echo.
python run_controller.py %*

pause
