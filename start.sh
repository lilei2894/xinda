#!/bin/bash

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

# 启动后端
start_backend() {
    echo "📦 启动后端服务..."
    cd xinda-backend
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        echo "   创建Python虚拟环境..."
        python3 -m venv venv
    fi
    
    # 使用 venv 内的解释器（避免系统无 pip/uvicorn 命令、或未正确激活环境）
    PY="./venv/bin/python"
    if [ ! -x "$PY" ]; then
        echo "❌ 未找到 $PY，请删除 xinda-backend/venv 后重试"
        cd ..
        exit 1
    fi

    echo "   安装Python依赖（这可能需要几分钟）..."
    "$PY" -m pip install -q fastapi "uvicorn[standard]" python-multipart sqlalchemy pillow python-docx PyPDF2 PyMuPDF requests python-dotenv || {
        echo "❌ pip 安装失败"
        cd ..
        exit 1
    }

    # 创建必要目录
    mkdir -p uploads data

    # 启动后端
    echo "   启动FastAPI服务在端口8000..."
    "$PY" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"
}

# 启动前端
start_frontend() {
    echo ""
    echo "📦 启动前端服务..."
    cd xinda-frontend
    
    # 安装依赖（如果需要）
    if [ ! -d "node_modules" ]; then
        echo "   安装Node.js依赖..."
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
echo "📄 测试PDF文件位置: jacar_beijing_results/"
echo "   - 共有 $(ls jacar_beijing_results/*.pdf 2>/dev/null | wc -l) 个PDF文件"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 等待用户按Ctrl+C
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT
wait
