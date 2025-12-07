@echo off
title RAG Content Generator - Quick Start

echo ========================================
echo   RAG Content Generator Quick Start
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ Error: Please run this script from the main project directory
    echo    (The directory containing app.py)
    pause
    exit /b 1
)

echo 🔍 Checking prerequisites...

REM Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python is not installed or not in PATH
    echo    Please install Python 3.8+ and try again
    pause
    exit /b 1
)
echo ✅ Python found

REM Check Node.js
node -v >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js is not installed or not in PATH
    echo    Please install Node.js 16+ and try again
    pause
    exit /b 1
)
echo ✅ Node.js found

echo.
echo 📦 Installing dependencies...

REM Install Python dependencies
echo Installing Python packages...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)
echo ✅ Python dependencies installed

REM Install Node.js dependencies
echo Installing Node.js packages...
cd frontend
npm install
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install Node.js dependencies
    pause
    exit /b 1
)
echo ✅ Node.js dependencies installed
cd ..

echo.
echo 🚀 Starting services...

REM Start backend in background
echo Starting backend server...
start "RAG Backend" cmd /k "python app.py"

REM Wait a moment for backend to start
timeout /t 3 >nul

REM Start frontend
echo Starting frontend development server...
cd frontend
start "RAG Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ========================================
echo   🎉 RAG Content Generator Started!
echo ========================================
echo.
echo   Backend API: http://localhost:5000
echo   Frontend:    http://localhost:3000
echo.
echo   📝 Two terminal windows have opened:
echo      - Backend server (Python/Flask)
echo      - Frontend server (React/Vite)
echo.
echo   🌐 Open http://localhost:3000 in your browser
echo.
echo   📚 See PROJECT_OVERVIEW.md for detailed documentation
echo.
echo ========================================

pause