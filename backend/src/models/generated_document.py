import uuid
from enum import Enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.src.models.base import Base


class DocCode(str, Enum):
    SAP = "SAP"
    PRA = "PRA"
    RTM = "RTM"
    STP = "STP"
    UTR = "UTR"
    ASR = "ASR"


class DocumentStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    GENERATING = "GENERATING"
    AI_COMPLETE = "AI_COMPLETE"
    IN_REVIEW = "IN_REVIEW"
    HITL_COMPLETE = "HITL_COMPLETE"


class GeneratedDocument(Base):
    __tablename__ = "generated_documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"), nullable=False)
    doc_code: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default=DocumentStatus.NOT_STARTED)
    ai_pdf_path: Mapped[str | None] = mapped_column(String, nullable=True)
    word_path: Mapped[str | None] = mapped_column(String, nullable=True)
    hitl_pdf_path: Mapped[str | None] = mapped_column(String, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    hitl_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    generated_content: Mapped[dict | None] = mapped_column(JSON, nullable=True)
