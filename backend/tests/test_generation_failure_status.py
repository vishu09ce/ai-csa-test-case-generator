import pytest
from unittest.mock import AsyncMock, patch

from backend.src.services.generation_service import generate_sap
from backend.src.models import GeneratedDocument, GenerationJob, DocumentStatus, JobStatus, DocCode


@pytest.mark.asyncio
async def test_failed_generation_resets_document_and_records_error(db, project):
    project_id = project["id"]
    with patch("backend.src.services.generation_service.extract_content", return_value={}), \
         patch("backend.src.services.generation_service.build_sap_prompt", return_value="prompt"), \
         patch("backend.src.services.generation_service.call_llm",
               new=AsyncMock(side_effect=RuntimeError("PDF conversion failed: no converter"))):
        with pytest.raises(RuntimeError):
            await generate_sap(project_id, "LIMS", db)

    doc = db.query(GeneratedDocument).filter_by(project_id=project_id, doc_code=DocCode.SAP).one()
    job = db.query(GenerationJob).filter_by(project_id=project_id, doc_code=DocCode.SAP).one()

    assert doc.status == DocumentStatus.NOT_STARTED
    assert job.status == JobStatus.FAILED
    assert "no converter" in job.error_message


@pytest.mark.asyncio
async def test_status_endpoint_reports_failed_job_error(client, db, project):
    project_id = project["id"]
    with patch("backend.src.services.generation_service.extract_content", return_value={}), \
         patch("backend.src.services.generation_service.build_sap_prompt", return_value="prompt"), \
         patch("backend.src.services.generation_service.call_llm",
               new=AsyncMock(side_effect=RuntimeError("LLM down"))):
        with pytest.raises(RuntimeError):
            await generate_sap(project_id, "LIMS", db)

    body = client.get(f"/api/projects/{project_id}/status").json()
    sap = next(d for d in body["documents"] if d["doc_code"] == "SAP")
    assert sap["status"] != "GENERATING"
    assert body["active_jobs"][0]["status"] == "FAILED"
    assert body["active_jobs"][0]["error"] == "LLM down"
