from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProcessingHistoryBase(BaseModel):
    original_filename: str
    file_type: str

class ProcessingHistoryCreate(ProcessingHistoryBase):
    pass

class ProcessingHistory(ProcessingHistoryBase):
    id: str
    ocr_text: Optional[str] = None
    translated_text: Optional[str] = None
    status: str
    upload_time: datetime
    model_endpoint: str

    class Config:
        from_attributes = True
