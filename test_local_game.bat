@echo off
REM ============================================================================
REM CodeBreak Local Game Test Script
REM Tests the game client locally before deploying to EC2
REM ============================================================================

echo ================================
echo CodeBreak Local Game Tester
echo ================================
echo.

REM Check if we're in the correct directory
if not exist "frontend\unified_game_launcher.py" (
    echo ERROR: Please run this script from the CodeBreak root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)
python --version
echo.

echo [2/5] Checking/Installing dependencies...
cd frontend
python install_dependencies.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)
echo.

echo [3/5] Checking for client config...
if not exist "client_config.json" (
    echo WARNING: No client_config.json found
    echo.
    echo Creating a test configuration...
    echo You'll need to login through the web browser to get your token
    echo.
    
    REM Create a template config
    echo { > client_config.json
    echo   "server_url": "http://3.19.244.138:8000", >> client_config.json
    echo   "token": "YOUR_TOKEN_HERE", >> client_config.json
    echo   "username": "testplayer" >> client_config.json
    echo } >> client_config.json
    
    echo Template created. Opening browser for login...
    timeout /t 2 >nul
    start http://3.19.244.138:8000/login
    echo.
    echo After logging in, the game will create your config automatically.
    echo.
) else (
    echo Found existing client_config.json
    echo.
)

echo [4/5] Testing game imports...
python -c "import pygame; import websockets; import requests; print('All imports successful!')"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Some Python modules failed to import
    echo Try running: python install_dependencies.py
    pause
    exit /b 1
)
echo.

echo [5/5] Starting game launcher...
echo.
echo ================================
echo Game will start in 3 seconds...
echo ================================
timeout /t 3 >nul

REM Start the game
python unified_game_launcher.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ================================
    echo Game exited with an error
    echo ================================
    echo.
    echo Common issues:
    echo 1. No internet connection
    echo 2. Server is down (check http://3.19.244.138:8000)
    echo 3. Invalid login credentials
    echo 4. Missing dependencies
    echo.
    echo Check the error messages above for details.
)

cd ..
echo.
pause
