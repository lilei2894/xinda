#!/bin/bash

# 信达 - Mac 一键打包脚本

echo "===================================="
echo "     信达 - Mac 打包脚本"
echo "===================================="
echo ""

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$PROJECT_DIR/xinda-frontend"
BACKEND_DIR="$PROJECT_DIR/xinda-backend"
OUTPUT_DIR="$PROJECT_DIR/package/dist_mac"

# 检查环境
echo "[1/4] 检查环境..."
if ! command -v node &> /dev/null; then
    echo "错误: 未安装 Node.js"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "错误: 未安装 Python"
    exit 1
fi

echo "环境检查通过"
echo ""

# 安装前端依赖
echo "[2/4] 安装前端依赖..."
cd "$FRONTEND_DIR"
npm install
echo "前端依赖安装完成"
echo ""

# 安装后端依赖
echo "[3/4] 安装后端依赖..."
cd "$BACKEND_DIR"
if [ -d "venv" ]; then
    rm -rf venv
fi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
echo "后端依赖安装完成"
echo ""

# 创建输出目录
echo "[4/4] 准备输出目录..."
mkdir -p "$OUTPUT_DIR"

# 复制后端
cp -r "$BACKEND_DIR/dist/xinda" "$OUTPUT_DIR/" 2>/dev/null || (
    # 如果没有打包后端，复制源码
    cp -r "$BACKEND_DIR" "$OUTPUT_DIR/xinda-backend"
    mkdir -p "$OUTPUT_DIR/xinda-backend/venv"
    source venv/bin/activate
    pip freeze > "$OUTPUT_DIR/requirements.txt"
    deactivate
)

# 复制前端
cp -r "$FRONTEND_DIR" "$OUTPUT_DIR/xinda-frontend"

# 复制启动脚本
mkdir -p "$OUTPUT_DIR/start.command"

# 创建启动脚本（双击可运行）
cat > "$OUTPUT_DIR/启动信达.command" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

echo "===================================="
echo "     信达 - 启动中..."
echo "===================================="

# 设置端口
FRONTEND_PORT=3000
BACKEND_PORT=8000

echo "前端端口: $FRONTEND_PORT"
echo "后端端口: $BACKEND_PORT"
echo ""

# 创建必要目录
mkdir -p uploads data

# 启动后端
echo "[1/2] 启动后端服务..."
open -a Terminal "$PWD/xinda-backend/venv/bin/python" "$PWD/xinda-backend/main.py" --port=$BACKEND_PORT

sleep 3

# 启动前端
echo "[2/2] 启动前端服务..."
open -a Terminal "cd $PWD/xinda-frontend && npm run dev"

echo ""
echo "===================================="
echo "     启动完成！"
echo "===================================="
echo ""
echo "请在浏览器中访问: http://localhost:$FRONTEND_PORT"
echo ""

# 打开浏览器
open http://localhost:$FRONTEND_PORT

read -p "按回车键退出..."
EOF

chmod +x "$OUTPUT_DIR/启动信达.command"

# 创建使用说明
cat > "$OUTPUT_DIR/使用说明.txt" << 'EOF'
信达 - 外文文档处理工作台 (Mac版)

使用方法:
1. 双击 [启动信达.command] 运行程序
2. 程序将自动打开两个终端窗口（后端和前端）
3. 浏览器访问 http://localhost:3000

注意事项:
- 前端端口: 3000
- 后端端口: 8000
- 上传的文件保存在 uploads 目录
- 数据库文件保存在 data 目录
- 请勿关闭这两个终端窗口

如需停止服务，关闭终端窗口即可。
EOF

echo ""
echo "===================================="
echo "     打包完成！"
echo "===================================="
echo ""
echo "输出目录: $OUTPUT_DIR"
echo ""
echo "分发方式："
echo "1. 将整个文件夹压缩为 .zip"
echo "2. 用户解压后双击 [启动信达.command]"
echo ""
read -p "按回车键退出..."