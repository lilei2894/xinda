import requests
import subprocess
import json
import platform
import os
import re
import time
from collections import Counter
from services import prompts as prompts_module

USE_CURL_FALLBACK = platform.system() == 'Darwin'

class TranslateService:
    def __init__(self, model=None, endpoint=None, language=None, api_key=None):
        self.api_endpoint = endpoint or os.getenv("OLLAMA_ENDPOINT", "http://172.25.249.20:30000")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3.5-uncensored-35B")
        self.language = language or "jp"
        self.api_key = api_key
        self.max_translate_retries = int(os.getenv("TRANSLATE_MAX_RETRIES", "2"))
        self.translate_timeout = int(os.getenv("TRANSLATE_TIMEOUT", "300"))
        self.title_timeout = int(os.getenv("TRANSLATE_TITLE_TIMEOUT", "60"))
    
    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _post_with_curl(self, url, payload, timeout=None):
        if timeout is None:
            timeout = self.translate_timeout
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
    
    def _contains_source_language(self, text):
        if self.language == "jp":
            return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text))
        elif self.language == "en":
            return bool(re.search(r'[a-zA-Z]{4,}', text))
        return False
    
    def _contains_instruction_markers(self, text):
        markers = ['【', '】', '绝对禁止', '必须遵守', '待翻译文本', '请将以下', '规则：', '规则1', 'Paragraph Merging', 'Content Requirements']
        count = sum(1 for m in markers if m in text)
        return count >= 2
    
    def _clean_translation_output(self, text):
        text = re.sub(r'^【.*?】\s*\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n?【.*?】\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^规则[：:].*?\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\..*?\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[-•*]\s.*?\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'^待翻译文本[：:]\s*\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'^翻译结果[：:]\s*\n?', '', text, flags=re.MULTILINE)
        text = re.sub(r'^译文[：:]\s*\n?', '', text, flags=re.MULTILINE)
        text = text.strip()
        return text
    
    def _detect_hallucination(self, text):
        if not text or len(text) < 50:
            return False
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if len(lines) < 3:
            return False
        
        n = 3
        ngrams = []
        for i in range(len(lines) - n + 1):
            ngram = '\n'.join(lines[i:i+n])
            ngrams.append(ngram)
        
        if not ngrams:
            return False
        
        counter = Counter(ngrams)
        most_common_count = counter.most_common(1)[0][1]
        
        repetition_ratio = most_common_count / len(ngrams) if ngrams else 0
        
        unique_chars = len(set(text))
        total_chars = len(text)
        char_ratio = unique_chars / total_chars if total_chars > 0 else 1.0
        
        if repetition_ratio > 0.3:
            return True
        
        if char_ratio < 0.15:
            return True
        
        return False
    
    def translate_to_chinese(self, source_text):
        from models.database import SessionLocal
        db = SessionLocal()
        try:
            prompt = prompts_module.get_translate_prompt(self.language, db)
        finally:
            db.close()
        
        base = self.api_endpoint.rstrip('/')
        url = f"{base}/chat/completions" if base.endswith('/v1') else f"{base}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": source_text}
            ],
            "max_tokens": 4000
        }
        
        last_error = None
        for attempt in range(self.max_translate_retries + 1):
            try:
                response = requests.post(url, headers=self._get_headers(), json=payload, timeout=self.translate_timeout)
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
                last_error = Exception(f"Translation timeout after 300 seconds")
                continue
            except Exception as e:
                last_error = Exception(f"Translation failed: {str(e)}")
                continue
            
            try:
                text = result["choices"][0]["message"]["content"].strip()
            except KeyError:
                last_error = Exception(f"Invalid API response format")
                continue
            
            text = self._clean_translation_output(text)
            
            if self._contains_instruction_markers(text) and attempt < self.max_translate_retries:
                continue
            
            if self._contains_source_language(text) and attempt < self.max_translate_retries:
                continue
            
            if self._detect_hallucination(text) and attempt < self.max_translate_retries:
                continue
            
            return text
        
        raise last_error
    
    def generate_title(self, text, use_translated=True):
        if not text or len(text) < 20:
            return None
        
        sample_text = text[:2000] if len(text) > 2000 else text
        
        try:
            base = self.api_endpoint.rstrip('/')
            url = f"{base}/chat/completions" if base.endswith('/v1') else f"{base}/v1/chat/completions"
            
            if use_translated:
                prompt_content = f"请根据以下文档内容，生成一个简短的标题（不超过20个字），仅输出标题，不要任何解释：\n\n{sample_text}"
            else:
                prompt_content = f"请根据以下OCR识别的外语文档内容，生成一个简短的标题（不超过20个字），仅输出标题，不要任何解释：\n\n{sample_text}"
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt_content
                        }
                    ],
                    "max_tokens": 50
                },
                timeout=self.title_timeout
            )
            response.raise_for_status()
            result = response.json()
            title = result["choices"][0]["message"]["content"].strip()
            title = re.sub(r'^["「『]|["」』]$', '', title)
            if len(title) > 30:
                title = title[:30]
            return title
        except Exception:
            return None
    
    def generate_title_from_ocr_fallback(self, ocr_text):
        if not ocr_text:
            return None
        lines = ocr_text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line and len(line) > 2 and len(line) <= 100:
                if i == 0:
                    continue
                return line
        return None
    
    def translate_to_chinese_stream(self, source_text, callback):
        from models.database import SessionLocal
        db = SessionLocal()
        try:
            prompt = prompts_module.get_translate_prompt(self.language, db)
        finally:
            db.close()
        
        base = self.api_endpoint.rstrip('/')
        url = f"{base}/chat/completions" if base.endswith('/v1') else f"{base}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": source_text}
            ],
            "max_tokens": 4000,
            "stream": True
        }
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, stream=True, timeout=self.translate_timeout)
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
                                time.sleep(0.05)
                    except json.JSONDecodeError:
                        continue
            
            return self._clean_translation_output(full_text)
        except Exception as e:
            raise Exception(f"Stream translation failed: {str(e)}")
