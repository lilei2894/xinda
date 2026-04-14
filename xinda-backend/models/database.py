from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from datetime import datetime, timezone, timedelta
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/xinda.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

SHANGHAI_TZ = timezone(timedelta(hours=8))

def shanghai_now():
    return datetime.now(SHANGHAI_TZ)

class ProcessingHistory(Base):
    __tablename__ = "processing_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    upload_time = Column(DateTime, default=shanghai_now)
    ocr_text = Column(Text, nullable=True)
    translated_text = Column(Text, nullable=True)
    status = Column(String, default="pending")
    model_endpoint = Column(String, nullable=True)
    total_pages = Column(String, nullable=True)
    content_title = Column(String, nullable=True)
    ocr_model_id = Column(String, nullable=True)
    translate_model_id = Column(String, nullable=True)
    doc_language = Column(String, nullable=True)
    ocr_paused = Column(String, default="false")
    trans_paused = Column(String, default="false")
    ocr_last_page = Column(String, default="0")

class Provider(Base):
    __tablename__ = "providers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)  # e.g., "ollama", "openai", "custom-ai"
    display_name = Column(String, nullable=False)  # e.g., "Ollama", "OpenAI"
    base_url = Column(String, nullable=False)  # e.g., "http://localhost:11434"
    api_key = Column(String, nullable=True)  # stored as plain text (existing pattern)
    is_active = Column(String, default="true")  # "true"/"false" as string for SQLite simplicity
    created_at = Column(DateTime, default=shanghai_now)
    
    models = relationship("ModelEntry", back_populates="provider", cascade="all, delete-orphan")

class ModelEntry(Base):
    __tablename__ = "model_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    model_id = Column(String, nullable=False)  # e.g., "gpt-4o", "qwen2.5-vl"
    display_name = Column(String, nullable=False)  # e.g., "GPT-4o", "Qwen 2.5 VL"
    model_type = Column(String, nullable=False)  # "ocr", "translate", or "both"
    is_default = Column(String, default="false")  # "true"/"false"
    is_active = Column(String, default="true")  # "true"/"false"
    
    provider = relationship("Provider", back_populates="models")

class AppConfig(Base):
    __tablename__ = "app_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, nullable=False, unique=True)
    value = Column(String, nullable=True)

class LanguagePrompt(Base):
    __tablename__ = "language_prompts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    language_code = Column(String, nullable=False, unique=True)  # e.g., "en", "zh", "ja"
    language_name = Column(String, nullable=False)  # e.g., "English", "中文", "日本語"
    ocr_prompt = Column(Text, nullable=True)  # OCR prompt template
    translate_prompt = Column(Text, nullable=True)  # Translation prompt template
    color = Column(String, nullable=True)  # Color for language tag, e.g., "#3B82F6"
    created_at = Column(DateTime, default=shanghai_now)
    updated_at = Column(DateTime, default=shanghai_now, onupdate=shanghai_now)

Base.metadata.create_all(bind=engine)

# Migration: add columns to tables if not exist
import sqlite3
try:
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_path[2:])
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(model_entries)")
    columns = [col[1] for col in cursor.fetchall()]
    if "is_active" not in columns:
        cursor.execute("ALTER TABLE model_entries ADD COLUMN is_active TEXT DEFAULT 'true'")
        conn.commit()
    cursor.execute("PRAGMA table_info(processing_history)")
    ph_columns = [col[1] for col in cursor.fetchall()]
    if "content_title" not in ph_columns:
        cursor.execute("ALTER TABLE processing_history ADD COLUMN content_title TEXT")
        conn.commit()
    if "ocr_model_id" not in ph_columns:
        cursor.execute("ALTER TABLE processing_history ADD COLUMN ocr_model_id TEXT")
        conn.commit()
    if "translate_model_id" not in ph_columns:
        cursor.execute("ALTER TABLE processing_history ADD COLUMN translate_model_id TEXT")
        conn.commit()
    if "doc_language" not in ph_columns:
        cursor.execute("ALTER TABLE processing_history ADD COLUMN doc_language TEXT")
        conn.commit()
    if "ocr_paused" not in ph_columns:
        cursor.execute("ALTER TABLE processing_history ADD COLUMN ocr_paused TEXT DEFAULT 'false'")
        conn.commit()
    if "trans_paused" not in ph_columns:
        cursor.execute("ALTER TABLE processing_history ADD COLUMN trans_paused TEXT DEFAULT 'false'")
        conn.commit()
    if "ocr_last_page" not in ph_columns:
        cursor.execute("ALTER TABLE processing_history ADD COLUMN ocr_last_page TEXT DEFAULT '0'")
        conn.commit()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.execute("PRAGMA wal_autocheckpoint=100")
    conn.commit()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='language_prompts'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE language_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language_code TEXT NOT NULL UNIQUE,
                language_name TEXT NOT NULL,
                ocr_prompt TEXT,
                translate_prompt TEXT,
                color TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
    else:
        cursor.execute("PRAGMA table_info(language_prompts)")
        lp_columns = [row[1] for row in cursor.fetchall()]
        if "color" not in lp_columns:
            cursor.execute("ALTER TABLE language_prompts ADD COLUMN color TEXT")
            conn.commit()
    
    ocr_template = """# Role
你是一名专业的文档OCR识别专家，擅长识别和处理历史档案文献中的{lang}文本。

# Task
识别图片中{lang}主体文档的全部文本内容，输出完整的识别结果。

# Format Requirements
1. **段落合并**：同一自然段落因排版宽度被切断的文字，必须合并为一行，中间不换行
2. **段落分隔**：段落之间用两个换行符（空一行）分隔
3. **标题处理**：标题和副标题独占一行，前后各空一行
4. **列表处理**：列表项、表格行各自独占一行

# OCR Principles
1. **主体识别**：仅识别图片中央的主体文档文本
2. **边缘忽略**：忽略以下边缘内容：
   - REEL编号、胶片编号
   - 机构水印、印章
   - 页眉、页脚
   - 扫描标记、档案编号
   - 边框外的文字
3. **输出纯净**：
   - 仅输出识别的{lang}文本
   - 不输出HTML/XML标签或格式标记
   - 不添加任何解释、说明、前缀、标注
   - 不重复同一段文字

# Output
直接输出识别的文本内容，无需任何附加说明。"""

    trans_template = """请将以下{lang}文本翻译成中文。

要求：
1. 直接输出翻译结果，不要任何解释或说明
2. 保持原文段落结构
3. 使用现代白话中文，不用文言文
4. 人名地名机构名用中文音译"""

    default_prompts = [
        ("jp", "日文", ocr_template.format(lang="日文"), trans_template.format(lang="日文"), "#D4A5A5"),
        ("en", "英文", ocr_template.format(lang="英文"), trans_template.format(lang="英文"), "#8FA3A6"),
        ("de", "德文", ocr_template.format(lang="德文"), trans_template.format(lang="德文"), "#A8C5B5"),
        ("fr", "法文", ocr_template.format(lang="法文"), trans_template.format(lang="法文"), "#B5A8C5"),
        ("ru", "俄文", ocr_template.format(lang="俄文"), trans_template.format(lang="俄文"), "#C5A8A8"),
        ("es", "西班牙文", ocr_template.format(lang="西班牙文"), trans_template.format(lang="西班牙文"), "#A8B5C5"),
    ]
    
    for code, name, ocr, trans, color in default_prompts:
        cursor.execute(
            "INSERT OR IGNORE INTO language_prompts (language_code, language_name, ocr_prompt, translate_prompt, color, created_at, updated_at) VALUES (?, ?, ?, ?, ?, datetime('now', '+8 hours'), datetime('now', '+8 hours'))",
            (code, name, ocr, trans, color)
        )
    
    cursor.execute("UPDATE language_prompts SET language_name = '日文' WHERE language_code = 'jp'")
    cursor.execute("UPDATE language_prompts SET language_name = '英文' WHERE language_code = 'en'")
    cursor.execute("UPDATE language_prompts SET language_name = '德文' WHERE language_code = 'de'")
    cursor.execute("UPDATE language_prompts SET language_name = '法文' WHERE language_code = 'fr'")
    cursor.execute("UPDATE language_prompts SET language_name = '俄文' WHERE language_code = 'ru'")
    cursor.execute("UPDATE language_prompts SET language_name = '西班牙文' WHERE language_code = 'es'")
    
    cursor.execute("UPDATE language_prompts SET color = '#D4A5A5' WHERE language_code = 'jp' AND (color IS NULL OR color = '')")
    cursor.execute("UPDATE language_prompts SET color = '#8FA3A6' WHERE language_code = 'en' AND (color IS NULL OR color = '')")
    cursor.execute("UPDATE language_prompts SET color = '#A8C5B5' WHERE language_code = 'de' AND (color IS NULL OR color = '')")
    cursor.execute("UPDATE language_prompts SET color = '#B5A8C5' WHERE language_code = 'fr' AND (color IS NULL OR color = '')")
    cursor.execute("UPDATE language_prompts SET color = '#C5A8A8' WHERE language_code = 'ru' AND (color IS NULL OR color = '')")
    cursor.execute("UPDATE language_prompts SET color = '#A8B5C5' WHERE language_code = 'es' AND (color IS NULL OR color = '')")
    
    cursor.execute("UPDATE language_prompts SET language_code = 'jp' WHERE language_code = 'ja'")
    cursor.execute("UPDATE processing_history SET doc_language = 'jp' WHERE doc_language = 'ja'")
    cursor.execute("UPDATE processing_history SET model_endpoint = 'jp' WHERE model_endpoint = 'ja'")
    
    cursor.execute("UPDATE language_prompts SET ocr_prompt = ?, translate_prompt = ? WHERE language_code = 'jp'", (ocr_template.format(lang="日文"), trans_template.format(lang="日文")))
    cursor.execute("UPDATE language_prompts SET ocr_prompt = ?, translate_prompt = ? WHERE language_code = 'en'", (ocr_template.format(lang="英文"), trans_template.format(lang="英文")))
    cursor.execute("UPDATE language_prompts SET ocr_prompt = ?, translate_prompt = ? WHERE language_code = 'de'", (ocr_template.format(lang="德文"), trans_template.format(lang="德文")))
    cursor.execute("UPDATE language_prompts SET ocr_prompt = ?, translate_prompt = ? WHERE language_code = 'fr'", (ocr_template.format(lang="法文"), trans_template.format(lang="法文")))
    cursor.execute("UPDATE language_prompts SET ocr_prompt = ?, translate_prompt = ? WHERE language_code = 'ru'", (ocr_template.format(lang="俄文"), trans_template.format(lang="俄文")))
    cursor.execute("UPDATE language_prompts SET ocr_prompt = ?, translate_prompt = ? WHERE language_code = 'es'", (ocr_template.format(lang="西班牙文"), trans_template.format(lang="西班牙文")))
    
    conn.commit()
    
    conn.close()
except Exception:
    pass

def seed_default_providers(db):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
