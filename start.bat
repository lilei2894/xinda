@echo off
chcp 65001 >nul
setlocal

echo ====================================
echo   信达 - 启动脚本
echo ====================================
echo.

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%xinda-backend"
set "FRONTEND_DIR=%PROJECT_DIR%xinda-frontend"

echo [Step 1/4] 检测 Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 错误: 未安装 Node.js
    echo.
    echo 请从以下地址下载并安装 Node.js 22 LTS:
    echo   https://nodejs.org/
    echo.
    echo 安装完成后，重新运行此脚本。
    echo.
    goto :end
)
echo OK - Node.js 版本:
node --version
echo.

echo [Step 2/4] 检测 Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
)
if %errorlevel% neq 0 (
    py --version >nul 2>&1
)
if %errorlevel% neq 0 (
    echo.
    echo 错误: 未安装 Python
    echo.
    echo 请从以下地址下载并安装 Python 3.13:
    echo   https://www.python.org/downloads/
    echo.
    echo 安装时请勾选 "Add Python to PATH" 选项！
    echo.
    echo 安装完成后，重新运行此脚本。
    echo.
    goto :end
)
echo OK - Python 版本:
python --version
echo.

echo [Step 3/4] 安装后端依赖...
cd /d "%BACKEND_DIR%"
if not exist "venv" (
    echo 创建 Python 虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo 错误: 创建虚拟环境失败
        echo 可能原因: Python 未正确安装或版本过低
        goto :end
    )
)

call venv\Scripts\activate.bat
echo 安装 Python 包（首次运行需要几分钟）...
pip install -q fastapi uvicorn python-multipart sqlalchemy pillow python-docx PyPDF2 PyMuPDF requests python-dotenv httpx
if %errorlevel% neq 0 (
    echo 错误: pip 安装失败
    echo 可能原因: 网络问题或 pip 版本过低
    goto :end
)

if not exist "uploads" mkdir uploads
if not exist "data" mkdir data
echo OK - 后端依赖安装完成
echo.

echo [Step 4/4] 安装前端依赖...
cd /d "%FRONTEND_DIR%"
if not exist "node_modules" (
    echo 安装 Node.js 包（首次运行需要几分钟）...
    npm install --silent
    if %errorlevel% neq 0 (
        echo 错误: npm 安装失败
        echo 可能原因: 网络问题或 npm 版本过低
        goto :end
    )
)
echo OK - 前端依赖安装完成
echo.

cd /d "%PROJECT_DIR%"
echo ====================================
echo   启动服务
echo ====================================
echo.

echo [1/2] 启动后端服务（端口 8000）...
cd /d "%BACKEND_DIR%"
call venv\Scripts\activate.bat
start /b python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
cd /d "%PROJECT_DIR%"
timeout /t 3 /nobreak >nul
echo 后端服务已启动

echo [2/2] 启动前端服务（端口 3000）...
cd /d "%FRONTEND_DIR%"
start /b npm run dev -- --webpack
cd /d "%PROJECT_DIR%"
timeout /t 5 /nobreak >nul
echo 前端服务已启动

echo.
echo ====================================
echo   服务运行中
echo ====================================
echo.
echo 前端地址: http://localhost:3000
echo 后端地址: http://localhost:8000
echo API文档:  http://localhost:8000/docs
echo.

echo 正在打开浏览器...
timeout /t 2 /nobreak >nul
start http://localhost:3000
echo 浏览器已打开
echo.

echo ====================================
echo   使用说明
echo ====================================
echo.
echo - 服务在后台运行
echo - 关闭此窗口可停止所有服务
echo - 首次启动需等待编译（1-2分钟）
echo.

:end
echo 按任意键退出...
pause >nul
