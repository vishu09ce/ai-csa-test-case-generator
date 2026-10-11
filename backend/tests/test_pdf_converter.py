import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from backend.src.services import pdf_converter
from backend.src.services.pdf_converter import convert_to_pdf


@pytest.fixture
def word_file(tmp_path):
    path = tmp_path / "SAP_report.docx"
    path.write_bytes(b"fake docx")
    return str(path)


def _fake_soffice_run(args, **kwargs):
    """Simulate LibreOffice writing <name>.pdf into the --outdir folder."""
    out_dir = args[args.index("--outdir") + 1]
    base = os.path.splitext(os.path.basename(args[-1]))[0]
    with open(os.path.join(out_dir, base + ".pdf"), "wb") as f:
        f.write(b"%PDF-fake")
    return MagicMock(returncode=0, stdout="", stderr="")


def test_missing_word_file_raises(tmp_path):
    with pytest.raises(HTTPException) as exc:
        convert_to_pdf(str(tmp_path / "missing.docx"), str(tmp_path / "out.pdf"))
    assert "Word file not found" in exc.value.detail


def test_uses_libreoffice_when_available(word_file, tmp_path):
    pdf_path = str(tmp_path / "SAP_ai.pdf")
    with patch.object(pdf_converter.shutil, "which", return_value="/usr/bin/soffice"), \
         patch.object(pdf_converter.subprocess, "run", side_effect=_fake_soffice_run) as run, \
         patch.object(pdf_converter, "_convert_with_docx2pdf") as docx2pdf:
        convert_to_pdf(word_file, pdf_path)

    args = run.call_args[0][0]
    assert args[:4] == ["/usr/bin/soffice", "--headless", "--convert-to", "pdf"]
    assert os.path.exists(pdf_path)
    docx2pdf.assert_not_called()


def test_libreoffice_failure_raises_http_exception(word_file, tmp_path):
    failed = MagicMock(returncode=1, stdout="", stderr="boom")
    with patch.object(pdf_converter.shutil, "which", return_value="/usr/bin/soffice"), \
         patch.object(pdf_converter.subprocess, "run", return_value=failed):
        with pytest.raises(HTTPException) as exc:
            convert_to_pdf(word_file, str(tmp_path / "out.pdf"))
    assert "PDF conversion failed" in exc.value.detail
    assert "boom" in exc.value.detail


def test_falls_back_to_docx2pdf_without_libreoffice(word_file, tmp_path):
    pdf_path = str(tmp_path / "out.pdf")
    with patch.object(pdf_converter.shutil, "which", return_value=None), \
         patch.object(pdf_converter, "_convert_with_docx2pdf") as docx2pdf:
        convert_to_pdf(word_file, pdf_path)
    docx2pdf.assert_called_once_with(word_file, pdf_path)
