from datetime import datetime, timezone
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from backend.src.models import (
    Project, GeneratedDocument, DocumentStatus, ProjectState, DocCode
)
from backend.src.utils.file_validator import validate_upload
from backend.src.utils.file_store import hitl_pdf_path, stp_exec_hitl_pdf_path, save_file
from backend.src.services.pdf_converter import convert_to_pdf
import tempfile
import os

# Maps each doc code to the state the project must be in for that HITL upload
HITL_STATE_MAP = {
    DocCode.SAP: ProjectState.SAP_REVIEW,
    DocCode.PRA: ProjectState.PRA_REVIEW,
    DocCode.RTM: ProjectState.RTM_REVIEW,
    DocCode.STP: ProjectState.PROTOCOL_REVIEW,
    DocCode.UTR: ProjectState.PROTOCOL_REVIEW,
    DocCode.ASR: ProjectState.SUMMARY_REVIEW,
}

# Maps each HITL completion to the documents that must also be complete before state advances
JOINT_GATE = {
    DocCode.STP: DocCode.UTR,
    DocCode.UTR: DocCode.STP,
}


async def handle_hitl_upload(
    project_id: str,
    doc_code: str,
    file: UploadFile,
    db: Session
) -> GeneratedDocument:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    expected_state = HITL_STATE_MAP.get(doc_code)
    if project.state != expected_state:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot upload {doc_code} HITL file. Project must be in {expected_state} state."
        )

    doc_record = db.query(GeneratedDocument).filter(
        GeneratedDocument.project_id == project_id,
        GeneratedDocument.doc_code == doc_code
    ).first()
    if not doc_record or doc_record.status == DocumentStatus.NOT_STARTED:
        raise HTTPException(status_code=400, detail=f"{doc_code} has not been generated yet.")

    content, ext = await validate_upload(file)
    if ext != ".docx":
        raise HTTPException(status_code=400, detail="HITL upload must be a .docx Word file.")

    # Save the uploaded Word file to a temp location then convert to HITL PDF
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        pdf_path = hitl_pdf_path(project_id, doc_code)
        convert_to_pdf(tmp_path, pdf_path)
    finally:
        os.unlink(tmp_path)

    doc_record.hitl_pdf_path = pdf_path
    doc_record.hitl_uploaded_at = datetime.now(timezone.utc)
    doc_record.status = DocumentStatus.HITL_COMPLETE
    db.commit()
    db.refresh(doc_record)

    return doc_record


def can_advance_state(project_id: str, doc_code: str, db: Session) -> bool:
    # For joint gates (STP + UTR), both must be HITL_COMPLETE before advancing
    partner = JOINT_GATE.get(doc_code)
    if partner:
        partner_record = db.query(GeneratedDocument).filter(
            GeneratedDocument.project_id == project_id,
            GeneratedDocument.doc_code == partner
        ).first()
        if not partner_record or partner_record.status != DocumentStatus.HITL_COMPLETE:
            return False
    return True


def advance_project_state(project_id: str, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    try:
        project.advance_state()
        db.commit()
        db.refresh(project)
        return project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
