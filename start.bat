@echo off
setlocal enabledelayedexpansion

:: Check for administrator privileges
net session >nul 2>&1
if %errorlevel% equ 0 goto :admin_ok

:: Not running as admin - elevate
echo =========================================
echo   Administrator Privileges Required
echo =========================================
echo.
echo This script needs administrator privileges to install:
echo   - Node.js 22 LTS
echo   - Python 3.13
echo.
echo Requesting administrator privileges...
echo.

:: Try to elevate using PowerShell
powershell -Command "Start-Process '%~f0' -Verb RunAs"
exit /b

:admin_ok
echo ====================================
echo   Xinda Project Launcher
echo   (Running as Administrator)
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
    echo This may take a few minutes...
    echo Note: If winget fails, please install manually from https://nodejs.org/
    echo.
    winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements 2>nul
    
    if %errorlevel% equ 0 (
        echo.
        echo Adding Node.js to PATH...
        
        REM Get Node.js installation path
        set "NODE_PATH=%ProgramFiles%\nodejs"
        if exist "%NODE_PATH%" (
            REM Add to PATH for current session
            set "PATH=%NODE_PATH%;%PATH%"
            
            REM Add to user PATH permanently
            powershell -Command "[Environment]::SetEnvironmentVariable('PATH', [Environment]::GetEnvironmentVariable('PATH', 'User') + ';%NODE_PATH%', 'User')" 2>nul
            
            echo Node.js added to PATH successfully.
        )
        
        echo.
        echo ========================================
        echo   SUCCESS: Node.js 22 installed
        echo ========================================
        echo.
        echo IMPORTANT: You must restart this script for PATH to refresh.
        echo.
        echo Please:
        echo   1. Close this command window
        echo   2. Open a NEW command window
        echo   3. Run this script again
        echo.
        pause
        exit /b 0
    ) else (
        echo.
        echo ========================================
        echo   WARNING: winget installation failed
        echo ========================================
        echo.
        echo This is likely due to permission restrictions.
        echo.
        echo Solution - Install Node.js manually:
        echo   1. Download from: https://nodejs.org/
        echo   2. Run the installer as Administrator
        echo   3. Restart this script
        echo.
        pause
        exit /b 1
    )
) else (
    echo ========================================
    echo   winget not available
    echo ========================================
    echo.
    echo Solution - Install Node.js manually:
    echo   1. Download from: https://nodejs.org/
    echo   2. Run the installer
    echo   3. Restart this script
    echo.
    pause
    exit /b 1
)

:node_done

REM Function to install Python
echo [Step 2/4] Check Python...

REM First check if python command works (not just exists in PATH)
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo OK - Python found:
    python --version
    echo.
    goto :python_done
)

REM Try python3
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo OK - Python found:
    python3 --version
    echo.
    goto :python_done
)

REM Try py launcher
py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo OK - Python found (using py launcher):
    py --version
    echo.
    set "PYTHON_CMD=py"
    goto :python_done
)

REM Check if python is just a Microsoft Store shortcut
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo Found python command but it's not working properly.
    echo This is likely the Microsoft Store shortcut.
    echo.
) else (
    echo Python not found.
)

echo Python not found. Installing Python 3.13...
where winget >nul 2>&1
if %errorlevel% equ 0 (
    echo Using winget to install Python 3.13...
    echo This may take a few minutes...
    echo.
    
    REM Try the override first (auto-add to PATH)
    winget install Python.Python.3.13 --accept-source-agreements --accept-package-agreements --override "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0" 2>nul
    
    REM If that failed, try without override
    if %errorlevel% neq 0 (
        echo Retry with default settings...
        winget install Python.Python.3.13 --accept-source-agreements --accept-package-agreements 2>nul
    )
    
    if %errorlevel% equ 0 (
        echo.
        echo ========================================
        echo   Python 3.13 installed - configuring PATH
        echo ========================================
        echo.
        
        REM Find Python installation
        set "PYTHON_PATH="
        
        REM Try common installation paths
        if exist "%LOCALAPPDATA%\Programs\Python\Python313" (
            set "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python313"
        )
        if exist "%LOCALAPPDATA%\Programs\Python\Python312" (
            set "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python312"
        )
        if exist "%LOCALAPPDATA%\Programs\Python\Python311" (
            set "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python311"
        )
        if exist "%ProgramFiles%\Python313" (
            set "PYTHON_PATH=%ProgramFiles%\Python313"
        )
        
        if defined PYTHON_PATH (
            echo Found Python at: %PYTHON_PATH%
            echo Adding to PATH...
            
            REM Add to current session PATH
            set "PATH=%PYTHON_PATH%;%PYTHON_PATH%\Scripts;%PATH%"
            
            REM Add to system PATH permanently (requires admin)
            setx PATH "%PATH%;%PYTHON_PATH%;%PYTHON_PATH%\Scripts" >nul 2>&1
            
            REM Also try user PATH
            powershell -Command "[Environment]::SetEnvironmentVariable('PATH', [Environment]::GetEnvironmentVariable('PATH', 'User') + ';%PYTHON_PATH%;%PYTHON_PATH%\Scripts', 'User')" 2>nul
            
            echo PATH updated.
        ) else (
            echo Warning: Could not find Python installation path.
            echo Please check if Python was installed correctly.
        )
        
        echo.
        echo ========================================
        echo   SUCCESS: Python 3.13 installed
        echo ========================================
        echo.
        echo IMPORTANT:
        echo   - Python was installed but PATH changes may require a new terminal
        echo   - Please close this window and open a NEW command prompt
        echo   - Run this script again to continue
        echo.
        pause
        exit /b 0
    ) else (
        echo.
        echo ========================================
        echo   ERROR: Python installation failed
        echo ========================================
        echo.
        echo Please install Python manually:
        echo   1. Download from: https://www.python.org/downloads/
        echo   2. IMPORTANT: Check "Add Python to PATH" during installation
        echo   3. Run the installer as Administrator
        echo   4. Restart this script
        echo.
        pause
        exit /b 1
    )
) else (
    echo ========================================
    echo   winget not available
    echo ========================================
    echo.
    echo Please install Python manually:
    echo   1. Download from: https://www.python.org/downloads/
    echo   2. IMPORTANT: Check "Add Python to PATH" during installation
    echo   3. Run the installer
    echo   4. Restart this script
    echo.
    pause
    exit /b 1
)

:python_done

echo [Step 3/4] Backend dependencies...
echo Verifying Python installation...

REM Try multiple ways to verify Python
set "PYTHON_WORKS=0"

python --version >nul 2>&1
if %errorlevel% equ 0 set "PYTHON_WORKS=1"

if %PYTHON_WORKS% equ 0 (
    python3 --version >nul 2>&1
    if %errorlevel% equ 0 set "PYTHON_WORKS=1"
)

if %PYTHON_WORKS% equ 0 (
    py --version >nul 2>&1
    if %errorlevel% equ 0 set "PYTHON_WORKS=1"
)

if %PYTHON_WORKS% equ 0 (
    echo.
    echo ========================================
    echo   ERROR: Python not accessible
    echo ========================================
    echo.
    echo Python command not found. This may be because:
    echo   1. Python was not installed correctly
    echo   2. PATH was not set properly
    echo   3. The "python" shortcut points to Microsoft Store
    echo.
    echo Solution:
    echo   1. Close this command window
    echo   2. Open a NEW command window as Administrator
    echo   3. Run: where python
    echo   4. If shows Microsoft Store shortcut, disable it:
    echo      Settings > Apps > Advanced app settings > App execution aliases
    echo   5. Or manually add Python to PATH:
    echo      setx PATH "%%PATH%%;C:\Users\YOURNAME\AppData\Local\Programs\Python\Python313"
    echo   6. Then run this script again
    echo.
    pause
    exit /b 1
)

echo Python verified: OK
echo.

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
echo   Verifying Environment
echo ====================================
echo.

echo Final check: Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not accessible in PATH
    echo Please restart the script in a new command window.
    pause
    exit /b 1
)
python --version

echo.
echo Final check: Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not accessible in PATH
    echo Please restart the script in a new command window.
    pause
    exit /b 1
)
node --version

echo.
echo ====================================
echo   Environment Ready
echo ====================================
echo.
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