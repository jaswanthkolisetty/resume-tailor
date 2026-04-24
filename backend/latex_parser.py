"""Parse a LaTeX resume string into a Resume model."""

import logging
import re

from models.resume import (
    ContactInfo,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    Resume,
    Section,
    SectionKind,
    SkillCategory,
)

logger = logging.getLogger(__name__)


def _extract_braced(text: str, pos: int) -> tuple[str, int]:
    """Return (inner_content, end_pos) for balanced braces starting at `pos`."""
    if pos >= len(text) or text[pos] != "{":
        raise ValueError(f"Expected '{{' at position {pos}")
    depth = 0
    i = pos
    while i < len(text):
        if text[i] == "\\":
            i += 2  # skip escaped character (e.g. \{ \} \\)
            continue
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[pos + 1 : i], i + 1
        i += 1
    raise ValueError("Unbalanced braces in LaTeX source")


def _next_braced(text: str, pos: int) -> tuple[str, int]:
    """Skip whitespace then extract one braced argument."""
    while pos < len(text) and text[pos] in " \t\n\r":
        pos += 1
    return _extract_braced(text, pos)


def _n_braced_args(text: str, pos: int, n: int) -> tuple[list[str], int]:
    args: list[str] = []
    for _ in range(n):
        arg, pos = _next_braced(text, pos)
        args.append(arg)
    return args, pos


def _parse_contact(block: str) -> ContactInfo:
    info = ContactInfo()

    m = re.search(r"\\scshape\s+([^\}\\]+)", block)
    if m:
        info.name = m.group(1).strip()

    m = re.search(r"mailto:([^\}]+)", block)
    if m:
        info.email = m.group(1).strip()

    m = re.search(r"\((\d{3})\)\s*[\-–]?\s*(\d{3})[\-–](\d{4})", block)
    if m:
        info.phone = f"({m.group(1)}) {m.group(2)}-{m.group(3)}"

    m = re.search(r"https?://(?:www\.)?linkedin\.com/in/([^\}\s]+)", block)
    if m:
        info.linkedin = f"linkedin.com/in/{m.group(1).rstrip('/')}"

    m = re.search(r"https?://(?:www\.)?github\.com/([^\}\s]+)", block)
    if m:
        info.github = f"github.com/{m.group(1).rstrip('/')}"

    m = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s+[A-Z]{2})", block)
    if m:
        info.location = m.group(1)

    return info


_KIND_MAP: list[tuple[str, SectionKind]] = [
    ("experience", SectionKind.EXPERIENCE),
    ("work history", SectionKind.EXPERIENCE),
    ("project", SectionKind.PROJECTS),
    ("education", SectionKind.EDUCATION),
    ("skill", SectionKind.SKILLS),
    ("technical", SectionKind.SKILLS),
    ("core", SectionKind.SKILLS),
    ("competenc", SectionKind.SKILLS),
]


def _detect_kind(title: str) -> SectionKind:
    lower = title.lower()
    for keyword, kind in _KIND_MAP:
        if keyword in lower:
            return kind
    return SectionKind.CUSTOM


def _extract_bullets(block: str) -> list[str]:
    bullets: list[str] = []
    for m in re.finditer(r"\\resumeItem\s*\{", block):
        try:
            content, _ = _extract_braced(block, m.end() - 1)
            content = re.sub(r"\\textbf\{([^}]*)\}", r"\1", content)
            bullets.append(content.strip())
        except ValueError:
            logger.warning("Could not parse \\resumeItem at offset %d", m.start())
    if bullets:
        return bullets
    # Fallback: plain \item bullets (non-Jake's-Resume templates)
    for m in re.finditer(r"\\item\b\s*", block):
        start = m.end()
        end = block.find("\n", start)
        if end == -1:
            end = len(block)
        content = block[start:end].strip()
        content = re.sub(r"\\textbf\{([^}]*)\}", r"\1", content)
        content = re.sub(r"\\href\{[^}]*\}\{([^}]*)\}", r"\1", content)
        content = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", content)
        content = re.sub(r"\\[a-zA-Z&]+\s*", "", content).strip()
        if len(content) > 5:
            bullets.append(content)
    return bullets


def _split_dates(raw: str) -> tuple[str, str]:
    parts = re.split(r"\s*--\s*", raw, maxsplit=1)
    return parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""


def _bullet_region(body: str, after: int) -> list[str]:
    """Extract bullets from the entry body starting at `after`."""
    next_entry = re.search(r"\\resumeSubheading|\\resumeProjectHeading", body[after:])
    upper = after + next_entry.start() if next_entry else len(body)
    region = body[after:upper]
    # Jake's Resume style
    ls = region.find(r"\resumeItemListStart")
    le = region.find(r"\resumeItemListEnd")
    if ls != -1 and le != -1:
        return _extract_bullets(region[ls:le])
    # Standard itemize style
    ls2 = region.find(r"\begin{itemize}")
    le2 = region.find(r"\end{itemize}")
    if ls2 != -1 and le2 != -1:
        return _extract_bullets(region[ls2:le2])
    return _extract_bullets(region)


def _parse_experience_entries(body: str) -> list[ExperienceEntry]:
    entries: list[ExperienceEntry] = []
    for m in re.finditer(r"\\resumeSubheading\s*\{", body):
        try:
            args, pos = _n_braced_args(body, m.end() - 1, 4)
        except ValueError:
            continue
        company, date_range, role, location = args
        start_date, end_date = _split_dates(date_range)
        entries.append(
            ExperienceEntry(
                company=company.strip(),
                role=role.strip(),
                location=location.strip(),
                start_date=start_date,
                end_date=end_date,
                bullets=_bullet_region(body, pos),
            )
        )
    return entries


def _parse_project_entries(body: str) -> list[ProjectEntry]:
    entries: list[ProjectEntry] = []
    for m in re.finditer(r"\\resumeProjectHeading\s*\{", body):
        try:
            args, pos = _n_braced_args(body, m.end() - 1, 2)
        except ValueError:
            continue
        heading, date_range = args

        tech_m = re.search(r"\s*--\s*(.+)$|\$\|\$\s*\\emph\{([^}]+)\}", heading)
        if tech_m:
            technologies = (tech_m.group(1) or tech_m.group(2) or "").strip()
            name = heading[: tech_m.start()].strip()
        else:
            technologies, name = "", heading.strip()
        name = re.sub(r"\\textbf\{([^}]+)\}", r"\1", name).strip()

        next_m = re.search(r"\\resumeProjectHeading", body[pos:])
        upper = pos + next_m.start() if next_m else len(body)
        region = body[pos:upper]
        ls = region.find(r"\resumeItemListStart")
        le = region.find(r"\resumeItemListEnd")
        bullets = _extract_bullets(region[ls:le]) if ls != -1 and le != -1 else []

        start_date, end_date = _split_dates(date_range)
        entries.append(
            ProjectEntry(
                name=name,
                technologies=technologies,
                start_date=start_date,
                end_date=end_date,
                bullets=bullets,
            )
        )
    return entries


def _parse_education_entries(body: str) -> list[EducationEntry]:
    entries: list[EducationEntry] = []
    for m in re.finditer(r"\\resumeSubheading\s*\{", body):
        try:
            args, pos = _n_braced_args(body, m.end() - 1, 4)
        except ValueError:
            continue
        institution, date_range, degree_field, location = args

        gpa = ""
        gpa_m = re.search(r"GPA\s+([\d.]+/[\d.]+)", degree_field)
        if gpa_m:
            gpa = gpa_m.group(1)
            degree_field = degree_field[: gpa_m.start()].rstrip(", ").strip()

        next_m = re.search(r"\\resumeSubheading", body[pos:])
        upper = pos + next_m.start() if next_m else len(body)
        region = body[pos:upper]
        ls = region.find(r"\resumeItemListStart")
        le = region.find(r"\resumeItemListEnd")
        bullets = _extract_bullets(region[ls:le]) if ls != -1 and le != -1 else []

        start_date, end_date = _split_dates(date_range)
        entries.append(
            EducationEntry(
                institution=institution.strip(),
                degree=degree_field.strip(),
                location=location.strip(),
                start_date=start_date,
                end_date=end_date,
                gpa=gpa,
                bullets=bullets,
            )
        )
    return entries


def _parse_skill_categories(body: str) -> list[SkillCategory]:
    categories: list[SkillCategory] = []
    for m in re.finditer(r"\\textbf\{([^}]+?):\}\s*(.+?)(?=\\\\|\n|$)", body):
        category = m.group(1).strip()
        items_raw = m.group(2).strip()
        items_raw = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", items_raw)
        items_raw = re.sub(r"\\[a-zA-Z&]+\s*", "", items_raw)
        items = [i.strip() for i in items_raw.split(",") if i.strip()]
        if category and items:
            categories.append(SkillCategory(category=category, items=items))
    return categories


def parse(tex: str) -> Resume:
    """Parse a LaTeX resume string into a Resume model."""
    doc_parts = tex.split(r"\begin{document}", 1)
    preamble = doc_parts[0]
    body = doc_parts[1] if len(doc_parts) > 1 else ""

    postamble = ""
    end_idx = body.rfind(r"\end{document}")
    if end_idx != -1:
        postamble = body[end_idx:]
        body = body[:end_idx]

    contact = ContactInfo()
    center_m = re.search(r"\\begin\{center\}(.*?)\\end\{center\}", body, re.DOTALL)
    if center_m:
        contact = _parse_contact(center_m.group(1))

    section_re = re.compile(r"\\section\*?\{([^}]+)\}")
    section_matches = list(section_re.finditer(body))

    header_latex = body[: section_matches[0].start()] if section_matches else body

    sections: list[Section] = []
    for i, match in enumerate(section_matches):
        title = match.group(1).strip()
        body_start = match.end()
        body_end = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(body)
        section_body = body[body_start:body_end]
        kind = _detect_kind(title)

        exp_entries: list[ExperienceEntry] = []
        proj_entries: list[ProjectEntry] = []
        edu_entries: list[EducationEntry] = []
        skill_cats: list[SkillCategory] = []

        if kind == SectionKind.EXPERIENCE:
            exp_entries = _parse_experience_entries(section_body)
        elif kind == SectionKind.PROJECTS:
            proj_entries = _parse_project_entries(section_body)
        elif kind == SectionKind.EDUCATION:
            edu_entries = _parse_education_entries(section_body)
        elif kind == SectionKind.SKILLS:
            skill_cats = _parse_skill_categories(section_body)

        sections.append(
            Section(
                title=title,
                kind=kind,
                raw_latex=match.group(0) + section_body,
                experience_entries=exp_entries,
                project_entries=proj_entries,
                education_entries=edu_entries,
                skill_categories=skill_cats,
            )
        )

    return Resume(
        preamble=preamble,
        header_latex=header_latex,
        contact=contact,
        sections=sections,
        postamble=postamble,
    )
