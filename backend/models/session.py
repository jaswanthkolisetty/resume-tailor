"""Session and per-section state models."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from models.resume import Resume, SectionKind


class SectionStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    DRAFT_READY = "draft_ready"
    ACCEPTED = "accepted"


class SectionState(BaseModel):
    section_title: str
    kind: SectionKind
    # Plain-text snapshot of the original section content captured at session start.
    original_content: str = ""
    draft: str = ""
    critique: str = ""
    final: str = ""
    user_feedback: str = ""
    status: SectionStatus = SectionStatus.PENDING


class ReviewResult(BaseModel):
    ats_review: str = ""
    human_review: str = ""
    generated_at: datetime | None = None


class SessionStatus(str, Enum):
    ACTIVE = "active"
    REVIEWING = "reviewing"
    COMPLETE = "complete"


class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_title: str
    company_name: str
    job_description: str
    resume: Resume
    sections: dict[str, SectionState] = {}
    review: ReviewResult = Field(default_factory=ReviewResult)
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
