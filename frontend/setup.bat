@echo off
echo 🚀 Setting up RAG Content Generator Frontend...

REM Check if Node.js is installed
node -v >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js is not installed. Please install Node.js 16+ first.
    pause
    exit /b 1
)

echo ✅ Node.js found: 
node -v

REM Install dependencies
echo 📦 Installing dependencies...
npm install

if %ERRORLEVEL% EQU 0 (
    echo ✅ Dependencies installed successfully
) else (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

REM Create environment file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file...
    echo # Frontend Environment Variables > .env
    echo VITE_API_BASE_URL=http://localhost:5000/api >> .env
    echo VITE_APP_TITLE=RAG Content Generator >> .env
    echo VITE_APP_DESCRIPTION=Advanced AI with Retrieval-Augmented Generation >> .env
    echo ✅ .env file created
)

echo.
echo 🎉 Setup complete! You can now:
echo.
echo    Start development server:
echo    npm run dev
echo.
echo    Build for production:
echo    npm run build
echo.
echo    Preview production build:
echo    npm run preview
echo.
echo 📝 Make sure your backend service is running on port 5000
echo 🌐 Frontend will be available at http://localhost:3000
echo.
pause