from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from backend.src.database import get_db
from backend.src.models import Project, ProjectState, GeneratedDocument, SourceDocument

router = APIRouter(prefix="/api/projects", tags=["projects"])

VALID_SYSTEM_TYPES = {"MES", "LIMS", "QMS", "CAPA", "DMS", "LMS", "ERP"}


class ProjectCreate(BaseModel):
    name: str
    system_type: str

    @field_validator("system_type")
    @classmethod
    def validate_system_type(cls, v: str) -> str:
        if v.upper() not in VALID_SYSTEM_TYPES:
            raise ValueError(f"Invalid system type. Must be one of: {', '.join(VALID_SYSTEM_TYPES)}")
        return v.upper()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Project name cannot be empty.")
        if len(v) > 200:
            raise ValueError("Project name cannot exceed 200 characters.")
        return v


class ProjectUpdate(BaseModel):
    name: str | None = None
    system_type: str | None = None


@router.post("")
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=payload.name, system_type=payload.system_type)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("")
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    docs = db.query(GeneratedDocument).filter(GeneratedDocument.project_id == project_id).all()
    sources = db.query(SourceDocument).filter(SourceDocument.project_id == project_id).all()
    return {"project": project, "documents": docs, "source_documents": sources}


@router.patch("/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if not project.is_editable():
        raise HTTPException(status_code=400, detail="Project can only be edited in Draft state.")
    if payload.name:
        project.name = payload.name.strip()
    if payload.system_type:
        if payload.system_type.upper() not in VALID_SYSTEM_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid system type.")
        project.system_type = payload.system_type.upper()
    db.commit()
    db.refresh(project)
    return project
