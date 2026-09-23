@echo off
cd /d "%~dp0"
if exist "dist\RetroSFX\RetroSFX.exe" (
    "dist\RetroSFX\RetroSFX.exe" %*
) else (
    python server.py %*
)
if errorlevel 1 pause
