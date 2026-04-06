# Work Plan: 外文档案文献处理工作台（代号 xinda）

## 项目概览

**中文名称**: 外文档案文献处理工作台 · **代号**: xinda  
**项目类型**: Web 应用 Demo 原型  
**核心功能**: OCR 文本提取 + 日文翻译 + 图文对照 + Word 导出  
**技术栈**: Next.js 14 + FastAPI + SQLite + Ollama  
**交付目标**: 最小可用版本 (MVP)

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    用户浏览器 (Next.js 14)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 上传页面  │  │ 结果展示  │  │ 历史记录  │  │ 设置页面  │   │
│  │          │  │ (图文对照)│  │          │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                         ↕ HTTP API
┌─────────────────────────────────────────────────────────────┐
│                  后端服务 (FastAPI + Python)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ API Endpoints                                         │  │
│  │  • POST /api/upload          - 文件上传               │  │
│  │  • POST /api/process         - OCR + 翻译处理         │  │
│  │  • GET  /api/history         - 历史记录查询           │  │
│  │  • GET  /api/result/{id}     - 获取处理结果           │  │
│  │  • GET  /api/export/{id}     - Word 导出              │  │
│  │  • POST /api/config          - 配置模型端点           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Processing Pipeline                                   │  │
│  │  1. 文件验证 (PDF/JPG)                                 │  │
│  │  2. 图像预处理 (PDF → 图像转换)                         │  │
│  │  3. OCR 提取 (Ollama API 调用)                         │  │
│  │  4. 翻译处理 (Ollama API 调用)                         │  │
│  │  5. 结果存储 (SQLite)                                  │  │
│  │  6. Word 生成 (python-docx)                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         ↕ HTTP API
┌─────────────────────────────────────────────────────────────┐
│               Ollama 服务器 (172.25.249.29:30000)            │
│                模型: qwen3.5-uncensored-35B                  │
│              (视觉识别 + 多语言翻译能力)                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   数据存储 (SQLite)                          │
│  Table: processing_history                                  │
│   • id (主键)                                               │
│   • original_filename (原始文件名)                           │
│   • file_type (文件类型: pdf/jpg)                            │
│   • upload_time (上传时间)                                  │
│   • ocr_text (提取文本)                                     │
│   • translated_text (翻译文本)                              │
│   • status (处理状态)                                       │
│   • model_endpoint (模型端点)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 第一阶段：项目初始化 (预计 2-3 小时)

### 任务 1.1: 创建项目结构

**目标**: 搭建前后端项目骨架

**前端 (Next.js 14)**:
```bash
# 项目初始化
npx create-next-app@latest xinda-frontend
  - TypeScript: Yes
  - ESLint: Yes
  - Tailwind CSS: Yes
  - App Router: Yes
  - Src directory: Yes
```

**后端 (FastAPI)**:
```bash
# 项目结构
mkdir xinda-backend
cd xinda-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install fastapi uvicorn python-multipart sqlalchemy pillow python-docx PyPDF2
```

**验证标准**:
- [ ] 前端可启动 (`npm run dev` 显示 Welcome 页面)
- [ ] 后端可启动 (`uvicorn main:app --reload` 显示 API 文档)
- [ ] 前后端可互相访问 (CORS 配置正确)

**文件清单**:
```
xinda-frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx (首页/上传页)
│   │   ├── result/[id]/page.tsx (结果页)
│   │   ├── history/page.tsx (历史页)
│   │   └── settings/page.tsx (设置页)
│   ├── components/
│   │   ├── FileUpload.tsx
│   │   ├── ImageTextViewer.tsx
│   │   └── Navbar.tsx
│   └── lib/
│       └── api.ts (API 调用封装)
├── package.json
└── next.config.js

xinda-backend/
├── main.py (FastAPI 入口)
├── models/
│   ├── __init__.py
│   ├── database.py (SQLite 连接)
│   └── schemas.py (Pydantic 模型)
├── routers/
│   ├── __init__.py
│   ├── upload.py
│   ├── process.py
│   ├── history.py
│   └── config.py
├── services/
│   ├── __init__.py
│   ├── ocr_service.py
│   ├── translate_service.py
│   └── export_service.py
├── requirements.txt
└── .env
```

---

### 任务 1.2: 配置开发环境

**前端配置**:
- 配置 Tailwind CSS
- 配置 API 代理 (开发环境)
- 配置环境变量 (`NEXT_PUBLIC_API_URL`)

**后端配置**:
- 创建 SQLite 数据库
- 配置 CORS (允许前端域名)
- 配置环境变量 (Ollama 端点、文件存储路径)

**环境变量模板**:
```env
# Backend (.env)
OLLAMA_ENDPOINT=http://172.25.249.29:30000
DATABASE_URL=sqlite:///./data/xinda.db
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=20971520  # 20MB

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

**验证标准**:
- [ ] 前端环境变量可读取
- [ ] 后端环境变量可读取
- [ ] SQLite 数据库文件创建成功
- [ ] CORS 配置正确 (前端可调用后端 API)

---

## 第二阶段：核心功能实现 (预计 6-8 小时)

### 任务 2.1: 文件上传功能

**前端 (上传页面)**:
```typescript
// src/components/FileUpload.tsx
- 拖拽上传区域
- 文件类型验证 (PDF/JPG)
- 文件大小验证 (≤20MB)
- 上传进度条
- 上传成功/失败提示
```

**后端 (上传 API)**:
```python
# routers/upload.py
POST /api/upload
  - 接收 multipart/form-data
  - 验证文件类型 (application/pdf, image/jpeg)
  - 验证文件大小
  - 生成唯一文件名 (UUID)
  - 保存到 uploads 目录
  - 创建数据库记录 (status=pending)
  - 返回 record_id
```

**验证标准**:
- [ ] 可成功上传 PDF 文件
- [ ] 可成功上传 JPG 文件
- [ ] 拒绝非 PDF/JPG 文件 (返回 400 错误)
- [ ] 拒绝超过 20MB 文件 (返回 413 错误)
- [ ] 上传后可在 uploads 目录找到文件
- [ ] 数据库创建对应记录

---

### 任务 2.2: OCR 文本提取

**后端 (OCR 服务)**:
```python
# services/ocr_service.py
import requests
from PIL import Image
import fitz  # PyMuPDF

class OCRService:
    def pdf_to_images(self, pdf_path):
        """将 PDF 转换为图像列表"""
        doc = fitz.open(pdf_path)
        images = []
        for page in doc:
            pix = page.get_pixmap()
            images.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
        return images
    
    def call_ollama_vision(self, image_base64):
        """调用 Ollama API 进行 OCR"""
        response = requests.post(
            f"{OLLAMA_ENDPOINT}/api/generate",
            json={
                "model": "qwen3.5-uncensored-35B",
                "prompt": "请识别并提取这张图片中的所有日文文本，保持原有格式。",
                "images": [image_base64]
            }
        )
        return response.json()["response"]
    
    def extract_text(self, file_path, file_type):
        """主入口：提取文本"""
        if file_type == "pdf":
            images = self.pdf_to_images(file_path)
        else:
            images = [Image.open(file_path)]
        
        all_text = []
        for image in images:
            # 图像转 base64
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # 调用 OCR
            text = self.call_ollama_vision(img_base64)
            all_text.append(text)
        
        return "\n\n".join(all_text)
```

**后端 (处理 API)**:
```python
# routers/process.py
POST /api/process
  - 接收 record_id
  - 从数据库读取文件路径
  - 调用 ocr_service.extract_text()
  - 更新数据库 (ocr_text, status=ocr_done)
  - 返回 OCR 结果
```

**验证标准**:
- [ ] PDF 文件可成功提取文本
- [ ] JPG 文件可成功提取文本
- [ ] 多页 PDF 可提取所有页面文本
- [ ] Ollama API 调用成功
- [ ] 提取的文本保存到数据库
- [ ] 处理状态正确更新

---

### 任务 2.3: 文本翻译功能

**后端 (翻译服务)**:
```python
# services/translate_service.py
class TranslateService:
    def translate_japanese_to_chinese(self, japanese_text):
        """将日文翻译为中文"""
        response = requests.post(
            f"{OLLAMA_ENDPOINT}/api/generate",
            json={
                "model": "qwen3.5-uncensored-35B",
                "prompt": f"请将以下日文翻译成中文，保持原有格式：\n\n{japanese_text}"
            }
        )
        return response.json()["response"]
```

**后端 (处理 API 扩展)**:
```python
# routers/process.py (扩展)
POST /api/process
  - OCR 提取完成后
  - 调用 translate_service.translate_japanese_to_chinese()
  - 更新数据库 (translated_text, status=completed)
  - 返回完整结果
```

**验证标准**:
- [ ] 日文文本可成功翻译为中文
- [ ] 翻译结果保持原有格式 (段落、换行)
- [ ] Ollama API 调用成功
- [ ] 翻译结果保存到数据库
- [ ] 处理状态更新为 completed

---

### 任务 2.4: 图文对照展示

**前端 (结果页面)**:
```typescript
// src/app/result/[id]/page.tsx
- 左侧：原始图像显示 (PDF 显示第一页，JPG 显示原图)
- 右侧：上部分显示 OCR 文本，下部分显示翻译文本
- 同步滚动 (图像和文本对应)
- 文本可复制
- 下载按钮

// src/components/ImageTextViewer.tsx
- 图像缩放控制
- 文本区域高亮
- 布局调整 (左右/上下)
```

**API 端点**:
```python
GET /api/result/{id}
  - 返回：
    {
      "id": "uuid",
      "original_filename": "document.pdf",
      "file_type": "pdf",
      "image_urls": ["/api/image/{id}/1", "/api/image/{id}/2"],  # PDF 多页
      "ocr_text": "提取的日文文本",
      "translated_text": "翻译的中文文本",
      "upload_time": "2024-01-01 12:00:00",
      "status": "completed"
    }
```

**验证标准**:
- [ ] 图像正确显示
- [ ] OCR 文本正确显示
- [ ] 翻译文本正确显示
- [ ] 文本可复制
- [ ] 响应式布局 (桌面/移动端)

---

### 任务 2.5: Word 导出功能

**后端 (导出服务)**:
```python
# services/export_service.py
from docx import Document
from docx.shared import Inches, Pt

class ExportService:
    def export_to_word(self, record):
        """生成 Word 文档"""
        doc = Document()
        
        # 标题
        doc.add_heading(f'文档处理结果: {record.original_filename}', 0)
        
        # 基本信息
        doc.add_paragraph(f'处理时间: {record.upload_time}')
        doc.add_paragraph(f'文件类型: {record.file_type}')
        
        # OCR 文本
        doc.add_heading('提取的日文文本', level=1)
        doc.add_paragraph(record.ocr_text)
        
        # 翻译文本
        doc.add_heading('中文翻译', level=1)
        doc.add_paragraph(record.translated_text)
        
        # 原始图像（如果是 JPG）
        if record.file_type == 'jpg':
            doc.add_heading('原始图像', level=1)
            doc.add_picture(record.file_path, width=Inches(6))
        
        # 保存到内存流
        file_stream = BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        
        return file_stream
```

**API 端点**:
```python
GET /api/export/{id}
  - 调用 export_service.export_to_word()
  - 返回 Word 文件流
  - Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
  - Content-Disposition: attachment; filename=result_{id}.docx
```

**验证标准**:
- [ ] Word 文件成功生成
- [ ] 文件包含标题、OCR 文本、翻译文本
- [ ] JPG 文件包含原始图像
- [ ] 浏览器可成功下载

---

### 任务 2.6: 历史记录管理

**后端 (历史 API)**:
```python
# routers/history.py
GET /api/history
  - 查询参数：page, page_size
  - 返回所有处理记录列表
  - 支持分页

GET /api/history/{id}
  - 返回单个记录详情

DELETE /api/history/{id}
  - 删除记录及对应文件
```

**前端 (历史页面)**:
```typescript
// src/app/history/page.tsx
- 表格显示所有历史记录
  - 文件名
  - 文件类型
  - 上传时间
  - 处理状态
  - 操作（查看、导出、删除）
- 分页控制
- 搜索/筛选（可选，MVP 阶段可省略）
```

**验证标准**:
- [ ] 可查看所有历史记录
- [ ] 可分页浏览
- [ ] 可删除记录（包括文件）
- [ ] 可跳转到结果页面
- [ ] 可重新导出 Word

---

### 任务 2.7: 设置页面

**后端 (配置 API)**:
```python
# routers/config.py
POST /api/config
  - 接收：{"model_endpoint": "http://xxx:port"}
  - 保存到配置文件/数据库
  - 返回成功状态

GET /api/config
  - 返回当前配置
```

**前端 (设置页面)**:
```typescript
// src/app/settings/page.tsx
- 显示当前模型端点
- 输入框修改端点
- 测试连接按钮（调用 Ollama API 验证）
- 保存按钮
```

**验证标准**:
- [ ] 可显示当前配置
- [ ] 可修改模型端点
- [ ] 可测试连接（显示成功/失败）
- [ ] 配置持久化保存

---

## 第三阶段：测试与优化 (预计 2-3 小时)

### 任务 3.1: 手工测试核心路径

**测试用例**:
1. **上传 PDF 文件**
   - [ ] 上传单个 PDF 文件成功
   - [ ] 上传多页 PDF 文件，所有页面正确处理
   - [ ] 上传超大文件 (>20MB) 被拒绝

2. **上传 JPG 文件**
   - [ ] 上传 JPG 图片成功
   - [ ] 上传 PNG 文件被拒绝

3. **OCR 提取**
   - [ ] 可正确提取清晰文本的 PDF
   - [ ] 可正确提取清晰文本的 JPG
   - [ ] 可提取模糊文档的文本（准确率要求不高）

4. **翻译功能**
   - [ ] 可将日文翻译为中文
   - [ ] 翻译结果基本通顺（Demo 阶段可接受）

5. **图文对照**
   - [ ] 左图右文正确显示
   - [ ] 文本可复制
   - [ ] 滚动流畅

6. **Word 导出**
   - [ ] 可成功下载 Word 文件
   - [ ] Word 内容正确
   - [ ] 文件可正常打开

7. **历史记录**
   - [ ] 可查看所有历史记录
   - [ ] 可删除记录
   - [ ] 可重新查看结果

8. **设置页面**
   - [ ] 可修改模型端点
   - [ ] 测试连接成功/失败正确显示

---

### 任务 3.2: 错误处理优化

**关键错误场景**:
1. **文件上传失败**
   - 显示友好错误信息
   - 不崩溃

2. **Ollama API 调用失败**
   - 显示超时错误
   - 显示连接失败错误
   - 提供"重试"按钮

3. **文件不存在**
   - 404 错误页面
   - 返回友好提示

4. **数据库错误**
   - 捕获异常
   - 返回统一错误格式

**验证标准**:
- [ ] 所有错误场景有友好提示
- [ ] 不出现未捕获的异常
- [ ] 错误信息清晰易懂

---

### 任务 3.3: 性能优化（可选）

**优化项（如果时间允许）**:
1. **大文件处理**
   - 分块上传
   - 后台任务队列（Celery）

2. **响应速度**
   - 数据库索引
   - API 响应缓存

3. **用户体验**
   - 加载状态指示器
   - 处理进度实时更新

**验证标准**:
- [ ] 10 页 PDF 处理时间 < 30 秒
- [ ] 单页 JPG 处理时间 < 10 秒
- [ ] 前端响应流畅

---

## 第四阶段：文档与交付 (预计 1 小时)

### 任务 4.1: 创建 README.md

**内容**:
1. 项目简介
2. 功能特性
3. 技术栈
4. 安装步骤
5. 配置说明（Ollama 端点）
6. 运行方式
7. 使用指南
8. 已知问题
9. 未来规划

**验证标准**:
- [ ] README 清晰完整
- [ ] 新用户可按 README 独立运行

---

### 任务 4.2: 创建启动脚本

**前端启动脚本**:
```bash
# start-frontend.sh
#!/bin/bash
cd xinda-frontend
npm install
npm run dev
```

**后端启动脚本**:
```bash
# start-backend.sh
#!/bin/bash
cd xinda-backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**验证标准**:
- [ ] 启动脚本可成功运行
- [ ] 前后端同时启动成功

---

### 任务 4.3: 创建依赖清单

**前端 package.json**:
- Next.js 14
- TypeScript
- Tailwind CSS
- Axios (API 调用)

**后端 requirements.txt**:
- FastAPI
- Uvicorn
- SQLAlchemy
- python-multipart
- Pillow
- python-docx
- PyPDF2
- PyMuPDF (fitz)
- Requests

**验证标准**:
- [ ] 所有依赖可成功安装
- [ ] 版本明确指定

---

## 第五阶段：演示准备 (预计 30 分钟)

### 任务 5.1: 准备演示数据

**测试文件**:
- [ ] 准备 2-3 个日文 PDF 示例文档
- [ ] 准备 1-2 个日文 JPG 示例图片
- [ ] 确保文档内容清晰，易于 OCR

**演示脚本**:
1. 打开应用，显示上传页面
2. 上传一个 PDF 文件
3. 等待处理，显示图文对照结果
4. 点击"导出 Word"，下载文件
5. 打开历史记录页面
6. 打开设置页面，修改端点（演示）
7. 上传一个 JPG 文件，重复上述流程

---

### 任务 5.2: 演示环境检查

**检查清单**:
- [ ] Ollama 服务器可访问 (172.25.249.29:30000)
- [ ] 前端可正常启动
- [ ] 后端可正常启动
- [ ] 数据库可正常读写
- [ ] 所有核心路径可正常执行

**备选方案**:
- [ ] 如果 Ollama 服务器不可用，准备备用端点
- [ ] 如果远程演示，准备录屏视频

---

## 技术风险与应对

### 风险 1: Ollama API 调用超时

**应对**:
- 设置合理的超时时间（30 秒）
- 显示处理中的加载状态
- 提供重试按钮
- 考虑后台任务队列（MVP 阶段可省略）

### 风险 2: OCR 准确率不高

**应对**:
- 提示用户上传清晰文档
- 展示 Demo 时使用高质量文档
- 明确说明这是技术限制

### 风险 3: PDF 多页处理慢

**应对**:
- 显示处理进度
- 限制单次上传页数（例如 ≤10 页）
- 提示用户耐心等待

### 风险 4: 跨域问题

**应对**:
- 后端配置 CORS
- 允许前端域名访问
- 开发环境使用 Next.js API 代理

---

## 项目结构总览

```
xinda/
├── xinda-frontend/          # Next.js 14 前端
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx              # 上传页面
│   │   │   ├── result/[id]/page.tsx  # 结果页面
│   │   │   ├── history/page.tsx      # 历史页面
│   │   │   └── settings/page.tsx     # 设置页面
│   │   ├── components/
│   │   │   ├── FileUpload.tsx        # 文件上传组件
│   │   │   ├── ImageTextViewer.tsx   # 图文对照组件
│   │   │   └── Navbar.tsx            # 导航栏
│   │   └── lib/
│   │       └── api.ts                # API 调用封装
│   ├── package.json
│   └── next.config.js
│
├── xinda-backend/           # FastAPI 后端
│   ├── main.py                       # 入口文件
│   ├── models/
│   │   ├── database.py              # SQLite 连接
│   │   └── schemas.py               # Pydantic 模型
│   ├── routers/
│   │   ├── upload.py                # 上传路由
│   │   ├── process.py               # 处理路由
│   │   ├── history.py               # 历史路由
│   │   └── config.py                # 配置路由
│   ├── services/
│   │   ├── ocr_service.py           # OCR 服务
│   │   ├── translate_service.py     # 翻译服务
│   │   └── export_service.py        # 导出服务
│   ├── requirements.txt
│   └── .env
│
├── uploads/                   # 上传文件存储
├── data/                      # 数据库文件
│   └── xinda.db
│
├── README.md
├── start-frontend.sh
└── start-backend.sh
```

---

## 时间估算

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| 第一阶段 | 项目初始化 | 2-3 小时 |
| 第二阶段 | 核心功能实现 | 6-8 小时 |
| 第三阶段 | 测试与优化 | 2-3 小时 |
| 第四阶段 | 文档与交付 | 1 小时 |
| 第五阶段 | 演示准备 | 30 分钟 |
| **总计** | | **12-16 小时** |

**建议**：分 2-3 个工作日完成，每日 4-6 小时开发时间。

---

## 成功标准

### 必须完成（MVP）:
- [x] 用户可上传 PDF/JPG 文件
- [x] 系统可提取文本（OCR）
- [x] 系统可翻译日文为中文
- [x] 用户可查看图文对照结果
- [x] 用户可导出 Word 文档
- [x] 用户可查看历史记录
- [x] 用户可配置模型端点

### 加分项（时间允许）:
- [ ] 美观的 UI 设计
- [ ] 错误处理更完善
- [ ] 性能优化
- [ ] 批量上传功能

---

## 自动决策说明（MVP 缺省原则）

基于 MVP（最小可用版本）原则，以下问题采用合理默认值：

### ✅ 问题1：Ollama API 格式
**决策**：使用 OpenAI 兼容 API 格式（更通用）
- 端点：`POST {OLLAMA_ENDPOINT}/v1/chat/completions`
- 请求体：使用 messages 格式，content 包含文本和图像 URL
- 模型名称保持 `qwen3.5-uncensored-35B`
- 如需认证，从环境变量读取 API Key

**实现时可调整**：如果实际 API 不是 OpenAI 兼容格式，可在实施阶段调整为原生 Ollama API 格式。

### ✅ 问题2：PDF 处理库
**决策**：使用 **PyMuPDF (fitz)**
- 理由：PDF 转图像质量高，支持多页 PDF，OCR 场景最佳
- 安装：`pip install PyMuPDF`
- 备选：如果安装困难，可在实施阶段改用 PyPDF2

### ✅ 问题3：文件大小限制
**决策**：保留 **20MB 文件大小限制**
- 理由：避免处理超大文件导致超时和资源占用
- 实现：前端验证 + 后端验证双重保护
- 用户可在设置页面调整限制（未来功能）

---

## 注意事项

1. **Ollama 服务器稳定性**：确保演示时服务器可访问，准备备用方案
2. **文件大小限制**：避免上传过大文件导致处理超时
3. **Demo 数据准备**：提前准备高质量日文文档，确保 Demo 流畅
4. **用户体验**：即使是 Demo，也要保证基本流畅度
5. **错误提示**：提供清晰的错误信息，避免用户困惑

---

## 下一步行动

用户确认计划后，使用 `/start-work` 命令开始实施执行。