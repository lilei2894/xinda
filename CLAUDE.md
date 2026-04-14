# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

xinda (外文档案文献处理工作台) is a web-based document OCR and translation tool for foreign language documents (Japanese, English, German, French, Russian, Spanish). It processes PDF/JPG files, performs OCR recognition, and translates content to Chinese.

## Commands

### Start the application
- **All services (Mac/Linux)**: `./start.sh`
- **All services (Windows)**: `start.bat`
- **Backend only**: `cd xinda-backend && source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- **Frontend only**: `cd xinda-frontend && npm run dev`

### Development
- **Install backend deps**: `cd xinda-backend && pip install -r requirements.txt`
- **Install frontend deps**: `cd xinda-frontend && npm install`
- **Lint frontend**: `cd xinda-frontend && npm run lint`
- **Backend API docs**: http://localhost:8000/docs (FastAPI auto-generated)

## Architecture

### Backend (FastAPI)
- **main.py**: FastAPI app entry point with CORS, router registration
- **routers/**: API endpoints organized by domain
  - `upload.py`: File upload and validation
  - `process.py`: Processing workflow orchestration
  - `result.py`: Result retrieval and streaming (SSE)
  - `history.py`: History record management
  - `providers.py`: AI provider/model CRUD operations
  - `prompts.py`: Language-specific prompt templates
  - `config.py`: App configuration
- **services/**: Business logic
  - `ocr_service.py`: Vision model calls, PDF-to-image conversion, hallucination detection
  - `translate_service.py`: Translation model calls, output cleaning
  - `export_service.py`: Word document generation (python-docx)
  - `stream_store.py`: SSE streaming state management
- **models/**: SQLAlchemy models and database schema
  - `database.py`: Tables: ProcessingHistory, Provider, ModelEntry, AppConfig, LanguagePrompt
  - SQLite database with WAL mode

### Frontend (Next.js 16 App Router)
- **src/app/**: Pages using Next.js App Router
  - `page.tsx`: Main upload interface
  - `history/`: History list page
  - `result/[id]/`: Document result viewer with image/text panels
  - `settings/`: Model provider configuration
  - `usage/`: Usage guide page
- **src/components/**: React components (FileUpload, HistoryList, ModelSettingsModal, PromptSettingsModal, ExportModal, etc.)
- **src/lib/api.ts**: Axios-based API client with all endpoint functions

### AI Integration
- Supports multiple providers: Ollama, OpenAI, DeepSeek, Alibaba, Google
- Provider API follows OpenAI-compatible `/v1/chat/completions` format
- Vision models for OCR, text models for translation
- Streaming support via SSE for real-time progress updates

## Key Patterns

### Processing Flow
1. Upload file → create ProcessingHistory record (status: pending)
2. Process endpoint triggers OCR page-by-page (via `ocr_service.py`)
3. Each page: PDF-to-image → base64 encode → vision model call → hallucination check
4. Translation follows OCR completion (via `translate_service.py`)
5. Results stored in database, accessible via result endpoint or SSE stream

### Language Prompts
- `LanguagePrompt` table stores OCR and translate prompts per language code
- Prompts fetched dynamically based on document language (jp, en, de, fr, ru, es)
- Auto-detection available via `detect_language()` in ocr_service.py

### Model Selection
- `Provider` + `ModelEntry` tables manage multiple AI providers
- Models have `model_type`: "ocr", "translate", or "both"
- Frontend sends `ocr_model_id` and `translate_model_id` with processing requests

## Important Notes

- Frontend API base URL: `NEXT_PUBLIC_API_URL` env var (defaults to `http://localhost:8000/api`)
- Backend uses Shanghai timezone (UTC+8) for timestamps
- PDF processing is page-by-page; recommend ≤50 pages per document (configurable via `MAX_PDF_PAGES`)
- macOS backend uses curl fallback for API calls due to Python SSL issues
- Database migrations handled inline in `database.py` with ALTER TABLE statements

## Environment Variables

### Backend
- `BACKEND_PORT`: Server port (default: 8000)
- `UPLOAD_DIR`: File upload directory (default: ./uploads)
- `MAX_FILE_SIZE`: Max upload size in bytes (default: 52428800 = 50MB)
- `MAX_PDF_PAGES`: Max PDF pages before warning (default: 500)
- `ALLOWED_ORIGINS`: CORS origins, comma-separated (default: "*" for local dev)
- `DATABASE_URL`: SQLite database path (default: sqlite:///./data/xinda.db)
- `OCR_TIMEOUT`: OCR API call timeout in seconds (default: 300)
- `OCR_DETECT_TIMEOUT`: Language detection timeout in seconds (default: 60)
- `OCR_MAX_RETRIES`: OCR retry count for hallucination detection (default: 2)
- `TRANSLATE_TIMEOUT`: Translation API call timeout in seconds (default: 300)
- `TRANSLATE_TITLE_TIMEOUT`: Title generation timeout in seconds (default: 60)
- `TRANSLATE_MAX_RETRIES`: Translation retry count (default: 2)

### Frontend
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000/api)
- `PORT`: Frontend server port (default: 3000)

## Testing

Run backend tests:
```bash
cd xinda-backend
pytest tests/ -v
```