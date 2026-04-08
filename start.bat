@echo off
setlocal

echo ====================================
echo   Xinda Project Launcher
echo ====================================
echo.

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%xinda-backend"
set "FRONTEND_DIR=%PROJECT_DIR%xinda-frontend"

echo DEBUG: PROJECT_DIR = %PROJECT_DIR%
echo DEBUG: BACKEND_DIR = %BACKEND_DIR%
echo.

echo [Step 1/4] Check Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js not found. Please install Node.js 22 from: https://nodejs.org/
    echo.
    echo Then run this script again.
    pause
    exit /b 1
)
echo OK - Node.js:
node --version
echo.

echo [Step 2/4] Check Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
)
if %errorlevel% neq 0 (
    py --version >nul 2>&1
)
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.13 from: https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    echo Then run this script again.
    pause
    exit /b 1
)
echo OK - Python:
python --version
echo.

echo [Step 3/4] Backend dependencies...
cd /d "%BACKEND_DIR%"
if not exist "venv" (
    echo Creating venv...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing Python packages...
pip install -q fastapi uvicorn python-multipart sqlalchemy pillow python-docx PyPDF2 PyMuPDF requests python-dotenv httpx
if %errorlevel% neq 0 (
    echo ERROR: pip install failed
    pause
    exit /b 1
)
if not exist "uploads" mkdir uploads
if not exist "data" mkdir data
echo OK - Backend ready
echo.

echo [Step 4/4] Frontend dependencies...
cd /d "%FRONTEND_DIR%"
if not exist "node_modules" (
    echo Installing npm packages...
    npm install --silent
    if %errorlevel% neq 0 (
        echo ERROR: npm install failed
        pause
        exit /b 1
    )
)
echo Check Next.js version...
call npm list next | findstr "15.2.4" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing stable Next.js...
    call npm install next@15.2.4 eslint-config-next@15.2.4 --save
)
echo OK - Frontend ready
echo.

cd /d "%PROJECT_DIR%"
echo ====================================
echo   Start Services
echo ====================================
echo.

echo [1/2] Starting Backend (port 8000)...
cd /d "%BACKEND_DIR%"
call venv\Scripts\activate.bat
start /b python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
cd /d "%PROJECT_DIR%"
timeout /t 3 /nobreak >nul
echo Backend started

echo [2/2] Starting Frontend (port 3000)...
cd /d "%FRONTEND_DIR%"
start /b npm run dev
cd /d "%PROJECT_DIR%"
timeout /t 5 /nobreak >nul
echo Frontend started

echo.
echo ====================================
echo   DONE
echo ====================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo.

echo Opening browser...
start http://localhost:3000
echo.
echo Press Enter to exit...
pause >nul