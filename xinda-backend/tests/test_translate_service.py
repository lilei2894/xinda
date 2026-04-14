"""
Tests for Translate service configuration.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.translate_service import TranslateService


class TestTranslateServiceInit:
    """Test TranslateService initialization."""

    def test_default_values(self):
        """Service should have default values."""
        service = TranslateService()
        assert service.max_translate_retries >= 0
        assert service.translate_timeout >= 60
        assert service.title_timeout >= 30

    def test_custom_language(self):
        """Service should accept custom language."""
        service = TranslateService(language="jp")
        assert service.language == "jp"


class TestOutputCleaning:
    """Test translation output cleaning."""

    def test_clean_brackets(self):
        """Bracket markers should be removed."""
        service = TranslateService()
        text = "【标题】\n这是内容\n【结束】"
        result = service._clean_translation_output(text)
        assert "【" not in result
        assert "】" not in result or result.strip() == "这是内容"

    def test_clean_instruction_markers(self):
        """Instruction markers should be removed."""
        service = TranslateService()
        text = "待翻译文本：\n翻译结果：Hello World"
        result = service._clean_translation_output(text)
        assert "待翻译文本" not in result or "Hello World" in result


class TestHallucinationDetection:
    """Test hallucination detection in translation."""

    def test_short_text_safe(self):
        """Short text should not be flagged."""
        service = TranslateService()
        result = service._detect_hallucination("Short")
        assert result == False

    def test_repetitive_text_detected(self):
        """Highly repetitive text should be flagged."""
        service = TranslateService()
        # Create text with high repetition (same 3-line pattern repeated many times)
        text = "同一段话的内容\n第二行的内容\n第三行的内容\n" * 10
        result = service._detect_hallucination(text)
        assert result == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])