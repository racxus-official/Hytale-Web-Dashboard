@echo off
setlocal enabledelayedexpansion

:: --- HYTALE DASHBOARD WINDOWS LAUNCHER ---
echo ========================================
echo   Hytale Web Dashboard - Windows Mode
echo ========================================

:: Get current directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.
    pause
    exit /b
)

:: 2. Setup Virtual Environment
if not exist "venv" (
    echo [INFO] Creating virtual environment (venv)...
    python -m venv venv
)

:: 3. Activate venv and check dependencies
call venv\Scripts\activate

echo [INFO] Verifying dependencies...
:: Silent check and install
python -c "import flask, flask_cors, psutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing missing dependencies (Flask, CORS, psutil)...
    pip install Flask Flask-CORS psutil
)

:: 4. Auto-Sync config.json for Windows
:: This tells the API to use the current directory paths
python -c "import json, os; config_path = 'config.json'; script_path = os.path.join(os.getcwd(), 'start.sh').replace('\\', '/'); server_path = os.path.join(os.getcwd(), 'Server').replace('\\', '/'); data = {'admin_token': 'admin', 'start_script': script_path, 'server_dir': server_path, 'max_ram': 12}; f = open(config_path, 'w'); json.dump(data, f, indent=4); f.close()"

:: 5. Start Dashboard
echo [INFO] Starting Web Dashboard...
echo [URL] http://localhost:5000
echo ----------------------------------------
python server_api.py

pause