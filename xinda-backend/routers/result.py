from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import FileResponse, StreamingResponse
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


@router.get("/page/{record_id}/{page_num}")
async def get_pdf_page(
    record_id: str,
    page_num: int,
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    if record.file_type != "pdf":
        raise HTTPException(status_code=400, detail="Not a PDF file")
    
    resolved_path = resolve_file_path(record.file_path)
    
    if not os.path.exists(resolved_path):
        raise HTTPException(status_code=404, detail=f"File not found: {resolved_path}")
    
    try:
        doc = fitz.open(resolved_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open PDF: {str(e)}")
    
    total_pages = doc.page_count
    if page_num < 1 or page_num > total_pages:
        doc.close()
        raise HTTPException(status_code=400, detail=f"Page number out of range. PDF has {total_pages} pages.")
    
    try:
        page_obj = doc[page_num - 1]
        pix = page_obj.get_pixmap(dpi=300)
        png_bytes = pix.tobytes("png")
        doc.close()
        
        return StreamingResponse(
            BytesIO(png_bytes),
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=page_{page_num}.png"}
        )
    except Exception as e:
        doc.close()
        raise HTTPException(status_code=500, detail=f"Failed to render page: {str(e)}")


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
    doc_lang = body.doc_language if body and body.doc_language else "jp"
    
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
    from services.stream_store import append_stream_text, set_stream_status, clear_stream_data
    db = SessionLocal()
    try:
        record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
        if not record:
            return
        
        clear_stream_data(record_id)
        
        ocr_kwargs = {'language': doc_lang}
        if ocr_endpoint:
            ocr_kwargs['endpoint'] = ocr_endpoint
        if ocr_model:
            ocr_kwargs['model'] = ocr_model
        if ocr_api_key:
            ocr_kwargs['api_key'] = ocr_api_key
        current_ocr_service = OCRService(**ocr_kwargs) if ocr_kwargs else ocr_service
        
        trans_kwargs = {'language': doc_lang}
        if ocr_endpoint:
            trans_kwargs['endpoint'] = ocr_endpoint
        if ocr_model:
            trans_kwargs['model'] = ocr_model
        if ocr_api_key:
            trans_kwargs['api_key'] = ocr_api_key
        current_trans_service = TranslateService(**trans_kwargs) if trans_kwargs else translate_service
        
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
        
        def ocr_callback(chunk, full_text):
            append_stream_text(record_id, 'ocr', chunk, page)
        
        new_ocr_text = current_ocr_service.call_vision_model_stream(img_base64, ocr_callback)
        
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
        
        def trans_callback(chunk, full_text):
            append_stream_text(record_id, 'trans', chunk, page)
        
        new_translated_text = current_trans_service.translate_to_chinese_stream(new_ocr_text, trans_callback)
        
        trans_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.translated_text or '')
        trans_dict = {int(pnum): content for pnum, content in trans_pages}
        trans_dict[page] = new_translated_text
        
        new_trans_full = []
        for p in range(1, max_page + 1):
            content = trans_dict.get(p, '')
            new_trans_full.append(f"=== Page {p} ===\n{content}")
        record.translated_text = "\n\n".join(new_trans_full)
        
        db.commit()
        set_stream_status(record_id, "completed")
    except Exception as e:
        print(f"[REPROCESS OCR ERROR] record_id={record_id}, page={page}, error={e}")
        import traceback
        traceback.print_exc()
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
    from services.stream_store import append_stream_text, set_stream_status, clear_stream_data
    db = SessionLocal()
    try:
        record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
        if not record:
            return
        
        clear_stream_data(record_id)
        
        trans_kwargs = {}
        if trans_endpoint:
            trans_kwargs['endpoint'] = trans_endpoint
        if trans_model:
            trans_kwargs['model'] = trans_model
        if trans_api_key:
            trans_kwargs['api_key'] = trans_api_key
        trans_kwargs['language'] = record.doc_language or 'jp'
        current_trans_service = TranslateService(**trans_kwargs) if trans_kwargs else translate_service
        
        ocr_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.ocr_text or '')
        ocr_dict = {int(pnum): content for pnum, content in ocr_pages}
        
        if page not in ocr_dict:
            return
        
        page_ocr_text = ocr_dict[page]
        if not page_ocr_text.strip():
            return
        
        def trans_callback(chunk, full_text):
            append_stream_text(record_id, 'trans', chunk, page)
        
        new_translated_text = current_trans_service.translate_to_chinese_stream(page_ocr_text, trans_callback)
        
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
        set_stream_status(record_id, "completed")
    except Exception as e:
        print(f"[REPROCESS TRANS ERROR] record_id={record_id}, page={page}, error={e}")
        import traceback
        traceback.print_exc()
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
    except Exception as e:
        print(f"[CONTINUE PROCESSING ERROR] record_id={record_id}, error={e}")
        import traceback
        traceback.print_exc()
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
    doc_lang = body.doc_language if body and body.doc_language else "jp"
    
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


@router.patch("/{record_id}/language")
async def update_record_language(
    record_id: str,
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    language = data.get("doc_language", "").strip()
    record.doc_language = language or "auto"
    db.commit()
    db.refresh(record)
    
    return {"id": record.id, "doc_language": record.doc_language}


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


@router.get("/stream/{record_id}")
async def stream_result(record_id: str, db: Session = Depends(get_db)):
    from services.stream_store import get_stream_data
    import asyncio
    import json
    
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    async def event_generator():
        last_data = {}
        while True:
            current_data = get_stream_data(record_id)
            
            if current_data != last_data:
                yield f"data: {json.dumps(current_data)}\n\n"
                last_data = current_data
            
            if current_data.get('status') == 'completed':
                break
            
            await asyncio.sleep(0.1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
