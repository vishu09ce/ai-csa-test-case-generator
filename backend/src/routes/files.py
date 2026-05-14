import os
import zipfile
import tempfile
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.src.database import get_db
from backend.src.models import Project, ProjectState, GeneratedDocument
from backend.src.utils.file_store import get_project_dir, zip_package_path

router = APIRouter(prefix="/api/projects", tags=["files"])


@router.get("/{project_id}/files/{file_name}")
def download_file(project_id: str, file_name: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Prevent path traversal attacks
    safe_name = os.path.basename(file_name)
    project_dir = get_project_dir(project_id)
    file_path = os.path.join(project_dir, safe_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(path=file_path, filename=safe_name)


@router.get("/{project_id}/package")
def download_package(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.state != ProjectState.COMPLETE:
        raise HTTPException(status_code=400, detail="ZIP package is only available when the project is Complete.")

    docs = db.query(GeneratedDocument).filter(GeneratedDocument.project_id == project_id).all()
    package_path = zip_package_path(project_id)

    with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for doc in docs:
            if doc.ai_pdf_path and os.path.exists(doc.ai_pdf_path):
                zf.write(doc.ai_pdf_path, os.path.basename(doc.ai_pdf_path))
            if doc.hitl_pdf_path and os.path.exists(doc.hitl_pdf_path):
                zf.write(doc.hitl_pdf_path, os.path.basename(doc.hitl_pdf_path))

    return FileResponse(
        path=package_path,
        filename=os.path.basename(package_path),
        media_type="application/zip"
    )
