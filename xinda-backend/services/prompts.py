def get_ocr_prompt(language: str, db=None) -> str:
    if db:
        from models.database import LanguagePrompt
        prompt = db.query(LanguagePrompt).filter(LanguagePrompt.language_code == language).first()
        if prompt and prompt.ocr_prompt:
            return prompt.ocr_prompt
    
    lang_name = {'jp': '日文', 'en': '英文', 'de': '德文', 'fr': '法文', 'ru': '俄文', 'es': '西班牙文'}.get(language, '外文')
    
    return f'''请识别这张图片中的{lang_name}文本。

要求：
1. 仅输出识别的文本内容
2. 保持段落结构
3. 不要添加任何解释'''

def get_translate_prompt(language: str, db=None) -> str:
    if db:
        from models.database import LanguagePrompt
        prompt = db.query(LanguagePrompt).filter(LanguagePrompt.language_code == language).first()
        if prompt and prompt.translate_prompt:
            return prompt.translate_prompt
    
    lang_name = {'jp': '日文', 'en': '英文', 'de': '德文', 'fr': '法文', 'ru': '俄文', 'es': '西班牙文'}.get(language, '外文')
    
    return f'''请将以下{lang_name}翻译成中文。

要求：
1. 直接输出翻译结果
2. 保持段落结构
3. 使用现代白话文'''

def get_language_detection_prompt(db=None) -> str:
    if db:
        from models.database import AppConfig
        config = db.query(AppConfig).filter(AppConfig.key == 'language_detection_prompt').first()
        if config and config.value:
            return config.value
    
    return '仅输出语言代码：jp en de fr ru es'