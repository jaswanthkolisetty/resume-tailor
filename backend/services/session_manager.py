"""In-memory session store."""

import logging
from datetime import datetime, timezone

from models.resume import Resume
from models.session import ReviewResult, SectionState, Session, SessionStatus
from services.generation import section_to_text

logger = logging.getLogger(__name__)


class SessionNotFoundError(KeyError):
    pass


class SessionManager:
    def __init__(self) -> None:
        self._store: dict[str, Session] = {}

    def create(
        self,
        resume: Resume,
        job_title: str,
        company_name: str,
        job_description: str,
    ) -> Session:
        sections = {
            s.title: SectionState(
                section_title=s.title,
                kind=s.kind,
                original_content=section_to_text(s),
            )
            for s in resume.sections
        }
        session = Session(
            job_title=job_title,
            company_name=company_name,
            job_description=job_description,
            resume=resume,
            sections=sections,
        )
        self._store[session.id] = session
        logger.info("Created session %s (%d sections)", session.id, len(sections))
        return session

    def get(self, session_id: str) -> Session:
        try:
            return self._store[session_id]
        except KeyError:
            raise SessionNotFoundError(f"Session not found: {session_id}")

    def save(self, session: Session) -> None:
        session.updated_at = datetime.now(timezone.utc)
        self._store[session.id] = session

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)
        logger.info("Deleted session %s", session_id)

    def list_ids(self) -> list[str]:
        return list(self._store.keys())

    def update_review(self, session_id: str, ats: str = "", human: str = "") -> Session:
        session = self.get(session_id)
        session.review = ReviewResult(
            ats_review=ats,
            human_review=human,
            generated_at=datetime.now(timezone.utc),
        )
        session.status = SessionStatus.REVIEWING
        self.save(session)
        return session


# Module-level singleton used by route handlers.
session_manager = SessionManager()
