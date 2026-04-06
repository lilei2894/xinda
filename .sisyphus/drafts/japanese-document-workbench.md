# Draft: 外文档案文献处理工作台（代号 xinda）

## Requirements (confirmed)
- **核心功能**: OCR + 翻译日文档案，图文对照展示
- **输入格式**: PDF 或 JPG 图像
- **AI 集成**: 支持多种大语言模型，用户可配置 API-key
- **默认模型**: 一个默认模型硬编码
- **历史记录**: 记录处理历史
- **导出功能**: 支持 Word 文档导出
- **目标**: 创建 Demo 原型给用户展示

## Technical Decisions
- **应用形式**: Web 应用（浏览器访问，易演示）
- **默认模型**: Ollama 本地模型（离线运行，隐私性好）
- **历史存储**: SQLite 本地数据库（轻量级，无需额外服务）
- **API-key 配置**: 运行时输入（界面设置页面，保存到本地配置）
- **前端框架**: Next.js 14（全栈能力，开发体验优秀）
- **后端语言**: Python (FastAPI)（AI 生态丰富）
- **Ollama 配置**: 远程服务器部署，地址 `172.25.249.29:30000`，模型 `qwen3.5-uncensored-35B`
- **核心功能**: OCR 文本提取 + 翻译功能 + 图文对照展示 + Word 导出
- **测试策略**: 无自动化测试，手工测试核心路径
- **交付范围**: 最小可用版本（MVP），核心功能 + 简单 UI
- **页面结构**: 上传页面 + 处理结果展示页 + 历史记录页 + 设置页面
- **部署方式**: 本地开发环境运行

## Architecture Design
```
Frontend (Next.js 14) ←→ Backend API (FastAPI) ←→ Ollama Server (172.25.249.29:30000)
                 ↓                              ↓
            SQLite DB                    File uploads processing
```

## Scope Boundaries
- **INCLUDE**: 
  - OCR 文本提取（PDF/JPG）
  - 日文翻译（调用 Ollama）
  - 图文对照展示
  - Word 文档导出
  - 历史记录管理
  - 模型配置（API 地址设置）
- **EXCLUDE (Demo阶段)**:
  - 自动化测试
  - 精美 UI 设计（仅简单可用）
  - 完善的错误处理
  - 性能优化
  - Batch 批量处理
  - 用户认证系统
  - 文件大小验证（先忽略）
  - 文件大小限制验证