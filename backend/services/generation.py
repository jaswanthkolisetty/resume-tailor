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
    "You are a world-class resume writer who specialises in making senior engineers look like the "
    "perfect hire for their target role. You think deeply about what the company needs, then craft "
    "a resume that tells a compelling, specific, technically credible story. "
    "Follow all instructions precisely. Always use the candidate's actual companies, roles, and "
    "tech stack as anchors — never contradict stated facts."
)

_INSTRUCTIONS: dict[str, str] = {
    "experience": (
        "OUTPUT FORMAT:\n"
        "- Return ONLY bullet points, one per line, no heading, no preamble.\n"
        "- 5–8 bullets per role.\n"
        "- Each bullet: action verb + specific technology or method + quantified outcome or scale.\n"
        "- Bullets must interlock — they should together describe a coherent project or workstream. "
        "A reviewer should be able to picture exactly what was built and why it mattered.\n"
        "- Use the candidate's actual companies, roles, and tech stack as anchors.\n"
        "- Work only from what the base resume evidences. If the JD requires something the candidate "
        "has not demonstrated, do not invent coverage. Surface the gap in the critique phase instead."
    ),
    "skills": (
        "OUTPUT FORMAT:\n"
        "- Return the skills list in 'Category: item1, item2, ...' format.\n"
        "- Lead with categories most critical to this specific JD.\n"
        "- Surface the most JD-relevant items first within each category.\n"
        "- You may add skills the candidate demonstrably has based on their experience and the JD's needs.\n"
        "- Return ONLY the skills list. No bullets, no preamble, no explanation."
    ),
    "summary": (
        "OUTPUT FORMAT:\n"
        "- Write a 3–4 sentence professional paragraph (NOT a bullet list).\n"
        "- Sentence 1: who this person is and what they're exceptional at, in this domain.\n"
        "- Sentence 2–3: 2–3 specific capabilities that map directly to what this JD needs — "
        "name real technologies or methods.\n"
        "- Sentence 4: what draws them to this type of work or company mission.\n"
        "- Write it like a top candidate wrote it, not a template. Sound specific and earned.\n"
        "- Return ONLY the paragraph. No heading, no bullets, no preamble."
    ),
}


def _get_kind_instructions(section: Section) -> str | None:
    """Return prompt instructions string, or None to skip the LLM entirely."""
    title_lower = section.title.lower()
    if section.kind in (SectionKind.EXPERIENCE, SectionKind.PROJECTS):
        return _INSTRUCTIONS["experience"]
    if section.kind == SectionKind.SKILLS:
        return _INSTRUCTIONS["skills"]
    if section.kind == SectionKind.EDUCATION:
        return None  # preserve as-is
    # CUSTOM: summary gets a paragraph rewrite; everything else (certifications etc.) is preserved
    if any(w in title_lower for w in ("summary", "objective", "profile", "about")):
        return _INSTRUCTIONS["summary"]
    return None  # preserve as-is


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
    kind_instructions: str,
) -> str:
    prompt = _TMPL["section_draft"].format(
        section_title=section_title,
        section_content=section_content,
        job_title=job_title,
        company_name=company_name,
        job_description=job_description,
        kind_instructions=kind_instructions,
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
    kind_instructions: str,
) -> str:
    prompt = _TMPL["rewrite_with_feedback"].format(
        section_title=section_title,
        original_content=original_content,
        draft=draft,
        critique=critique,
        user_feedback=user_feedback or "No additional feedback.",
        job_title=job_title,
        job_description=job_description,
        kind_instructions=kind_instructions,
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
    Sections like Education and Certifications are returned as-is without LLM calls.
    """
    kind_instructions = _get_kind_instructions(section)
    content = section_to_text(section)

    if kind_instructions is None:
        # Nothing to tailor — return original content unchanged
        logger.info("Skipping LLM for section (preserve as-is): %s", section.title)
        return content, "No tailoring needed for this section type.", content

    draft = await draft_section(
        section_title=section.title,
        section_content=content,
        job_title=job_title,
        company_name=company_name,
        job_description=job_description,
        kind_instructions=kind_instructions,
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
        kind_instructions=kind_instructions,
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
