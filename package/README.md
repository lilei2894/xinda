# 信达打包说明

## 快速开始

### 步骤 1：准备环境

在 **Windows 电脑**上需要安装：
- **Node.js 18+**（从 https://nodejs.org 下载 LTS 版本）
- **Python 3.9+**（从 https://www.python.org 下载，勾选 "Add to PATH"）

### 步骤 2：获取项目

将整个 `xinda` 项目文件夹复制到 Windows 电脑。

### 步骤 3：运行打包脚本

1. 进入项目目录 `xinda\package\`
2. 双击运行 `build-windows.bat`

脚本会自动执行：
- 安装前端依赖并构建
- 打包 Python 后端为可执行文件
- 创建启动脚本

### 步骤 4：获取打包结果

打包完成后，结果在：
```
xinda\package\dist\xinda\
├── xinda.exe              ← Python 后端程序
├── xinda-frontend/        ← Next.js 前端源码
│   ├── node_modules/     ← 前端依赖
│   ├── .next/            ← 前端构建产物
│   └── src/
├── uploads/               ← 上传目录（运行时创建）
├── data/                  ← 数据库目录（运行时创建）
├── 启动信达.bat          ← 双击启动
└── 使用说明.txt
```

### 步骤 5：分发

将 `dist\xinda` 文件夹压缩成 zip，发给用户即可。

用户解压后双击 `启动信达.bat`，程序会自动启动前端和后端服务。

---

## 使用流程

用户使用流程：
1. 下载并解压 `xinda.zip`
2. 双击 `启动信达.bat`
3. 程序自动启动两个服务：
   - 前端：http://localhost:3000
   - 后端：http://localhost:8000
4. 自动打开浏览器访问 http://localhost:3000

---

## 注意事项

1. **端口占用**：确保 3000 和 8000 端口未被占用
2. **首次配置**：首次使用需在 [模型设置] 中配置 AI 服务 API
3. **停止服务**：关闭命令行窗口即可停止服务

---

## 目录结构

```
xinda/
├── xinda-frontend/     # Next.js 前端源码
├── xinda-backend/     # FastAPI 后端源码
├── package/           # 打包脚本
│   ├── build-windows.bat   # Windows 打包脚本（双击运行）
│   └── README.md          # 本说明
└── README.md          # 项目说明
```

---

## 技术方案

- **后端打包**：PyInstaller --onedir（单目录打包）
- **前端**：Next.js 开发模式（运行时编译）
- **优点**：无需构建前端静态文件，打包更简单
- **缺点**：首次启动需要等待 Node.js 编译

---

## 常见问题

### Q: 启动很慢怎么办？
A: 首次启动需要编译 Next.js，等待 1-2 分钟，之后会很快。

### Q: 端口被占用？
A: 关闭其他占用 3000/8000 端口的程序，或手动修改启动脚本中的端口。

### Q: 杀毒软件拦截？
A: 将 xinda 文件夹添加到杀毒软件白名单。

---

如有问题，请检查：
1. Node.js 和 Python 是否正确安装
2. 端口 3000 和 8000 是否被占用
3. 杀毒软件是否拦截了 exe 文件