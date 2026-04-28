@echo off
chcp 65001 >nul
echo ========================================
echo    AIR DOME 3D Simulator R13 (Modular)
echo    OzoMeta Architecture
echo ========================================
echo.
echo Starting program...
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Python execution failed.
    echo Please check Python 3.8+ is installed.
    echo.
    pause
)
