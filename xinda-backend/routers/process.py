from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
from models.database import get_db, ProcessingHistory
from services.ocr_service import OCRService
from services.translate_service import TranslateService
import asyncio

router = APIRouter()

ocr_service = OCRService()
translate_service = TranslateService()

@router.post("/{record_id}")
async def process_file(
    record_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    if record.status not in ["uploaded"]:
        raise HTTPException(status_code=400, detail=f"File already processed (status: {record.status})")
    
    try:
        record.status = "processing"
        db.commit()
        
        ocr_text = ocr_service.extract_text(record.file_path, record.file_type)
        record.ocr_text = ocr_text
        record.status = "ocr_done"
        db.commit()
        
        import re
        ocr_pages = re.findall(r'=== Page (\d+) ===\n([\s\S]*?)(?=\n\n=== Page \d+ ===|$)', ocr_text)
        translated_pages = []
        for page_num, page_content in ocr_pages:
            if page_content.strip() and not page_content.strip().startswith('Error:'):
                translated_content = translate_service.translate_to_chinese(page_content)
                translated_pages.append(f"=== Page {page_num} ===\n{translated_content}")
            else:
                translated_pages.append(f"=== Page {page_num} ===\n{page_content}")
        
        record.translated_text = "\n\n".join(translated_pages)
        record.status = "completed"
        db.commit()
        
        return {
            "id": record.id,
            "original_filename": record.original_filename,
            "file_type": record.file_type,
            "ocr_text": record.ocr_text,
            "translated_text": record.translated_text,
            "status": record.status,
            "upload_time": record.upload_time.isoformat()
        }
    except Exception as e:
        record.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
