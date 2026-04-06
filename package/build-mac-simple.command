#!/bin/bash

# ============================================
# 信达 - Mac 极简打包方案
# ============================================

# 使用方法:
# 1. 在 Mac 终端运行: chmod +x build-mac-simple.command
# 2. 双击运行: ./build-mac-simple.command

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/dist"

echo "===================================="
echo "     信达 - Mac 打包"
echo "===================================="
echo ""

# 创建输出目录
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/xinda"

# 1. 复制后端源码
echo "[1/3] 复制后端..."
cp -r "$SCRIPT_DIR/xinda-backend" "$OUTPUT_DIR/xinda/"

# 2. 复制前端源码
echo "[2/3] 复制前端..."
cp -r "$SCRIPT_DIR/xinda-frontend" "$OUTPUT_DIR/xinda/"

# 3. 创建启动脚本（双击运行）
echo "[3/3] 创建启动脚本..."

cat > "$OUTPUT_DIR/xinda/启动.command" << 'SCRIPT'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "===================================="
echo "     信达 启动中..."
echo "===================================="

# 端口设置
read -p "前端端口 [3000]: " FE_PORT
FE_PORT=${FE_PORT:-3000}
read -p "后端端口 [8000]: " BE_PORT
BE_PORT=${BE_PORT:-8000}

echo ""
echo "前端: $FE_PORT"
echo "后端: $BE_PORT"
echo ""

# 创建目录
mkdir -p "$DIR/xinda-frontend/uploads"
mkdir -p "$DIR/xinda-backend/data"

# 安装后端依赖
echo "[1/2] 启动后端..."
cd "$DIR/xinda-backend"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
python3 main.py --port=$BE_PORT &
sleep 2

# 启动前端
echo "[2/2] 启动前端..."
cd "$DIR/xinda-frontend"
npm run dev &
sleep 3

echo ""
echo "===================================="
echo "     启动完成！"
echo "===================================="
echo "访问: http://localhost:$FE_PORT"
echo ""
echo "按回车键停止服务..."

read -p "" 
kill %1 %2 2>/dev/null
SCRIPT

chmod +x "$OUTPUT_DIR/xinda/启动.command"

# 创建说明
cat > "$OUTPUT_DIR/xinda/使用说明.txt" << 'EOF'
信达 - 外文文档处理工作台 (Mac版)

使用方法:
1. 打开终端，进入 xinda 目录
2. 安装依赖:
   - cd xinda-backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
   - cd ../xinda-frontend && npm install
3. 启动: ./启动.command

或双击启动.command（需在终端先运行一次安装依赖）

端口: 前端 3000, 后端 8000
EOF

# 打包
cd "$OUTPUT_DIR"
zip -r xinda-mac.zip xinda/

echo ""
echo "===================================="
echo "     打包完成！"
echo "===================================="
echo ""
echo "文件位置: $OUTPUT_DIR/xinda-mac.zip"
echo ""
echo "用户使用: 解压后运行 ./启动.command"
echo ""