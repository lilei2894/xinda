from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from fastapi import Depends
from pydantic import BaseModel
from typing import Optional
from models.database import get_db, ProcessingHistory, Provider
from services.ocr_service import OCRService
from services.translate_service import TranslateService
from routers.upload import process_file_background
import os
import re
import fitz
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

router = APIRouter()
ocr_executor = ThreadPoolExecutor(max_workers=2)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")

ocr_service = OCRService()
translate_service = TranslateService()


def resolve_file_path(file_path: str) -> str:
    if os.path.isabs(file_path):
        return file_path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, file_path)


@router.get("/{record_id}")
async def get_result(
    record_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    image_urls = []
    if record.file_type == "pdf":
        pass
    else:
        image_urls.append(f"/api/file/{record.id}")
    
    return {
        "id": record.id,
        "original_filename": record.original_filename,
        "file_type": record.file_type,
        "total_pages": record.total_pages,
        "image_urls": image_urls,
        "ocr_text": record.ocr_text,
        "translated_text": record.translated_text,
        "upload_time": record.upload_time.isoformat(),
        "status": record.status,
        "model_endpoint": record.model_endpoint,
        "content_title": record.content_title,
        "ocr_model_id": record.ocr_model_id,
        "translate_model_id": record.translate_model_id,
        "doc_language": record.doc_language
    }


@router.get("/file/{record_id}")
async def get_file(
    record_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    resolved_path = resolve_file_path(record.file_path)
    
    if not os.path.exists(resolved_path):
        raise HTTPException(status_code=404, detail=f"File not found: {resolved_path}")
    
    content_type = "application/pdf" if record.file_type == "pdf" else "image/jpeg"
    return FileResponse(resolved_path, media_type=content_type, filename=record.original_filename)


class ResetRequest(BaseModel):
    ocr_model_id: Optional[str] = None
    translate_model_id: Optional[str] = None
    endpoint: Optional[str] = None
    doc_language: Optional[str] = "auto"


@router.post("/{record_id}/reset")
async def reset_processing(
    record_id: str,
    body: ResetRequest = Body(default=None),
    db: Session = Depends(get_db),
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    record.ocr_text = None
    record.translated_text = None
    record.status = "processing"
    
    ocr_model_full = body.ocr_model_id if body and body.ocr_model_id else record.ocr_model_id
    trans_model_full = body.translate_model_id if body and body.translate_model_id else record.translate_model_id
    endpoint = body.endpoint if body and body.endpoint else ""
    language = body.doc_language if body and body.doc_language else (record.doc_language or "auto")
    
    ocr_api_key = None
    translate_api_key = None
    ocr_model = ocr_model_full
    trans_model = trans_model_full
    
    if ocr_model_full and '/' in ocr_model_full:
        parts = ocr_model_full.split('/')
        provider_id = int(parts[0])
        provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if provider:
            ocr_api_key = provider.api_key
        ocr_model = parts[1]
    
    if trans_model_full and '/' in trans_model_full:
        parts = trans_model_full.split('/')
        provider_id = int(parts[0])
        provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if provider:
            translate_api_key = provider.api_key
        trans_model = parts[1]
    
    record.ocr_model_id = body.ocr_model_id if body and body.ocr_model_id else record.ocr_model_id
    record.translate_model_id = body.translate_model_id if body and body.translate_model_id else record.translate_model_id
    record.doc_language = language
    db.commit()
    
    ocr_executor.submit(
        process_file_background,
        record_id,
        record.file_path,
        record.file_type,
        ocr_model,
        trans_model,
        endpoint,
        language,
        ocr_api_key,
        translate_api_key,
    )
    
    return {"message": "Processing reset and restarted"}


class ReprocessRequest(BaseModel):
    ocr_model_id: Optional[str] = None
    endpoint: Optional[str] = None
    doc_language: Optional[str] = None


class ReprocessTransRequest(BaseModel):
    translate_model_id: Optional[str] = None
    endpoint: Optional[str] = None


class ContinueRequest(BaseModel):
    ocr_model_id: Optional[str] = None
    translate_model_id: Optional[str] = None
    endpoint: Optional[str] = None
    doc_language: Optional[str] = None


@router.post("/{record_id}/reprocess-ocr")
async def reprocess_ocr(
    record_id: str,
    page: int,
    body: ReprocessRequest = Body(default=None),
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    ocr_endpoint = body.endpoint if body and body.endpoint else None
    ocr_model_full = body.ocr_model_id if body and body.ocr_model_id else None
    doc_lang = body.doc_language if body and body.doc_language else "ja"
    
    ocr_api_key = None
    ocr_model = ocr_model_full
    
    if ocr_model_full and '/' in ocr_model_full:
        parts = ocr_model_full.split('/')
        provider_id = int(parts[0])
        provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if provider:
            ocr_api_key = provider.api_key
        ocr_model = parts[1]
    
    ocr_executor.submit(
        _reprocess_ocr_background,
        record_id, page, ocr_endpoint, ocr_model, doc_lang, ocr_api_key
    )
    
    return {"message": "OCR reprocessing started in background"}


def _reprocess_ocr_background(record_id: str, page: int, ocr_endpoint: str, ocr_model: str, doc_lang: str, ocr_api_key: str = None):
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
        if not record:
            return
        
        current_ocr_service = OCRService(endpoint=ocr_endpoint, model=ocr_model, language=doc_lang, api_key=ocr_api_key) if ocr_endpoint or ocr_model else ocr_service
        current_trans_service = TranslateService(endpoint=ocr_endpoint, model=ocr_model, api_key=ocr_api_key) if ocr_endpoint or ocr_model else translate_service
        
        resolved_path = resolve_file_path(record.file_path)
        if record.file_type == "pdf":
            doc = fitz.open(resolved_path)
            if page > doc.page_count:
                doc.close()
                return
            page_obj = doc[page - 1]
            pix = page_obj.get_pixmap()
            img = Image.open(BytesIO(pix.tobytes("png")))
            doc.close()
        else:
            img = Image.open(resolved_path)
        
        img_base64 = current_ocr_service.image_to_base64(img)
        new_ocr_text = current_ocr_service.call_vision_model(img_base64)
        
        ocr_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.ocr_text or '')
        ocr_dict = {int(pnum): content for pnum, content in ocr_pages}
        ocr_dict[page] = new_ocr_text
        
        max_page = max(ocr_dict.keys()) if ocr_dict else page
        new_ocr_full = []
        for p in range(1, max_page + 1):
            content = ocr_dict.get(p, '')
            new_ocr_full.append(f"=== Page {p} ===\n{content}")
        record.ocr_text = "\n\n".join(new_ocr_full)
        db.commit()
        
        new_translated_text = current_trans_service.translate_to_chinese(new_ocr_text)
        trans_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.translated_text or '')
        trans_dict = {int(pnum): content for pnum, content in trans_pages}
        trans_dict[page] = new_translated_text
        
        new_trans_full = []
        for p in range(1, max_page + 1):
            content = trans_dict.get(p, '')
            new_trans_full.append(f"=== Page {p} ===\n{content}")
        record.translated_text = "\n\n".join(new_trans_full)
        
        db.commit()
    except Exception:
        pass
    finally:
        db.close()


@router.post("/{record_id}/reprocess-translate")
async def reprocess_translate(
    record_id: str,
    page: int,
    body: ReprocessTransRequest = Body(default=None),
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    trans_endpoint = body.endpoint if body and body.endpoint else None
    trans_model_full = body.translate_model_id if body and body.translate_model_id else None
    
    trans_api_key = None
    trans_model = trans_model_full
    
    if trans_model_full and '/' in trans_model_full:
        parts = trans_model_full.split('/')
        provider_id = int(parts[0])
        provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if provider:
            trans_api_key = provider.api_key
        trans_model = parts[1]
    
    ocr_executor.submit(
        _reprocess_translate_background,
        record_id, page, trans_endpoint, trans_model, trans_api_key
    )
    
    return {"message": "Translation reprocessing started in background"}


def _reprocess_translate_background(record_id: str, page: int, trans_endpoint: str, trans_model: str, trans_api_key: str = None):
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
        if not record:
            return
        
        current_trans_service = TranslateService(endpoint=trans_endpoint, model=trans_model, api_key=trans_api_key) if trans_endpoint or trans_model else translate_service
        
        ocr_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.ocr_text or '')
        ocr_dict = {int(pnum): content for pnum, content in ocr_pages}
        
        if page not in ocr_dict:
            return
        
        page_ocr_text = ocr_dict[page]
        if not page_ocr_text.strip():
            return
        
        new_translated_text = current_trans_service.translate_to_chinese(page_ocr_text)
        
        trans_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.translated_text or '')
        trans_dict = {int(pnum): content for pnum, content in trans_pages}
        trans_dict[page] = new_translated_text
        
        max_page = max(max(ocr_dict.keys()), max(trans_dict.keys())) if trans_dict else max(ocr_dict.keys())
        new_trans_full = []
        for p in range(1, max_page + 1):
            content = trans_dict.get(p, '')
            new_trans_full.append(f"=== Page {p} ===\n{content}")
        record.translated_text = "\n\n".join(new_trans_full)
        
        db.commit()
    except Exception:
        pass
    finally:
        db.close()


def run_continue_processing(
    record_id: str,
    ocr_endpoint: str,
    ocr_model: str,
    trans_model: str,
    doc_lang: str,
    ocr_api_key: str,
    trans_api_key: str
):
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
        if not record:
            return
        
        total_pages = int(record.total_pages) if record.total_pages else 1
        ocr_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.ocr_text or '')
        ocr_dict = {int(pnum): content for pnum, content in ocr_pages}
        trans_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.translated_text or '')
        trans_dict = {int(pnum): content for pnum, content in trans_pages}
        
        ocr_complete_pages = {p for p, c in ocr_dict.items() if c.strip() and not c.strip().startswith('Error:')}
        trans_complete_pages = {p for p, c in trans_dict.items() if c.strip() and not c.strip().startswith('Error:')}
        
        if len(ocr_complete_pages) < total_pages:
            try:
                resolved_path = resolve_file_path(record.file_path)
                if record.file_type == "pdf":
                    doc = fitz.open(resolved_path)
                else:
                    doc = None
                
                for idx in range(total_pages):
                    page_num = idx + 1
                    if page_num in ocr_complete_pages:
                        continue
                    
                    # 每次处理前重新读取最新的模型设置
                    db.refresh(record)
                    current_ocr_model_full = record.ocr_model_id
                    current_ocr_model = ocr_model
                    current_ocr_api_key = ocr_api_key
                    current_ocr_endpoint = ocr_endpoint
                    
                    if current_ocr_model_full and '/' in current_ocr_model_full:
                        parts = current_ocr_model_full.split('/')
                        provider_id = int(parts[0])
                        provider = db.query(Provider).filter(Provider.id == provider_id).first()
                        if provider:
                            current_ocr_model = parts[1]
                            current_ocr_api_key = provider.api_key
                            current_ocr_endpoint = provider.base_url
                    
                    current_ocr_service = OCRService(
                        endpoint=current_ocr_endpoint, 
                        model=current_ocr_model, 
                        language=doc_lang, 
                        api_key=current_ocr_api_key
                    )
                    
                    try:
                        if record.file_type == "pdf":
                            page_obj = doc[idx]
                            pix = page_obj.get_pixmap()
                            img = Image.open(BytesIO(pix.tobytes("png")))
                        else:
                            img = Image.open(resolved_path)
                        
                        img_base64 = current_ocr_service.image_to_base64(img)
                        text = current_ocr_service.call_vision_model(img_base64)
                        ocr_dict[page_num] = text
                    except Exception as e:
                        ocr_dict[page_num] = f"Error: {str(e)}"
                    
                    new_ocr_full = []
                    for p in range(1, total_pages + 1):
                        content = ocr_dict.get(p, '')
                        new_ocr_full.append(f"=== Page {p} ===\n{content}")
                    record.ocr_text = "\n\n".join(new_ocr_full)
                    db.commit()
                
                if doc:
                    doc.close()
            except Exception as e:
                return
        
        ocr_complete_pages = {p for p, c in ocr_dict.items() if c.strip() and not c.strip().startswith('Error:')}
        
        if len(trans_complete_pages) < len(ocr_complete_pages):
            for page_num in sorted(ocr_complete_pages):
                if page_num in trans_complete_pages:
                    continue
                
                # 每次翻译前重新读取最新的模型设置
                db.refresh(record)
                current_trans_model_full = record.translate_model_id
                current_trans_model = trans_model
                current_trans_api_key = trans_api_key
                current_trans_endpoint = ocr_endpoint
                
                if current_trans_model_full and '/' in current_trans_model_full:
                    parts = current_trans_model_full.split('/')
                    provider_id = int(parts[0])
                    provider = db.query(Provider).filter(Provider.id == provider_id).first()
                    if provider:
                        current_trans_model = parts[1]
                        current_trans_api_key = provider.api_key
                        current_trans_endpoint = provider.base_url
                
                current_trans_service = TranslateService(
                    endpoint=current_trans_endpoint, 
                    model=current_trans_model, 
                    api_key=current_trans_api_key
                )
                
                try:
                    translated = current_trans_service.translate_to_chinese(ocr_dict[page_num])
                    trans_dict[page_num] = translated
                except Exception as e:
                    trans_dict[page_num] = f"Error: {str(e)}"
                
                new_trans_full = []
                for p in range(1, total_pages + 1):
                    content = trans_dict.get(p, '')
                    new_trans_full.append(f"=== Page {p} ===\n{content}")
                record.translated_text = "\n\n".join(new_trans_full)
                db.commit()
        
        ocr_complete_count = len(ocr_complete_pages)
        trans_complete_pages = {p for p, c in trans_dict.items() if c.strip() and not c.strip().startswith('Error:')}
        trans_complete_count = len(trans_complete_pages)
        
        if ocr_complete_count >= total_pages and trans_complete_count >= total_pages:
            record.status = "completed"
        else:
            record.status = "processing"
        db.commit()
    except Exception:
        pass
    finally:
        db.close()


@router.post("/{record_id}/continue")
async def continue_processing(
    record_id: str,
    body: ContinueRequest = Body(default=None),
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    total_pages = int(record.total_pages) if record.total_pages else 1
    ocr_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.ocr_text or '')
    ocr_dict = {int(pnum): content for pnum, content in ocr_pages}
    trans_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.translated_text or '')
    trans_dict = {int(pnum): content for pnum, content in trans_pages}
    
    ocr_complete_pages = {p for p, c in ocr_dict.items() if c.strip() and not c.strip().startswith('Error:')}
    trans_complete_pages = {p for p, c in trans_dict.items() if c.strip() and not c.strip().startswith('Error:')}
    
    if len(ocr_complete_pages) >= total_pages and len(trans_complete_pages) >= total_pages:
        return {"message": "Already completed", "status": "completed"}
    
    ocr_endpoint = body.endpoint if body and body.endpoint else None
    ocr_model_full = body.ocr_model_id if body and body.ocr_model_id else None
    trans_model_full = body.translate_model_id if body and body.translate_model_id else None
    doc_lang = body.doc_language if body and body.doc_language else "ja"
    
    ocr_api_key = None
    trans_api_key = None
    ocr_model = ocr_model_full
    trans_model = trans_model_full
    provider_base_url = None
    
    if ocr_model_full and '/' in ocr_model_full:
        parts = ocr_model_full.split('/')
        provider_id = int(parts[0])
        provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if provider:
            ocr_api_key = provider.api_key
            provider_base_url = provider.base_url
        ocr_model = parts[1]
    
    if trans_model_full and '/' in trans_model_full:
        parts = trans_model_full.split('/')
        provider_id = int(parts[0])
        provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if provider:
            trans_api_key = provider.api_key
            if not provider_base_url:
                provider_base_url = provider.base_url
        trans_model = parts[1]
    
    if not ocr_endpoint:
        ocr_endpoint = provider_base_url
    
    record.status = "processing"
    db.commit()
    
    ocr_executor.submit(
        run_continue_processing,
        record_id,
        ocr_endpoint,
        ocr_model,
        trans_model,
        doc_lang,
        ocr_api_key,
        trans_api_key
    )
    
    return {"message": "Processing started", "status": "processing"}


@router.patch("/{record_id}/title")
async def update_content_title(
    record_id: str,
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    title = data.get("content_title", "").strip()
    if len(title) > 100:
        title = title[:100]
    
    record.content_title = title or None
    db.commit()
    db.refresh(record)
    
    return {"id": record.id, "content_title": record.content_title}


@router.post("/{record_id}/auto-title")
async def auto_generate_title(
    record_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    if record.content_title:
        return {"id": record.id, "content_title": record.content_title, "generated": False}
    
    ocr_text = record.ocr_text or ""
    title = ""
    
    for line in ocr_text.split('\n'):
        line = line.strip()
        if line and len(line) > 2 and len(line) <= 100:
            title = line
            break
    
    if title:
        record.content_title = title
        db.commit()
        db.refresh(record)
        return {"id": record.id, "content_title": record.content_title, "generated": True}
    
    return {"id": record.id, "content_title": None, "generated": False}


@router.patch("/{record_id}/model")
async def update_record_model(
    record_id: str,
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    ocr_model_id = data.get("ocr_model_id")
    translate_model_id = data.get("translate_model_id")
    
    if ocr_model_id is not None:
        record.ocr_model_id = ocr_model_id
    if translate_model_id is not None:
        record.translate_model_id = translate_model_id
    
    db.commit()
    db.refresh(record)
    
    return {"id": record.id, "ocr_model_id": record.ocr_model_id, "translate_model_id": record.translate_model_id}


@router.post("/{record_id}/pause-ocr")
async def pause_ocr(
    record_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    ocr_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.ocr_text or '')
    last_page = max([int(p) for p, _ in ocr_pages], default=0)
    
    record.ocr_paused = "true"
    record.ocr_last_page = str(last_page)
    db.commit()
    
    return {"message": "OCR paused", "last_page": last_page}


@router.post("/{record_id}/resume-ocr")
async def resume_ocr(
    record_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    record.ocr_paused = "false"
    db.commit()
    
    ocr_model_full = record.ocr_model_id or ''
    trans_model_full = record.translate_model_id or ''
    language = record.doc_language or "ja"
    
    ocr_api_key = None
    trans_api_key = None
    ocr_model = ocr_model_full
    trans_model = trans_model_full
    
    if ocr_model_full and '/' in ocr_model_full:
        parts = ocr_model_full.split('/')
        provider_id = int(parts[0])
        provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if provider:
            ocr_api_key = provider.api_key
        ocr_model = parts[1]
    
    if trans_model_full and '/' in trans_model_full:
        parts = trans_model_full.split('/')
        provider_id = int(parts[0])
        provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if provider:
            trans_api_key = provider.api_key
        trans_model = parts[1]
    
    ocr_executor.submit(
        _resume_ocr_background,
        record_id, record.file_path, record.file_type,
        ocr_model, trans_model, language, ocr_api_key, trans_api_key
    )
    
    return {"message": "OCR resumed"}


def _resume_ocr_background(record_id: str, file_path: str, file_type: str, ocr_model: str, trans_model: str, language: str, ocr_api_key: str = None, trans_api_key: str = None):
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
        if not record:
            return
        
        total_pages = int(record.total_pages) if record.total_pages else 1
        start_page = int(record.ocr_last_page or '0') + 1
        
        ocr_service = OCRService(model=ocr_model, endpoint=None, language=language, api_key=ocr_api_key)
        trans_service = TranslateService(model=trans_model, endpoint=None, language=language, api_key=trans_api_key)
        
        resolved_path = resolve_file_path(file_path)
        
        ocr_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.ocr_text or '')
        ocr_dict = {int(pnum): content for pnum, content in ocr_pages}
        
        trans_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.translated_text or '')
        trans_dict = {int(pnum): content for pnum, content in trans_pages}
        
        for idx in range(start_page - 1, total_pages):
            page_num = idx + 1
            if record.ocr_paused == "true":
                break
            
            try:
                if file_type == "pdf":
                    doc = fitz.open(resolved_path)
                    page_obj = doc[page_num - 1]
                    pix = page_obj.get_pixmap()
                    img = Image.open(BytesIO(pix.tobytes("png")))
                    doc.close()
                else:
                    img = Image.open(resolved_path)
                
                img_base64 = ocr_service.image_to_base64(img)
                text = ocr_service.call_vision_model(img_base64)
                ocr_dict[page_num] = text
            except Exception as e:
                ocr_dict[page_num] = f"Error: {str(e)}"
            
            new_ocr_full = []
            for p in range(1, total_pages + 1):
                content = ocr_dict.get(p, '')
                new_ocr_full.append(f"=== Page {p} ===\n{content}")
            record.ocr_text = "\n\n".join(new_ocr_full)
            db.commit()
            
            if text and not text.startswith('Error:'):
                try:
                    translated = trans_service.translate_to_chinese(text)
                except Exception as e:
                    translated = f"Error: {str(e)}"
                trans_dict[page_num] = translated
                
                new_trans_full = []
                for p in range(1, total_pages + 1):
                    content = trans_dict.get(p, '')
                    new_trans_full.append(f"=== Page {p} ===\n{content}")
                record.translated_text = "\n\n".join(new_trans_full)
                db.commit()
        
        record.ocr_paused = "false"
        record.status = "completed"
        db.commit()
    except Exception:
        pass
    finally:
        db.close()


@router.post("/{record_id}/pause-translate")
async def pause_translate(
    record_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    record.trans_paused = "true"
    db.commit()
    
    return {"message": "Translation paused"}


@router.post("/{record_id}/resume-translate")
async def resume_translate(
    record_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    record.trans_paused = "false"
    db.commit()
    
    trans_model_full = record.translate_model_id or ''
    trans_api_key = None
    trans_model = trans_model_full
    
    if trans_model_full and '/' in trans_model_full:
        parts = trans_model_full.split('/')
        provider_id = int(parts[0])
        provider = db.query(Provider).filter(Provider.id == provider_id).first()
        if provider:
            trans_api_key = provider.api_key
        trans_model = parts[1]
    
    ocr_executor.submit(
        _resume_translate_background,
        record_id, trans_model, trans_api_key
    )
    
    return {"message": "Translation resumed"}


def _resume_translate_background(record_id: str, trans_model: str, trans_api_key: str = None):
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
        if not record:
            return
        
        total_pages = int(record.total_pages) if record.total_pages else 1
        language = record.doc_language or "ja"
        
        trans_service = TranslateService(model=trans_model, endpoint=None, language=language, api_key=trans_api_key)
        
        ocr_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.ocr_text or '')
        ocr_dict = {int(pnum): content for pnum, content in ocr_pages}
        
        trans_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.translated_text or '')
        trans_dict = {int(pnum): content for pnum, content in trans_pages}
        
        for page_num in range(1, total_pages + 1):
            if record.trans_paused == "true":
                break
            
            if page_num not in ocr_dict:
                continue
            
            page_content = ocr_dict[page_num]
            if not page_content.strip() or page_content.strip().startswith('Error:'):
                continue
            
            try:
                translated = trans_service.translate_to_chinese(page_content)
            except Exception as e:
                translated = f"Error: {str(e)}"
            
            trans_dict[page_num] = translated
            
            new_trans_full = []
            for p in range(1, total_pages + 1):
                content = trans_dict.get(p, '')
                new_trans_full.append(f"=== Page {p} ===\n{content}")
            record.translated_text = "\n\n".join(new_trans_full)
            db.commit()
        
        record.trans_paused = "false"
        db.commit()
    except Exception:
        pass
    finally:
        db.close()
