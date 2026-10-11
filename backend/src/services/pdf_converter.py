import os
import shutil
import subprocess
import tempfile
from fastapi import HTTPException

LIBREOFFICE_TIMEOUT_SECONDS = 120


def _find_libreoffice() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def _convert_with_libreoffice(soffice: str, word_path: str, pdf_path: str) -> None:
    # LibreOffice names the output after the input file, so convert into a
    # temp folder and then move the result to the requested pdf_path.
    with tempfile.TemporaryDirectory() as out_dir:
        result = subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", out_dir, word_path],
            capture_output=True,
            text=True,
            timeout=LIBREOFFICE_TIMEOUT_SECONDS,
        )
        base_name = os.path.splitext(os.path.basename(word_path))[0]
        produced = os.path.join(out_dir, base_name + ".pdf")
        if result.returncode != 0 or not os.path.exists(produced):
            raise RuntimeError(f"LibreOffice error: {(result.stderr or result.stdout).strip()}")
        shutil.move(produced, pdf_path)


def _convert_with_docx2pdf(word_path: str, pdf_path: str) -> None:
    from docx2pdf import convert
    convert(word_path, pdf_path)


def convert_to_pdf(word_path: str, pdf_path: str) -> None:
    if not os.path.exists(word_path):
        raise HTTPException(status_code=500, detail=f"Word file not found for PDF conversion: {word_path}")
    try:
        soffice = _find_libreoffice()
        if soffice:
            _convert_with_libreoffice(soffice, word_path, pdf_path)
        else:
            _convert_with_docx2pdf(word_path, pdf_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF conversion failed: {str(e)}")
