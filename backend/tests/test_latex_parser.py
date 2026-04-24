"""Unit tests for latex_parser.parse()."""

from pathlib import Path

import pytest

from latex_parser import parse
from models.resume import Resume, SectionKind

FIXTURE = Path(__file__).parent / "fixtures" / "sample_resume.tex"


@pytest.fixture(scope="module")
def resume() -> Resume:
    return parse(FIXTURE.read_text(encoding="utf-8"))


def test_preamble_captured(resume: Resume) -> None:
    assert r"\documentclass" in resume.preamble


def test_postamble_captured(resume: Resume) -> None:
    assert r"\end{document}" in resume.postamble


def test_section_count(resume: Resume) -> None:
    assert len(resume.sections) == 6


def test_section_titles(resume: Resume) -> None:
    titles = [s.title for s in resume.sections]
    assert "Professional Experience" in titles
    assert "Education" in titles
    assert "Selected Projects" in titles
    assert "Core Skills" in titles


def test_contact_name(resume: Resume) -> None:
    assert resume.contact.name == "JASWANTH KOLISETTY"


def test_contact_email(resume: Resume) -> None:
    assert resume.contact.email == "jaswanthkolisetty@gmail.com"


def test_contact_phone(resume: Resume) -> None:
    assert resume.contact.phone == "(551) 375-6656"


def test_contact_linkedin(resume: Resume) -> None:
    assert "jaswanthkolisetty" in resume.contact.linkedin


def test_contact_github(resume: Resume) -> None:
    assert "jaswanthkolisetty" in resume.contact.github


def test_contact_location(resume: Resume) -> None:
    assert resume.contact.location == "Frisco, TX"


def test_experience_kind(resume: Resume) -> None:
    section = next(s for s in resume.sections if s.title == "Professional Experience")
    assert section.kind == SectionKind.EXPERIENCE


def test_education_kind(resume: Resume) -> None:
    section = next(s for s in resume.sections if s.title == "Education")
    assert section.kind == SectionKind.EDUCATION


def test_projects_kind(resume: Resume) -> None:
    section = next(s for s in resume.sections if s.title == "Selected Projects")
    assert section.kind == SectionKind.PROJECTS


def test_skills_kind(resume: Resume) -> None:
    section = next(s for s in resume.sections if s.title == "Core Skills")
    assert section.kind == SectionKind.SKILLS


@pytest.fixture(scope="module")
def experience(resume: Resume):
    return next(s for s in resume.sections if s.title == "Professional Experience")


def test_experience_entry_count(experience) -> None:
    assert len(experience.experience_entries) == 4


def test_first_experience_company(experience) -> None:
    assert experience.experience_entries[0].company == "JSP IT Services LLC"


def test_first_experience_role(experience) -> None:
    assert experience.experience_entries[0].role == "AI Platform Engineer"


def test_first_experience_location(experience) -> None:
    assert experience.experience_entries[0].location == "Mountain View, CA"


def test_first_experience_dates(experience) -> None:
    entry = experience.experience_entries[0]
    assert entry.start_date == "Aug 2025"
    assert entry.end_date == "Present"


def test_first_experience_bullet_count(experience) -> None:
    assert len(experience.experience_entries[0].bullets) == 9


def test_first_experience_bullet_content(experience) -> None:
    bullets = experience.experience_entries[0].bullets
    assert any("RAG" in b for b in bullets)


@pytest.fixture(scope="module")
def education(resume: Resume):
    return next(s for s in resume.sections if s.title == "Education")


def test_education_entry_count(education) -> None:
    assert len(education.education_entries) == 1


def test_education_institution(education) -> None:
    assert education.education_entries[0].institution == "Stevens Institute of Technology"


def test_education_degree(education) -> None:
    assert "Master of Science" in education.education_entries[0].degree


def test_education_gpa(education) -> None:
    assert education.education_entries[0].gpa == "3.9/4.0"


def test_education_dates(education) -> None:
    entry = education.education_entries[0]
    assert entry.start_date == "Aug 2023"
    assert entry.end_date == "Dec 2024"


@pytest.fixture(scope="module")
def projects(resume: Resume):
    return next(s for s in resume.sections if s.title == "Selected Projects")


def test_project_entry_count(projects) -> None:
    assert len(projects.project_entries) == 2


def test_first_project_name(projects) -> None:
    assert "Transformer" in projects.project_entries[0].name


def test_first_project_technologies(projects) -> None:
    assert "PyTorch" in projects.project_entries[0].technologies


def test_first_project_has_bullets(projects) -> None:
    assert len(projects.project_entries[0].bullets) >= 1


@pytest.fixture(scope="module")
def skills(resume: Resume):
    return next(s for s in resume.sections if s.title == "Core Skills")


def test_skill_category_count(skills) -> None:
    assert len(skills.skill_categories) >= 5


def test_languages_category(skills) -> None:
    lang = next(c for c in skills.skill_categories if c.category == "Languages")
    assert "Python" in lang.items
    assert "Go" in lang.items


def test_raw_latex_contains_section_header(resume: Resume) -> None:
    for section in resume.sections:
        assert rf"\section{{{section.title}}}" in section.raw_latex
