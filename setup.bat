@echo off
:: OptiMatch - Setup Launcher
:: Double-click this file to run the full setup and build run.exe

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Setup failed. See error above.
    pause
    exit /b %ERRORLEVEL%
)
pause
