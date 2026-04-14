"""
Tests for OCR service configuration.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ocr_service import OCRService


class TestOCRServiceInit:
    """Test OCRService initialization."""

    def test_default_values(self):
        """Service should have default values."""
        service = OCRService()
        assert service.max_ocr_retries >= 0
        assert service.ocr_timeout >= 60
        assert service.detect_timeout >= 30

    def test_custom_model(self):
        """Service should accept custom model."""
        service = OCRService(model="custom-model")
        assert service.model == "custom-model"

    def test_custom_endpoint(self):
        """Service should accept custom endpoint."""
        service = OCRService(endpoint="http://custom:8080")
        assert service.api_endpoint == "http://custom:8080"

    def test_custom_language(self):
        """Service should accept custom language."""
        service = OCRService(language="en")
        assert service.language == "en"

    def test_custom_api_key(self):
        """Service should accept custom API key."""
        service = OCRService(api_key="test-key")
        assert service.api_key == "test-key"

    def test_headers_with_api_key(self):
        """Headers should include Authorization when API key is set."""
        service = OCRService(api_key="test-key")
        headers = service._get_headers()
        assert "Authorization" in headers
        assert "Bearer" in headers["Authorization"]

    def test_headers_without_api_key(self):
        """Headers should not include Authorization without API key."""
        service = OCRService()
        headers = service._get_headers()
        assert "Authorization" not in headers


class TestHallucinationDetection:
    """Test hallucination detection logic."""

    def test_short_text_not_hallucination(self):
        """Short text should not be flagged as hallucination."""
        service = OCRService()
        result = service.detect_hallucination("This is a short text.")
        assert result == False

    def test_empty_text_not_hallucination(self):
        """Empty text should not be flagged."""
        service = OCRService()
        result = service.detect_hallucination("")
        assert result == False

    def test_prompt_markers_detected(self):
        """Prompt markers should be detected as hallucination."""
        service = OCRService()
        # Text containing prompt instruction markers (must be >= 50 chars)
        text = "段落合并规则非常重要，内容要求必须严格遵守，绝不可重复输出内容，不要输出HTML标签格式。" + "正常内容填充" * 5
        result = service.detect_hallucination(text)
        assert result == True

    def test_hallucination_detection_works(self):
        """Hallucination detection should run without errors."""
        service = OCRService()
        # Just verify the function runs and returns a boolean
        text = "Some random text content that is long enough to pass the minimum length check threshold."
        result = service.detect_hallucination(text)
        assert isinstance(result, bool)

    def test_repetitive_chars_detected(self):
        """Highly repetitive characters should be flagged."""
        service = OCRService()
        # Create text with very low character diversity (repeating same chars)
        text = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" * 3
        result = service.detect_hallucination(text)
        # This should be flagged due to low unique char ratio
        assert result == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])