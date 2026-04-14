from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
from typing import List
from models.database import get_db, ProcessingHistory, LanguagePrompt
import os

router = APIRouter()


def _get_lang_color(lang_code: str, db: Session):
    if not lang_code:
        return None
    lang = db.query(LanguagePrompt).filter(LanguagePrompt.language_code == lang_code).first()
    return lang.color if lang else None


@router.get("")
@router.get("/")
async def get_history(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    offset = (page - 1) * page_size
    records = db.query(ProcessingHistory)\
        .order_by(ProcessingHistory.upload_time.desc())\
        .offset(offset)\
        .limit(page_size)\
        .all()
    
    total = db.query(ProcessingHistory).count()
    
    def calculate_status(record):
        if record.status == 'failed' or record.status == 'pending':
            return record.status
        
        total_pages = int(record.total_pages) if record.total_pages else 1
        
        ocr_pages = []
        if record.ocr_text:
            import re
            ocr_pages = re.findall(r'=== Page \d+ ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.ocr_text)
        ocr_complete = len([p for p in ocr_pages if p.strip() and not p.strip().startswith('Error:')])
        
        trans_pages = []
        if record.translated_text:
            trans_pages = re.findall(r'=== Page \d+ ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', record.translated_text)
        trans_complete = len([p for p in trans_pages if p.strip() and not p.strip().startswith('Error:')])
        
        if ocr_complete >= total_pages and trans_complete >= total_pages:
            return 'completed'
        elif ocr_complete > 0 or trans_complete > 0:
            return 'processing'
        else:
            return 'pending'
    
    return {
        "records": [
            {
                "id": record.id,
                "original_filename": record.original_filename,
                "file_type": record.file_type,
                "status": calculate_status(record),
                "total_pages": record.total_pages,
                "upload_time": record.upload_time.isoformat(),
                "content_title": record.content_title,
                "doc_language": record.doc_language,
                "language_color": _get_lang_color(record.doc_language, db) if record.doc_language else None
            }
            for record in records
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{record_id}")
async def get_record(
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
        image_urls.append(f"/api/image/{record.id}/1")
    
    return {
        "id": record.id,
        "original_filename": record.original_filename,
        "file_type": record.file_type,
        "image_urls": image_urls,
        "ocr_text": record.ocr_text,
        "translated_text": record.translated_text,
        "upload_time": record.upload_time.isoformat(),
        "status": record.status,
        "model_endpoint": record.model_endpoint
    }

@router.delete("/{record_id}")
async def delete_record(
    record_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    if record.file_path and os.path.exists(record.file_path):
        os.remove(record.file_path)
    
    db.delete(record)
    db.commit()
    
    return {"message": "Record deleted successfully"}
