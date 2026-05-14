import uuid
from enum import Enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from backend.src.models.base import Base


class ProjectState(str, Enum):
    DRAFT = "DRAFT"
    SAP_REVIEW = "SAP_REVIEW"
    PRA_REVIEW = "PRA_REVIEW"
    RTM_REVIEW = "RTM_REVIEW"
    PROTOCOL_REVIEW = "PROTOCOL_REVIEW"
    EXECUTION = "EXECUTION"
    SUMMARY_REVIEW = "SUMMARY_REVIEW"
    COMPLETE = "COMPLETE"


# Defines the only valid forward transitions — system-enforced, no reversals
STATE_TRANSITIONS: dict[ProjectState, ProjectState] = {
    ProjectState.DRAFT: ProjectState.SAP_REVIEW,
    ProjectState.SAP_REVIEW: ProjectState.PRA_REVIEW,
    ProjectState.PRA_REVIEW: ProjectState.RTM_REVIEW,
    ProjectState.RTM_REVIEW: ProjectState.PROTOCOL_REVIEW,
    ProjectState.PROTOCOL_REVIEW: ProjectState.EXECUTION,
    ProjectState.EXECUTION: ProjectState.SUMMARY_REVIEW,
    ProjectState.SUMMARY_REVIEW: ProjectState.COMPLETE,
}


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: f"PROJ-{uuid.uuid4().hex[:8].upper()}")
    name: Mapped[str] = mapped_column(String, nullable=False)
    industry: Mapped[str] = mapped_column(String, nullable=False, default="Life Sciences")
    system_type: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False, default=ProjectState.DRAFT)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def advance_state(self) -> None:
        current = ProjectState(self.state)
        next_state = STATE_TRANSITIONS.get(current)
        if next_state is None:
            raise ValueError(f"Project is already in terminal state: {self.state}")
        self.state = next_state

    def is_editable(self) -> bool:
        return self.state == ProjectState.DRAFT
