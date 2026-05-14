from fastapi import UploadFile, HTTPException
import pypdf
import io

ALLOWED_EXTENSIONS = {".docx", ".pdf"}
MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def validate_extension(filename: str) -> str:
    lower = filename.lower()
    for ext in ALLOWED_EXTENSIONS:
        if lower.endswith(ext):
            return ext
    raise HTTPException(
        status_code=400,
        detail="Unsupported file format. Please upload a .docx or text-based .pdf file."
    )


async def validate_file_size(file: UploadFile) -> bytes:
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE_MB}MB."
        )
    return content


def validate_pdf_is_text_based(content: bytes) -> None:
    try:
        reader = pypdf.PdfReader(io.BytesIO(content))
        if len(reader.pages) == 0:
            raise HTTPException(status_code=400, detail="PDF file appears to be empty or corrupted.")
        # A scanned PDF has no extractable text across all pages
        text = "".join(
            page.extract_text() or "" for page in reader.pages
        )
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Scanned or image-based PDFs are not supported. Please upload a text-based PDF or convert to Word format."
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read PDF file. The file may be corrupted or password-protected."
        )


async def validate_upload(file: UploadFile) -> tuple[bytes, str]:
    ext = validate_extension(file.filename)
    content = await validate_file_size(file)
    if ext == ".pdf":
        validate_pdf_is_text_based(content)
    return content, ext
