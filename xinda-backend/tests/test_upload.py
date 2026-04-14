"""
Tests for file upload validation.
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers.upload import sanitize_filename, MAX_FILE_SIZE, MAX_PDF_PAGES, ALLOWED_EXTENSIONS


class TestSanitizeFilename:
    """Test filename sanitization to prevent path traversal."""

    def test_normal_filename(self):
        """Normal filename should pass through unchanged."""
        result = sanitize_filename("document.pdf")
        assert result == "document.pdf"

    def test_filename_with_spaces(self):
        """Filename with spaces should be converted."""
        result = sanitize_filename("my document.pdf")
        assert " " not in result
        assert ".pdf" in result

    def test_path_traversal_slash(self):
        """Path traversal with slash should be blocked."""
        result = sanitize_filename("../../etc/passwd.pdf")
        assert "/" not in result or result == "_.._.._etc_passwd.pdf"

    def test_path_traversal_backslash(self):
        """Path traversal with backslash should be blocked."""
        result = sanitize_filename("..\\..\\etc\\passwd.pdf")
        assert "\\" not in result

    def test_null_byte(self):
        """Null byte should be removed."""
        result = sanitize_filename("doc\x00ument.pdf")
        assert "\x00" not in result

    def test_chinese_filename(self):
        """Chinese characters should be preserved."""
        result = sanitize_filename("中文文档.pdf")
        assert "中文" in result or "中" in result
        assert ".pdf" in result

    def test_empty_filename(self):
        """Empty filename should get default value."""
        result = sanitize_filename("")
        assert result == "unnamed_file"

    def test_long_filename(self):
        """Long filename should be truncated."""
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name)
        assert len(result) <= 200

    def test_special_characters(self):
        """Special characters should be replaced."""
        result = sanitize_filename("file<>:\"|?.pdf")
        # Special chars should be replaced with underscore
        assert "<" not in result
        assert ">" not in result


class TestConfiguration:
    """Test configuration values."""

    def test_max_file_size_reasonable(self):
        """Max file size should be reasonable (>= 10MB)."""
        assert MAX_FILE_SIZE >= 10 * 1024 * 1024

    def test_max_pdf_pages_reasonable(self):
        """Max PDF pages should be reasonable (>= 100)."""
        assert MAX_PDF_PAGES >= 100

    def test_allowed_extensions(self):
        """Allowed extensions should include pdf and jpg."""
        assert ".pdf" in ALLOWED_EXTENSIONS
        assert ".jpg" in ALLOWED_EXTENSIONS
        assert ".jpeg" in ALLOWED_EXTENSIONS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])