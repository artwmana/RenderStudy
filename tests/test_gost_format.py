from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.shared import Cm, Pt

from RenderStudy.gost_format import (
    apply_body_paragraph_format,
    apply_caption_format,
    apply_heading_format,
    apply_page_layout,
    apply_single_line_spacing,
)


def test_apply_page_layout():
    doc = Document()
    apply_page_layout(doc)
    section = doc.sections[0]

    assert abs(section.page_height - Cm(29.7)) < 1000
    assert abs(section.page_width - Cm(21.0)) < 1000
    assert abs(section.left_margin - Cm(3.0)) < 1000
    assert abs(section.right_margin - Cm(1.5)) < 1000
    assert abs(section.top_margin - Cm(2.0)) < 1000
    assert abs(section.bottom_margin - Cm(2.0)) < 1000


def test_apply_single_line_spacing():
    doc = Document()
    p = doc.add_paragraph()
    apply_single_line_spacing(p)

    assert p.paragraph_format.line_spacing_rule == WD_LINE_SPACING.SINGLE
    assert p.paragraph_format.line_spacing == 1.0


def test_apply_body_paragraph_format():
    doc = Document()
    p = doc.add_paragraph()
    apply_body_paragraph_format(p)

    assert p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY
    assert p.paragraph_format.space_after == Pt(0)
    assert p.paragraph_format.space_before == Pt(0)
    assert p.paragraph_format.line_spacing_rule == WD_LINE_SPACING.SINGLE
    assert p.paragraph_format.line_spacing == 1.0
    # docx converts Cm(1.25) to EMU, asserting closeness
    assert abs(p.paragraph_format.first_line_indent - Cm(1.25)) < 1000


def test_apply_heading_format_default():
    doc = Document()
    p = doc.add_paragraph("Test Heading")
    apply_heading_format(p)

    assert p.alignment == WD_ALIGN_PARAGRAPH.LEFT
    assert p.paragraph_format.space_after == Pt(0)
    assert p.paragraph_format.space_before == Pt(0)
    assert p.paragraph_format.line_spacing_rule == WD_LINE_SPACING.SINGLE
    assert p.paragraph_format.line_spacing == 1.0
    assert p.paragraph_format.page_break_before is False
    assert p.paragraph_format.left_indent == Cm(0)
    assert p.paragraph_format.right_indent == Cm(0)
    assert p.paragraph_format.first_line_indent == Cm(0)

    for run in p.runs:
        assert run.font.name == "Times New Roman"
        assert run.font.size == Pt(14)
        assert run.bold is True
        assert run.italic is False


def test_apply_heading_format_centered_and_indented():
    doc = Document()
    p = doc.add_paragraph("Test Heading")
    apply_heading_format(p, centered=True, with_indent=True)

    assert p.alignment == WD_ALIGN_PARAGRAPH.CENTER
    assert abs(p.paragraph_format.first_line_indent - Cm(1.25)) < 1000


def test_apply_caption_format_default():
    doc = Document()
    p = doc.add_paragraph("Test Caption")
    apply_caption_format(p)

    assert p.alignment == WD_ALIGN_PARAGRAPH.LEFT
    assert p.paragraph_format.space_after == Pt(0)
    assert p.paragraph_format.space_before == Pt(0)
    assert p.paragraph_format.line_spacing_rule == WD_LINE_SPACING.SINGLE
    assert p.paragraph_format.line_spacing == 1.0
    assert p.paragraph_format.first_line_indent == Cm(0)

    for run in p.runs:
        assert run.font.name == "Times New Roman"
        assert run.font.size == Pt(14)
        assert run.bold is False
        assert run.italic is False


def test_apply_caption_format_centered_with_space():
    doc = Document()
    p = doc.add_paragraph("Test Caption")
    apply_caption_format(p, centered=True, space_after=12)

    assert p.alignment == WD_ALIGN_PARAGRAPH.CENTER
    assert p.paragraph_format.space_after == Pt(12)
