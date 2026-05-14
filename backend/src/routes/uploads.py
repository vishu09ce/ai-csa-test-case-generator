from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.src.database import get_db
from backend.src.services.upload_service import handle_source_upload
from backend.src.services.hitl_service import handle_hitl_upload

router = APIRouter(prefix="/api/projects", tags=["uploads"])


@router.post("/{project_id}/upload/source")
async def upload_source_document(
    project_id: str,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await handle_source_upload(project_id, doc_type.upper(), file, db)


@router.post("/{project_id}/upload/hitl/{doc_code}")
async def upload_hitl_document(
    project_id: str,
    doc_code: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await handle_hitl_upload(project_id, doc_code.upper(), file, db)
