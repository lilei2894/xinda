# 外文档案文献处理工作台

项目代号：**xinda**

一个基于 Web 的外文文档（支持日文、英文、德文、法文等）OCR 识别和翻译工具。

## ⚠️ 重要说明

**识别与翻译的质量取决于模型能力与提示词的设置。**

- 不同 AI 模型对不同语言的识别和翻译能力存在差异
- 提示词（Prompt）直接影响识别准确率和翻译质量
- 建议使用者根据实际处理效果，持续维护和优化提示词配置
- 可以针对不同语种（如日文、英文、德文、法文等）设置专属的提示词

## 功能特性

- ✅ 文件上传（支持 PDF 和 JPG，最大 20MB）
- ✅ 多语种 OCR 文本识别（自动检测或手动选择）
- ✅ 多语种翻译为中文（日文、英文、德文、法文等）
- ✅ 图文对照展示
- ✅ Word 文档导出（识别稿/翻译稿）
- ✅ 历史记录管理
- ✅ 模型端点配置（支持 Ollama、OpenAI、Custom AI 等）
- ✅ 可自定义提示词模板
- ✅ 暂停/继续功能（OCR、翻译可独立控制）
- ✅ 重新识别/翻译当前页
- ✅ 捐赠支持

## 技术栈

### 前端
- **Next.js 16** - React 框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式框架
- **Axios** - HTTP 客户端

### 后端
- **FastAPI** - Python Web 框架
- **SQLAlchemy** - ORM
- **SQLite** - 数据库
- **PyMuPDF** - PDF 处理
- **Pillow** - 图像处理
- **python-docx** - Word 文档生成
- **httpx** - HTTP 客户端

### AI 模型（需自行配置）

本系统支持 Ollama、OpenAI、阿里云、DeepSeek、Google 等多种 AI 模型供应商。推荐使用支持视觉能力的模型进行 OCR 识别。

详细模型选择建议请参考 [使用指南](xinda-frontend/public/usage.md) 中的模型配置说明。

## 项目结构

```
xinda/
├── xinda-frontend/          # Next.js 前端
│   ├── src/
│   │   ├── app/               # App Router 页面
│   │   ├── components/        # React 组件
│   │   └── lib/              # API 封装
│   ├── package.json
│   └── .env.local             # 前端环境变量
│
├── xinda-backend/           # FastAPI 后端
│   ├── models/                # 数据库模型
│   ├── routers/               # API 路由
│   ├── services/              # 业务服务
│   ├── main.py                # FastAPI 入口
│   ├── requirements.txt       # Python 依赖
│   └── .env                   # 后端环境变量
│
├── package/                   # Windows 打包脚本
├── uploads/                   # 上传文件存储
├── data/                      # 数据库文件
└── README.md                  # 项目文档
```

## 安装步骤

### 前置要求

- Node.js 18+
- Python 3.9+
- Ollama 服务器（或使用其他 AI API）

### 1. 安装前端依赖

```bash
cd xinda-frontend
npm install
```

### 2. 安装后端依赖

```bash
cd ../xinda-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 配置环境变量

#### 后端配置 (.env)

```env
# AI 模型端点配置
OLLAMA_ENDPOINT=http://localhost:11434
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# 数据库配置
DATABASE_URL=sqlite:///./data/xinda.db

# 上传配置
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=20971520
```

#### 前端配置 (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## 运行方式

### 快速启动

```bash
# 使用项目提供的启动脚本（同时启动前后端）
./start.sh
```

### 手动启动

#### 启动后端服务

```bash
cd xinda-backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端将在 http://localhost:8000 运行，API 文档：http://localhost:8000/docs

#### 启动前端服务

```bash
cd xinda-frontend
npm run dev
```

前端将在 http://localhost:3000 运行

## 使用指南

### 1. 配置模型供应商

首次使用前，需要在「模型设置」中添加 AI 模型供应商：
- 输入供应商名称、API 地址、API Key
- 添加可用模型列表
- 测试连接确保配置正确

### 2. 上传文件

- 打开浏览器访问 http://localhost:3000
- 拖拽或点击上传 PDF 或 JPG 文件

### 3. 选择模型与设置

- **识别模型**：选择用于 OCR 识别的视觉模型
- **翻译模型**：选择用于翻译的文本模型
- **语种选择**：建议选择具体语种（如「日文」）以获得更好效果，「自动检测」可能需要更长的检测时间

### 4. 配置提示词（重要！）

点击「提示词设置」进入配置页面，针对每种语言设置专属提示词：
- **OCR 识别提示词**：告诉模型如何识别文档中的文字
- **翻译提示词**：告诉模型如何翻译特定语言到中文
- **语言检测提示词**：用于自动检测文档语种

提示词配置直接影响最终识别和翻译质量，请根据实际效果调整。

### 5. 查看处理结果

- 文件上传后自动跳转到结果页面
- 左侧显示原始图像
- 中间显示识别出的外文文本
- 右侧显示中文翻译

### 6. 暂停/继续

- 处理过程中可暂停 OCR 或翻译任务
- 暂停不影响其他任务继续进行
- 暂停后更换模型，继续时使用新模型

### 7. 导出结果

- 在结果页面点击「导出」按钮
- 可选择导出识别稿（外文原文）或翻译稿（中文）
- 导出会生成 Word 文档

## API 文档

后端启动后，访问 http://localhost:8000/docs 查看 FastAPI 自动生成的 API 文档。

### 主要端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/upload | 上传文件 |
| POST | /api/upload/{id}/process | 开始处理文件 |
| GET | /api/result/{id} | 获取处理结果 |
| GET | /api/history | 获取历史记录 |
| DELETE | /api/history/{id} | 删除历史记录 |
| GET | /api/export/{id}/ocr | 导出识别稿 |
| GET | /api/export/{id}/translate | 导出翻译稿 |
| GET | /api/providers | 获取模型供应商列表 |
| POST | /api/prompts | 管理提示词配置 |
| POST | /api/result/{id}/pause-ocr | 暂停 OCR |
| POST | /api/result/{id}/resume-ocr | 继续 OCR |
| POST | /api/result/{id}/pause-translate | 暂停翻译 |
| POST | /api/result/{id}/resume-translate | 继续翻译 |

## 已知问题与限制

1. PDF 多页处理时间较长，建议单次上传不超过 20 页
2. OCR 准确率受以下因素影响：
   - 文档清晰度（模糊、污损会影响识别）
   - 字体类型（手写体识别效果较差）
   - 选择的模型能力
   - 提示词配置
3. 翻译质量取决于：
   - 选择的翻译模型能力
   - 翻译提示词的质量
   - 源语言的复杂程度

## 维护建议

1. **定期更新模型**：使用更强大的模型版本可显著提升效果
2. **优化提示词**：根据实际处理结果持续调整提示词
3. **分语种配置**：建议为每种常用语言设置专属提示词
4. **监控处理效果**：定期检查识别和翻译质量，及时调整

## Windows 打包分发

项目提供了 Windows 打包脚本，可将应用打包为便携版 EXE：

1. 将项目复制到 Windows 电脑
2. 双击运行 `package/build-windows.bat`
3. 等待打包完成，得到 `package/dist/xinda/` 文件夹
4. 将该文件夹压缩成分发包

用户解压后双击 `启动信达.bat` 即可使用。

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。