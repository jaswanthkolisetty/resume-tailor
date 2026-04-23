"""Pydantic models representing a parsed LaTeX resume."""

from enum import Enum

from pydantic import BaseModel


class SectionKind(str, Enum):
    EXPERIENCE = "experience"
    PROJECTS = "projects"
    EDUCATION = "education"
    SKILLS = "skills"
    CUSTOM = "custom"


class ContactInfo(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""


class ExperienceEntry(BaseModel):
    company: str = ""
    role: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    bullets: list[str] = []


class ProjectEntry(BaseModel):
    name: str = ""
    technologies: str = ""
    start_date: str = ""
    end_date: str = ""
    bullets: list[str] = []


class EducationEntry(BaseModel):
    institution: str = ""
    degree: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: str = ""
    bullets: list[str] = []


class SkillCategory(BaseModel):
    category: str = ""
    items: list[str] = []


class Section(BaseModel):
    title: str
    kind: SectionKind
    # Raw LaTeX for this section, used by the assembler for round-trip fidelity.
    raw_latex: str
    experience_entries: list[ExperienceEntry] = []
    project_entries: list[ProjectEntry] = []
    education_entries: list[EducationEntry] = []
    skill_categories: list[SkillCategory] = []


class Resume(BaseModel):
    # Everything before \begin{document}, preserved verbatim.
    preamble: str = ""
    contact: ContactInfo = ContactInfo()
    sections: list[Section] = []
    # Anything after the last section up to \end{document}.
    postamble: str = ""
