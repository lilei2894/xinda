def get_ocr_prompt(language: str, db=None) -> str:
    if db:
        from models.database import LanguagePrompt
        prompt = db.query(LanguagePrompt).filter(LanguagePrompt.language_code == language).first()
        if prompt and prompt.ocr_prompt:
            return prompt.ocr_prompt
    
    lang_name = {"jp": "日文", "en": "英文", "de": "德文", "fr": "法文"}.get(language, "外文")
    
    return f"""# Role
你是一名专业的文档OCR识别专家，擅长识别和处理历史档案文献中的{lang_name}文本。

# Task
识别图片中{lang_name}主体文档的全部文本内容，输出完整的识别结果。

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
   - 仅输出识别的{lang_name}文本
   - 不输出HTML/XML标签或格式标记
   - 不添加任何解释、说明、前缀、标注
   - 不重复同一段文字

# Output
直接输出识别的文本内容，无需任何附加说明。"""

def get_translate_prompt(language: str, db=None) -> str:
    if db:
        from models.database import LanguagePrompt
        prompt = db.query(LanguagePrompt).filter(LanguagePrompt.language_code == language).first()
        if prompt and prompt.translate_prompt:
            return prompt.translate_prompt
    
    lang_name = {"jp": "日文", "en": "英文", "de": "德文", "fr": "法文", "ru": "俄文", "es": "西班牙文"}.get(language, "外文")
    
    return f"""请将以下{lang_name}文本翻译成中文。

要求：
1. 直接输出翻译结果，不要任何解释或说明
2. 保持原文段落结构
3. 使用现代白话中文，不用文言文
4. 人名地名机构名用中文音译"""

def get_language_detection_prompt(db=None) -> str:
    if db:
        from models.database import AppConfig
        config = db.query(AppConfig).filter(AppConfig.key == "language_detection_prompt").first()
        if config and config.value:
            return config.value
    
    return """# Role
你是一名语言识别专家。

# Task
识别图片中文字的主要语言。

# Output Format
仅输出以下语言代码之一，不要输出任何其他内容或解释：
- "jp" 表示日文
- "en" 表示英文  
- "de" 表示德文
- "fr" 表示法文
- "ru" 表示俄文
- "es" 表示西班牙文

# Output
直接输出语言代码，无任何附加内容。"""
