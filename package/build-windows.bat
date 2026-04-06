@echo off
setlocal enabledelayedexpansion

echo ====================================
echo     信达 - 一键打包脚本 (Windows)
echo ====================================
echo.

set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%xinda-backend"
set "FRONTEND_DIR=%PROJECT_DIR%xinda-frontend"
set "OUTPUT_DIR=%PROJECT_DIR%dist"

echo [步骤 1/6] 检查环境...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未安装 Node.js
    pause
    exit /b 1
)

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未安装 Python
    pause
    exit /b 1
)

where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装 PyInstaller...
    pip install pyinstaller
)
echo 环境检查通过
echo.

echo [步骤 2/6] 安装前端依赖...
cd /d "%FRONTEND_DIR%"
call npm install
if %errorlevel% neq 0 (
    echo 错误: 前端依赖安装失败
    pause
    exit /b 1
)
echo 前端依赖安装完成
echo.

echo [步骤 3/6] 安装后端依赖...
cd /d "%BACKEND_DIR%"
if exist "venv" rmdir /s /q "venv"
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
pip install pyinstaller
call deactivate.bat
echo 后端依赖安装完成
echo.

echo [步骤 4/6] 打包后端为可执行文件...
cd /d "%BACKEND_DIR%"
if exist "uploads_temp" rmdir /s /q "uploads_temp"
if exist "data_temp" rmdir /s /q "data_temp"
mkdir uploads_temp
mkdir data_temp
call venv\Scripts\activate.bat
pyinstaller --onedir --name xinda --add-data "uploads_temp;uploads" --add-data "data_temp;data" main.py
call deactivate.bat
echo 后端打包完成
echo.

echo [步骤 5/6] 准备输出目录...
if not exist "%OUTPUT_DIR%\xinda" mkdir "%OUTPUT_DIR%\xinda"

xcopy /e /i /y "%BACKEND_DIR%\dist\xinda\*" "%OUTPUT_DIR%\xinda\"

echo 复制前端运行环境...
if not exist "%OUTPUT_DIR%\xinda\xinda-frontend" mkdir "%OUTPUT_DIR%\xinda\xinda-frontend"
xcopy /e /i /y "%FRONTEND_DIR%\package.json" "%OUTPUT_DIR%\xinda\xinda-frontend\"
xcopy /e /i /y "%FRONTEND_DIR%\package-lock.json" "%OUTPUT_DIR%\xinda\xinda-frontend\" 2>nul
xcopy /e /i /y "%FRONTEND_DIR%\node_modules" "%OUTPUT_DIR%\xinda\xinda-frontend\node_modules\"
xcopy /e /i /y "%FRONTEND_DIR%\next.config.ts" "%OUTPUT_DIR%\xinda\xinda-frontend\"
xcopy /e /i /y "%FRONTEND_DIR%\tsconfig.json" "%OUTPUT_DIR%\xinda\xinda-frontend\" 2>nul
xcopy /e /i /y "%FRONTEND_DIR%\src" "%OUTPUT_DIR%\xinda\xinda-frontend\src\"
xcopy /e /i /y "%FRONTEND_DIR%\public" "%OUTPUT_DIR%\xinda\xinda-frontend\public\" 2>nul

echo [步骤 6/6] 创建启动脚本...
(
echo @echo off
echo title 信达 - 外文文档处理工作台
echo.
echo set /p "FRONTEND_PORT=请输入前端端口（默认 3000）: "
echo if not defined FRONTEND_PORT set FRONTEND_PORT=3000
echo set /p "BACKEND_PORT=请输入后端端口（默认 8000）: "
echo if not defined BACKEND_PORT set BACKEND_PORT=8000
echo.
echo cd /d "%%~dp0"
echo if not exist "uploads" mkdir uploads
echo if not exist "data" mkdir data
echo.
echo echo [1/2] 启动后端服务（端口 %%BACKEND_PORT%%）...
echo start "信达后端" cmd /k "cd /d %%~dp0 && xinda.exe --port %%BACKEND_PORT%%"
echo timeout /t 3 /nobreak ^>nul
echo.
echo echo [2/2] 启动前端服务（端口 %%FRONTEND_PORT%%）...
echo start "信达前端" cmd /k "cd %%~dp0xinda-frontend && node node_modules\next\dist\bin\next start -p %%FRONTEND_PORT%%"
echo timeout /t 5 /nobreak ^>nul
echo.
echo start http://localhost:%%FRONTEND_PORT%%
echo.
echo ====================================
echo     启动完成！
echo ====================================
echo.
echo 浏览器访问: http://localhost:%%FRONTEND_PORT%%
echo 后端API: http://localhost:%%BACKEND_PORT%%
echo.
echo 注意：请勿关闭这两个命令行窗口
echo.
pause
) > "%OUTPUT_DIR%\xinda\启动信达.bat"

(
echo 信达 - 外文文档处理工作台
echo.
echo 使用方法:
echo   1. 双击 [启动信达.bat]
echo   2. 输入前端端口（默认 3000）
echo   3. 输入后端端口（默认 8000）
echo   4. 程序自动启动并打开浏览器
echo.
echo 首次使用请在 [模型设置] 中配置 AI 服务 API
echo.
echo 如需停止服务，关闭命令行窗口即可
) > "%OUTPUT_DIR%\xinda\使用说明.txt"

echo 创建完成
echo.

if exist "%BACKEND_DIR%\dist" rmdir /s /q "%BACKEND_DIR%\dist"
if exist "%BACKEND_DIR%\build" rmdir /s /q "%BACKEND_DIR%\build"
if exist "%BACKEND_DIR%\*.spec" del "%BACKEND_DIR%\*.spec" 2>nul
if exist "%BACKEND_DIR%\venv" rmdir /s /q "%BACKEND_DIR%\venv"
if exist "%BACKEND_DIR%\uploads_temp" rmdir /s /q "%BACKEND_DIR%\uploads_temp"
if exist "%BACKEND_DIR%\data_temp" rmdir /s /q "%BACKEND_DIR%\data_temp"

echo.
echo ====================================
echo     打包完成!
echo ====================================
echo.
echo 输出目录: %OUTPUT_DIR%\xinda\
echo 启动方式: 双击 [启动信达.bat]
echo.
pause