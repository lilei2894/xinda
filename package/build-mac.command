#!/bin/bash

# 信达 - Mac 极简打包脚本
# 无需安装任何打包工具，直接复制所有依赖

echo "===================================="
echo "     信达 - Mac 一键打包"
echo "===================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/package/dist_mac"

# 1. 创建目录结构
echo "[1/3] 创建目录结构..."
mkdir -p "$OUTPUT_DIR/xinda-app"
cd "$OUTPUT_DIR/xinda-app"

# 2. 复制后端（包含虚拟环境）
echo "[2/3] 复制后端..."
cp -r "$SCRIPT_DIR/xinda-backend" "$OUTPUT_DIR/xinda-app/backend"

# 复制 Python 依赖
cd "$SCRIPT_DIR/xinda-backend"
python3 -m venv venv
source venv/bin/activate
pip freeze > "$OUTPUT_DIR/xinda-app/backend/requirements.txt"
deactivate

# 3. 复制前端
echo "[3/3] 复制前端..."
cp -r "$SCRIPT_DIR/xinda-frontend" "$OUTPUT_DIR/xinda-app/frontend"

# 4. 创建启动脚本（双击可运行）
cat > "$OUTPUT_DIR/xinda-app/启动.command" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

echo "===================================="
echo "     信达 启动中..."
echo "===================================="

FRONTEND_PORT=3000
BACKEND_PORT=8000

echo "前端端口: $FRONTEND_PORT"
echo "后端端口: $BACKEND_PORT"
echo ""

# 创建目录
mkdir -p frontend/uploads frontend/data backend/data 2>/dev/null

# 启动后端
cd "backend"
source venv/bin/activate
python3 main.py --port=$BACKEND_PORT &
BACKEND_PID=$!
deactivate

sleep 2

# 启动前端
cd "../frontend"
npm run dev &
FRONTEND_PID=$!

sleep 3

echo ""
echo "===================================="
echo "     启动完成！"
echo "===================================="
echo "请访问: http://localhost:$FRONTEND_PORT"
echo ""
echo "按回车键停止服务..."

read -p "" 

kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
echo "服务已停止"
EOF

chmod +x "$OUTPUT_DIR/xinda-app/启动.command"

# 创建说明文件
cat > "$OUTPUT_DIR/xinda-app/使用说明.txt" << 'EOF'
信达 - 外文文档处理工作台 (Mac版)

使用方法:
1. 右键点击 [启动.command] -> 打开 -> 允许运行
2. 或在终端运行: cd xinda-app && ./启动.command

首次运行:
- 需要安装 Node.js (如果没有)
- 需要安装 Python 3.9+ (如果没有)

端口:
- 前端: 3000
- 后端: 8000

停止:
- 按 Ctrl+C 或关闭终端窗口
EOF

# 压缩
echo ""
echo "正在创建压缩包..."
cd "$OUTPUT_DIR"
zip -r xinda-mac.zip xinda-app/

echo ""
echo "===================================="
echo "     打包完成！"
echo "===================================="
echo ""
echo "输出文件: $OUTPUT_DIR/xinda-mac.zip"
echo ""
echo "用户只需要："
echo "1. 解压 xinda-mac.zip"
echo "2. 双击 [启动.command]"
echo ""