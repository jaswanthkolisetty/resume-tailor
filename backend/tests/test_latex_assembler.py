"""Round-trip tests for latex_assembler.assemble()."""

from pathlib import Path

import pytest

from latex_assembler import assemble
from latex_parser import parse
from models.resume import Resume

FIXTURE = Path(__file__).parent / "fixtures" / "sample_resume.tex"


@pytest.fixture(scope="module")
def original() -> Resume:
    return parse(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def roundtripped(original: Resume) -> Resume:
    return parse(assemble(original))


# ─── Structural round-trip ────────────────────────────────────────────────────


def test_roundtrip_section_count(original: Resume, roundtripped: Resume) -> None:
    assert len(roundtripped.sections) == len(original.sections)


def test_roundtrip_section_titles(original: Resume, roundtripped: Resume) -> None:
    assert [s.title for s in roundtripped.sections] == [s.title for s in original.sections]


def test_roundtrip_section_kinds(original: Resume, roundtripped: Resume) -> None:
    assert [s.kind for s in roundtripped.sections] == [s.kind for s in original.sections]


# ─── Contact round-trip ───────────────────────────────────────────────────────


def test_roundtrip_contact_name(original: Resume, roundtripped: Resume) -> None:
    assert roundtripped.contact.name == original.contact.name


def test_roundtrip_contact_email(original: Resume, roundtripped: Resume) -> None:
    assert roundtripped.contact.email == original.contact.email


def test_roundtrip_contact_phone(original: Resume, roundtripped: Resume) -> None:
    assert roundtripped.contact.phone == original.contact.phone


def test_roundtrip_contact_location(original: Resume, roundtripped: Resume) -> None:
    assert roundtripped.contact.location == original.contact.location


# ─── Experience round-trip ────────────────────────────────────────────────────


def test_roundtrip_experience_count(original: Resume, roundtripped: Resume) -> None:
    orig = next(s for s in original.sections if s.title == "Professional Experience")
    rt = next(s for s in roundtripped.sections if s.title == "Professional Experience")
    assert len(rt.experience_entries) == len(orig.experience_entries)


def test_roundtrip_experience_companies(original: Resume, roundtripped: Resume) -> None:
    orig = next(s for s in original.sections if s.title == "Professional Experience")
    rt = next(s for s in roundtripped.sections if s.title == "Professional Experience")
    assert [e.company for e in rt.experience_entries] == [e.company for e in orig.experience_entries]


def test_roundtrip_experience_bullets_preserved(original: Resume, roundtripped: Resume) -> None:
    orig = next(s for s in original.sections if s.title == "Professional Experience")
    rt = next(s for s in roundtripped.sections if s.title == "Professional Experience")
    for orig_entry, rt_entry in zip(orig.experience_entries, rt.experience_entries):
        assert rt_entry.bullets == orig_entry.bullets


def test_roundtrip_modified_bullet(original: Resume) -> None:
    """Assembling with a changed bullet should produce updated LaTeX."""
    import copy
    modified = copy.deepcopy(original)
    exp_section = next(s for s in modified.sections if s.title == "Professional Experience")
    exp_section.experience_entries[0].bullets[0] = "MODIFIED BULLET TEXT"

    tex = assemble(modified)
    assert "MODIFIED BULLET TEXT" in tex

    reparsed = parse(tex)
    rt_section = next(s for s in reparsed.sections if s.title == "Professional Experience")
    assert rt_section.experience_entries[0].bullets[0] == "MODIFIED BULLET TEXT"


# ─── Education round-trip ─────────────────────────────────────────────────────


def test_roundtrip_education_institution(original: Resume, roundtripped: Resume) -> None:
    orig = next(s for s in original.sections if s.title == "Education")
    rt = next(s for s in roundtripped.sections if s.title == "Education")
    assert rt.education_entries[0].institution == orig.education_entries[0].institution


def test_roundtrip_education_gpa(original: Resume, roundtripped: Resume) -> None:
    orig = next(s for s in original.sections if s.title == "Education")
    rt = next(s for s in roundtripped.sections if s.title == "Education")
    assert rt.education_entries[0].gpa == orig.education_entries[0].gpa


# ─── Projects round-trip ──────────────────────────────────────────────────────


def test_roundtrip_project_count(original: Resume, roundtripped: Resume) -> None:
    orig = next(s for s in original.sections if s.title == "Selected Projects")
    rt = next(s for s in roundtripped.sections if s.title == "Selected Projects")
    assert len(rt.project_entries) == len(orig.project_entries)


def test_roundtrip_project_bullets(original: Resume, roundtripped: Resume) -> None:
    orig = next(s for s in original.sections if s.title == "Selected Projects")
    rt = next(s for s in roundtripped.sections if s.title == "Selected Projects")
    for orig_entry, rt_entry in zip(orig.project_entries, rt.project_entries):
        assert rt_entry.bullets == orig_entry.bullets


# ─── Skills round-trip ────────────────────────────────────────────────────────


def test_roundtrip_skill_category_count(original: Resume, roundtripped: Resume) -> None:
    orig = next(s for s in original.sections if s.title == "Core Skills")
    rt = next(s for s in roundtripped.sections if s.title == "Core Skills")
    assert len(rt.skill_categories) == len(orig.skill_categories)


def test_roundtrip_skill_items(original: Resume, roundtripped: Resume) -> None:
    orig = next(s for s in original.sections if s.title == "Core Skills")
    rt = next(s for s in roundtripped.sections if s.title == "Core Skills")
    for orig_cat, rt_cat in zip(orig.skill_categories, rt.skill_categories):
        assert rt_cat.category == orig_cat.category
        assert rt_cat.items == orig_cat.items


# ─── Document structure ───────────────────────────────────────────────────────


def test_assembled_has_begin_document(original: Resume) -> None:
    assert r"\begin{document}" in assemble(original)


def test_assembled_has_end_document(original: Resume) -> None:
    assert r"\end{document}" in assemble(original)


def test_assembled_has_documentclass(original: Resume) -> None:
    assert r"\documentclass" in assemble(original)
