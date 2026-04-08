@echo off
setlocal

echo ====================================
echo   Xinda Project Launcher
echo ====================================
echo.

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%xinda-backend"
set "FRONTEND_DIR=%PROJECT_DIR%xinda-frontend"

REM Function to install Node.js
echo [Step 1/4] Check Node.js...
where node >nul 2>&1
if %errorlevel% equ 0 (
    echo OK - Node.js found:
    node --version
    echo.
    goto :node_done
)

echo Node.js not found. Installing Node.js 22...
where winget >nul 2>&1
if %errorlevel% equ 0 (
    echo Using winget to install Node.js 22...
    winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
    if %errorlevel% equ 0 (
        echo SUCCESS: Node.js 22 installed
        echo Please close this window and run the script again to continue.
        pause
        exit /b 0
    ) else (
        echo WARNING: winget installation failed. Please install manually from https://nodejs.org/
        pause
        exit /b 1
    )
) else (
    echo WARNING: winget not available. Please install Node.js manually from https://nodejs.org/
    pause
    exit /b 1
)

:node_done

REM Function to install Python
echo [Step 2/4] Check Python...
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo OK - Python found:
    python --version
    echo.
    goto :python_done
)

echo Python not found. Installing Python 3.13...
where winget >nul 2>&1
if %errorlevel% equ 0 (
    echo Using winget to install Python 3.13...
    winget install Python.Python.3.13 --accept-source-agreements --accept-package-agreements
    if %errorlevel% equ 0 (
        echo SUCCESS: Python 3.13 installed
        echo Please close this window and run the script again to continue.
        pause
        exit /b 0
    ) else (
        echo WARNING: winget installation failed. Please install manually from https://www.python.org/downloads/
        pause
        exit /b 1
    )
) else (
    echo WARNING: winget not available. Please install Python manually from https://www.python.org/downloads/
    pause
    exit /b 1
)

:python_done

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
    cd /d "%PROJECT_DIR%"
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
        cd /d "%PROJECT_DIR%"
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
echo OK - Frontend ready (Next.js 15.2.4)
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
echo Backend started (background)

echo [2/2] Starting Frontend (port 3000)...
cd /d "%FRONTEND_DIR%"
start /b npm run dev
cd /d "%PROJECT_DIR%"
timeout /t 5 /nobreak >nul
echo Frontend started (background)

echo.
echo ====================================
echo   Services Running
echo ====================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.

echo Opening browser in 2 seconds...
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo.
echo ====================================
echo   RUNNING - Press Ctrl+C to stop
echo ====================================
echo.
echo Services are running in background.
echo Close this window to stop all services.
echo.

REM Keep the window open
cmd /k