@echo off
color 0a
echo ========================================================
echo   Setting up Auto-Start on Windows 11 Login
echo ========================================================
echo.

set SCRIPT_DIR=%~dp0
set TARGET=%SCRIPT_DIR%run_silent.vbs
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%STARTUP_DIR%\PhoneGamepadController.lnk'); $s.TargetPath = '%TARGET%'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.Save()"

if %errorlevel% equ 0 (
    echo [SUCCESS] Phone Controller will now run silently in the background
    echo           every time your laptop turns on. No terminal window will appear!
) else (
    echo [ERROR] Failed to register startup shortcut.
)

echo.
pause
