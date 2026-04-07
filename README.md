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

### 3. 启动服务

```bash
# 使用启动脚本（同时启动前后端）
./start.sh
```

或手动启动：

```bash
# 后端
cd xinda-backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端（新终端）
cd xinda-frontend
npm run dev
```

前端：http://localhost:3000
后端 API 文档：http://localhost:8000/docs

### 4. 配置模型

首次使用需要在「模型设置」中添加 AI 模型供应商。支持 Ollama、OpenAI、阿里云、DeepSeek、Google 等。

详细使用说明请查看 [使用指南](xinda-frontend/public/usage.md)。

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