import base64
import requests
import subprocess
import json
import platform
from io import BytesIO
from PIL import Image
import fitz
import os
import re
from collections import Counter
from services import prompts as prompts_module

USE_CURL_FALLBACK = platform.system() == 'Darwin'

class OCRService:
    def __init__(self, model=None, endpoint=None, language=None, api_key=None):
        self.api_endpoint = endpoint or os.getenv("OLLAMA_ENDPOINT", "http://172.25.249.20:30000")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3.5-uncensored-35B")
        self.language = language or "jp"
        self.api_key = api_key
        self.max_ocr_retries = int(os.getenv("OCR_MAX_RETRIES", "2"))
        self.ocr_timeout = int(os.getenv("OCR_TIMEOUT", "300"))
        self.detect_timeout = int(os.getenv("OCR_DETECT_TIMEOUT", "60"))
    
    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _post_with_curl(self, url, payload, timeout=None):
        if timeout is None:
            timeout = self.ocr_timeout
        curl_headers = ["-H", "Content-Type: application/json"]
        if self.api_key:
            curl_headers.extend(["-H", f"Authorization: Bearer {self.api_key}"])

        cmd = [
            "curl", "-s", "-X", "POST",
            *curl_headers,
            "-d", json.dumps(payload),
            "--connect-timeout", "30",
            "-m", str(timeout),
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
        if result.returncode != 0:
            raise Exception(f"curl failed: {result.stderr}")

        return json.loads(result.stdout)
    
    def detect_hallucination(self, text):
        if not text or len(text) < 50:
            return False
        
        prompt_markers = ['段落合并规则', '内容要求', '必须严格遵守', '绝不可重复', '不要输出HTML', 'Paragraph Merging Rules', 'Content Requirements']
        if sum(1 for m in prompt_markers if m in text) >= 2:
            return True
        
        for line in text.split('\n'):
            line = line.strip()
            if len(line) < 20:
                continue
            for sub_len in range(5, len(line) // 4):
                for start in range(0, len(line) - sub_len * 2 + 1):
                    sub = line[start:start + sub_len]
                    if len(sub) < 5:
                        continue
                    count = line.count(sub)
                    if count >= 3:
                        return True
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if len(lines) >= 3:
            n = 3
            ngrams = []
            for i in range(len(lines) - n + 1):
                ngram = '\n'.join(lines[i:i+n])
                ngrams.append(ngram)
            
            if ngrams:
                counter = Counter(ngrams)
                most_common_count = counter.most_common(1)[0][1]
                repetition_ratio = most_common_count / len(ngrams)
                if repetition_ratio > 0.3:
                    return True
        
        unique_chars = len(set(text))
        total_chars = len(text)
        char_ratio = unique_chars / total_chars if total_chars > 0 else 1.0
        
        if char_ratio < 0.20:
            return True
        
        return False
    
    def pdf_to_images(self, pdf_path):
        doc = fitz.open(pdf_path)
        images = []
        for page in doc:
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            img = Image.open(BytesIO(img_data))
            images.append(img)
        doc.close()
        return images
    
    def image_to_base64(self, image):
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return img_base64
    
    def detect_language(self, image_base64):
        print('[DETECT-LANG] Starting...')
        from models.database import SessionLocal
        db = SessionLocal()
        try:
            language_detection_prompt = prompts_module.get_language_detection_prompt(db)
            print(f'[DETECT-LANG] Got prompt, length: {len(language_detection_prompt)}')
        finally:
            db.close()
        
        base = self.api_endpoint.rstrip('/')
        url = f'{base}/chat/completions' if base.endswith('/v1') else f'{base}/v1/chat/completions'
        print(f'[DETECT-LANG] URL: {url}')
        print(f'[DETECT-LANG] Model: {self.model}')
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'user',
                            'content': [
                                {'type': 'text', 'text': language_detection_prompt},
                                {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image_base64}'}}
                            ]
                        }
                    ],
                    'max_tokens': 10,
                    'temperature': 0.1,
                },
                timeout=self.detect_timeout
            )
            print(f'[DETECT-LANG] Response status: {response.status_code}')
            response.raise_for_status()
            result = response.json()
            print(f'[DETECT-LANG] Response: {result}')
            content = result['choices'][0]['message']['content']
            detected = content.strip().lower()
            print(f'[DETECT-LANG] Raw detected: {detected}')
        except Exception as e:
            print(f'[DETECT-LANG] API error: {e}')
            return 'en'
        
        if detected == 'ja':
            detected = 'jp'
        elif detected == 'zh':
            detected = 'en'
        
        from models.database import LanguagePrompt
        db = SessionLocal()
        try:
            valid_codes = [l.language_code for l in db.query(LanguagePrompt).all()]
            print(f'[DETECT-LANG] Valid codes: {valid_codes}')
        finally:
            db.close()
        
        if detected not in valid_codes:
            print(f'[DETECT-LANG] Invalid code {detected}, fallback to en')
            detected = 'en'
        print(f'[DETECT-LANG] Final: {detected}')
        return detected
    
    def call_vision_model(self, image_base64):
        from models.database import SessionLocal
        db = SessionLocal()
        try:
            prompt = prompts_module.get_ocr_prompt(self.language, db)
        finally:
            db.close()
        
        base = self.api_endpoint.rstrip('/')
        url = f"{base}/chat/completions" if base.endswith('/v1') else f"{base}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ],
            "max_tokens": 4000
        }
        
        last_error = None
        for attempt in range(self.max_ocr_retries + 1):
            try:
                response = requests.post(url, headers=self._get_headers(), json=payload, timeout=self.ocr_timeout)
                response.raise_for_status()
                result = response.json()
            except requests.ConnectionError:
                if USE_CURL_FALLBACK:
                    try:
                        result = self._post_with_curl(url, payload)
                    except Exception as e:
                        last_error = Exception(f"Both requests and curl failed: {e}")
                        continue
                else:
                    last_error = Exception(f"Cannot connect to API at {self.api_endpoint}")
                    continue
            except requests.Timeout:
                last_error = Exception(f"API timeout after 300 seconds")
                continue
            except Exception as e:
                last_error = Exception(f"API call failed: {str(e)}")
                continue
            
            try:
                text = result["choices"][0]["message"]["content"]
            except KeyError:
                last_error = Exception(f"Invalid API response format")
                continue
            
            if self.detect_hallucination(text) and attempt < self.max_ocr_retries:
                continue
            
            return text
        
        raise last_error
    
    def extract_text(self, file_path, file_type):
        if file_type == "pdf":
            images = self.pdf_to_images(file_path)
        else:
            images = [Image.open(file_path)]
        
        all_text = []
        for idx, image in enumerate(images):
            try:
                img_base64 = self.image_to_base64(image)
                text = self.call_vision_model(img_base64)
                all_text.append(f"=== Page {idx + 1} ===\n{text}")
            except Exception as e:
                all_text.append(f"=== Page {idx + 1} ===\nError: {str(e)}")
        
        return "\n\n".join(all_text)
    
    def call_vision_model_stream(self, image_base64, callback):
        from models.database import SessionLocal
        db = SessionLocal()
        try:
            prompt = prompts_module.get_ocr_prompt(self.language, db)
        finally:
            db.close()
        
        base = self.api_endpoint.rstrip('/')
        url = f"{base}/chat/completions" if base.endswith('/v1') else f"{base}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ],
            "max_tokens": 4000,
            "stream": True
        }
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, stream=True, timeout=self.ocr_timeout)
            response.raise_for_status()
            
            full_text = ""
            for line in response.iter_lines():
                if not line:
                    continue
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    data_str = line_text[6:]
                    if data_str == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data_str)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                full_text += content
                                callback(content, full_text)
                    except json.JSONDecodeError:
                        continue
            
            return full_text
        except Exception as e:
            raise Exception(f"Stream API call failed: {str(e)}")
