@echo off
setlocal enabledelayedexpansion

title SpendWise Launcher

echo ========================================================
echo   SpendWise - Personal Expense Tracker & Budget Manager
echo ========================================================
echo.

cd /d "%~dp0"

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not found in PATH!
    echo Please install Python 3.10+ from python.org and add it to your PATH.
    pause
    exit /b 1
)

:: Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment (.venv)...
    call .venv\Scripts\activate.bat
)

:: Seed database if spendwise.db does not exist yet
if not exist "spendwise.db" (
    echo [INFO] Initializing and seeding database with sample data...
    python seed_data.py
)

:: Open the browser in 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000"

:: Start Uvicorn Server
echo [INFO] Starting FastAPI server at http://127.0.0.1:8000 ...
echo [INFO] Press Ctrl+C to stop the server anytime.
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
