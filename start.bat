@echo off
setlocal

echo ====================================
echo   Xinda Project Launcher
echo ====================================
echo.

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%xinda-backend"
set "FRONTEND_DIR=%PROJECT_DIR%xinda-frontend"

echo [Step 1/4] Check Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Node.js not installed
    echo.
    echo Please download and install Node.js 22 LTS:
    echo   https://nodejs.org/
    echo.
    echo After installation, run this script again.
    echo.
    goto :end
)
echo OK - Node.js version:
node --version
echo.

echo [Step 2/4] Check Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
)
if %errorlevel% neq 0 (
    py --version >nul 2>&1
)
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python not installed
    echo.
    echo Please download and install Python 3.13:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    echo After installation, run this script again.
    echo.
    goto :end
)
echo OK - Python version:
python --version
echo.

echo [Step 3/4] Install backend dependencies...
cd /d "%BACKEND_DIR%"
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        echo Possible reason: Python not installed correctly or version too low
        goto :end
    )
)

call venv\Scripts\activate.bat
echo Installing Python packages (may take a few minutes)...
pip install -q fastapi uvicorn python-multipart sqlalchemy pillow python-docx PyPDF2 PyMuPDF requests python-dotenv httpx
if %errorlevel% neq 0 (
    echo ERROR: pip install failed
    echo Possible reason: Network issue or pip version too low
    goto :end
)

if not exist "uploads" mkdir uploads
if not exist "data" mkdir data
echo OK - Backend dependencies installed
echo.

echo [Step 4/4] Install frontend dependencies...
cd /d "%FRONTEND_DIR%"
if not exist "node_modules" (
    echo Installing Node.js packages (may take a few minutes)...
    npm install --silent
    if %errorlevel% neq 0 (
        echo ERROR: npm install failed
        echo Possible reason: Network issue or npm version too low
        goto :end
    )
)
echo OK - Frontend dependencies installed
echo.

cd /d "%PROJECT_DIR%"
echo ====================================
echo   Start Services
echo ====================================
echo.

echo [1/2] Starting backend (port 8000)...
cd /d "%BACKEND_DIR%"
call venv\Scripts\activate.bat
start /b python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
cd /d "%PROJECT_DIR%"
timeout /t 3 /nobreak >nul
echo Backend started

echo [2/2] Starting frontend (port 3000)...
cd /d "%FRONTEND_DIR%"
start /b npm run dev -- --webpack
cd /d "%PROJECT_DIR%"
timeout /t 5 /nobreak >nul
echo Frontend started

echo.
echo ====================================
echo   Services Running
echo ====================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.

echo Opening browser...
timeout /t 2 /nobreak >nul
start http://localhost:3000
echo Browser opened
echo.

echo ====================================
echo   Instructions
echo ====================================
echo.
echo - Services are running in background
echo - Close this window to stop all services
echo - First startup may take 1-2 minutes to compile
echo.

:end
echo Press any key to exit...
pause >nul
