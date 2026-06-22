"""Document parsing and OCR tool stubs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from config.settings import get_settings


def parse_document(file_path: str, max_pages: int | None = None) -> dict[str, Any]:
    """Parse a PDF or plain-text file into structured content."""
    settings = get_settings()
    path = Path(file_path)
    page_limit = max_pages if max_pages is not None else settings.max_pdf_pages

    if not path.exists():
        return {
            "text": "",
            "page_count": 0,
            "metadata": {"title": None, "error": f"File not found: {file_path}"},
        }

    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="replace")
        return {
            "text": text,
            "page_count": 1,
            "metadata": {"title": path.stem, "content_type": "text/plain"},
        }

    return {
        "text": (
            f"[stub] Parsed document placeholder for {path.name}. "
            f"Production implementation will use pypdf/pdfplumber (max {page_limit} pages)."
        ),
        "page_count": min(2, page_limit),
        "metadata": {"title": path.stem, "content_type": "application/pdf"},
    }


def ocr_document(file_path: str, language: str = "deu") -> dict[str, Any]:
    """OCR stub for scanned PDFs and images."""
    path = Path(file_path)
    if not path.exists():
        return {
            "text": "",
            "confidence": 0.0,
            "error": f"File not found: {file_path}",
        }

    return {
        "text": (
            f"[stub] OCR output for {path.name} (language={language}). "
            "Production implementation will use pytesseract."
        ),
        "confidence": 0.95,
    }
