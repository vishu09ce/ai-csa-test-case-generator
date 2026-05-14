import pytest
from fastapi import HTTPException
from backend.src.utils.file_validator import validate_extension, validate_pdf_is_text_based


def test_valid_docx_extension():
    assert validate_extension("document.docx") == ".docx"


def test_valid_pdf_extension():
    assert validate_extension("document.pdf") == ".pdf"


def test_invalid_extension_raises():
    with pytest.raises(HTTPException) as exc:
        validate_extension("document.xlsx")
    assert exc.value.status_code == 400
    assert "Unsupported file format" in exc.value.detail


def test_uppercase_extension_accepted():
    assert validate_extension("DOCUMENT.DOCX") == ".docx"


def test_scanned_pdf_raises():
    # Minimal valid PDF with no text content
    empty_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF"
    with pytest.raises(HTTPException) as exc:
        validate_pdf_is_text_based(empty_pdf)
    assert exc.value.status_code == 400
    assert "Scanned" in exc.value.detail


def test_invalid_pdf_bytes_raises():
    with pytest.raises(HTTPException) as exc:
        validate_pdf_is_text_based(b"this is not a pdf")
    assert exc.value.status_code == 400
