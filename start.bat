@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ====================================
echo   外文档案文献处理工作台 - 启动脚本
echo   (Windows 版本)
echo ====================================
echo.

REM 设置项目根目录
set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%xinda-backend"
set "FRONTEND_DIR=%PROJECT_DIR%xinda-frontend"

REM 检查 Node.js
echo [步骤 1/4] 检查 Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 错误: 未安装 Node.js
    echo 请从 https://nodejs.org/ 下载并安装 Node.js LTS 版本
    echo.
    pause
    exit /b 1
)
echo Node.js 已安装:
node --version
echo.

REM 检查 Python
echo [步骤 2/4] 检查 Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 错误: 未安装 Python
    echo 请从 https://www.python.org/downloads/ 下载并安装 Python 3.9+
    echo.
    pause
    exit /b 1
)
echo Python 已安装:
python --version
echo.

REM 安装后端依赖
echo [步骤 3/4] 安装后端依赖...
cd /d "%BACKEND_DIR%"
if not exist "venv" (
    echo 创建 Python 虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate.bat
echo 安装 Python 包（这可能需要几分钟）...
pip install -q fastapi "uvicorn[standard]" python-multipart sqlalchemy pillow python-docx PyPDF2 PyMuPDF requests python-dotenv httpx
if %errorlevel% neq 0 (
    echo 错误: Python 依赖安装失败
    cd /d "%PROJECT_DIR%"
    pause
    exit /b 1
)

if not exist "uploads" mkdir uploads
if not exist "data" mkdir data
echo 后端依赖已安装
echo.

REM 安装前端依赖
echo [步骤 4/4] 安装前端依赖...
cd /d "%FRONTEND_DIR%"
if not exist "node_modules" (
    echo 安装 Node.js 依赖（这可能需要几分钟）...
    npm install --silent
    if %errorlevel% neq 0 (
        echo 错误: Node.js 依赖安装失败
        cd /d "%PROJECT_DIR%"
        pause
        exit /b 1
    )
)

REM 确保使用稳定版本的 Next.js
echo 检查 Next.js 版本...
call npm list next | findstr "15.2.4" >nul 2>&1
if %errorlevel% neq 0 (
    echo 警告: Next.js 版本不是 15.2.4，正在安装稳定版本...
    call npm install next@15.2.4 eslint-config-next@15.2.4 --save
)
echo 前端依赖已安装（Next.js 15.2.4）
echo.

cd /d "%PROJECT_DIR%"
echo ====================================
echo   启动服务
echo ====================================
echo.

REM 启动后端服务
echo [1/2] 启动后端服务（端口 8000）...
start "信达后端" cmd /k "cd /d "%BACKEND_DIR%" && call venv\Scripts\activate.bat && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul

REM 启动前端服务
echo [2/2] 启动前端服务（端口 3000）...
start "信达前端" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"
timeout /t 5 /nobreak >nul

echo.
echo ====================================
echo   服务启动完成！
echo ====================================
echo.
echo 前端地址: http://localhost:3000
echo 后端地址: http://localhost:8000
echo API文档:  http://localhost:8000/docs
echo.

REM 自动打开浏览器
echo 正在打开浏览器...
timeout /t 2 /nobreak >nul
start http://localhost:3000
echo 浏览器已打开
echo.
echo ====================================
echo   使用说明
echo ====================================
echo.
echo - 程序已在两个独立窗口中运行
echo - 请勿关闭这两个命令行窗口
echo - 按 Ctrl+C 可停止服务
echo - 首次启动需要等待 1-2 分钟编译
echo.
pause