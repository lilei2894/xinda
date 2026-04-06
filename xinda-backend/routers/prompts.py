from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from models.database import get_db, LanguagePrompt, AppConfig

router = APIRouter()

class LanguagePromptCreate(BaseModel):
    language_code: str
    language_name: str
    ocr_prompt: Optional[str] = None
    translate_prompt: Optional[str] = None

class LanguagePromptUpdate(BaseModel):
    language_name: Optional[str] = None
    ocr_prompt: Optional[str] = None
    translate_prompt: Optional[str] = None

class LanguagePromptResponse(BaseModel):
    id: int
    language_code: str
    language_name: str
    ocr_prompt: Optional[str]
    translate_prompt: Optional[str]
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[LanguagePromptResponse])
async def get_prompts(db: Session = Depends(get_db)):
    prompts = db.query(LanguagePrompt).order_by(LanguagePrompt.id).all()
    return prompts

@router.post("", response_model=LanguagePromptResponse)
async def create_language_prompt(data: LanguagePromptCreate, db: Session = Depends(get_db)):
    existing = db.query(LanguagePrompt).filter(LanguagePrompt.language_code == data.language_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Language code already exists")
    
    prompt = LanguagePrompt(
        language_code=data.language_code,
        language_name=data.language_name,
        ocr_prompt=data.ocr_prompt,
        translate_prompt=data.translate_prompt
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    
    await update_language_detection_prompt(db)
    
    return prompt

@router.put("/{language_code}", response_model=LanguagePromptResponse)
async def update_language_prompt(language_code: str, data: LanguagePromptUpdate, db: Session = Depends(get_db)):
    prompt = db.query(LanguagePrompt).filter(LanguagePrompt.language_code == language_code).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Language not found")
    
    if data.language_name is not None:
        prompt.language_name = data.language_name
    if data.ocr_prompt is not None:
        prompt.ocr_prompt = data.ocr_prompt
    if data.translate_prompt is not None:
        prompt.translate_prompt = data.translate_prompt
    
    db.commit()
    db.refresh(prompt)
    
    return prompt

@router.delete("/{language_code}")
async def delete_language_prompt(language_code: str, db: Session = Depends(get_db)):
    prompt = db.query(LanguagePrompt).filter(LanguagePrompt.language_code == language_code).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Language not found")
    
    db.delete(prompt)
    db.commit()
    
    await update_language_detection_prompt(db)
    
    return {"message": "Language deleted successfully"}

@router.post("/{language_code}/generate")
async def generate_prompts(language_code: str, language_name: str, db: Session = Depends(get_db)):
    existing = db.query(LanguagePrompt).filter(LanguagePrompt.language_code == language_code).first()
    if existing:
        if existing.ocr_prompt and existing.translate_prompt:
            return {"message": "Prompts already exist", "ocr_prompt": existing.ocr_prompt, "translate_prompt": existing.translate_prompt}
    
    en_prompt = db.query(LanguagePrompt).filter(LanguagePrompt.language_code == "en").first()
    if not en_prompt:
        raise HTTPException(status_code=400, detail="English prompt template not found")
    
    ocr_template = en_prompt.ocr_prompt or ""
    translate_template = en_prompt.translate_prompt or ""
    
    ocr_template = ocr_template.replace("English", language_name)
    ocr_template = ocr_template.replace("english", language_name.lower())
    
    translate_template = translate_template.replace("English", language_name)
    translate_template = translate_template.replace("english", language_name.lower())
    
    if existing:
        existing.ocr_prompt = ocr_template
        existing.translate_prompt = translate_template
        existing.language_name = language_name
        db.commit()
        db.refresh(existing)
        await update_language_detection_prompt(db)
        return {"message": "Prompts generated successfully", "ocr_prompt": ocr_template, "translate_prompt": translate_template}
    else:
        prompt = LanguagePrompt(
            language_code=language_code,
            language_name=language_name,
            ocr_prompt=ocr_template,
            translate_prompt=translate_template
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        
        await update_language_detection_prompt(db)
        
        return {"message": "Prompts generated successfully", "ocr_prompt": ocr_template, "translate_prompt": translate_template}

async def update_language_detection_prompt(db: Session):
    prompts = db.query(LanguagePrompt).all()
    if not prompts:
        return
    
    language_codes = [p.language_code for p in prompts]
    language_names = [f'"{p.language_name}" ({p.language_code})' for p in prompts]
    
    detection_prompt = f"""Please identify the primary language of the text in this image.
Respond with ONLY one of the following language codes: {", ".join(language_codes)}.
Do not include any other text or explanation."""
    
    config = db.query(AppConfig).filter(AppConfig.key == "language_detection_prompt").first()
    if config:
        config.value = detection_prompt
    else:
        config = AppConfig(key="language_detection_prompt", value=detection_prompt)
        db.add(config)
    db.commit()

@router.get("/detection")
async def get_language_detection_prompt(db: Session = Depends(get_db)):
    config = db.query(AppConfig).filter(AppConfig.key == "language_detection_prompt").first()
    if not config:
        await update_language_detection_prompt(db)
        config = db.query(AppConfig).filter(AppConfig.key == "language_detection_prompt").first()
    return {"prompt": config.value if config else ""}
