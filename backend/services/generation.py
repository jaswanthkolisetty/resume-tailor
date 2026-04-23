"""Orchestrates the LLM generation loop: draft → self-critique → rewrite."""

import logging
import re
from pathlib import Path

from models.resume import Section, SectionKind
from services.ollama import ollama

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


_TMPL: dict[str, str] = {
    "section_draft": _load("section_draft.txt"),
    "self_critique": _load("self_critique.txt"),
    "rewrite_with_feedback": _load("rewrite_with_feedback.txt"),
    "ats_review": _load("ats_review.txt"),
    "human_review": _load("human_review.txt"),
}

_SYSTEM = (
    "You are an expert resume writer and career coach. "
    "Follow instructions precisely. Never fabricate facts or metrics."
)


# ─── Section → plain text ─────────────────────────────────────────────────────


def section_to_text(section: Section) -> str:
    """Render a section's structured data as plain text for LLM input."""
    lines: list[str] = []

    if section.kind == SectionKind.EXPERIENCE:
        for e in section.experience_entries:
            lines.append(f"{e.role} at {e.company} | {e.location} | {e.start_date} – {e.end_date}")
            for b in e.bullets:
                lines.append(f"- {b}")

    elif section.kind == SectionKind.PROJECTS:
        for e in section.project_entries:
            header = e.name
            if e.technologies:
                header += f" | {e.technologies}"
            lines.append(header)
            for b in e.bullets:
                lines.append(f"- {b}")

    elif section.kind == SectionKind.EDUCATION:
        for e in section.education_entries:
            lines.append(f"{e.degree} | {e.institution} | {e.start_date} – {e.end_date}")
            if e.gpa:
                lines.append(f"  GPA: {e.gpa}")
            for b in e.bullets:
                lines.append(f"- {b}")

    elif section.kind == SectionKind.SKILLS:
        for cat in section.skill_categories:
            lines.append(f"{cat.category}: {', '.join(cat.items)}")

    else:
        # CUSTOM — strip basic LaTeX markup for readability
        stripped = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", section.raw_latex)
        stripped = re.sub(r"\\[a-zA-Z]+", " ", stripped).strip()
        lines.append(stripped)

    return "\n".join(lines)


# ─── Individual generation steps ─────────────────────────────────────────────


async def draft_section(
    section_title: str,
    section_content: str,
    job_title: str,
    company_name: str,
    job_description: str,
) -> str:
    prompt = _TMPL["section_draft"].format(
        section_title=section_title,
        section_content=section_content,
        job_title=job_title,
        company_name=company_name,
        job_description=job_description,
    )
    logger.info("Drafting section: %s", section_title)
    return await ollama.generate(prompt, system=_SYSTEM)


async def critique_section(
    section_title: str,
    section_draft: str,
    job_title: str,
    job_description: str,
) -> str:
    prompt = _TMPL["self_critique"].format(
        section_title=section_title,
        section_draft=section_draft,
        job_title=job_title,
        job_description=job_description,
    )
    logger.info("Critiquing section: %s", section_title)
    return await ollama.generate(prompt, system=_SYSTEM)


async def rewrite_section(
    section_title: str,
    original_content: str,
    draft: str,
    critique: str,
    user_feedback: str,
    job_title: str,
    job_description: str,
) -> str:
    prompt = _TMPL["rewrite_with_feedback"].format(
        section_title=section_title,
        original_content=original_content,
        draft=draft,
        critique=critique,
        user_feedback=user_feedback or "No additional feedback.",
        job_title=job_title,
        job_description=job_description,
    )
    logger.info("Rewriting section: %s", section_title)
    return await ollama.generate(prompt, system=_SYSTEM)


# ─── Full section loop ────────────────────────────────────────────────────────


async def run_section_loop(
    section: Section,
    job_title: str,
    company_name: str,
    job_description: str,
    user_feedback: str = "",
) -> tuple[str, str, str]:
    """Run draft → critique → rewrite for a section.

    Returns (draft, critique, final_rewrite) as plain-text strings.
    """
    content = section_to_text(section)

    draft = await draft_section(
        section_title=section.title,
        section_content=content,
        job_title=job_title,
        company_name=company_name,
        job_description=job_description,
    )
    critique = await critique_section(
        section_title=section.title,
        section_draft=draft,
        job_title=job_title,
        job_description=job_description,
    )
    final = await rewrite_section(
        section_title=section.title,
        original_content=content,
        draft=draft,
        critique=critique,
        user_feedback=user_feedback,
        job_title=job_title,
        job_description=job_description,
    )
    return draft, critique, final


# ─── Review passes ────────────────────────────────────────────────────────────


async def run_ats_review(
    resume_text: str,
    job_title: str,
    job_description: str,
) -> str:
    prompt = _TMPL["ats_review"].format(
        resume_text=resume_text,
        job_title=job_title,
        job_description=job_description,
    )
    logger.info("Running ATS review")
    return await ollama.generate(prompt, system=_SYSTEM)


async def run_human_review(
    resume_text: str,
    job_title: str,
    company_name: str,
    job_description: str,
) -> str:
    prompt = _TMPL["human_review"].format(
        resume_text=resume_text,
        job_title=job_title,
        company_name=company_name,
        job_description=job_description,
    )
    logger.info("Running human review")
    return await ollama.generate(prompt, system=_SYSTEM)
