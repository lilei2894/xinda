# Draft: 项目打包方案分析

## 项目规模评估

### 前端 (Next.js 16)
- 依赖：react, react-dom, next, axios, pdfjs-dist, react-markdown, react-pdf, tailwindcss 等
- `node_modules/` 估计：**150-300MB**
- 构建后 `.next/` 估计：**20-50MB**
- Next.js standalone 输出估计：**30-60MB**

### 后端 (FastAPI + Python)
- 依赖：fastapi, uvicorn, PyMuPDF, Pillow, python-docx, sqlalchemy, PyPDF2 等
- `venv/` 虚拟环境估计：**100-200MB**
- 重依赖：PyMuPDF（含 MuPDF 二进制）、Pillow（含图像处理库）

### 总体估计
- 源码本身：~50KB（很小）
- 全部依赖（开发状态）：**250-500MB**
- 优化打包后估计：**150-300MB**

## 打包方案分析

### 方案 A：单文件 exe
- ❌ **不推荐**
- 单文件包含 Python 运行时 + Node.js 运行时 + 所有依赖
- 体积可能 500MB+
- 启动时需要解压到临时目录，启动慢
- 运行时文件操作复杂

### 方案 B：exe 启动器 + 依赖文件夹（推荐）
- ✅ **推荐**
- 绿色文件夹，用户直接拷贝运行
- 结构：
  ```
  xinda-app/
  ├── xinda.exe          # PyInstaller 打包的启动器
  ├── _internal/           # PyInstaller 自动生成的后端运行时
  ├── frontend/            # Next.js standalone 构建产物
  ├── node.exe             # Node.js 运行时（Windows 精简版，~30MB）
  ├── uploads/             # 用户上传目录
  ├── data/                # SQLite 数据库
  └── .env                 # 配置文件
  ```

### 方案 C：exe + 安装程序
- 可选增强
- 使用 Inno Setup / NSIS 创建安装程序
- 安装到 Program Files，创建桌面快捷方式

## 技术实现要点

### 1. 后端打包 (PyInstaller)
```bash
pyinstaller --name xinda-backend \
  --add-data "routers:routers" \
  --add-data "services:services" \
  --add-data "models:models" \
  --hidden-import pymupdf \
  --hidden-import PIL \
  main.py
```

### 2. 前端打包 (Next.js standalone)
```typescript
// next.config.ts
const nextConfig: NextConfig = {
  output: 'standalone',
};
```
输出在 `.next/standalone/`，只需 `node.exe` 即可运行。

### 3. 启动器 (launcher.py)
```python
import subprocess
import webbrowser
import time
import sys
import os

def main():
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    
    # 启动后端
    subprocess.Popen([sys.executable, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000'])
    
    # 启动前端
    subprocess.Popen(['node.exe', 'server.js'], cwd=os.path.join(base_dir, 'frontend'))
    
    # 等待服务就绪
    time.sleep(5)
    
    # 打开浏览器
    webbrowser.open('http://localhost:3000')
```

### 4. 最终打包脚本
将所有内容组装到一个文件夹，用户直接拷贝。

## 待确认问题
1. 目标平台：仅 Windows？还是也需要 macOS/Linux？
2. Node.js 运行时：嵌入（+30MB，零依赖）还是要求用户预装？
3. 安装程序：纯绿色文件夹还是需要 .exe 安装向导？
4. Ollama 依赖：Ollama 是外部服务，需要用户单独安装配置，还是在打包范围内？
