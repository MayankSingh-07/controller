@echo off
color 0e
echo ========================================================
echo   Removing Auto-Start Shortcut
echo ========================================================
echo.

set SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\PhoneGamepadController.lnk

if exist "%SHORTCUT%" (
    del "%SHORTCUT%"
    echo [SUCCESS] Removed Phone Controller from Windows startup.
) else (
    echo [INFO] Startup shortcut was not found.
)

echo.
pause
