#!/bin/bash
# 信达打包脚本 - Mac/Linux 版本
# 用于准备前端文件和依赖列表

echo "=== 信达打包准备脚本 ==="
echo ""

# 检查环境
echo "[1/4] 检查环境..."
if ! command -v npm &> /dev/null; then
    echo "错误: 未找到 npm，请安装 Node.js"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

echo "环境检查完成"
echo ""

# 构建前端
echo "[2/4] 构建前端..."
cd ../xinda-frontend
npm run build

if [ $? -ne 0 ]; then
    echo "错误: 前端构建失败"
    exit 1
fi

echo "前端构建完成"
echo ""

# 复制前端到后端
echo "[3/4] 复制前端文件..."
cd ../xinda-backend
rm -rf frontend_build
mkdir -p frontend_build
cp -r ../xinda-frontend/out/* frontend_build/

echo "前端文件已复制到 frontend_build"
echo ""

# 创建依赖列表
echo "[4/4] 生成依赖列表..."
pip freeze > package-requirements.txt

echo "依赖列表已保存到 package-requirements.txt"
echo ""

echo "=== 准备完成 ==="
echo ""
echo "下一步："
echo "1. 将项目复制到 Windows 电脑"
echo "2. 在 Windows 上运行: pyinstaller --onedir --name xinda --add-data \"frontend_build;frontend\" main.py"
echo "3. 或者运行 Windows 版本的打包脚本"