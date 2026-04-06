from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends
import os
import json
from models.database import get_db, ProcessingHistory, Provider, AppConfig
from services.export_service import ExportService
from fastapi.responses import StreamingResponse
import io
import urllib.parse

router = APIRouter()
export_service = ExportService()

@router.get("/export/{record_id}")
async def export_to_word(
    record_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    
    if not record:
        return {"error": "Record not found"}
    
    if record.status != "completed":
        return {"error": "Record not processed yet"}
    
    word_file = export_service.export_to_word(record)
    safe_name = urllib.parse.quote(f"result_{record_id}.docx")
    
    return StreamingResponse(
        io.BytesIO(word_file.read()),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}"
        }
    )


@router.get("/export/{record_id}/ocr")
async def export_ocr_only(
    record_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        return {"error": "Record not found"}
    
    word_file = export_service.export_ocr_only(record)
    safe_name = urllib.parse.quote(f"{record.original_filename}_识别稿.docx")
    return StreamingResponse(
        io.BytesIO(word_file.read()),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}"
        }
    )


@router.get("/export/{record_id}/translate")
async def export_translate_only(
    record_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(ProcessingHistory).filter(ProcessingHistory.id == record_id).first()
    if not record:
        return {"error": "Record not found"}
    
    word_file = export_service.export_translate_only(record)
    safe_name = urllib.parse.quote(f"{record.original_filename}_翻译稿.docx")
    return StreamingResponse(
        io.BytesIO(word_file.read()),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}"
        }
    )

@router.get("/config")
async def get_config(db: Session = Depends(get_db)):
    # Get all providers
    providers = db.query(Provider).all()
    providers_list = [
        {
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "base_url": p.base_url,
            "is_active": p.is_active,
        }
        for p in providers
    ]
    
    # Get stored config values
    def get_config_value(key, default):
        cfg = db.query(AppConfig).filter(AppConfig.key == key).first()
        return cfg.value if cfg else default
    
    return {
        "model_endpoint": os.getenv("OLLAMA_ENDPOINT", "http://172.25.249.29:30000"),
        "doc_language": get_config_value("doc_language", "auto"),
        "ocr_model_id": get_config_value("ocr_model_id", None),
        "translate_model_id": get_config_value("translate_model_id", None),
        "providers": providers_list,
    }

@router.post("/config")
async def update_config(config: dict, db: Session = Depends(get_db)):
    # Update or create each config value
    for key in ["doc_language", "ocr_model_id", "translate_model_id"]:
        if key in config:
            existing = db.query(AppConfig).filter(AppConfig.key == key).first()
            if existing:
                existing.value = config[key]
            else:
                new_cfg = AppConfig(key=key, value=config[key])
                db.add(new_cfg)
    
    # Also handle model_endpoint for backward compatibility
    if "model_endpoint" in config:
        records = db.query(ProcessingHistory).all()
        for record in records:
            record.model_endpoint = config.get("model_endpoint")
    
    db.commit()
    return {"message": "Config updated successfully"}
