import pytest


def test_create_project(client):
    resp = client.post("/api/projects", json={"name": "My LIMS", "system_type": "LIMS"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "My LIMS"
    assert data["system_type"] == "LIMS"
    assert data["state"] == "DRAFT"


def test_create_project_normalises_system_type(client):
    resp = client.post("/api/projects", json={"name": "QMS Project", "system_type": "qms"})
    assert resp.status_code == 200
    assert resp.json()["system_type"] == "QMS"


def test_create_project_invalid_system_type(client):
    resp = client.post("/api/projects", json={"name": "Bad Type", "system_type": "XYZ"})
    assert resp.status_code == 422


def test_create_project_empty_name(client):
    resp = client.post("/api/projects", json={"name": "   ", "system_type": "LIMS"})
    assert resp.status_code == 422


def test_create_project_name_too_long(client):
    resp = client.post("/api/projects", json={"name": "A" * 201, "system_type": "LIMS"})
    assert resp.status_code == 422


def test_list_projects_empty(client):
    resp = client.get("/api/projects")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_projects_returns_created(client, project):
    resp = client.get("/api/projects")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["id"] == project["id"]


def test_get_project(client, project):
    resp = client.get(f"/api/projects/{project['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project"]["id"] == project["id"]
    assert data["documents"] == []
    assert data["source_documents"] == []


def test_get_project_not_found(client):
    resp = client.get("/api/projects/nonexistent-id")
    assert resp.status_code == 404


def test_update_project_name(client, project):
    resp = client.patch(f"/api/projects/{project['id']}", json={"name": "Updated Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


def test_update_project_not_editable_after_draft(client, project, db):
    from backend.src.models.project import Project, ProjectState
    p = db.query(Project).filter(Project.id == project["id"]).first()
    p.state = ProjectState.SAP_REVIEW
    db.commit()

    resp = client.patch(f"/api/projects/{project['id']}", json={"name": "No Change"})
    assert resp.status_code == 400


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
