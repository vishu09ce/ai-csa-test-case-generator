import io
import pypdf
import docx
from fastapi import HTTPException


def parse_docx(content: bytes) -> str:
    try:
        doc = docx.Document(io.BytesIO(content))
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read Word file. The file may be corrupted or in an unsupported format."
        )


def parse_pdf(content: bytes) -> str:
    try:
        reader = pypdf.PdfReader(io.BytesIO(content))
        return "\n".join(
            page.extract_text() or "" for page in reader.pages
        ).strip()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read PDF file. The file may be corrupted or password-protected."
        )


def parse_document(content: bytes, ext: str) -> str:
    if ext == ".docx":
        return parse_docx(content)
    if ext == ".pdf":
        return parse_pdf(content)
    raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")
