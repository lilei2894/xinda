@echo off
setlocal EnableDelayedExpansion

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
    echo ERROR: Node.js not installed
    echo Please install from https://nodejs.org/
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
    echo ERROR: Python not installed
    echo Please install from https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation
    goto :end
)
echo OK - Python version:
python --version
echo.

echo [Step 3/4] Install backend dependencies...
cd /d "%BACKEND_DIR%"
echo Current directory: %cd%
echo.

if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        goto :end
    )
    echo Virtual environment created
)

echo Checking venv structure...
dir venv\Scripts >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: venv\Scripts directory not found
    goto :end
)

echo Using Python directly from venv...
set "PYTHON=venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo ERROR: python.exe not found at %PYTHON%
    goto :end
)

echo Checking uv (fast Python installer)...
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing uv...
    "%PYTHON%" -m pip install uv
)
echo Installing Python packages with uv (faster)...
echo.

"%PYTHON%" -m uv pip install fastapi uvicorn python-multipart sqlalchemy pillow python-docx PyPDF2 PyMuPDF requests python-dotenv httpx

if %errorlevel% neq 0 (
    echo.
    echo ERROR: pip install failed
    echo.
    echo Try running manually:
    echo   cd xinda-backend
    echo   venv\Scripts\python.exe -m pip install fastapi uvicorn python-multipart sqlalchemy pillow python-docx PyPDF2 PyMuPDF requests python-dotenv httpx
    echo.
    goto :end
)

echo.
echo OK - Backend dependencies installed
echo.

if not exist "uploads" mkdir uploads
if not exist "data" mkdir data
echo.

echo [Step 4/4] Install frontend dependencies...
cd /d "%FRONTEND_DIR%"
echo Current directory: %cd%
echo.

if not exist "node_modules" (
    echo Checking npm...
    where npm >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR: npm not found
        goto :end
    )
    
    echo Installing Node.js packages...
    echo This may take several minutes, please wait...
    echo.
    
    call npm install
    
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: npm install failed
        echo.
        goto :end
    )
    
    echo OK - Frontend dependencies installed
    echo.
) else (
    echo node_modules already exists, skipping
    echo.
)

cd /d "%PROJECT_DIR%"
echo ====================================
echo   Start Services
echo ====================================
echo.

echo [1/2] Starting backend (port 8000)...
cd /d "%BACKEND_DIR%"
start "" /b venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
cd /d "%PROJECT_DIR%"
timeout /t 5 /nobreak >nul

echo [2/2] Starting frontend (port 3000)...
cd /d "%FRONTEND_DIR%"
start "" /b npm run dev -- --turbopack
cd /d "%PROJECT_DIR%"
timeout /t 5 /nobreak >nul

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
echo   SUCCESS - All Done!
echo ====================================
echo.
echo Services are running in background
echo Close this window to stop all services
echo.
echo Press any key to exit...

:end
pause >nul
