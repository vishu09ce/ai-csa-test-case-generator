from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from backend.src.database import get_db
from backend.src.models import Project, ProjectState, DocCode
from backend.src.services.upload_service import check_mandatory_uploads
from backend.src.services.generation_service import (
    generate_sap, generate_pra, generate_rtm_stp_utr, generate_asr
)
from backend.src.services.hitl_service import can_advance_state, advance_project_state

router = APIRouter(prefix="/api/projects", tags=["generation"])


@router.post("/{project_id}/start")
async def start_generation(project_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.state != ProjectState.DRAFT:
        raise HTTPException(status_code=400, detail="Generation can only be started from Draft state.")
    if not check_mandatory_uploads(project_id, db):
        raise HTTPException(status_code=400, detail="URS and FRS must be uploaded before generation can begin.")

    advance_project_state(project_id, db)
    db.refresh(project)
    background_tasks.add_task(generate_sap, project_id, project.system_type, db)
    return {"message": "SAP generation started.", "state": project.state}


@router.post("/{project_id}/submit/{doc_code}")
async def submit_for_review(
    project_id: str,
    doc_code: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    doc_code = doc_code.upper()
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    if not can_advance_state(project_id, doc_code, db):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot advance state. All required HITL documents must be uploaded first."
        )

    advance_project_state(project_id, db)
    db.refresh(project)
    new_state = project.state

    # Trigger next generation based on new state
    if new_state == ProjectState.PRA_REVIEW:
        background_tasks.add_task(generate_pra, project_id, project.system_type, db)
    elif new_state == ProjectState.RTM_REVIEW:
        background_tasks.add_task(generate_rtm_stp_utr, project_id, db)
    elif new_state == ProjectState.SUMMARY_REVIEW:
        background_tasks.add_task(generate_asr, project_id, db)

    return {"message": f"Submitted. Project advanced to {new_state}.", "state": new_state}
