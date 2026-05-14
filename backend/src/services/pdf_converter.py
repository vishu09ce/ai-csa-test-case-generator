import os
from docx2pdf import convert
from fastapi import HTTPException


def convert_to_pdf(word_path: str, pdf_path: str) -> None:
    if not os.path.exists(word_path):
        raise HTTPException(status_code=500, detail=f"Word file not found for PDF conversion: {word_path}")
    try:
        convert(word_path, pdf_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF conversion failed: {str(e)}")
