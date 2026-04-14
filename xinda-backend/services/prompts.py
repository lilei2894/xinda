def get_ocr_prompt(language: str, db=None) -> str:
    if db:
        from models.database import LanguagePrompt
        prompt = db.query(LanguagePrompt).filter(LanguagePrompt.language_code == language).first()
        if prompt and prompt.ocr_prompt:
            return prompt.ocr_prompt
    
    return f"""Please identify the main document content in this image.

【Paragraph Merging Rules - Most Important, Must Follow Strictly】
- Text from the same natural paragraph that was cut due to layout width must be merged into one line, without any line breaks in between
- Only insert a line break when the content is clearly a new paragraph (e.g., indented start, heading, subtitle)
- Separate paragraphs with two line breaks (\\n\\n)
- Headings and subtitles must be on their own lines, with one blank line before and after
- List items, table rows, etc. must each be on their own line

【Content Requirements】
- Only identify the main document text in the center of the image, ignore peripheral content
- Ignore: REEL numbers, institutional watermarks, headers/footers, scan marks, archive numbers, text outside borders
- Output only the identified text, nothing else
- Do not output HTML tags, XML tags, or any markup
- Do not add any explanations, notes, or prefixes
- Never repeat the same paragraph multiple times"""

def get_translate_prompt(language: str, db=None) -> str:
    if db:
        from models.database import LanguagePrompt
        prompt = db.query(LanguagePrompt).filter(LanguagePrompt.language_code == language).first()
        if prompt and prompt.translate_prompt:
            return prompt.translate_prompt
    
    return f"""You are a professional translator. Your sole responsibility is to translate text into modern Chinese written language.

Rules:
1. Output must be 100% Chinese translation results
2. Do not retain original text or fragments
3. Do not use classical Chinese or semi-classical expressions
4. Must use modern Chinese written language (similar to news reports, academic papers)
5. Proper nouns (names, places, institutions) should be transliterated into Chinese characters
6. Strictly maintain the original paragraph structure, never merge multiple paragraphs into one
7. Absolutely do not output any explanations, notes, prefixes, suffixes, headings, or markers
8. If there is content that cannot be translated, explain it in Chinese"""

def get_language_detection_prompt(db=None) -> str:
    if db:
        from models.database import AppConfig
        config = db.query(AppConfig).filter(AppConfig.key == "language_detection_prompt").first()
        if config and config.value:
            return config.value
    
    return """Please identify the primary language of the text in this image.
Respond with ONLY one of the following language codes: "jp" for Japanese, "en" for English, "de" for German, "fr" for French.
Do not include any other text or explanation."""
