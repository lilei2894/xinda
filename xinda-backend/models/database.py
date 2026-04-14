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
    
    cursor.execute("SELECT COUNT(*) FROM language_prompts")
    if cursor.fetchone()[0] == 0:
        default_en_ocr = """Please identify the main document content in this image.

【Paragraph Merging Rules - Most Important, Must Follow Strictly】
- Text from the same natural paragraph that was cut due to layout width must be merged into one line, without any line breaks in between
- Only insert a line break when the content is clearly a new paragraph (e.g., indented start, heading, subtitle)
- Separate paragraphs with two line breaks (\\n\\n)
- Headings and subtitles must be on their own lines, with one blank line before and after
- List items, table rows, etc. must each be on their own line

【Content Requirements】
- Only identify the main document text in the center of the image, ignore peripheral content
- Ignore: REEL numbers, institutional watermarks, headers/footers, scan marks, archive numbers, text outside borders
- Output only the identified text, nothing else
- Do not output HTML tags, XML tags, or any markup
- Do not add any explanations, notes, or prefixes
- Never repeat the same paragraph multiple times"""

        default_en_trans = """You are a professional English-to-Chinese translator. Your sole responsibility is to translate English text into modern Chinese written language.

Rules:
1. Output must be 100% Chinese translation results, absolutely no English words or phrases
2. Do not retain original English text or fragments
3. Do not use classical Chinese or semi-classical expressions
4. Must use modern Chinese written language (similar to news reports, academic papers)
5. Proper nouns (names, places, institutions) should be transliterated into Chinese characters
6. Strictly maintain the original paragraph structure, never merge multiple paragraphs into one
7. Absolutely do not output any explanations, notes, prefixes, suffixes, headings, or markers
8. If there is content that cannot be translated, explain it in Chinese"""

        default_ja_ocr = """请识别这张图片中的日文主体文档内容。

【段落合并规则 - 最重要，必须严格遵守】
- 图片中因排版宽度而被切断的同一自然段的文字，必须合并为一行，中间不要有任何换行
- 只有当内容明显是新段落（如缩进开头、标题、副标题）时才换行
- 段落之间必须用两个换行符（\\n\\n）分隔
- 标题、副标题必须独占一行，前后各空一行
- 列表项、表格行等必须各自独占一行

【内容要求】
- 仅识别图片中央的主体文档文本，忽略边缘的附加内容
- 忽略：REEL编号、机构水印、页眉页脚、扫描标记、档案编号、边框外的文字
- 仅输出识别出的日文文本，不要任何其他内容
- 不要输出HTML标签、XML标签或任何 markup
- 不要添加任何解释、说明或前缀
- 绝不可重复同一段文字多次"""

        default_ja_trans = """你是一名专业日中翻译员。你的唯一职责是将日文翻译成现代中文白话书面语。

规则：
1. 输出必须100%为中文翻译结果，绝不可包含任何日文假名（平假名、片假名）
2. 不得保留日文原文或日文片段
3. 不得使用文言文、古文或半文半白的表达
4. 必须使用现代中文白话书面语（类似新闻报道、学术论文的语体）
5. 专有名词（人名、地名、机构名）音译为中文汉字
6. 严格保持原文段落结构，绝不可将多个段落合并为一段
7. 绝对不要输出任何解释、说明、前缀、后缀、标题、标记
8. 如果原文中有无法翻译的内容，用中文说明即可，不可保留日文"""

        default_prompts = [
            ("en", "英文", default_en_ocr, default_en_trans, "#8FA3A6"),
            ("jp", "日文", default_ja_ocr, default_ja_trans, "#D4A5A5"),
        ]
        for code, name, ocr, trans, color in default_prompts:
            cursor.execute(
                "INSERT OR IGNORE INTO language_prompts (language_code, language_name, ocr_prompt, translate_prompt, color, created_at, updated_at) VALUES (?, ?, ?, ?, ?, datetime('now', '+8 hours'), datetime('now', '+8 hours'))",
                (code, name, ocr, trans, color)
            )
        conn.commit()
    else:
        cursor.execute("UPDATE language_prompts SET language_name = '英文' WHERE language_code = 'en'")
        cursor.execute("UPDATE language_prompts SET language_name = '日文' WHERE language_code = 'jp'")
        cursor.execute("UPDATE language_prompts SET color = '#8FA3A6' WHERE language_code = 'en' AND (color IS NULL OR color = '')")
        cursor.execute("UPDATE language_prompts SET color = '#D4A5A5' WHERE language_code = 'jp' AND (color IS NULL OR color = '')")
        
        cursor.execute("UPDATE language_prompts SET language_code = 'jp' WHERE language_code = 'ja'")
        cursor.execute("UPDATE processing_history SET doc_language = 'jp' WHERE doc_language = 'ja'")
        cursor.execute("UPDATE processing_history SET model_endpoint = 'jp' WHERE model_endpoint = 'ja'")
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
