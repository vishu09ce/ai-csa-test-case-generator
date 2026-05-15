from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.src.database import get_db
from backend.src.models import Project, GeneratedDocument, GenerationJob

router = APIRouter(prefix="/api/projects", tags=["status"])


@router.get("/{project_id}/status")
def get_project_status(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    docs = db.query(GeneratedDocument).filter(
        GeneratedDocument.project_id == project_id
    ).all()

    jobs = db.query(GenerationJob).filter(
        GenerationJob.project_id == project_id
    ).order_by(GenerationJob.started_at.desc()).all()

    return {
        "project_id": project_id,
        "state": project.state,
        "documents": [
            {
                "doc_code": d.doc_code,
                "status": d.status,
                "generated_at": d.generated_at,
                "hitl_uploaded_at": d.hitl_uploaded_at,
                "has_ai_pdf": bool(d.ai_pdf_path),
                "has_word": bool(d.word_path),
                "has_hitl_pdf": bool(d.hitl_pdf_path),
            }
            for d in docs
        ],
        "active_jobs": [
            {
                "doc_code": j.doc_code,
                "status": j.status,
                "started_at": j.started_at,
                "completed_at": j.completed_at,
                "error": j.error_message,
                "total_requirements": j.total_requirements,
                "completed_requirements": j.completed_requirements,
            }
            for j in jobs[:5]
        ],
    }
