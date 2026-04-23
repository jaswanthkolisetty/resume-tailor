"""Reassemble a Resume model back into a LaTeX string."""

import re

from models.resume import Resume, Section, SectionKind


def _replace_bullet_blocks(raw: str, all_bullets: list[list[str]]) -> str:
    """Swap each \\resumeItemListStart...End block with bullets from the model."""
    idx = 0

    def replacer(m: re.Match) -> str:
        nonlocal idx
        if idx >= len(all_bullets):
            return m.group(0)
        lines = "\n".join(f"    \\resumeItem{{{b}}}" for b in all_bullets[idx])
        idx += 1
        return f"\\resumeItemListStart\n{lines}\n  \\resumeItemListEnd"

    return re.sub(
        r"\\resumeItemListStart.*?\\resumeItemListEnd",
        replacer,
        raw,
        flags=re.DOTALL,
    )


def _bullets_per_entry(section: Section) -> list[list[str]]:
    if section.kind == SectionKind.EXPERIENCE:
        return [e.bullets for e in section.experience_entries]
    if section.kind == SectionKind.PROJECTS:
        return [e.bullets for e in section.project_entries]
    if section.kind == SectionKind.EDUCATION:
        return [e.bullets for e in section.education_entries]
    return []


def _rebuild_skills(section: Section) -> str:
    skill_lines = "\n".join(
        f"\\textbf{{{cat.category}:}} {', '.join(cat.items)} \\\\"
        for cat in section.skill_categories
    )
    return f"\\section{{{section.title}}}\n\\small{{\n{skill_lines}\n}}\n"


def _rebuild_section(section: Section) -> str:
    if section.kind == SectionKind.CUSTOM:
        return section.raw_latex
    if section.kind == SectionKind.SKILLS:
        return _rebuild_skills(section)
    return _replace_bullet_blocks(section.raw_latex, _bullets_per_entry(section))


def assemble(resume: Resume) -> str:
    """Reassemble a Resume model into a LaTeX string."""
    parts: list[str] = [
        resume.preamble,
        r"\begin{document}",
        resume.header_latex,
    ]
    for section in resume.sections:
        parts.append(_rebuild_section(section))
    parts.append(resume.postamble)
    return "".join(parts)
