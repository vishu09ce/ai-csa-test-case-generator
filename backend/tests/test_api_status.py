import pytest


def test_status_not_found(client):
    resp = client.get("/api/projects/nonexistent/status")
    assert resp.status_code == 404


def test_status_fresh_project(client, project):
    resp = client.get(f"/api/projects/{project['id']}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_id"] == project["id"]
    assert data["state"] == "DRAFT"
    assert data["documents"] == []
    assert data["active_jobs"] == []


def test_status_reflects_state_after_upload(client, project):
    import io
    from docx import Document

    def make_docx():
        doc = Document()
        doc.add_paragraph("Requirement content")
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    for doc_type in ("URS", "FRS", "BRD"):
        client.post(
            f"/api/projects/{project['id']}/upload/source",
            data={"doc_type": doc_type},
            files={"file": (f"{doc_type.lower()}.docx", make_docx(),
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )

    resp = client.get(f"/api/projects/{project['id']}/status")
    assert resp.status_code == 200
    assert resp.json()["state"] == "DRAFT"
