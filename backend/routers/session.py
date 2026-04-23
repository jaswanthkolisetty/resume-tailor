"""Session lifecycle API routes."""

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from latex_assembler import assemble
from latex_parser import parse
from models.resume import SectionKind
from models.session import SectionStatus, Session
from services.generation import run_ats_review, run_human_review, run_section_loop
from services.session_manager import SessionNotFoundError, session_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/session", tags=["session"])


# ─── Schemas ──────────────────────────────────────────────────────────────────


class StartRequest(BaseModel):
    resume_latex: str
    job_title: str
    company_name: str
    job_description: str


class StartResponse(BaseModel):
    session_id: str
    sections: list[str]
    status: str


class SectionResponse(BaseModel):
    draft: str
    critique: str
    final: str
    status: str


class RefineRequest(BaseModel):
    user_feedback: str


class AcceptResponse(BaseModel):
    section: str
    status: str


class ReviewResponse(BaseModel):
    ats_review: str
    human_review: str


class ExportResponse(BaseModel):
    latex: str


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _get_or_404(session_id: str) -> Session:
    try:
        return session_manager.get(session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")


def _get_section_or_404(session: Session, name: str):
    state = session.sections.get(name)
    resume_section = next((s for s in session.resume.sections if s.title == name), None)
    if not state or not resume_section:
        raise HTTPException(status_code=404, detail=f"Section not found: {name}")
    return state, resume_section


def _parse_bullets(text: str) -> list[str]:
    return [
        line.lstrip("-•* ").strip()
        for line in text.splitlines()
        if line.strip() and len(line.strip()) > 2
    ]


def _redistribute(bullets: list[str], all_entries: list[list[str]]) -> None:
    """Spread bullets across entries proportional to their original counts."""
    if not all_entries or not bullets:
        return
    total = sum(len(b) for b in all_entries)
    start = 0
    for i, entry in enumerate(all_entries):
        orig = len(entry)
        take = max(1, round(len(bullets) * orig / total)) if total else 1
        if i == len(all_entries) - 1:
            entry[:] = bullets[start:]
        else:
            entry[:] = bullets[start : start + take]
            start += take


def _apply_final(session: Session, section_name: str) -> None:
    """Write accepted bullet text back into the resume section entries."""
    state = session.sections[section_name]
    bullets = _parse_bullets(state.final or state.draft)
    sec = next(s for s in session.resume.sections if s.title == section_name)

    if sec.kind == SectionKind.EXPERIENCE and sec.experience_entries:
        _redistribute(bullets, [e.bullets for e in sec.experience_entries])
    elif sec.kind == SectionKind.PROJECTS and sec.project_entries:
        _redistribute(bullets, [e.bullets for e in sec.project_entries])
    elif sec.kind == SectionKind.EDUCATION and sec.education_entries:
        _redistribute(bullets, [e.bullets for e in sec.education_entries])
    # SKILLS / CUSTOM: raw_latex is preserved as-is


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/start", response_model=StartResponse)
def start_session(body: StartRequest) -> StartResponse:
    try:
        resume = parse(body.resume_latex)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"LaTeX parse error: {exc}")

    session = session_manager.create(
        resume=resume,
        job_title=body.job_title,
        company_name=body.company_name,
        job_description=body.job_description,
    )
    return StartResponse(
        session_id=session.id,
        sections=list(session.sections.keys()),
        status=session.status.value,
    )


@router.post("/{session_id}/section/{section_name}/generate", response_model=SectionResponse)
async def generate_section(session_id: str, section_name: str) -> SectionResponse:
    session = _get_or_404(session_id)
    state, resume_section = _get_section_or_404(session, section_name)

    state.status = SectionStatus.GENERATING
    session_manager.save(session)

    draft, critique, final = await run_section_loop(
        section=resume_section,
        job_title=session.job_title,
        company_name=session.company_name,
        job_description=session.job_description,
        user_feedback=state.user_feedback,
    )

    state.draft, state.critique, state.final = draft, critique, final
    state.status = SectionStatus.DRAFT_READY
    session_manager.save(session)

    return SectionResponse(draft=draft, critique=critique, final=final, status=state.status.value)


@router.post("/{session_id}/section/{section_name}/refine", response_model=SectionResponse)
async def refine_section(session_id: str, section_name: str, body: RefineRequest) -> SectionResponse:
    session = _get_or_404(session_id)
    state, resume_section = _get_section_or_404(session, section_name)

    state.user_feedback = body.user_feedback
    state.status = SectionStatus.GENERATING
    session_manager.save(session)

    draft, critique, final = await run_section_loop(
        section=resume_section,
        job_title=session.job_title,
        company_name=session.company_name,
        job_description=session.job_description,
        user_feedback=state.user_feedback,
    )

    state.draft, state.critique, state.final = draft, critique, final
    state.status = SectionStatus.DRAFT_READY
    session_manager.save(session)

    return SectionResponse(draft=draft, critique=critique, final=final, status=state.status.value)


@router.post("/{session_id}/section/{section_name}/accept", response_model=AcceptResponse)
def accept_section(session_id: str, section_name: str) -> AcceptResponse:
    session = _get_or_404(session_id)
    state, _ = _get_section_or_404(session, section_name)

    _apply_final(session, section_name)
    state.status = SectionStatus.ACCEPTED
    session_manager.save(session)

    return AcceptResponse(section=section_name, status=state.status.value)


@router.post("/{session_id}/review", response_model=ReviewResponse)
async def review_session(session_id: str) -> ReviewResponse:
    session = _get_or_404(session_id)
    resume_text = assemble(session.resume)

    ats, human = await asyncio.gather(
        run_ats_review(resume_text, session.job_title, session.job_description),
        run_human_review(resume_text, session.job_title, session.company_name, session.job_description),
    )

    session_manager.update_review(session_id, ats=ats, human=human)
    return ReviewResponse(ats_review=ats, human_review=human)


@router.get("/{session_id}/export", response_model=ExportResponse)
def export_session(session_id: str) -> ExportResponse:
    session = _get_or_404(session_id)
    return ExportResponse(latex=assemble(session.resume))
