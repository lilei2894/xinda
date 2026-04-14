from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from models.database import get_db, LanguagePrompt, AppConfig

router = APIRouter()

OCR_TEMPLATE = """# Role
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

TRANSLATE_TEMPLATE = """请将以下{lang}文本翻译成中文。

要求：
1. 直接输出翻译结果，不要任何解释或说明
2. 保持原文段落结构
3. 使用现代白话中文，不用文言文
4. 人名地名机构名用中文音译"""

class LanguagePromptCreate(BaseModel):
    language_code: str
    language_name: str
    ocr_prompt: Optional[str] = None
    translate_prompt: Optional[str] = None

class LanguagePromptUpdate(BaseModel):
    language_name: Optional[str] = None
    ocr_prompt: Optional[str] = None
    translate_prompt: Optional[str] = None
    color: Optional[str] = None

class LanguagePromptResponse(BaseModel):
    id: int
    language_code: str
    language_name: str
    ocr_prompt: Optional[str]
    translate_prompt: Optional[str]
    color: Optional[str]
    
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
    if data.color is not None:
        prompt.color = data.color
    
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
    
    ocr_prompt = OCR_TEMPLATE.format(lang=language_name)
    translate_prompt = TRANSLATE_TEMPLATE.format(lang=language_name)
    
    if existing:
        existing.ocr_prompt = ocr_prompt
        existing.translate_prompt = translate_prompt
        existing.language_name = language_name
        db.commit()
        db.refresh(existing)
        await update_language_detection_prompt(db)
        return {"message": "Prompts generated successfully", "ocr_prompt": ocr_prompt, "translate_prompt": translate_prompt}
    else:
        prompt = LanguagePrompt(
            language_code=language_code,
            language_name=language_name,
            ocr_prompt=ocr_prompt,
            translate_prompt=translate_prompt
        )
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        
        await update_language_detection_prompt(db)
        
        return {"message": "Prompts generated successfully", "ocr_prompt": ocr_prompt, "translate_prompt": translate_prompt}

async def update_language_detection_prompt(db: Session):
    prompts = db.query(LanguagePrompt).all()
    if not prompts:
        return
    
    language_codes = [p.language_code for p in prompts]
    language_list = ", ".join([f'- "{p.language_code}" 表示{p.language_name}' for p in prompts])
    
    detection_prompt = f"""# Role
你是一名语言识别专家。

# Task
识别图片中文字的主要语言。

# Output Format
仅输出以下语言代码之一，不要输出任何其他内容或解释：
{language_list}

# Output
直接输出语言代码，无任何附加内容。"""
    
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
