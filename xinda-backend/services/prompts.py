def get_ocr_prompt(language: str, db=None) -> str:
    if db:
        from models.database import LanguagePrompt
        prompt = db.query(LanguagePrompt).filter(LanguagePrompt.language_code == language).first()
        if prompt and prompt.ocr_prompt:
            return prompt.ocr_prompt
    
    lang_name = {'jp': '日文', 'en': '英文', 'de': '德文', 'fr': '法文', 'ru': '俄文', 'es': '西班牙文'}.get(language, '外文')
    
    return f'''## 角色
你是专业文献OCR识别专家，擅长识别{lang_name}历史档案文献。

## 任务
识别图片中的{lang_name}文本，输出识别结果。

## 格式要求
1. 保持段落结构，段落之间用两个换行符分隔
2. 同一自然段落被排版切断的文字，必须合并为一行
3. 模糊文字用[?]标注，不要猜测

## 约束条件
仅输出识别文本，不要添加任何解释或说明。
'''

def get_translate_prompt(language: str, db=None) -> str:
    if db:
        from models.database import LanguagePrompt
        prompt = db.query(LanguagePrompt).filter(LanguagePrompt.language_code == language).first()
        if prompt and prompt.translate_prompt:
            return prompt.translate_prompt
    
    lang_name = {'jp': '日文', 'en': '英文', 'de': '德文', 'fr': '法文', 'ru': '俄文', 'es': '西班牙文'}.get(language, '外文')
    
    return f'''## 角色
你是专业文献翻译专家，精通{lang_name}与中文互译。

## 任务
将以下{lang_name}文本翻译成中文。

## 格式要求
1. 保持原文段落结构
2. 使用现代白话中文，不用文言文
3. 专业术语首次出现时保留原文并加中文注释

## 约束条件
直接输出翻译结果，不要解释翻译过程或添加任何说明。
'''

def get_language_detection_prompt(db=None) -> str:
    if db:
        from models.database import AppConfig
        config = db.query(AppConfig).filter(AppConfig.key == 'language_detection_prompt').first()
        if config and config.value:
            return config.value
    
    return '仅输出语言代码：jp en de fr ru es'
