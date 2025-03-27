@echo off
echo CyberShield AI Backup Utility
echo ============================
echo.

REM Check if WSL is available
where wsl >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Windows Subsystem for Linux (WSL) not found.
    echo Please install WSL to run the backup scripts.
    echo Visit: https://docs.microsoft.com/en-us/windows/wsl/install
    exit /b 1
)

echo Running backup through WSL...
wsl bash ./backup-tools/backup.sh
echo.
echo Backup process completed.