from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import Optional
import os
import uuid
import threading
import time
import sys
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from models.database import get_db, ProcessingHistory, Provider
from services.ocr_service import OCRService
from services.translate_service import TranslateService
from services.stream_store import set_stream_data, append_stream_text, get_stream_page_text, clear_stream_data, set_stream_status
import fitz
from PIL import Image
from io import BytesIO

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")

def resolve_file_path(file_path: str) -> str:
    if os.path.isabs(file_path):
        return file_path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, file_path)
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "52428800"))
MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "500"))

upload_executor = ThreadPoolExecutor(max_workers=2)

os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = ["application/pdf", "image/jpeg", "image/jpg"]
ALLOWED_EXTENSIONS = [".pdf", ".jpg", ".jpeg"]

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and ensure safe characters."""
    # Remove path separators and null bytes
    filename = filename.replace("/", "_").replace("\\", "_").replace("\x00", "")
    # Keep only alphanumeric, dots, underscores, hyphens, and Chinese characters
    filename = re.sub(r'[^\w\u4e00-\u9fff.-]', '_', filename)
    # Prevent empty filename
    if not filename or filename.strip() == "":
        filename = "unnamed_file"
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    return filename


def process_file_background(record_id: str, file_path: str, file_type: str, ocr_model: str, translate_model: str, endpoint: str, language: str = "jp", ocr_api_key: str = None, translate_api_key: str = None):
    import fitz
    from PIL import Image
    from io import BytesIO
    from models.database import SessionLocal
    
    db = SessionLocal()
    try:
        record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
        if not record:
            return
        
        clear_stream_data(record_id)
        set_stream_status(record_id, "processing")
        record.status = "processing"
        
        db.commit()
        
        ocr_service = OCRService(model=ocr_model, endpoint=endpoint, language=language, api_key=ocr_api_key)
        translate_service = TranslateService(model=translate_model, endpoint=endpoint, language=language, api_key=translate_api_key)
        
        if file_type == "pdf":
            pdf_doc = fitz.open(file_path)
            record.total_pages = str(pdf_doc.page_count)
            total_pages = pdf_doc.page_count
            pdf_doc.close()
        else:
            total_pages = 1
        
        ocr_done = {}
        trans_done = {}
        ocr_page_complete = {}
        lock = threading.Lock()
        
        def ocr_worker():
            try:
                if file_type == "pdf":
                    doc = fitz.open(file_path)
                    for idx in range(doc.page_count):
                        page_num = idx + 1
                        
                        with lock:
                            prev_ocr_text = ocr_done.get(page_num - 1, '') if page_num > 1 else None
                        
                        if prev_ocr_text:
                            lines = prev_ocr_text.strip().split('\n')
                            non_empty_lines = [l.strip() for l in lines if l.strip()]
                            if non_empty_lines:
                                prev_ocr_text = '\n'.join(non_empty_lines[-3:])
                        
                        local_db = SessionLocal()
                        try:
                            local_record = local_db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
                            
                            current_ocr_model_full = local_record.ocr_model_id if local_record else None
                            current_ocr_model = ocr_model
                            current_ocr_api_key = ocr_api_key
                            current_endpoint = endpoint
                            
                            if current_ocr_model_full and '/' in current_ocr_model_full:
                                parts = current_ocr_model_full.split('/')
                                provider_id = int(parts[0])
                                provider = local_db.query(Provider).filter(Provider.id == provider_id).first()
                                if provider:
                                    current_ocr_model = parts[1]
                                    current_ocr_api_key = provider.api_key
                                    current_endpoint = provider.base_url
                            
                            current_ocr_service = OCRService(
                                model=current_ocr_model, 
                                endpoint=current_endpoint, 
                                language=language, 
                                api_key=current_ocr_api_key
                            )
                        finally:
                            local_db.close()
                        
                        try:
                            page_obj = doc[page_num - 1]
                            pix = page_obj.get_pixmap()
                            img = Image.open(BytesIO(pix.tobytes("png")))
                            
                            img_base64 = current_ocr_service.image_to_base64(img)
                            
                            def ocr_callback(chunk, full_text):
                                append_stream_text(record_id, 'ocr', chunk, page_num)
                            
                            text = current_ocr_service.call_vision_model_stream(img_base64, ocr_callback, prev_ocr_text)
                            with lock:
                                ocr_done[page_num] = text
                                ocr_page_complete[page_num] = True
                        except Exception as e:
                            with lock:
                                ocr_done[page_num] = f"Error: {str(e)}"
                                ocr_page_complete[page_num] = True
                    doc.close()
                else:
                    img = Image.open(file_path)
                    img_base64 = ocr_service.image_to_base64(img)
                    
                    def ocr_callback(chunk, full_text):
                        append_stream_text(record_id, 'ocr', chunk, 1)
                    
                    text = ocr_service.call_vision_model_stream(img_base64, ocr_callback, None)
                    with lock:
                        ocr_done[1] = text
                        ocr_page_complete[1] = True
            except Exception as e:
                for idx in range(1, total_pages + 1):
                    with lock:
                        if idx not in ocr_done:
                            ocr_done[idx] = f"Error: {str(e)}"
                            ocr_page_complete[idx] = True
        
        def translate_worker():
            while True:
                with lock:
                    pending_pages = []
                    for p in range(1, total_pages + 1):
                        if p not in trans_done and ocr_page_complete.get(p, False):
                            ocr_content = ocr_done.get(p, '')
                            if ocr_content and not ocr_content.strip().startswith('Error:') and ocr_content.strip():
                                pending_pages.append(p)
                    
                    ocr_complete = all(ocr_page_complete.get(p, False) for p in range(1, total_pages + 1))
                
                if not pending_pages and ocr_complete:
                    break
                
                if not pending_pages:
                    time.sleep(1)
                    continue
                
                for page_num in pending_pages:
                    with lock:
                        page_content = ocr_done.get(page_num, '')
                        prev_translated = trans_done.get(page_num - 1, '') if page_num > 1 else None
                    
                    prev_translated_text = None
                    if prev_translated:
                        lines = prev_translated.strip().split('\n')
                        non_empty_lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith('===')]
                        if non_empty_lines:
                            prev_translated_text = '\n'.join(non_empty_lines[-3:])
                    
                    local_db = SessionLocal()
                    try:
                        local_record = local_db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
                        
                        current_trans_model_full = local_record.translate_model_id if local_record else None
                        current_trans_model = translate_model
                        current_trans_api_key = translate_api_key
                        current_endpoint = endpoint
                        
                        if current_trans_model_full and '/' in current_trans_model_full:
                            parts = current_trans_model_full.split('/')
                            provider_id = int(parts[0])
                            provider = local_db.query(Provider).filter(Provider.id == provider_id).first()
                            if provider:
                                current_trans_model = parts[1]
                                current_trans_api_key = provider.api_key
                                current_endpoint = provider.base_url
                        
                        current_trans_service = TranslateService(
                            model=current_trans_model, 
                            endpoint=current_endpoint, 
                            language=language, 
                            api_key=current_trans_api_key
                        )
                    finally:
                        local_db.close()
                    
                    if page_content.strip() and not page_content.strip().startswith('Error:'):
                        try:
                            def trans_callback(chunk, full_text):
                                append_stream_text(record_id, 'trans', chunk, page_num)
                                with lock:
                                    trans_done[page_num] = full_text
                            
                            translated = current_trans_service.translate_to_chinese_stream(page_content, trans_callback, prev_translated_text)
                        except Exception as e:
                            translated = f"Error: {str(e)}"
                    else:
                        translated = page_content
                    
                    with lock:
                        trans_done[page_num] = translated
                    
                    with lock:
                        new_trans_full = []
                        for p in range(1, total_pages + 1):
                            content = trans_done.get(p, '')
                            new_trans_full.append(f"=== Page {p} ===\n{content}")
                        record.translated_text = "\n\n".join(new_trans_full)
                    db.commit()
                    
                    time.sleep(0.5)
        
        ocr_thread = threading.Thread(target=ocr_worker)
        trans_thread = threading.Thread(target=translate_worker)
        
        title_generated = False
        title_generate_threshold = 3 if total_pages > 3 else total_pages
        
        def try_generate_title():
            nonlocal title_generated
            if title_generated or record.content_title:
                return
            
            try:
                current_ocr_text = record.ocr_text or ""
                title = translate_service.generate_title(current_ocr_text, use_translated=False)
                if not title:
                    title = translate_service.generate_title_from_ocr_fallback(current_ocr_text)
                if title:
                    record.content_title = title
                    db.commit()
                    title_generated = True
            except Exception:
                pass
        
        ocr_thread.start()
        trans_thread.start()
        
        while ocr_thread.is_alive():
            time.sleep(2)
            with lock:
                new_ocr_full = []
                for p in range(1, total_pages + 1):
                    content = ocr_done.get(p, '')
                    new_ocr_full.append(f"=== Page {p} ===\n{content}")
                record.ocr_text = "\n\n".join(new_ocr_full)
            db.commit()
            
            completed_ocr = len([p for p in ocr_done if ocr_done.get(p, '').strip() and not ocr_done.get(p, '').strip().startswith('Error:')])
            if completed_ocr >= title_generate_threshold and not title_generated:
                try_generate_title()
        
        ocr_thread.join()
        trans_thread.join()
        
        with lock:
            new_ocr_full = []
            for p in range(1, total_pages + 1):
                content = ocr_done.get(p, '')
                new_ocr_full.append(f"=== Page {p} ===\n{content}")
            record.ocr_text = "\n\n".join(new_ocr_full)
            db.commit()
        
        if not title_generated and not record.content_title:
            try:
                current_ocr_text = record.ocr_text or ""
                title = translate_service.generate_title(current_ocr_text, use_translated=False)
                if not title:
                    title = translate_service.generate_title_from_ocr_fallback(current_ocr_text)
                if title:
                    record.content_title = title
                    db.commit()
            except Exception:
                pass
        
        with lock:
            new_trans_full = []
            for p in range(1, total_pages + 1):
                content = trans_done.get(p, '')
                new_trans_full.append(f"=== Page {p} ===\n{content}")
            full_translated_text = "\n\n".join(new_trans_full)
            record.translated_text = full_translated_text
            db.commit()
        
        # Check if all pages are complete before marking as completed
        ocr_pages_count = len([p for p in range(1, total_pages + 1) if ocr_done.get(p, '').strip() and not ocr_done.get(p, '').strip().startswith('Error:')])
        trans_pages_count = len([p for p in range(1, total_pages + 1) if trans_done.get(p, '').strip() and not trans_done.get(p, '').strip().startswith('Error:')])
        
        if ocr_pages_count >= total_pages and trans_pages_count >= total_pages:
            record.status = "completed"
            set_stream_status(record_id, "completed")
        else:
            record.status = "processing"
        db.commit()
    except Exception:
        record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
        if record:
            record.status = "failed"
            set_stream_status(record_id, "failed")
            db.commit()
    finally:
        db.close()


@router.post("", response_model=dict)
@router.post("/", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate content type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Only PDF and JPG files are allowed"
        )

    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '{file_ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File size ({file_size / (1024 * 1024):.1f}MB) exceeds limit of {max_mb:.0f}MB"
        )

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="File is empty"
        )

    # Sanitize filename
    safe_filename = sanitize_filename(file.filename)

    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    saved_filename = f"{file_id}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    file_type = "pdf" if file.content_type == "application/pdf" else "jpg"

    # Check PDF page count and validate
    total_pages = None
    if file_type == "pdf":
        import fitz
        try:
            pdf_doc = fitz.open(file_path)
            total_pages = pdf_doc.page_count
            pdf_doc.close()

            if total_pages > MAX_PDF_PAGES:
                # Return warning but still accept the file
                pass  # Frontend should handle this based on total_pages value
            if total_pages == 0:
                raise HTTPException(
                    status_code=400,
                    detail="PDF file has no pages"
                )
        except Exception as e:
            if "PDF" in str(e) or "page" in str(e).lower():
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid PDF file: {str(e)}"
                )

    record = ProcessingHistory(
        id=file_id,
        original_filename=safe_filename,
        file_type=file_type,
        file_path=file_path,
        total_pages=str(total_pages) if total_pages else None,
        status="pending"
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    response = {
        "id": record.id,
        "original_filename": record.original_filename,
        "file_type": record.file_type,
        "total_pages": record.total_pages,
        "status": record.status,
        "upload_time": record.upload_time.isoformat()
    }

    # Add warning for large PDFs
    if total_pages and total_pages > MAX_PDF_PAGES:
        response["warning"] = f"PDF has {total_pages} pages. Recommended maximum is {MAX_PDF_PAGES} pages for optimal performance."

    return response


@router.post("/{file_id}/process", response_model=dict)
async def process_file(
    file_id: str,
    ocr_model: str = None,
    translate_model: str = None,
    endpoint: str = None,
    language: str = "auto",
    db: Session = Depends(get_db),
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if record.status != "pending":
        raise HTTPException(status_code=400, detail=f"File cannot be processed (status: {record.status})")
    
    if not ocr_model or not translate_model or not endpoint:
        raise HTTPException(status_code=400, detail="Missing model configuration")
    
    def parse_model_id(model_id: str):
        if model_id and '/' in model_id:
            parts = model_id.split('/')
            return int(parts[0]), parts[1]
        return None, model_id
    
    ocr_provider_id, ocr_model_name = parse_model_id(ocr_model)
    translate_provider_id, translate_model_name = parse_model_id(translate_model)
    
    ocr_api_key = None
    translate_api_key = None
    
    if ocr_provider_id:
        ocr_provider = db.query(Provider).filter(Provider.id == ocr_provider_id).first()
        if ocr_provider:
            ocr_api_key = ocr_provider.api_key
    
    if translate_provider_id:
        translate_provider = db.query(Provider).filter(Provider.id == translate_provider_id).first()
        if translate_provider:
            translate_api_key = translate_provider.api_key
    
    record.ocr_model_id = ocr_model
    record.translate_model_id = translate_model
    record.doc_language = language
    
    # 如果是自动检测，在主线程中检测语言
    detected_language = None
    if language == "auto":
        print(f"[LANG-DEBUG] API: Starting auto-detect with model={ocr_model_name}")
        try:
            ocr_service_temp = OCRService(model=ocr_model_name, endpoint=endpoint, api_key=ocr_api_key)
            if record.file_type == "pdf":
                doc = fitz.open(resolve_file_path(record.file_path))
                page_obj = doc[0]
                pix = page_obj.get_pixmap()
                img = Image.open(BytesIO(pix.tobytes("png")))
                doc.close()
            else:
                img = Image.open(resolve_file_path(record.file_path))
            img_base64 = ocr_service_temp.image_to_base64(img)
            detected_language = ocr_service_temp.detect_language(img_base64)
            print(f"[LANG-DEBUG] API: Detect SUCCESS: {detected_language}")
            language = detected_language
            record.model_endpoint = detected_language
            record.doc_language = "auto"
        except Exception as e:
            print(f"[LANG-DEBUG] API: Detect FAILED: {e}")
            import traceback
            traceback.print_exc()
            record.status = "language_detection_failed"
            db.commit()
            return {
                "id": record.id,
                "status": "language_detection_failed",
                "message": "自动检测语言失败，请手动选择语种",
                "require_language_selection": True
            }
    
    db.commit()
    
    upload_executor.submit(
        process_file_background,
        file_id,
        record.file_path,
        record.file_type,
        ocr_model_name,
        translate_model_name,
        endpoint,
        language,
        ocr_api_key,
        translate_api_key,
    )
    
    record.status = "processing"
    db.commit()
    
    return {
        "id": record.id,
        "status": record.status,
        "message": "Processing started"
    }
