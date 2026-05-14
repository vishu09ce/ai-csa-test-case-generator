from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.src.models import SourceDocument, SourceDocType, Project, ProjectState
from backend.src.utils.file_validator import validate_upload
from backend.src.utils.file_parser import parse_document
from backend.src.utils.file_store import source_file_path, save_file


MANDATORY_DOCS = {SourceDocType.URS, SourceDocType.FRS}


async def handle_source_upload(
    project_id: str,
    doc_type: str,
    file: UploadFile,
    db: Session
) -> SourceDocument:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.state != ProjectState.DRAFT:
        raise HTTPException(status_code=400, detail="Source documents can only be uploaded while the project is in Draft state.")

    if doc_type not in SourceDocType.__members__:
        raise HTTPException(status_code=400, detail=f"Invalid document type. Must be one of: {', '.join(SourceDocType.__members__)}.")

    content, ext = await validate_upload(file)
    extracted_text = parse_document(content, ext)

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Document appears to contain no readable text.")

    path = source_file_path(project_id, doc_type, ext)
    await save_file(path, content)

    existing = db.query(SourceDocument).filter(
        SourceDocument.project_id == project_id,
        SourceDocument.doc_type == doc_type
    ).first()

    if existing:
        existing.file_name = file.filename
        existing.file_path = path
        existing.uploaded_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    record = SourceDocument(
        project_id=project_id,
        doc_type=doc_type,
        file_name=file.filename,
        file_path=path
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def check_mandatory_uploads(project_id: str, db: Session) -> bool:
    uploaded = {
        row.doc_type for row in
        db.query(SourceDocument).filter(SourceDocument.project_id == project_id).all()
    }
    return MANDATORY_DOCS.issubset(uploaded)
