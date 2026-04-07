#!/bin/bash

# ================================================
# 外文档案文献处理工作台 - 启动脚本
# 支持 Windows (PowerShell) 和 macOS/Linux
# ================================================

detect_os() {
    case "$(uname -s)" in
        Linux*)     echo "linux";;
        Darwin*)    echo "macos";;
        CYGWIN*|MINGW*|MSYS*) echo "windows";;
        *)          echo "unknown";;
    esac
}

echo "=========================================="
echo "  外文档案文献处理工作台 - 启动脚本"
echo "=========================================="
echo ""

# 检查并释放占用端口的进程
kill_port() {
    local port=$1
    local pid=$(lsof -t -i:$port 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "⚠️  端口 $port 被占用 (PID: $pid)，正在终止..."
        kill -9 $pid 2>/dev/null
        sleep 1
        echo "✅ 端口 $port 已释放"
    fi
}

# 检查并安装 Python
install_python() {
    local os=$1
    
    if command -v python3 &> /dev/null; then
        echo "✅ Python 已安装: $(python3 --version)"
        return 0
    fi
    
    echo "❌ Python 未安装，正在尝试安装..."
    
    if [ "$os" = "macos" ]; then
        # 检查 Homebrew
        if command -v brew &> /dev/null; then
            echo "   使用 Homebrew 安装 Python..."
            brew install python
            echo "✅ Python 安装完成"
            return 0
        else
            echo "❌ Homebrew 未安装，请先安装 Homebrew: https://brew.sh"
            return 1
        fi
    elif [ "$os" = "windows" ]; then
        # Windows - 尝试使用 winget 或 choco
        if command -v winget &> /dev/null; then
            echo "   使用 winget 安装 Python..."
            winget install Python.Python.3.11 --accept-source-agreements --accept-package-agreements
            echo "✅ Python 安装完成"
            return 0
        elif command -v choco &> /dev/null; then
            echo "   使用 Chocolatey 安装 Python..."
            choco install python --yes
            echo "✅ Python 安装完成"
            return 0
        else
            echo "❌ 请手动安装 Python: https://www.python.org/downloads/"
            return 1
        fi
    else
        echo "❌ 无法自动安装 Python，请手动安装"
        return 1
    fi
}

# 检查并安装 Node.js
install_nodejs() {
    local os=$1
    
    if command -v node &> /dev/null; then
        echo "✅ Node.js 已安装: $(node --version)"
        return 0
    fi
    
    echo "❌ Node.js 未安装，正在尝试安装..."
    
    if [ "$os" = "macos" ]; then
        if command -v brew &> /dev/null; then
            echo "   使用 Homebrew 安装 Node.js..."
            brew install node
            echo "✅ Node.js 安装完成"
            return 0
        else
            echo "❌ Homebrew 未安装，请先安装 Homebrew: https://brew.sh"
            return 1
        fi
    elif [ "$os" = "windows" ]; then
        if command -v winget &> /dev/null; then
            echo "   使用 winget 安装 Node.js..."
            winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
            echo "✅ Node.js 安装完成"
            return 0
        elif command -v choco &> /dev/null; then
            echo "   使用 Chocolatey 安装 Node.js..."
            choco install nodejs-lts --yes
            echo "✅ Node.js 安装完成"
            return 0
        else
            echo "❌ 请手动安装 Node.js: https://nodejs.org/"
            return 1
        fi
    else
        echo "❌ 无法自动安装 Node.js，请手动安装"
        return 1
    fi
}

# 启动后端
start_backend() {
    echo ""
    echo "📦 启动后端服务..."
    cd xinda-backend
    
    # 检查 Python
    if ! install_python "$OS"; then
        cd ..
        exit 1
    fi
    
    # 查找 Python 解释器
    PYTHON_CMD=""
    for cmd in python3 python; do
        if command -v $cmd &> /dev/null; then
            PYTHON_CMD=$cmd
            break
        fi
    done
    
    if [ -z "$PYTHON_CMD" ]; then
        echo "❌ 未找到 Python 解释器"
        cd ..
        exit 1
    fi
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        echo "   创建Python虚拟环境..."
        $PYTHON_CMD -m venv venv
    fi
    
    # 使用 venv 内的解释器
    PY="./venv/bin/python"
    if [ ! -x "$PY" ]; then
        PY="./venv/Scripts/python.exe"
    fi
    
    if [ ! -x "$PY" ]; then
        echo "   重新创建虚拟环境..."
        rm -rf venv
        $PYTHON_CMD -m venv venv
    fi
    
    if [ ! -x "$PY" ]; then
        echo "❌ 虚拟环境创建失败，请删除 xinda-backend/venv 后重试"
        cd ..
        exit 1
    fi
    
    echo "   安装Python依赖（这可能需要几分钟）..."
    $PY -m pip install -q fastapi "uvicorn[standard]" python-multipart sqlalchemy pillow python-docx PyPDF2 PyMuPDF requests python-dotenv httpx || {
        echo "❌ pip 安装失败"
        cd ..
        exit 1
    }
    
    # 创建必要目录
    mkdir -p uploads data
    
    # 启动后端
    echo "   启动FastAPI服务在端口8000..."
    $PY -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"
}

# 启动前端
start_frontend() {
    echo ""
    echo "📦 启动前端服务..."
    cd xinda-frontend
    
    # 检查 Node.js
    if ! install_nodejs "$OS"; then
        cd ..
        exit 1
    fi
    
    # 安装依赖（如果需要）
    if [ ! -d "node_modules" ]; then
        echo "   安装Node.js依赖（这可能需要几分钟）..."
        npm install --silent
    fi
    
    # 启动前端
    echo "   启动Next.js服务在端口3000..."
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"
}

# 主流程
OS=$(detect_os)
echo "🔍 检测操作系统: $OS"

echo ""
echo "🔍 检查端口..."
kill_port 8000
kill_port 3000

echo ""
echo "🚀 启动服务..."
start_backend
start_frontend

echo ""
echo "=========================================="
echo "  启动完成！"
echo "=========================================="
echo ""
echo "🌐 前端地址: http://localhost:3000"
echo "🔧 后端地址: http://localhost:8000"
echo "📚 API文档:  http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 等待用户按Ctrl+C
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT
wait