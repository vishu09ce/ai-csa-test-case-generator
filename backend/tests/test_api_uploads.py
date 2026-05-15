import io
import pytest
from docx import Document


def _make_docx_bytes(text: str = "Sample requirement content") -> bytes:
    doc = Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _make_pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 << /Type /Font "
        b"/Subtype /Type1 /BaseFont /Helvetica >> >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 100 700 Td "
        b"(Hello) Tj ET\nendstream\nendobj\nxref\n0 5\n"
        b"0000000000 65535 f \ntrailer\n<< /Size 5 /Root 1 0 R >>\n"
        b"startxref\n0\n%%EOF"
    )


def test_upload_urs_docx(client, project):
    resp = client.post(
        f"/api/projects/{project['id']}/upload/source",
        data={"doc_type": "URS"},
        files={"file": ("urs.docx", _make_docx_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert resp.status_code == 200
    assert resp.json()["doc_type"] == "URS"


def test_upload_frs_docx(client, project):
    resp = client.post(
        f"/api/projects/{project['id']}/upload/source",
        data={"doc_type": "FRS"},
        files={"file": ("frs.docx", _make_docx_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert resp.status_code == 200
    assert resp.json()["doc_type"] == "FRS"


def test_upload_brd_docx(client, project):
    resp = client.post(
        f"/api/projects/{project['id']}/upload/source",
        data={"doc_type": "BRD"},
        files={"file": ("brd.docx", _make_docx_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert resp.status_code == 200
    assert resp.json()["doc_type"] == "BRD"


def test_upload_invalid_extension_rejected(client, project):
    resp = client.post(
        f"/api/projects/{project['id']}/upload/source",
        data={"doc_type": "URS"},
        files={"file": ("urs.txt", b"plain text", "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_to_nonexistent_project(client):
    resp = client.post(
        "/api/projects/bad-id/upload/source",
        data={"doc_type": "URS"},
        files={"file": ("urs.docx", _make_docx_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert resp.status_code == 404


def test_upload_replaces_existing_source(client, project):
    file_data = _make_docx_bytes("Version 1")
    client.post(
        f"/api/projects/{project['id']}/upload/source",
        data={"doc_type": "URS"},
        files={"file": ("urs.docx", file_data, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    file_data_v2 = _make_docx_bytes("Version 2")
    resp = client.post(
        f"/api/projects/{project['id']}/upload/source",
        data={"doc_type": "URS"},
        files={"file": ("urs_v2.docx", file_data_v2, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert resp.status_code == 200
    assert resp.json()["file_name"] == "urs_v2.docx"
